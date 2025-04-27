from django.core.mail import mail_admins
from django.conf import settings

from .serializers import PaymentCartSerializer
from ..orders.models import Order, OrderItem
from ..cart.models import Cart
from decimal import Decimal
from django.db import transaction
from django.db.utils import OperationalError
from .emails import order_confirmation_email
from celery import shared_task, current_app
from celery.exceptions import MaxRetriesExceededError
import logging

logger = logging.getLogger(__name__)


def is_celery_healthy():
    try:
        current_app.connection().ensure_connection(max_retries=0)
        return True
    except Exception as e:
        logger.error(f"Celery broker is not healthy: {str(e)}")
        return False


def send_email_synchronously(order_id, user_email, first_name, total_amount, order_date, estimated_delivery):

    try:
        order_confirmation_email(
            order_id=order_id,
            user_email=user_email,
            first_name=first_name,
            total_amount=total_amount,
            order_date=order_date,
            estimated_delivery=estimated_delivery
        )

        logger.info(f"Synchronously sent order confirmation email for order {order_id} to {user_email}")
        return {"status": "success", "order_id": order_id, "email": user_email}
    except Exception as e:
        logger.exception(
            "Failed to send order confirmation email synchronously",
            extra={'order_id': order_id, 'user_email': user_email, 'error': str(e)}
        )
        return {"status": "failure", "order_id": order_id, "email": user_email, "error": str(e)}


@shared_task(bind=True, max_retries=3)
def send_order_confirmation_email(self, order_id, user_email, first_name, total_amount, order_date, estimated_delivery):

    try:
        order_confirmation_email(
            order_id=order_id,
            user_email=user_email,
            first_name=first_name,
            total_amount=total_amount,
            order_date=order_date,
            estimated_delivery=estimated_delivery
        )

        logger.info(f"Sent order confirmation email for order {order_id} to {user_email} via Celery")
        return {"status": "success", "order_id": order_id, "email": user_email}
    except Exception as e:
        logger.exception(
            "Failed to send order confirmation email via Celery",
            extra={'order_id': order_id, 'user_email': user_email, 'error': str(e)}
        )
        try:
            self.retry(exc=e, countdown=30)
        except MaxRetriesExceededError:
            logger.warning(f"Max retries exceeded for order {order_id}. Falling back to synchronous email sending.")
            return send_email_synchronously(order_id, user_email, first_name, total_amount)
