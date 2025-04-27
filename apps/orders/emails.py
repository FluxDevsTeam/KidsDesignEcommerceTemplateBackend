import logging
import os
from django.core.mail import send_mail
from django.conf import settings
from django.template import Template, Context
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def refund_confirmation_email(order_id, user_email, first_name, total_amount, refund_date):
    try:
        context = {
            'order_id': order_id,
            'first_name': first_name,
            'total_amount': total_amount,
            'currency': settings.PAYMENT_CURRENCY,
            'site_url': settings.ORDER_URL,
            'current_year': datetime.now().year,
            'refund_date': refund_date,
        }

        html_template_path = os.path.join(BASE_DIR, 'emails', 'refund_confirmation.html')
        txt_template_path = os.path.join(BASE_DIR, 'emails', 'refund_confirmation.txt')

        with open(html_template_path, 'r', encoding='utf-8') as f:
            html_template = Template(f.read())
        html_message = html_template.render(Context(context))

        with open(txt_template_path, 'r', encoding='utf-8') as f:
            txt_template = Template(f.read())
        plain_message = txt_template.render(Context(context))

        send_mail(
            subject=f"Ecommerce App Template - Refund Confirmation",
            message=plain_message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user_email],
            html_message=html_message,
            fail_silently=False,
        )
    except Exception as e:
        pass


def manual_refund_notification_email(order_id, user_id, first_name, last_name, phone_no, transaction_id, amount,
                                     provider, reason, admin_email):
    context = {
        'order_id': order_id,
        'user_id': user_id,
        'first_name': first_name,
        'last_name': last_name,
        'phone_no': phone_no,
        'transaction_id': transaction_id,
        'amount': amount,
        'provider': provider,
        'reason': reason,
        'site_url': settings.ORDER_URL,
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


def refund_initiated_notification_email(order_id, user_id, first_name, last_name, phone_no, transaction_id, amount,
                                        provider, admin_email):
    context = {
        'order_id': order_id,
        'user_id': user_id,
        'first_name': first_name,
        'last_name': last_name,
        'phone_no': phone_no,
        'transaction_id': transaction_id,
        'amount': amount,
        'provider': provider,
        'site_url': settings.ORDER_URL,
        'current_year': datetime.now().year,
    }

    html_template_path = os.path.join(BASE_DIR, 'emails', 'refund_initiated_notification.html')
    txt_template_path = os.path.join(BASE_DIR, 'emails', 'refund_initiated_notification.txt')

    with open(html_template_path, 'r', encoding='utf-8') as f:
        html_template = Template(f.read())
    html_message = html_template.render(Context(context))

    with open(txt_template_path, 'r', encoding='utf-8') as f:
        txt_template = Template(f.read())
    plain_message = txt_template.render(Context(context))

    send_mail(
        subject=f"Ecommerce App Template - Refund Initiated",
        message=plain_message,
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[admin_email],
        html_message=html_message,
        fail_silently=False,
    )
