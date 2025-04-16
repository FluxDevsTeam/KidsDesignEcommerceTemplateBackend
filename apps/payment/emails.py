import logging
import os
from ast import literal_eval
from django.core.mail import send_mail
from django.conf import settings
from django.template import Template, Context
from datetime import datetime

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# estimated delivery is a list inside a string so to work with it literal_eval does the conversion
def format_estimated_delivery(dates):
    date = literal_eval(dates)
    if len(date) >= 2:
        return f"{date[0]} - {date[1]}"
    elif len(date) <= 1:
        return date
    return "Not available"


def order_confirmation_email(order_id, user_email, first_name, total_amount, order_date, estimated_delivery):
    try:
        formatted_delivery = format_estimated_delivery(estimated_delivery)

        context = {
            'order_id': order_id,
            'first_name': first_name,
            'total_amount': total_amount,
            'currency': settings.PAYMENT_CURRENCY,
            'site_url': settings.ORDER_URL,
            'current_year': datetime.now().year,
            'estimated_delivery': formatted_delivery,
            'order_date': order_date,
        }

        html_template_path = os.path.join(BASE_DIR, 'emails', 'order_confirmation.html')
        txt_template_path = os.path.join(BASE_DIR, 'emails', 'order_confirmation.txt')

        with open(html_template_path, 'r', encoding='utf-8') as f:
            html_template = Template(f.read())
        html_message = html_template.render(Context(context))

        with open(txt_template_path, 'r', encoding='utf-8') as f:
            txt_template = Template(f.read())
        plain_message = txt_template.render(Context(context))

        send_mail(
            subject=f"Ecommerce App Template - Order Confirmation",
            message=plain_message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user_email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info("HTML order confirmation email sent",
                    extra={'order_id': order_id, 'user_email': user_email})
    except Exception as e:
        logger.exception("Failed to send HTML order confirmation email",
                         extra={'order_id': order_id, 'user_email': user_email, 'error': str(e)})
        raise