from django.core.cache import cache
from django.db.models import F, Sum
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.shortcuts import get_object_or_404, redirect
from .delivery_fee import calculate_delivery_fee
from ..cart.models import Cart
from .serializers import PaymentCartSerializer, InitiateSerializer
from ..orders.models import Order, OrderItem
from .payments import initiate_flutterwave_payment, initiate_paystack_payment
from django.utils.timezone import now
import requests
from decimal import Decimal
import logging
from django.db import transaction
from rest_framework_simplejwt.tokens import AccessToken
import hmac
import hashlib
import json
from django.conf import settings
from .tasks import send_order_confirmation_email, create_order_from_webhook, is_celery_healthy, send_email_synchronously
from django.contrib.auth import get_user_model
from .delivery_date import calculate_delivery_dates
from .utils import generate_confirm_token, swagger_helper, reverse_stock_addition
from ..products.models import Product, ProductSize

logger = logging.getLogger(__name__)

User = get_user_model()


class PaymentSummaryViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @swagger_helper("Payment", "Payment Summary")
    def list(self, request):
        try:
            cart = get_object_or_404(Cart, user=request.user)
            cart.delivery_fee = calculate_delivery_fee(cart)
            serializer = PaymentCartSerializer(cart)
            data = serializer.data

            if not cart.cartitem_cart.exists():
                return Response({"error": "Cart Is Empty"}, status=400)

            if not cart.state:
                return Response({"error": "State is required to calculate delivery date"}, status=400)

            # check for stock left
            for item in cart.cartitem_cart.all():
                if item.size.quantity < item.quantity:
                    return Response({"error": f"Insufficient stock for {item.product.name}"}, status=400)

            estimated_delivery = calculate_delivery_dates(cart.state)

            cart.estimated_delivery = estimated_delivery
            cart.save()

            data["estimated_delivery"] = estimated_delivery
            data["num_items"] = cart.cartitem_cart.count()
            return Response(data)

        except Exception as e:
            logger.exception("Error in payment summary", extra={'user_id': request.user.id})
            return Response({"error": f"Could not generate payment summary. Please try again."}, status=500)


class PaymentInitiateViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return InitiateSerializer

    @swagger_helper("Payment", "Initiate payment")
    def create(self, request):
        try:
            cart = get_object_or_404(Cart, user=request.user)
            if not cart.cartitem_cart.exists():
                return Response({"error": "Cart Is Empty"}, status=400)

            input_serializer = PaymentCartSerializer(cart, data=request.data, partial=True)
            if not input_serializer.is_valid():
                return Response(
                    {"error": "Invalid payment data", "details": input_serializer.errors},
                    status=400
                )

            with transaction.atomic():
                # this lock ProductSize rows for update. this prevents concurrent issues where there are limited stock
                cart_items = cart.cartitem_cart.select_related('size', 'product').all()
                product_sizes = ProductSize.objects.filter(id__in=[item.size.id for item in cart_items]).select_for_update()

                # Check stock availability
                for item in cart_items:
                    product_size = next(ps for ps in product_sizes if ps.id == item.size.id)
                    if product_size.quantity < item.quantity:
                        return Response({"error": f"Insufficient stock for {item.product.name}"}, status=400)

                cart.delivery_fee = calculate_delivery_fee(cart)
                cart.save()

                provider = input_serializer.validated_data.get("provider")
                redirect_url = settings.PAYMENT_SUCCESS_URL

                output_serializer = PaymentCartSerializer(cart)
                total_amount = output_serializer.data.get("total")
                if total_amount is None or total_amount <= 0:
                    return Response({"error": "Invalid payment amount", "message": "Amount must be greater than zero."}, status=400)

                token = generate_confirm_token(request.user, str(cart.id))

                # Initiate payment
                if provider == "flutterwave":
                    response = initiate_flutterwave_payment(token, total_amount, request.user)
                elif provider == "paystack":
                    response = initiate_paystack_payment(token, total_amount, request.user)
                else:
                    return Response({"error": "Invalid payment provider"}, status=400)

                # Deduct stock after payment initiation
                for item in cart_items:
                    product_size = next(ps for ps in product_sizes if ps.id == item.size.id)
                    product_size.quantity -= item.quantity
                    product_size.save()

            return Response({"data": response.data}, status=response.status_code)

        except Exception as e:
            logger.exception("Error initiating payment", extra={"user_id": request.user.id})
            return Response({"error": "Payment initiation failed. Please try again."}, status=500)


class PaymentSuccessViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    @swagger_helper("Payment", "Payment Successful")
    @transaction.atomic
    @action(detail=False, methods=["GET"])
    def confirm(self, request):
        try:
            tx_ref = request.query_params.get("tx_ref")
            amount = request.query_params.get("amount")
            provider = request.query_params.get("provider")
            token = request.query_params.get("confirm_token")
            transaction_id = request.query_params.get("transaction_id")
            amount_paid = request.query_params.get("amount")

            if not all([tx_ref, amount, provider, token, transaction_id, amount_paid]):
                logger.error("Missing required query parameters", extra={"query_params": request.query_params})
                return Response({"error": "Invalid request parameters."}, status=400)

            try:
                decoded = AccessToken(token)
                cart_id_from_token = decoded.get("cart_id")
                cart = get_object_or_404(Cart, user=request.user)
                if str(cart.id) != cart_id_from_token:
                    return Response({"error": "Token-cart mismatch."}, status=403)

            except Exception as e:
                logger.exception("Invalid token", extra={'user_id': request.user.id})
                return Response({"error": "Invalid token."}, status=403)

            if Order.objects.filter(transaction_id=tx_ref).exists():

                return Response({"message": "Order already processed.", "transaction_id": tx_ref}, status=200)

            provider_config = settings.PAYMENT_PROVIDERS[provider]

            # Use transaction_id if available and provider is flutterwave, otherwise use tx_ref
            if provider == "flutterwave" and transaction_id:
                url = "https://api.flutterwave.com/v3/transactions/{}/verify".format(transaction_id)
            else:
                url = provider_config["verify_url"].format(tx_ref)

            headers = {
                "Authorization": f"Bearer {provider_config['secret_key']}",
                "Content-Type": "application/json"
            }

            logger.debug(
                f"Verification request: provider={provider}, url={url}, headers={headers}, tx_ref={tx_ref}, transaction_id={transaction_id}"
            )

            try:
                verification_response = requests.get(url, headers=headers)
                logger.debug(
                    f"Verification response: status={verification_response.status_code}, body={verification_response.text}"
                )
                verification_response.raise_for_status()
            except requests.exceptions.RequestException as err:
                logger.error(f"{provider.capitalize()} verification failed",
                             extra={'error': str(err), 'tx_ref': tx_ref, 'user_id': request.user.id})
                return redirect(f"http://127.0.0.1:8000/api/v1/cart/{cart_id_from_token}")

            response_data = verification_response.json()
            expected_currency = settings.PAYMENT_CURRENCY
            if provider == "flutterwave":

                verification_success = (
                        response_data.get("status") == "success" and
                        response_data["data"]["status"] == "successful" and
                        float(response_data["data"]["amount"]) >= float(amount_paid) and
                        response_data["data"]["currency"] == expected_currency and
                        response_data["data"]["tx_ref"] == tx_ref
                )
            else:
                verification_success = (
                        response_data.get("status") and
                        response_data["data"]["status"] == "success" and
                        (response_data["data"]["amount"] / 100) >= float(amount_paid) and
                        response_data["data"]["currency"] == expected_currency
                )

            if not verification_success:
                if response_data.get("data", {}).get("currency") != settings.PAYMENT_CURRENCY:
                    logger.error("Currency mismatch", extra={'provider': provider, 'tx_ref': tx_ref, 'currency': response_data["data"]["currency"]})
                    return Response({"error": "Currency not supported"}, status=400)
                logger.error(f"{provider.capitalize()} payment verification failed", extra={'response': response_data, 'tx_ref': tx_ref})

                # item was removed on payment initiation. so on any failure this function adds the stock back
                # reverse_stock_addition(cart, Product)
                return redirect(f"{settings.ORDER_URL}/cart/")

            serializer = PaymentCartSerializer(cart)
            server_total = serializer.data["total"]
            if abs(Decimal(str(server_total)) - Decimal(str(amount_paid))) > Decimal("0.01"):
                return Response({"error": "Payment amount mismatch", "message": "Reported amount does not match server calculation"}, status=400)

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
                transaction_id=tx_ref,
                payment_provider=provider,
                estimated_delivery=cart.estimated_delivery
            )

            for item in cart.cartitem_cart.all():
                product = item.product
                size = item.size
                size.quantity -= item.quantity
                product.save()
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=item.quantity,
                    name=product.name,
                    description=product.description,
                    colour=product.colour,
                    image1=product.image1,
                    price=product.price,
                    size=item.size.size
                )

            cart.cartitem_cart.all().delete()
            cache.delete(f"cart_item_list:{request.user.id}:*")
            cache.delete(f"cart_item_detail:{request.user.id}:{cart.id}")
            cache.delete(f"cart_list:{request.user.id}:*")

            if not is_celery_healthy():
                logger.warning("Celery is not healthy. Sending email synchronously now.")
                send_email_synchronously(
                    order_id=str(order.id),
                    user_email=order.email,
                    first_name=order.first_name,
                    total_amount=str(order.total_amount),
                    order_date=now().date(),
                    estimated_delivery=order.estimated_delivery
                )

            else:
                send_order_confirmation_email.apply_async(
                    kwargs={
                        'order_id': str(order.id),
                        'user_email': order.email,
                        'first_name': order.first_name,
                        'total_amount': str(order.total_amount),
                        'order_date': now().date(),
                        'estimated_delivery': order.estimated_delivery
                    },
                )
            return redirect(f"{settings.ORDER_URL}{order.id}")

        except Exception as e:
            # try:
                # item was removed on payment initiation. so on any failure this function adds the stock back
                # reverse_stock_addition(cart, Product)
            # except:
            #     pass
            logger.exception("Error processing payment success", extra={'user_id': request.user.id, 'tx_ref': tx_ref})
            return Response({"error": "Order processing failed", "message": "Please contact support."}, status=500)


class PaymentWebhookViewSet(viewsets.ViewSet):
    permission_classes = []

    @swagger_helper("Payment", "Payment Webhook")
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

            if not is_celery_healthy():
                logger.warning("Celery is not healthy. Sending email synchronously now.")
                create_order_from_webhook(
                    user_id=user.id,
                    cart_id=str(cart.id),
                    tx_ref=tx_ref,
                    provider=provider,
                    amount=amount,
                    email=email
                )

            else:
                create_order_from_webhook.apply_async(
                    kwargs={
                        "user_id": user.id,
                        "cart_id": str(cart.id),
                        "tx_ref": tx_ref,
                        "provider": provider,
                        "amount": amount,
                        "email": email
                    },
                )
            logger.info(f"Order creation queued for {tx_ref}", extra={'provider': provider, 'user_id': user.id})
            return Response({"message": "Webhook received and processing started"}, status=200)

        except Exception as e:
            logger.exception("Error processing webhook", extra={'tx_ref': tx_ref})
            return Response({"error": "Webhook processing failed"}, status=500)
