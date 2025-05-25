import logging
import os
from django.core.mail import send_mail
from django.conf import settings
from django.template import Template, Context
from datetime import datetime
from ast import literal_eval
from django.utils.functional import SimpleLazyObject
from ..ecommerce_admin.models import OrganizationSettings, DeveloperSettings

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

organization_settings = SimpleLazyObject(lambda: OrganizationSettings.objects.first())
organization = SimpleLazyObject(lambda: {
    'support_phone_number': getattr(organization_settings, 'phone_number', None),
    'support_email': getattr(organization_settings, 'customer_support_email', None),
    'admin_email': getattr(organization_settings, 'admin_email', None),
    'brand_logo': getattr(organization_settings, 'brand_logo', None),
    'facebook': getattr(organization_settings, 'facebook', None),
    'instagram': getattr(organization_settings, 'instagram', None),
    'x': getattr(organization_settings, 'twitter', None),
    'linkedin': getattr(organization_settings, 'linkedin', None),
    'tiktok': getattr(organization_settings, 'tiktok', None),
})


def get_support_phone_number():
    return organization['support_phone_number']


def get_support_email():
    return organization['support_email']


def get_admin_email():
    return organization['admin_email']


def get_brand_logo():
    return organization['brand_logo']


def get_fb_link():
    return organization['facebook']


def get_ig_link():
    return organization['instagram']


def get_x_link():
    return organization['x']


def get_linkedin_link():
    return organization['linkedin']


def get_tiktok_link():
    return organization['tiktok']


developer_settings = SimpleLazyObject(lambda: DeveloperSettings.objects.first())
developer = SimpleLazyObject(lambda: {
    'brand_name': getattr(developer_settings, 'brand_name', None),
    'terms_of_service': getattr(developer_settings, 'terms_of_service', None)
})


def get_brand_name():
    return developer['brand_name']


def get_terms_of_service():
    return developer['terms_of_service']


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

            'support_email': get_support_email(),
            'support_phone_number': get_support_phone_number(),
            'brand_name': get_brand_name(),
            'brand_logo': get_brand_logo(),
            'terms_of_service': get_terms_of_service(),
            'social_true': any((get_fb_link(), get_ig_link(), get_x_link(), get_linkedin_link(), get_tiktok_link())),
            'fb_link': get_fb_link(),
            'ig_link': get_ig_link(),
            'x_link': get_x_link(),
            'linkedin_link': get_linkedin_link(),
            'tiktok_link': get_tiktok_link()
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
            subject="Ecommerce App Template - Refund Confirmation",
            message=plain_message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user_email],
            html_message=html_message,
            fail_silently=False,
        )
    except Exception as e:
        pass


def refund_initiated_notification_email(order_id, user_id, first_name, last_name, phone_no, transaction_id, amount,
                                        provider, admin_email):
    try:
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

            'support_email': get_support_email(),
            'support_phone_number': get_support_phone_number(),
            'brand_name': get_brand_name(),
            'brand_logo': get_brand_logo(),
            'terms_of_service': get_terms_of_service(),
            'social_true': any((get_fb_link(), get_ig_link(), get_x_link(), get_linkedin_link(), get_tiktok_link())),
            'fb_link': get_fb_link(),
            'ig_link': get_ig_link(),
            'x_link': get_x_link(),
            'linkedin_link': get_linkedin_link(),
            'tiktok_link': get_tiktok_link()
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
    except Exception as e:
        pass


def order_shipped_email(order_id, user_email, first_name, estimated_delivery):
    formatted_delivery = format_estimated_delivery(estimated_delivery)

    try:
        context = {
            'order_id': order_id,
            'first_name': first_name,
            'estimated_delivery': formatted_delivery,
            'site_url': settings.ORDER_URL,
            'current_year': datetime.now().year,

            'support_email': get_support_email(),
            'support_phone_number': get_support_phone_number(),
            'brand_name': get_brand_name(),
            'brand_logo': get_brand_logo(),
            'terms_of_service': get_terms_of_service(),
            'social_true': any((get_fb_link(), get_ig_link(), get_x_link(), get_linkedin_link(), get_tiktok_link())),
            'fb_link': get_fb_link(),
            'ig_link': get_ig_link(),
            'x_link': get_x_link(),
            'linkedin_link': get_linkedin_link(),
            'tiktok_link': get_tiktok_link()
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

            'support_email': get_support_email(),
            'support_phone_number': get_support_phone_number(),
            'brand_name': get_brand_name(),
            'brand_logo': get_brand_logo(),
            'terms_of_service': get_terms_of_service(),
            'social_true': any((get_fb_link(), get_ig_link(), get_x_link(), get_linkedin_link(), get_tiktok_link())),
            'fb_link': get_fb_link(),
            'ig_link': get_ig_link(),
            'x_link': get_x_link(),
            'linkedin_link': get_linkedin_link(),
            'tiktok_link': get_tiktok_link()
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
