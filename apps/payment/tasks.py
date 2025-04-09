from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

from .serializers import PaymentCartSerializer
from ..orders.models import Order, OrderItem
from ..cart.models import Cart
from django.utils.timezone import now
from datetime import timedelta
from decimal import Decimal
from django.db import transaction
from django.db.utils import OperationalError
import logging

logger = logging.getLogger(__name__)


@shared_task
def send_order_confirmation_email(order_id, user_email, first_name, total_amount):
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
        logger.info("Email sent via Celery", extra={'order_id': order_id, 'user_email': user_email})
    except Exception as e:
        logger.exception("Failed to send email via Celery",
                         extra={'order_id': order_id, 'user_email': user_email, 'error': str(e)})


@shared_task(bind=True, max_retries=3)
def create_order_from_webhook(self, user_id, cart_id, tx_ref, provider, amount, email):
    try:
        with transaction.atomic():
            user = settings.AUTH_USER_MODEL.objects.get(id=user_id)
            cart = Cart.objects.get(id=cart_id, user=user)

            # Stock and price validation
            for item in cart.cartitem_cart.all():
                product = item.product
                if product.stock < item.quantity:
                    logger.warning("Insufficient stock in webhook task",
                                   extra={'product_id': product.id, 'user_id': user_id})
                    raise ValueError(f"Insufficient stock for {product.name}")
                if product.price != item.product.price:  # Adjust if CartItem stores price
                    logger.warning("Price changed in webhook task",
                                   extra={'product_id': product.id, 'user_id': user_id})
                    raise ValueError("Product prices have changed")

            serializer = PaymentCartSerializer(cart)
            server_total = serializer.data["total"]
            if abs(Decimal(str(server_total)) - Decimal(str(amount))) > Decimal("0.01"):
                logger.error("Webhook amount mismatch in task",
                             extra={'server_total': server_total, 'amount': amount, 'tx_ref': tx_ref})
                raise ValueError("Amount mismatch")

            order = Order.objects.create(
                user=user,
                status="Paid",
                delivery_fee=cart.delivery_fee,
                total_amount=server_total,
                first_name=cart.first_name or user.first_name,
                last_name=cart.last_name or user.last_name,
                email=cart.email or user.email,
                state=cart.state,
                city=cart.city,
                delivery_address=cart.delivery_address,
                phone_number=cart.phone_number or user.phone_number,
                # delivery_date= Null,
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
                    price=product.price
                )

            cart.cartitem_cart.all().delete()
            logger.info(f"Order {order.id} created via webhook task",
                        extra={'provider': provider, 'tx_ref': tx_ref, 'user_id': user_id})

            send_order_confirmation_email.delay(
                order_id=str(order.id),
                user_email=order.email,
                first_name=order.first_name,
                total_amount=str(order.total_amount)
            )

    except (OperationalError, ValueError) as e:
        logger.exception("Failed to create order in webhook task",
                         extra={'tx_ref': tx_ref, 'user_id': user_id, 'error': str(e)})
        try:
            self.retry(exc=e, countdown=60 * (self.request.retries + 1))  # Exponential backoff: 60s, 120s, 240s
        except self.MaxRetriesExceededError:
            logger.error("Max retries exceeded for order creation", extra={'tx_ref': tx_ref, 'user_id': user_id})
            # Optionally notify admin here
