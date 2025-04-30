import logging
import os
from django.core.mail import send_mail
from django.conf import settings
from django.template import Template, Context
from datetime import datetime
from ast import literal_eval

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def format_estimated_delivery(dates):
    date = literal_eval(dates)
    if len(date) >= 2:
        return f"{date[0]} - {date[1]}"
    elif len(date) <= 1:
        return date
    return "Not available"


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


def manual_refund_notification_email(order_id, user_id, first_name, last_name, phone_no, transaction_id, amount, provider, reason, admin_email):
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


def refund_initiated_notification_email(order_id, user_id, first_name, last_name, phone_no, transaction_id, amount, provider, admin_email):
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


def order_shipped_email(order_id, user_email, first_name, estimated_delivery):
    formatted_delivery = format_estimated_delivery(estimated_delivery)

    try:
        context = {
            'order_id': order_id,
            'first_name': first_name,
            'estimated_delivery': formatted_delivery,
            'site_url': settings.ORDER_URL,
            'current_year': datetime.now().year,
        }

        html_template_path = os.path.join(BASE_DIR, 'emails', 'order_shipped.html')
        txt_template_path = os.path.join(BASE_DIR, 'emails', 'order_shipped.txt')

        with open(html_template_path, 'r', encoding='utf-8') as f:
            html_template = Template(f.read())
        html_message = html_template.render(Context(context))

        with open(txt_template_path, 'r', encoding='utf-8') as f:
            txt_template = Template(f.read())
        plain_message = txt_template.render(Context(context))

        send_mail(
            subject=f"Ecommerce App Template - Your Order Has Been Shipped",
            message=plain_message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user_email],
            html_message=html_message,
            fail_silently=False,
        )
    except Exception as e:
        logging.error(f"Failed to send shipped email for order {order_id}: {str(e)}")


def order_delivered_email(order_id, user_email, first_name, delivery_date):
    try:
        context = {
            'order_id': order_id,
            'first_name': first_name,
            'delivery_date': delivery_date,
            'site_url': settings.ORDER_URL,
            'current_year': datetime.now().year,
        }

        html_template_path = os.path.join(BASE_DIR, 'emails', 'order_delivered.html')
        txt_template_path = os.path.join(BASE_DIR, 'emails', 'order_delivered.txt')

        with open(html_template_path, 'r', encoding='utf-8') as f:
            html_template = Template(f.read())
        html_message = html_template.render(Context(context))

        with open(txt_template_path, 'r', encoding='utf-8') as f:
            txt_template = Template(f.read())
        plain_message = txt_template.render(Context(context))

        send_mail(
            subject=f"Ecommerce App Template - Your Order Has Been Delivered",
            message=plain_message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user_email],
            html_message=html_message,
            fail_silently=False,
        )
    except Exception as e:
        logging.error(f"Failed to send delivered email for order {order_id}: {str(e)}")
