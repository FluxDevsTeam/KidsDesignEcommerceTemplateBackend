from drf_yasg.utils import swagger_auto_schema
from .pagination import PAGINATION_PARAMS
from django.core.mail import send_mail
from django.conf import settings
import requests


def swagger_helper(tags, model):
    def decorators(func):
        descriptions = {
            "list": f"Retrieve a list of {model}",
            "retrieve": f"Retrieve details of a specific {model}",
            "create": f"Create a new {model}",
            "partial_update": f"Update a {model}",
            "destroy": f"Delete a {model}",
        }

        action_type = func.__name__
        get_description = descriptions.get(action_type, f"{action_type} {model}")
        return swagger_auto_schema(manual_parameters=PAGINATION_PARAMS, operation_id=f"{action_type} {model}", operation_description=get_description, tags=[tags])(func)

    return decorators


def initiate_refund(order, is_admin=False):
    try:
        if order.payment_provider == "paystack":
            payload = {"transaction": order.transaction_id}
            headers = {
                "Authorization": f"Bearer {settings.PAYMENT_PROVIDERS['paystack']['secret_key']}",
                "Content-Type": "application/json"
            }
            response = requests.post(
                "https://api.paystack.co/refund",
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            notify_admin_for_refund_initiated(order)
            return True
        elif order.payment_provider == "flutterwave":
            if not order.transaction_id:
                return False
            url = f"https://api.flutterwave.com/v3/transactions/{order.transaction_id}/refund"
            headers = {
                "Authorization": f"Bearer {settings.PAYMENT_PROVIDERS['flutterwave']['secret_key']}",
                "Content-Type": "application/json"
            }
            payload = {}
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            notify_admin_for_refund_initiated(order)
            return True
    except requests.exceptions.RequestException:
        if not is_admin:
            notify_admin_for_manual_refund(order)
        return False


def notify_admin_for_manual_refund(order):
    send_mail(
        subject="Manual Refund Required",
        message=f"Refund failed for order {order.id}, user {order.email}, tx_ref {order.transaction_id}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=["admin@ecommercetemplate.com"],
        fail_silently=True
    )


def notify_admin_for_refund_initiated(order):
    send_mail(
        subject="Refund Initiated",
        message=f"A refund was initiated for order {order.id}, user {order.email}, tx_ref {order.transaction_id}, amount {settings.PAYMENT_CURRENCY} {order.total_amount}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=["admin@ecommercetemplate.com"],
        fail_silently=True
    )
