from .emails import order_confirmation_email, manual_refund_notification_email, user_refund_notification_email, admin_order_confirmation_email, admin_refund_notification_email
from celery import shared_task, current_app
from celery.exceptions import MaxRetriesExceededError


def is_celery_healthy():
    try:
        current_app.connection().ensure_connection(max_retries=0)
        return True
    except Exception as e:
        return False


def send_email_synchronously(order_id, user, total_amount, order_date, estimated_delivery, admin_email):
    try:
        order_confirmation_email(
            order_id=order_id,
            user=user,
            total_amount=total_amount,
            order_date=order_date,
            estimated_delivery=estimated_delivery
        )
        admin_order_confirmation_email(
            order_id=order_id,
            user=user,
            total_amount=total_amount,
            order_date=order_date,
            estimated_delivery=estimated_delivery,
            admin_email=admin_email
        )
        return {"status": "success", "order_id": order_id, "email": user.email}
    except Exception as e:
        return {"status": "failure", "order_id": order_id, "email": user.email, "error": str(e)}


def send_refund_email_synchronously(provider, amount, user, transaction_id, reason, admin_email):
    try:
        manual_refund_notification_email(
            provider=provider,
            amount=amount,
            user=user,
            transaction_id=transaction_id,
            reason=reason,
            admin_email=admin_email
        )
        return {"status": "success", "transaction_id": transaction_id, "email": admin_email}
    except Exception as e:
        return {"status": "failure", "transaction_id": transaction_id, "email": admin_email, "error": str(e)}


def send_user_refund_email_synchronously(user, amount, provider, transaction_id, currency, admin_email):
    try:
        user_refund_notification_email(
            user=user,
            amount=amount,
            provider=provider,
            transaction_id=transaction_id,
            currency=currency
        )
        admin_refund_notification_email(
            user=user,
            amount=amount,
            provider=provider,
            transaction_id=transaction_id,
            currency=currency,
            admin_email=admin_email
        )
        return {"status": "success", "transaction_id": transaction_id, "email": user.email}
    except Exception as e:
        return {"status": "failure", "transaction_id": transaction_id, "email": user.email, "error": str(e)}


@shared_task(bind=True, max_retries=3)
def send_order_confirmation_email(self, order_id, user_email, total_amount, order_date, estimated_delivery, admin_email,
                                  user_id):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.get(id=user_id)
    try:
        order_confirmation_email(
            order_id=order_id,
            user=user,
            total_amount=total_amount,
            order_date=order_date,
            estimated_delivery=estimated_delivery
        )
        admin_order_confirmation_email(
            order_id=order_id,
            user=user,
            total_amount=total_amount,
            order_date=order_date,
            estimated_delivery=estimated_delivery,
            admin_email=admin_email
        )
        return {"status": "success", "order_id": order_id, "email": user.email}
    except Exception as e:
        try:
            self.retry(exc=e, countdown=30)
        except MaxRetriesExceededError:
            return send_email_synchronously(order_id, user, total_amount, order_date, estimated_delivery, admin_email)


@shared_task(bind=True, max_retries=3)
def send_manual_refund_notification_email(self, provider, amount, user_id, transaction_id, reason, admin_email):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.get(id=user_id)
    try:
        manual_refund_notification_email(
            provider=provider,
            amount=amount,
            user=user,
            transaction_id=transaction_id,
            reason=reason,
            admin_email=admin_email
        )
        return {"status": "success", "transaction_id": transaction_id, "email": admin_email}
    except Exception as e:
        try:
            self.retry(exc=e, countdown=30)
        except MaxRetriesExceededError:
            return send_refund_email_synchronously(provider, amount, user, transaction_id, reason, admin_email)


@shared_task(bind=True, max_retries=3)
def send_user_refund_notification_email(self, user_id, amount, provider, transaction_id, currency, admin_email):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.get(id=user_id)
    try:
        user_refund_notification_email(
            user=user,
            amount=amount,
            provider=provider,
            transaction_id=transaction_id,
            currency=currency
        )
        admin_refund_notification_email(
            user=user,
            amount=amount,
            provider=provider,
            transaction_id=transaction_id,
            currency=currency,
            admin_email=admin_email
        )
        return {"status": "success", "transaction_id": transaction_id, "email": user.email}
    except Exception as e:
        try:
            self.retry(exc=e, countdown=30)
        except MaxRetriesExceededError:
            return send_user_refund_email_synchronously(user, amount, provider, transaction_id, currency, admin_email)
