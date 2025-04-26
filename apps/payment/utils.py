from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from math import radians, sin, cos, sqrt, atan2
from datetime import timedelta
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils.timezone import now
import logging
import requests
from django.conf import settings
from django.core.mail import send_mail
from .tasks import is_celery_healthy
from ..orders.tasks import refund_confirmation_email

logger = logging.getLogger(__name__)

AVAILABLE_STATES = ["Lagos", "Ogun", "Abuja", "Kaduna", "Anambra", "Cross River"]
WAREHOUSE_CITY = "Lagos"


state_coords = {
    "Lagos": (6.5244, 3.3792),
    "Ogun": (7.1604, 3.3481),
    "Oyo": (7.3775, 3.9470),
    "Osun": (7.5629, 4.5190),
    "Ondo": (7.1000, 4.8419),
    "Ekiti": (7.7180, 5.3101),
    "Edo": (6.5243, 5.9500),
    "Delta": (5.4891, 5.9891),
    "Kwara": (8.4800, 4.5400),
    "Kogi": (7.8000, 6.7333),
    "Niger": (9.6000, 6.5500),
    "Abuja": (9.0765, 7.3986),
    "Kaduna": (10.5105, 7.4165),
    "Kano": (12.0000, 8.5167),
    "Borno": (11.8333, 13.1500),
    "Yobe": (12.0000, 11.5000),
    "Sokoto": (13.0059, 5.2476),
    "Zamfara": (12.0000, 6.2333),
    "Taraba": (7.8704, 10.7903),
    "Gombe": (10.2900, 11.1700),
    "Bauchi": (10.3000, 9.8333),
    "Adamawa": (9.3265, 12.3984),
    "Katsina": (12.9855, 7.6170),
    "Jigawa": (12.2280, 9.5616),
    "Nasarawa": (8.4910, 8.5140),
    "Benue": (7.1907, 9.5616),
    "Kebbi": (12.4500, 4.1990),
    "Bayelsa": (4.9240, 6.2649),
    "Rivers": (4.8436, 6.9112),
    "Akwa Ibom": (5.0280, 7.9319),
    "Cross River": (5.9631, 8.3309),
    "Enugu": (6.4599, 7.5489),
    "Anambra": (6.2209, 6.9366),
    "Abia": (5.5320, 7.4860),
    "Imo": (5.4897, 7.0143),
    "Ebonyi": (6.3249, 8.1137),
    "FCT - Abuja": (9.0765, 7.3986),
}


def calculate_distance(coord1, coord2):
    R = 6371.0
    lat1, lon1 = coord1
    lat2, lon2 = coord2

    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c


def generate_confirm_token(user, cart_id):
    try:
        refresh = RefreshToken.for_user(user)
        refresh['cart_id'] = cart_id
        refresh['exp'] = int((now() + timedelta(hours=1)).timestamp())
        return str(refresh.access_token)
    except Exception as e:
        logger.exception("Error generating confirmation token", extra={'user_id': user.id})
        raise


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
        return swagger_auto_schema(operation_id=f"{action_type} {model}", operation_description=f"{get_description}. you dont need to pass in any data. just be authenticated (pass in JWT key) and the backend would process everything", tags=[tags])(func)

    return decorators


def initiate_refund(tx_ref, provider, amount, user, transaction_id=None, ):
    try:
        if provider == "paystack":
            payload = {"transaction": tx_ref}
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
            return True
        elif provider == "flutterwave":
            if not transaction_id:
                return False
            url = f"https://api.flutterwave.com/v3/transactions/{transaction_id}/refund"
            headers = {
                "Authorization": f"Bearer {settings.PAYMENT_PROVIDERS['flutterwave']['secret_key']}",
                "Content-Type": "application/json"
            }
            payload = {}
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return True
    except:
        notify_admin_for_manual_refund(tx_ref, provider, amount, user, transaction_id)
        return False


def notify_admin_for_manual_refund(tx_ref, provider, amount, user, transaction_id):
    phone_no = user.phone_number or None
    send_mail(
        subject="Manual Refund Required",
        message=f"Refund failed for: \nuser_id - {user.id}, \nname - {user.first_name} {user.last_name},\nphone no - {phone_no}\ntx_ref - {tx_ref}, \ntransaction_id - {transaction_id}, \nprovider - {provider}, \namount - {amount}. \nThis was due to insufficient stock. Please process manually.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=["suskidee@gmail.com"],
        fail_silently=True
    )

