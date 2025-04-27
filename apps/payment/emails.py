import logging
import os
from ast import literal_eval
from django.core.mail import send_mail
from django.conf import settings
from django.template import Template, Context
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
admin_email = settings.ADMIN_EMAIL


# estimated delivery is a list inside a string so to work with it literal_eval does the conversion
def format_estimated_delivery(dates):
    date = literal_eval(dates)
    if len(date) >= 2:
        return f"{date[0]} - {date[1]}"
    elif len(date) <= 1:
        return date
    return "Not available"


def order_confirmation_email(order_id, user_email, first_name, total_amount, order_date, estimated_delivery):

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


def manual_refund_notification_email(provider, amount, user_id, first_name, last_name, phone_no, transaction_id, reason, admin_email):
    context = {
        'provider': provider,
        'amount': amount,
        'user_id': user_id,
        'first_name': first_name,
        'last_name': last_name,
        'phone_no': phone_no or 'Not provided',
        'transaction_id': transaction_id,
        'reason': reason,
        'site_url': settings.SITE_URL,
        'current_year': datetime.now().year,
    }

    html_template_path = os.path.join(BASE_DIR, 'emails', 'manual_refund_notification.html')
    txt_template_path = os.path.join(BASE_DIR, 'emails', 'manual_refund_notification.txt')

    with open(html_template_path, 'r', encoding='utf-8') as f:
        html_template = Template(f.read())
    html_message = html_template.render(Context(context))

    with open(txt_template_path, 'r', encoding='utf-8') as f:
        txt_template = Template(f.read())
    plain_message = txt_template.render(Context(context))

    send_mail(
        subject=f"Ecommerce App Template - Manual Refund Required",
        message=plain_message,
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[admin_email],
        html_message=html_message,
        fail_silently=False,
    )


def user_refund_notification_email(user_email, first_name, amount, provider, transaction_id, currency):
    context = {
        'first_name': first_name,
        'amount': amount,
        'provider': provider,
        'transaction_id': transaction_id,
        'currency': currency,
        'site_url': settings.SITE_URL,
        'current_year': datetime.now().year,
    }

    html_template_path = os.path.join(BASE_DIR, 'emails', 'user_refund_notification.html')
    txt_template_path = os.path.join(BASE_DIR, 'emails', 'user_refund_notification.txt')

    with open(html_template_path, 'r', encoding='utf-8') as f:
        html_template = Template(f.read())
    html_message = html_template.render(Context(context))

    with open(txt_template_path, 'r', encoding='utf-8') as f:
        txt_template = Template(f.read())
    plain_message = txt_template.render(Context(context))

    send_mail(
        subject=f"Ecommerce App Template - Refund Initiated Due to Out of Stock",
        message=plain_message,
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[user_email, admin_email],
        html_message=html_message,
        fail_silently=False,
    )

