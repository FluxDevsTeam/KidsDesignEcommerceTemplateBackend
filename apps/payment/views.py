from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from ..cart.models import Cart, CartItem
from .serializers import PaymentCartSerializer
from ..orders.models import Order, OrderItem
from .payments import initiate_flutterwave_payment, initiate_paystack_payment, generate_confirm_token
from django.utils.timezone import now
from datetime import timedelta
import requests
from decimal import Decimal
from rest_framework import status
import logging
from django.db import transaction
from rest_framework_simplejwt.tokens import AccessToken
import hmac
import hashlib
import json
from django.core.mail import send_mail
from django.conf import settings
from .tasks import send_order_confirmation_email, create_order_from_webhook
from celery.exceptions import OperationalError
from django.contrib.auth import get_user_model
from .delivery_date import calculate_delivery_dates

logger = logging.getLogger(__name__)

User = get_user_model()


def calculate_delivery_fee(cart):
    subtotal = sum(item.product.price * item.quantity for item in cart.cartitem_cart.all())
    return Decimal("15.00") if subtotal > 0 else Decimal("0.00")


def get_day_suffix(day):
    return "th" if 11 <= day <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")


def send_confirmation_email(order_id, user_email, first_name, total_amount):
    try:
        send_order_confirmation_email.delay(order_id, user_email, first_name, total_amount)
        logger.info("Queued email task via Celery", extra={'order_id': order_id, 'user_email': user_email})
    except (OperationalError, AttributeError) as e:
        logger.warning("Celery not configured or failed", extra={'order_id': order_id, 'error': str(e)})
        subject = f"Order Confirmation - Order #{order_id}"
        message = (
            f"Dear {first_name},\n\n"
            f"Thank you for your order! Your order (#{order_id}) has been successfully placed.\n"
            f"Total Amount: {settings.PAYMENT_CURRENCY} {total_amount}\n"
            f"We’ll notify you once your order ships.\n\n"
            f"Best regards,\nASLUXURY ORIGINALS Team"
        )
        try:
            send_mail(
                subject,
                message,
                settings.EMAIL_HOST_USER,
                [user_email],
                fail_silently=False,
            )
            logger.info("Sent email synchronously", extra={'order_id': order_id, 'user_email': user_email})
        except Exception as email_err:
            logger.exception("Failed to send email synchronously",
                             extra={'order_id': order_id, 'user_email': user_email, 'error': str(email_err)})


class PaymentSummaryViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        try:
            cart = get_object_or_404(Cart, user=request.user)
            if cart.delivery_fee is None:
                cart.delivery_fee = calculate_delivery_fee(cart)

            serializer = PaymentCartSerializer(cart)
            data = serializer.data

            # Use calculate_delivery_dates based on cart.state
            if not cart.state:
                return Response({"error": "State is required to calculate delivery date"}, status=400)
            estimated_delivery = calculate_delivery_dates(cart.state)

            cart.estimated_delivery = estimated_delivery  # Save to cart
            cart.save()

            data["estimated_delivery"] = estimated_delivery
            data["num_items"] = cart.cartitem_cart.count()
            return Response(data)
        except Exception as e:
            logger.exception("Error in payment summary", extra={'user_id': request.user.id})
            return Response({"error": "Could not generate payment summary. Please try again."}, status=500)


class PaymentInitiateViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def create(self, request):
        try:
            cart = get_object_or_404(Cart, user=request.user)

            serializer = PaymentCartSerializer(cart, data=request.data, partial=True)
            if not serializer.is_valid():
                return Response({"error": "Invalid payment data", "details": serializer.errors}, status=400)

            if cart.delivery_fee is None:
                cart.delivery_fee = calculate_delivery_fee(cart)
                cart.save()

            serializer = PaymentCartSerializer(cart)
            total_amount = serializer.data["total"]
            if total_amount is None or total_amount <= 0:
                return Response({"error": "Invalid payment amount", "message": "Amount must be greater than zero."},
                                status=400)

            email = request.user.email or cart.email
            phone_no = request.user.phone_number or cart.phone_number or ""
            if not email:
                return Response({"error": "Email address is required for payment"}, status=400)

            provider = serializer.validated_data["provider"]
            redirect_url = serializer.validated_data["redirect_url"]

            if provider == "flutterwave":
                response = initiate_flutterwave_payment(total_amount, email, request.user, redirect_url)
            elif provider == "paystack":
                response = initiate_paystack_payment(total_amount, email, request.user, redirect_url)

            if response.status_code == 200:
                token = generate_confirm_token(request.user, str(cart.id))
                response.data["confirm_token"] = token
            return response

        except Exception as e:
            logger.exception("Error initiating payment", extra={'user_id': request.user.id})
            return Response({"error": "Payment initiation failed. Please try again."}, status=500)


class PaymentSuccessViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def create(self, request):
        try:
            token = request.data.get("confirm_token")
            if not token:
                return Response({"error": "Confirmation token is required"}, status=400)

            tx_ref = request.data.get("tx_ref")
            if not tx_ref:
                return Response({"error": "Transaction reference is required"}, status=400)

            provider = request.data.get("provider", "flutterwave").lower()
            if provider not in ["flutterwave", "paystack"]:
                return Response({"error": "Invalid payment provider"}, status=400)

            amount_paid = float(request.data.get("amount", 0))
            if amount_paid <= 0:
                return Response({"error": "Invalid payment amount"}, status=400)

            try:
                decoded = AccessToken(token)
                cart_id_from_token = decoded.get("cart_id")
                cart = get_object_or_404(Cart, user=request.user)
                if str(cart.id) != cart_id_from_token:
                    return Response({"error": "Token-cart mismatch."}, status=403)
            except Exception as e:
                logger.exception("Invalid token", extra={'user_id': request.user.id})
                return Response({"error": "Invalid token."}, status=403)

            if not cart.cartitem_cart.exists():
                logger.warning("Cart is empty during payment",
                               extra={'user_id': request.user.id, 'cart_id': str(cart.id)})
                return Response({"error": "Cart is empty"}, status=400)

            for item in cart.cartitem_cart.all():
                product = item.product
                if product.stock < item.quantity:
                    logger.warning("Insufficient stock", extra={'product_id': product.id, 'user_id': request.user.id})
                    return Response({"error": f"Insufficient stock for {product.name}"}, status=400)
                if product.price != item.product.price:
                    logger.warning("Price changed", extra={'product_id': product.id, 'user_id': request.user.id})
                    return Response({"error": "Product prices have changed. Please refresh your cart."}, status=400)

            if Order.objects.filter(transaction_id=tx_ref).exists():
                logger.info(f"Duplicate transaction attempt: {tx_ref}", extra={'user_id': request.user.id})
                return Response({"message": "Order already processed.", "transaction_id": tx_ref}, status=200)

            provider_config = settings.PAYMENT_PROVIDERS[provider]
            url = provider_config["verify_url"].format(tx_ref)
            headers = {"Authorization": f"Bearer {provider_config['secret_key']}"}

            try:
                verification_response = requests.get(url, headers=headers)
                verification_response.raise_for_status()
            except requests.exceptions.RequestException as err:
                logger.error(f"{provider.capitalize()} verification failed",
                             extra={'error': str(err), 'tx_ref': tx_ref, 'user_id': request.user.id})
                return Response({"error": "Payment verification failed", "details": str(err)}, status=400)

            response_data = verification_response.json()

            if provider == "flutterwave":
                verification_success = (
                    response_data.get("status") == "success" and
                    float(response_data["data"]["amount"]) >= amount_paid and
                    response_data["data"]["currency"] == settings.PAYMENT_CURRENCY
                )
            else:  # paystack
                verification_success = (
                    response_data.get("status") and
                    response_data["data"]["status"] == "success" and
                    (response_data["data"]["amount"] / 100) >= amount_paid and
                    response_data["data"]["currency"] == settings.PAYMENT_CURRENCY
                )

            if not verification_success:
                if response_data.get("data", {}).get("currency") != settings.PAYMENT_CURRENCY:
                    logger.error("Currency mismatch", extra={'provider': provider, 'tx_ref': tx_ref,
                                                             'currency': response_data["data"]["currency"]})
                    return Response({"error": "Currency not supported"}, status=400)
                logger.error(f"{provider.capitalize()} payment verification failed",
                             extra={'response': response_data, 'tx_ref': tx_ref})
                return Response(
                    {"error": "Payment verification failed", "details": response_data.get("message", "Unknown error")},
                    status=400)

            serializer = PaymentCartSerializer(cart)
            server_total = serializer.data["total"]
            if abs(Decimal(str(server_total)) - Decimal(str(amount_paid))) > Decimal("0.01"):
                logger.error("Amount mismatch",
                             extra={'server_total': server_total, 'amount_paid': amount_paid, 'tx_ref': tx_ref})
                return Response({"error": "Payment amount mismatch",
                                 "message": "Reported amount does not match server calculation"}, status=400)

            order = Order.objects.create(
                user=request.user,
                status="Paid",
                delivery_fee=cart.delivery_fee,
                total_amount=server_total,
                first_name=cart.first_name or request.user.first_name,
                last_name=cart.last_name or request.user.last_name,
                email=cart.email or request.user.email,
                state=cart.state,
                city=cart.city,
                delivery_address=cart.delivery_address,
                phone_number=cart.phone_number or request.user.phone_number,
                delivery_date=now() + timedelta(days=4),  # Optionally sync with calculate_delivery_dates
                transaction_id=tx_ref,
                payment_provider=provider,
                estimated_delivery=cart.estimated_delivery
            )

            for item in cart.cartitem_cart.all():
                product = item.product
                product.stock -= item.quantity
                product.save()
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=item.quantity,
                    name=product.name,
                    description=product.description,
                    colour="N/A",
                    image1=product.image1,
                    price=product.price,
                    size=item.size.name  # Save size from CartItem
                )

            cart.cartitem_cart.all().delete()
            logger.info(f"Order {order.id} created successfully",
                        extra={'provider': provider, 'tx_ref': tx_ref, 'user_id': request.user.id})

            send_confirmation_email(
                order_id=str(order.id),
                user_email=order.email,
                first_name=order.first_name,
                total_amount=str(order.total_amount)
            )

            return Response(
                {
                    "message": f"{provider.capitalize()} payment successful, order created.",
                    "order_id": str(order.id),
                    "transaction_id": tx_ref
                },
                status=200
            )

        except Exception as e:
            logger.exception("Error processing payment success", extra={'user_id': request.user.id, 'tx_ref': tx_ref})
            return Response({"error": "Order processing failed", "message": "Please contact support."}, status=500)


class PaymentWebhookViewSet(viewsets.ViewSet):
    permission_classes = []

    def create(self, request):
        try:
            if "HTTP_X_FLUTTERWAVE_SIGNATURE" in request.META:
                provider = "flutterwave"
                signature = request.META["HTTP_X_FLUTTERWAVE_SIGNATURE"]
                secret_key = settings.PAYMENT_PROVIDERS["flutterwave"]["secret_key"]
                expected_signature = hmac.new(secret_key.encode(), request.body, hashlib.sha256).hexdigest()
                if not hmac.compare_digest(signature, expected_signature):
                    logger.error("Invalid Flutterwave webhook signature")
                    return Response({"error": "Invalid signature"}, status=403)
            elif "HTTP_X_PAYSTACK_SIGNATURE" in request.META:
                provider = "paystack"
                signature = request.META["HTTP_X_PAYSTACK_SIGNATURE"]
                secret_key = settings.PAYMENT_PROVIDERS["paystack"]["secret_key"]
                expected_signature = hmac.new(secret_key.encode(), request.body, hashlib.sha256).hexdigest()
                if not hmac.compare_digest(signature, expected_signature):
                    logger.error("Invalid Paystack webhook signature")
                    return Response({"error": "Invalid signature"}, status=403)
            else:
                return Response({"error": "Unknown provider"}, status=400)

            payload = request.data
            logger.info(f"Webhook received from {provider}", extra={'payload': json.dumps(payload)})

            tx_ref = payload.get("tx_ref") if provider == "flutterwave" else payload.get("data", {}).get("reference")
            if not tx_ref:
                return Response({"error": "Missing transaction reference"}, status=400)

            if Order.objects.filter(transaction_id=tx_ref).exists():
                logger.info(f"Duplicate webhook for {tx_ref}")
                return Response({"message": "Transaction already processed"}, status=200)

            provider_config = settings.PAYMENT_PROVIDERS[provider]
            url = provider_config["verify_url"].format(tx_ref)
            headers = {"Authorization": f"Bearer {provider_config['secret_key']}"}
            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()
            except requests.exceptions.RequestException as err:
                logger.error(f"{provider.capitalize()} webhook verification failed",
                             extra={'error': str(err), 'tx_ref': tx_ref})
                return Response({"error": "Payment verification failed", "details": str(err)}, status=400)

            response_data = response.json()
            if provider == "flutterwave":
                status = response_data.get("status") == "success"
                amount = float(response_data["data"]["amount"])
                email = response_data["data"]["customer"]["email"]
                currency = response_data["data"]["currency"]
            else:  # paystack
                status = response_data.get("status") and response_data["data"]["status"] == "success"
                amount = response_data["data"]["amount"] / 100
                email = response_data["data"]["customer"]["email"]
                currency = response_data["data"]["currency"]

            if not status:
                logger.info(f"Webhook payment not successful for {tx_ref}", extra={'response': response_data})
                return Response({"message": "Payment not successful"}, status=200)

            if currency != settings.PAYMENT_CURRENCY:
                logger.error("Currency mismatch in webhook",
                             extra={'provider': provider, 'tx_ref': tx_ref, 'currency': currency})
                return Response({"error": "Currency not supported"}, status=400)

            user = User.objects.filter(email=email).first()
            if not user:
                logger.error(f"No user found for email {email}", extra={'tx_ref': tx_ref})
                return Response({"error": "User not found"}, status=400)
            cart = Cart.objects.filter(user=user).first()
            if not cart:
                logger.error(f"No cart found for user {user.email}", extra={'tx_ref': tx_ref, 'user_id': user.id})
                return Response({"error": "Cart not found"}, status=400)

            # Queue order creation as a Celery task
            create_order_from_webhook.delay(
                user_id=user.id,
                cart_id=str(cart.id),
                tx_ref=tx_ref,
                provider=provider,
                amount=amount,
                email=email
            )
            logger.info(f"Order creation queued for {tx_ref}", extra={'provider': provider, 'user_id': user.id})

            return Response({"message": "Webhook received and processing started"}, status=200)

        except Exception as e:
            logger.exception("Error processing webhook", extra={'tx_ref': tx_ref})
            return Response({"error": "Webhook processing failed"}, status=500)