from celery import shared_task, current_app
from .emails import refund_confirmation_email as email_func, refund_initiated_notification_email, order_shipped_email, order_delivered_email


def is_celery_healthy():
    try:
        current_app.connection().ensure_connection(max_retries=0)
        return True
    except Exception as e:
        return False


def send_refund_initiated_email_synchronously(order_id, user_id, first_name, last_name, phone_no, transaction_id, amount, provider, admin_email):
    try:
        refund_initiated_notification_email(
            order_id=order_id,
            user_id=user_id,
            first_name=first_name,
            last_name=last_name,
            phone_no=phone_no,
            transaction_id=transaction_id,
            amount=amount,
            provider=provider,
            admin_email=admin_email
        )
        return {"status": "success", "order_id": order_id, "email": admin_email}
    except Exception as e:
        return {"status": "failure", "order_id": order_id, "email": admin_email, "error": str(e)}


def send_shipped_email_synchronously(order_id, user_email, first_name, estimated_delivery):
    try:
        order_shipped_email(
            order_id=order_id,
            user_email=user_email,
            first_name=first_name,
            estimated_delivery=estimated_delivery
        )
        return {"status": "success", "order_id": order_id, "email": user_email}
    except Exception as e:
        return {"status": "failure", "order_id": order_id, "email": user_email, "error": str(e)}


def send_delivered_email_synchronously(order_id, user_email, first_name, delivery_date):
    try:
        order_delivered_email(
            order_id=order_id,
            user_email=user_email,
            first_name=first_name,
            delivery_date=delivery_date
        )
        return {"status": "success", "order_id": order_id, "email": user_email}
    except Exception as e:
        return {"status": "failure", "order_id": order_id, "email": user_email, "error": str(e)}


@shared_task(bind=True, max_retries=3)
def refund_confirmation_email(self, order_id, user_email, first_name, total_amount, refund_date):
    try:
        email_func(order_id, user_email, first_name, total_amount, refund_date)
        return {"status": "success", "order_id": order_id, "email": user_email}
    except Exception as e:
        try:
            self.retry(exc=e, countdown=30)
        except self.MaxRetriesExceededError:
            return {"status": "failure", "order_id": order_id, "email": user_email, "error": str(e)}


@shared_task(bind=True, max_retries=3)
def send_refund_initiated_notification_email(self, order_id, user_id, first_name, last_name, phone_no, transaction_id,
                                             amount, provider, admin_email):
    try:
        refund_initiated_notification_email(
            order_id=order_id,
            user_id=user_id,
            first_name=first_name,
            last_name=last_name,
            phone_no=phone_no,
            transaction_id=transaction_id,
            amount=amount,
            provider=provider,
            admin_email=admin_email
        )
        return {"status": "success", "order_id": order_id, "email": admin_email}
    except Exception as e:
        try:
            self.retry(exc=e, countdown=30)
        except self.MaxRetriesExceededError:
            return send_refund_initiated_email_synchronously(order_id, user_id, first_name, last_name, phone_no,
                                                             transaction_id, amount, provider, admin_email)


@shared_task(bind=True, max_retries=3)
def send_order_shipped_email(self, order_id, user_email, first_name, estimated_delivery):
    try:
        order_shipped_email(
            order_id=order_id,
            user_email=user_email,
            first_name=first_name,
            estimated_delivery=estimated_delivery
        )
        return {"status": "success", "order_id": order_id, "email": user_email}
    except Exception as e:
        try:
            self.retry(exc=e, countdown=30)
        except self.MaxRetriesExceededError:
            return send_shipped_email_synchronously(order_id, user_email, first_name, estimated_delivery)


# New Celery task for delivered email
@shared_task(bind=True, max_retries=3)
def send_order_delivered_email(self, order_id, user_email, first_name, delivery_date):
    try:
        order_delivered_email(
            order_id=order_id,
            user_email=user_email,
            first_name=first_name,
            delivery_date=delivery_date
        )
        return {"status": "success", "order_id": order_id, "email": user_email}
    except Exception as e:
        try:
            self.retry(exc=e, countdown=30)
        except self.MaxRetriesExceededError:
            return send_delivered_email_synchronously(order_id, user_email, first_name, delivery_date)
