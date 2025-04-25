from celery import shared_task, current_app
from .emails import refund_confirmation_email as email_func


def is_celery_healthy():
    try:
        current_app.connection().ensure_connection(max_retries=0)
        return True
    except Exception as e:
        return False


@shared_task
def refund_confirmation_email(order_id, user_email, first_name, total_amount, refund_date):
    email_func(order_id, user_email, first_name, total_amount, refund_date)