import os
import logging
from django.conf import settings
from django.core.mail import send_mail
from django.template import Template, Context
from datetime import datetime

logger = logging.getLogger(__name__)

def auth_success_email(user_email, action):
    try:
        if action not in ["login", "signup"]:
            raise ValueError("Invalid action: must be 'login' or 'signup'")

        context = {
            'action': action,
            'site_url': settings.SITE_URL,
            'current_year': datetime.now().year,
        }

        html_template_path = os.path.join(settings.BASE_DIR, 'apps', 'authentication', 'emails', 'auth_success.html')
        txt_template_path = os.path.join(settings.BASE_DIR, 'apps', 'authentication', 'emails', 'auth_success.txt')

        if not os.path.exists(html_template_path):
            logger.error(f"HTML template not found at {html_template_path}")
            raise FileNotFoundError(f"HTML template not found at {html_template_path}")
        if not os.path.exists(txt_template_path):
            logger.error(f"Text template not found at {txt_template_path}")
            raise FileNotFoundError(f"Text template not found at {txt_template_path}")

        with open(html_template_path, 'r', encoding='utf-8') as f:
            html_template = Template(f.read())
        html_message = html_template.render(Context(context))

        with open(txt_template_path, 'r', encoding='utf-8') as f:
            txt_template = Template(f.read())
        plain_message = txt_template.render(Context(context))

        send_mail(
            subject=f"Shop.co - {action.capitalize()} Successful",
            message=plain_message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user_email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"HTML {action} success email sent",
                    extra={'action': action, 'user_email': user_email})
    except FileNotFoundError as e:
        logger.exception(f"Template file error: {str(e)}",
                         extra={'action': action, 'user_email': user_email})
        raise
    except Exception as e:
        logger.exception(f"Failed to send HTML {action} success email",
                         extra={'action': action, 'user_email': user_email, 'error': str(e)})
        raise

def send_generic_email(user_email, email_type, subject, action, message, otp=None, link=None, link_text=None):
    try:
        valid_email_types = [
            'otp', 'confirmation', 'reset_link'
        ]
        if email_type not in valid_email_types:
            raise ValueError(f"Invalid email_type: must be one of {valid_email_types}")

        context = {
            'subject': subject,
            'action': action,
            'message': message,
            'otp': otp,
            'link': link,
            'link_text': link_text,
            'site_url': settings.SITE_URL,
            'current_year': datetime.now().year,
        }

        html_template_path = os.path.join(settings.BASE_DIR, 'apps', 'authentication', 'emails', 'generic_email.html')
        txt_template_path = os.path.join(settings.BASE_DIR, 'apps', 'authentication', 'emails', 'generic_email.txt')

        if not os.path.exists(html_template_path):
            logger.error(f"HTML template not found at {html_template_path}")
            raise FileNotFoundError(f"HTML template not found at {html_template_path}")
        if not os.path.exists(txt_template_path):
            logger.error(f"Text template not found at {txt_template_path}")
            raise FileNotFoundError(f"Text template not found at {txt_template_path}")

        with open(html_template_path, 'r', encoding='utf-8') as f:
            html_template = Template(f.read())
        html_message = html_template.render(Context(context))

        with open(txt_template_path, 'r', encoding='utf-8') as f:
            txt_template = Template(f.read())
        plain_message = txt_template.render(Context(context))

        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user_email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"Generic email sent",
                    extra={'email_type': email_type, 'user_email': user_email, 'subject': subject})
    except FileNotFoundError as e:
        logger.exception(f"Template file error: {str(e)}",
                         extra={'email_type': email_type, 'user_email': user_email})
        raise
    except Exception as e:
        logger.exception(f"Failed to send generic email",
                         extra={'email_type': email_type, 'user_email': user_email, 'error': str(e)})
        raise