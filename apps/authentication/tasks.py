from .emails import auth_success_email, send_generic_email
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


def send_email_synchronously(user_email, action=None, email_type=None, subject=None, message=None, otp=None, link=None,
                             link_text=None):
    try:
        send_generic_email(
            user_email=user_email,
            email_type=email_type,
            subject=subject,
            action=action,
            message=message,
            otp=otp,
            link=link,
            link_text=link_text
        )
        logger.info(f"Synchronously sent generic email to {user_email}",
                    extra={'email_type': email_type, 'subject': subject})
        return {"status": "success", "email_type": email_type, "email": user_email}
    except Exception as e:
        logger.exception(
            f"Failed to send email synchronously",
            extra={'action': action, 'email_type': email_type, 'user_email': user_email, 'error': str(e)}
        )
        return {"status": "failure", "email_type": email_type, "email": user_email, "error": str(e)}


@shared_task(bind=True, max_retries=3)
def send_auth_success_email(self, user_email, action):
    try:
        if action not in ["login", "signup"]:
            raise ValueError("Invalid action: must be 'login' or 'signup'")

        auth_success_email(
            user_email=user_email,
            action=action
        )
        logger.info(f"Sent {action} success email to {user_email} via Celery")
        return {"status": "success", "action": action, "email": user_email}
    except Exception as e:
        logger.exception(
            f"Failed to send {action} success email via Celery",
            extra={'action': action, 'user_email': user_email, 'error': str(e)}
        )
        try:
            self.retry(exc=e, countdown=30)
        except MaxRetriesExceededError:
            logger.warning(
                f"Max retries exceeded for {action} email to {user_email}. Falling back to synchronous email sending.")
            return send_email_synchronously(user_email=user_email, action=action)


@shared_task(bind=True, max_retries=3)
def send_generic_email_task(self, user_email, email_type, subject, action, message, otp=None, link=None,
                            link_text=None):
    try:
        valid_email_types = ['otp', 'confirmation', 'reset_link']
        if email_type not in valid_email_types:
            raise ValueError(f"Invalid email_type: must be one of {valid_email_types}")

        send_generic_email(
            user_email=user_email,
            email_type=email_type,
            subject=subject,
            action=action,
            message=message,
            otp=otp,
            link=link,
            link_text=link_text
        )
        logger.info(f"Sent generic email to {user_email} via Celery",
                    extra={'email_type': email_type, 'subject': subject})
        return {"status": "success", "email_type": email_type, "email": user_email}
    except Exception as e:
        logger.exception(
            f"Failed to send generic email via Celery",
            extra={'email_type': email_type, 'user_email': user_email, 'error': str(e)}
        )
        try:
            self.retry(exc=e, countdown=30)
        except MaxRetriesExceededError:
            logger.warning(
                f"Max retries exceeded for {email_type} email to {user_email}. Falling back to synchronous email sending.")
            return send_email_synchronously(
                user_email=user_email,
                email_type=email_type,
                subject=subject,
                action=action,
                message=message,
                otp=otp,
                link=link,
                link_text=link_text
            )