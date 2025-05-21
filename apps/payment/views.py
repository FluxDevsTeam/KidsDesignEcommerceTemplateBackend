from django.core.cache import cache
from django.views.decorators.csrf import csrf_exempt
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
from django.db import transaction, IntegrityError
from rest_framework_simplejwt.tokens import AccessToken
import hmac
import hashlib
from django.conf import settings
from .tasks import send_order_confirmation_email, is_celery_healthy, send_email_synchronously
from django.contrib.auth import get_user_model
from .delivery_date import calculate_delivery_dates
from .utils import generate_confirm_token, swagger_helper, initiate_refund
from ..products.models import Product, ProductSize
from .variables import order_route_frontend, frontend_base_route, backend_base_route, payment_failed_url, admin_email
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
                if not item.product.unlimited and item.size.quantity < item.quantity:
                    return Response({"error": f"Insufficient stock for {item.product.name}"}, status=400)

            estimated_delivery = calculate_delivery_dates(cart)
            cart.estimated_delivery = estimated_delivery
            cart.save()

            data["estimated_delivery"] = estimated_delivery
            data["num_items"] = cart.cartitem_cart.count()
            return Response(data)

        except Exception as e:
            return Response({"error": f"Could not generate payment summary. Please try again.{e}"}, status=500)


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

            # check stock availability
            for item in cart.cartitem_cart.all():
                if not item.product.unlimited and item.size.quantity < item.quantity:
                    return Response({"error": f"Insufficient stock for {item.product.name}"}, status=400)

            input_serializer = PaymentCartSerializer(cart, data=request.data, partial=True)
            if not input_serializer.is_valid():
                return Response({"error": "Invalid payment data", "details": input_serializer.errors}, status=400)
            cart.delivery_fee = calculate_delivery_fee(cart)
            cart.save()

            provider = input_serializer.validated_data.get("provider")

            output_serializer = PaymentCartSerializer(cart)
            total_amount = output_serializer.data.get("total")
            if total_amount is None or total_amount <= 0:
                return Response({"error": "Invalid payment amount", "message": "Amount must be greater than zero."}, status=400)

            token = generate_confirm_token(request.user, str(cart.id))

            if provider == "flutterwave":
                response = initiate_flutterwave_payment(token, total_amount, request.user)
            elif provider == "paystack":
                response = initiate_paystack_payment(token, total_amount, request.user)
            else:
                return Response({"error": "Invalid payment provider"}, status=400)

            return Response({"data": response.data}, status=response.status_code)

        except Exception as e:
            return Response({"error": "Payment initiation failed. Please try again."}, status=500)


class PaymentVerifyViewSet(viewsets.ViewSet):
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
            transaction_id = request.query_params.get("transaction_id") or tx_ref

            if not all([tx_ref, amount, provider, token]):
                return redirect(f"{payment_failed_url}/?data=Invalid-request-parameters")

            try:
                decoded = AccessToken(token)
                cart_id_from_token = decoded.get("cart_id")
                cart = get_object_or_404(Cart.objects.select_for_update(), id=cart_id_from_token)
                user = cart.user
            except Exception as e:
                return redirect(f"{payment_failed_url}/?data=Invalid-token-or-cart")

            existing_order = Order.objects.filter(tx_ref=tx_ref).first()
            if existing_order:
                return redirect(f"{order_route_frontend}/{existing_order.id}")

            provider_config = settings.PAYMENT_PROVIDERS[provider]
            url = provider_config["verify_url"].format(transaction_id)
            headers = {
                "Authorization": f"Bearer {provider_config['secret_key']}",
                "Content-Type": "application/json"
            }

            try:
                verification_response = requests.get(url, headers=headers, timeout=10)
                verification_response.raise_for_status()
            except requests.exceptions.RequestException as err:
                return redirect(f"{payment_failed_url}/?data=Payment-verification-failed")

            response_data = verification_response.json()
            expected_currency = settings.PAYMENT_CURRENCY
            flutterwave_transaction_id = None

            if provider == "flutterwave":
                verification_success = (
                    response_data.get("status") == "success" and
                    response_data["data"]["status"] == "successful" and
                    float(response_data["data"]["amount"]) >= float(amount) and
                    response_data["data"]["currency"] == expected_currency and
                    response_data["data"]["tx_ref"] == tx_ref
                )
                flutterwave_transaction_id = str(response_data["data"]["id"]) if verification_success else None
            else:
                verification_success = (
                    response_data.get("status") and
                    response_data["data"]["status"] == "success" and
                    (response_data["data"]["amount"] / 100) >= float(amount) and
                    response_data["data"]["currency"] == expected_currency
                )

            if not verification_success:
                return redirect(f"{payment_failed_url}/?data=Payment-verification-failed")

            serializer = PaymentCartSerializer(cart)
            server_total = serializer.data["total"]
            if abs(Decimal(str(server_total)) - Decimal(str(amount))) > Decimal("0.01"):
                return redirect(f"{payment_failed_url}/?data=Payment-amount-mismatch")

            # Check and deduct stock with lock
            cart_items = cart.cartitem_cart.select_related('size', 'product').all()
            product_size_ids = [item.size.id for item in cart_items]
            product_sizes = ProductSize.objects.filter(id__in=product_size_ids).select_for_update()

            for item in cart_items:
                product_size = next(ps for ps in product_sizes if ps.id == item.size.id)
                if not item.product.unlimited and product_size.quantity < item.quantity:
                    refund_result = initiate_refund(
                        provider=provider,
                        amount=amount,
                        user=user,
                        transaction_id=flutterwave_transaction_id if provider == "flutterwave" else transaction_id
                    )
                    if refund_result is True:
                        print("Refund initiated due to insufficient stock")
                        return redirect(f"{payment_failed_url}/?data=Insufficient-stock-Refund-initiated")
                    elif refund_result == "admin":
                        return redirect(f"{payment_failed_url}/?data=Insufficient-stock-Admin-notified")
                    else:
                        return redirect(f"{payment_failed_url}/?data=Insufficient-stock-Refund-failed-please-contact-support")

            # Deduct stock
            for item in cart_items:
                product_size = next(ps for ps in product_sizes if ps.id == item.size.id)
                if not item.product.unlimited:
                    product_size.quantity -= item.quantity
                    if product_size.quantity <= 0:
                        cache.delete_pattern("product_list:*")
                        cache.delete_pattern(f"product_detail:{product_size.product.id}")
                        cache.delete_pattern("search:*")
                        cache.delete_pattern("search_suggestions:*")
                        cache.delete_pattern("product_suggestions:*")
                        cache.delete_pattern("product_homepage:*")
                cache.delete_pattern(f"product_size_list:{product_size.product.id}:*")
                cache.delete_pattern(f"product_size_detail:{product_size.id}")
                product_size.save()

            try:
                order = Order.objects.create(
                    user=user,
                    status="PAID",
                    delivery_fee=cart.delivery_fee,
                    total_amount=server_total,
                    first_name=cart.first_name or user.first_name,
                    last_name=cart.last_name or user.last_name,
                    email=cart.email or user.email,
                    state=cart.state,
                    city=cart.city,
                    delivery_address=cart.delivery_address,
                    phone_number=cart.phone_number or user.phone_number,
                    transaction_id=flutterwave_transaction_id if provider == "flutterwave" else transaction_id,
                    tx_ref=tx_ref,
                    payment_provider=provider,
                    estimated_delivery=cart.estimated_delivery
                )
            except IntegrityError:
                existing_order = Order.objects.filter(tx_ref=tx_ref).first()
                if existing_order:
                    return redirect(f"{order_route_frontend}/{existing_order.id}")
                raise

            for item in cart.cartitem_cart.all():
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    name=item.product.name,
                    description=item.product.description,
                    colour=item.product.colour,
                    image1=item.product.image1,
                    price=item.size.price,
                    size=item.size.size
                )

            cart.cartitem_cart.all().delete()
            cache.delete_pattern(f"cart_item_list:{user.id}:*")
            cache.delete_pattern(f"cart_item_detail:{user.id}:{cart.id}")
            cache.delete_pattern(f"cart_list:{user.id}:*")

            if not is_celery_healthy():
                send_email_synchronously(
                    order_id=str(order.id),
                    user=user,
                    total_amount=str(order.total_amount),
                    order_date=now().date(),
                    estimated_delivery=order.estimated_delivery,
                    admin_email=admin_email
                )
            else:
                send_order_confirmation_email.apply_async(
                    kwargs={
                        'order_id': str(order.id),
                        'user_email': order.email,
                        'total_amount': str(order.total_amount),
                        'order_date': now().date(),
                        'estimated_delivery': order.estimated_delivery,
                        'admin_email': admin_email,
                        'user_id': user.id
                    }
                )

            return redirect(f"{order_route_frontend}/{order.id}")

        except Exception as e:
            return redirect(f"{payment_failed_url}/?data=Order-processing-failed-Please-contact-support")


class PaymentWebhookViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    @swagger_helper("Payment", "Payment Webhook")
    @transaction.atomic
    @action(detail=False, methods=["POST"])
    @csrf_exempt
    def create(self, request):
        try:
            if "HTTP_VERIF_HASH" in request.META:
                provider = "flutterwave"
                signature = request.META["HTTP_VERIF_HASH"]
                secret_hash = settings.PAYMENT_PROVIDERS["flutterwave"]["secret_hash"]
                if signature != secret_hash:
                    return Response({"error": "Invalid signature"}, status=401)
            elif "HTTP_X_PAYSTACK_SIGNATURE" in request.META:
                provider = "paystack"
                signature = request.META["HTTP_X_PAYSTACK_SIGNATURE"]
                secret_key = settings.PAYMENT_PROVIDERS["paystack"]["secret_key"]
                expected_signature = hmac.new(secret_key.encode(), request.body, hashlib.sha512).hexdigest()
                if not hmac.compare_digest(signature, expected_signature):
                    return Response({"error": "Invalid signature"}, status=403)
            else:
                payload = request.data
                if payload.get("event", "").startswith("charge") and "flw_ref" in payload.get("data", {}):
                    print("Detected Flutterwave payload, proceeding without signature (debug mode)")
                    provider = "flutterwave"
                else:
                    return Response({"error": "Unknown provider"}, status=400)

            payload = request.data

            if provider == "flutterwave":
                if payload.get("event") != "charge.completed":
                    return Response({"message": "Event ignored"}, status=200)
                data = payload.get("data", {})
                tx_ref = data.get("tx_ref")
                transaction_id = str(data.get("id"))
                status = data.get("status") == "successful"
                amount = float(data.get("amount", 0))
                email = data.get("customer", {}).get("email")
                currency = data.get("currency")
            else:
                if payload.get("event") != "charge.success":
                    return Response({"message": "Event ignored"}, status=200)
                data = payload.get("data", {})
                tx_ref = data.get("reference")
                transaction_id = tx_ref
                status = data.get("status") == "success"
                amount = float(data.get("amount", 0)) / 100
                email = data.get("customer", {}).get("email")
                currency = data.get("currency")

            if not all([tx_ref, amount, email]):
                return Response({"error": "Missing transaction reference, amount, or email"}, status=400)
            existing_order = Order.objects.filter(tx_ref=tx_ref).first()
            if existing_order:
                return Response({"message": "Transaction already processed"}, status=200)

            if not status:
                return Response({"message": "Payment not successful"}, status=200)

            if currency != settings.PAYMENT_CURRENCY:
                return Response({"error": "Currency not supported"}, status=400)

            user = User.objects.filter(email=email).first()
            if not user:
                return Response({"error": "User not found"}, status=400)
            cart = Cart.objects.filter(user=user).select_for_update().first()
            if not cart:
                return Response({"error": "Cart not found"}, status=400)

            provider_config = settings.PAYMENT_PROVIDERS[provider]
            url = provider_config["verify_url"].format(transaction_id)
            headers = {
                "Authorization": f"Bearer {provider_config['secret_key']}",
                "Content-Type": "application/json"
            }

            try:
                verification_response = requests.get(url, headers=headers, timeout=10)
                verification_response.raise_for_status()
            except requests.exceptions.RequestException as e:
                return Response({"error": "Payment verification failed"}, status=503)

            response_data = verification_response.json()
            expected_currency = settings.PAYMENT_CURRENCY
            flutterwave_transaction_id = None

            if provider == "flutterwave":
                verification_success = (
                        response_data.get("status") == "success" and
                        response_data["data"]["status"] == "successful" and
                        float(response_data["data"]["amount"]) >= float(amount) and
                        response_data["data"]["currency"] == expected_currency and
                        response_data["data"]["tx_ref"] == tx_ref
                )
                flutterwave_transaction_id = str(response_data["data"]["id"]) if verification_success else None
            else:
                verification_success = (
                        response_data.get("status") and
                        response_data["data"]["status"] == "success" and
                        (response_data["data"]["amount"] / 100) >= float(amount) and
                        response_data["data"]["currency"] == expected_currency
                )

            if not verification_success:
                return Response({"error": "Payment verification failed"}, status=400)

            serializer = PaymentCartSerializer(cart)
            server_total = serializer.data["total"]
            if abs(Decimal(str(server_total)) - Decimal(str(amount))) > Decimal("0.01"):
                return Response({"error": "Payment amount mismatch"}, status=400)

            cart_items = cart.cartitem_cart.select_related('size', 'product').all()
            product_size_ids = [item.size.id for item in cart_items]
            product_sizes = ProductSize.objects.filter(id__in=product_size_ids).select_for_update()

            for item in cart_items:
                product_size = next(ps for ps in product_sizes if ps.id == item.size.id)
                if not item.product.unlimited and product_size.quantity < item.quantity:
                    refund_result = initiate_refund(
                        provider=provider,
                        amount=amount,
                        user=user,
                        transaction_id=flutterwave_transaction_id if provider == "flutterwave" else transaction_id
                    )
                    if refund_result is True:
                        return Response("Insufficient stock. Refund initiated", status=200)
                    elif refund_result == "admin":
                        return Response("Insufficient stock. Admin notified", status=200)
                    else:
                        return Response("Insufficient stock. Refund failed. please contact support", status=200)

            for item in cart_items:
                product_size = next(ps for ps in product_sizes if ps.id == item.size.id)
                if not item.product.unlimited:
                    product_size.quantity -= item.quantity
                    if product_size.quantity <= 0:
                        cache.delete_pattern("product_list:*")
                        cache.delete_pattern(f"product_detail:{product_size.product.id}")
                        cache.delete_pattern("search:*")
                        cache.delete_pattern("search_suggestions:*")
                        cache.delete_pattern("product_suggestions:*")
                        cache.delete_pattern("product_homepage:*")
                cache.delete_pattern(f"product_size_list:{product_size.product.id}:*")
                cache.delete_pattern(f"product_size_detail:{product_size.id}")
                product_size.save()

            try:
                order = Order.objects.create(
                    user=user,
                    status="PAID",
                    delivery_fee=cart.delivery_fee,
                    total_amount=server_total,
                    first_name=cart.first_name or user.first_name,
                    last_name=cart.last_name or user.last_name,
                    email=cart.email or user.email,
                    state=cart.state,
                    city=cart.city,
                    delivery_address=cart.delivery_address,
                    phone_number=cart.phone_number or user.phone_number,
                    transaction_id=flutterwave_transaction_id if provider == "flutterwave" else transaction_id,
                    tx_ref=tx_ref,
                    payment_provider=provider,
                    estimated_delivery=cart.estimated_delivery
                )
            except IntegrityError:
                existing_order = Order.objects.filter(tx_ref=tx_ref).first()
                if existing_order:
                    return Response({"message": "Transaction already processed"}, status=200)
                raise

            for item in cart.cartitem_cart.all():
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    name=item.product.name,
                    description=item.product.description,
                    colour=item.product.colour,
                    image1=item.product.image1,
                    price=item.size.price,
                    size=item.size.size
                )

            cart.cartitem_cart.all().delete()
            cache.delete_pattern(f"cart_item_list:{user.id}:*")
            cache.delete_pattern(f"cart_item_detail:{user.id}:{cart.id}")
            cache.delete_pattern(f"cart_list:{user.id}:*")

            if not is_celery_healthy():
                send_email_synchronously(
                    order_id=str(order.id),
                    user=user,
                    total_amount=str(order.total_amount),
                    order_date=now().date(),
                    estimated_delivery=order.estimated_delivery,
                    admin_email=admin_email
                )
            else:
                send_order_confirmation_email.apply_async(
                    kwargs={
                        'order_id': str(order.id),
                        'user_email': order.email,
                        'total_amount': str(order.total_amount),
                        'order_date': now().date(),
                        'estimated_delivery': order.estimated_delivery,
                        'admin_email': admin_email,
                        'user_id': user.id
                    }
                )

            return Response({"message": "Webhook processed"}, status=200)

        except Exception as e:
            return Response({"error": "Webhook processing failed"}, status=500)
