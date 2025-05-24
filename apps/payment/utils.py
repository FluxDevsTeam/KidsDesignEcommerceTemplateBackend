from drf_yasg.utils import swagger_auto_schema
from math import radians, sin, cos, sqrt, atan2
from datetime import timedelta
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils.timezone import now
import requests
from django.conf import settings
from .tasks import is_celery_healthy, send_refund_email_synchronously, send_manual_refund_notification_email, \
    send_user_refund_email_synchronously, send_user_refund_notification_email
from .variables import warehouse_city, available_states, admin_email

AVAILABLE_STATES = available_states
WAREHOUSE_CITY = warehouse_city

state_coords = {
    "Abia": (5.5333, 7.4833),          # State capital (Umuahia)
    "Adamawa": (9.3265, 12.3984),      # State capital (Yola)
    "Akwa Ibom": (5.0079, 7.8494),     # State capital (Uyo)
    "Anambra": (6.2104, 7.0686),       # State capital (Awka)
    "Bauchi": (10.3158, 9.8442),       # State capital (Bauchi)
    "Bayelsa": (4.9267, 6.2676),       # State capital (Yenagoa)
    "Benue": (7.7328, 8.5391),         # State capital (Makurdi)
    "Borno": (11.8333, 13.1500),       # State capital (Maiduguri)
    "Cross River": (4.9500, 8.3250),   # State capital (Calabar)
    "Delta": (6.2048, 6.7320),         # State capital (Asaba)
    "Ebonyi": (6.3249, 8.1137),        # State capital (Abakaliki)
    "Edo": (6.3350, 5.6275),           # State capital (Benin City)
    "Ekiti": (7.6236, 5.2209),         # State capital (Ado-Ekiti)
    "Enugu": (6.4402, 7.5023),         # State capital (Enugu)
    "Gombe": (10.2897, 11.1673),       # State capital (Gombe)
    "Imo": (5.4926, 7.0260),           # State capital (Owerri)
    "Jigawa": (11.7017, 9.3346),       # State capital (Dutse)
    "Kaduna": (10.5167, 7.4333),       # State capital (Kaduna)
    "Kano": (12.0022, 8.5927),         # State capital (Kano)
    "Katsina": (12.9908, 7.6019),      # State capital (Katsina)
    "Kebbi": (12.4539, 4.1979),        # State capital (Birnin Kebbi)
    "Kogi": (7.8027, 6.7333),          # State capital (Lokoja)
    "Kwara": (8.5000, 4.5500),         # State capital (Ilorin)
    "Lagos": (6.5244, 3.3792),         # State capital (Ikeja)
    "Nasarawa": (8.5167, 8.5333),      # State capital (Lafia)
    "Niger": (9.6139, 6.5569),         # State capital (Minna)
    "Ogun": (7.1557, 3.3451),          # State capital (Abeokuta)
    "Ondo": (7.2500, 5.1950),          # State capital (Akure)
    "Osun": (7.7669, 4.5600),          # State capital (Osogbo)
    "Oyo": (7.3775, 3.9470),           # State capital (Ibadan)
    "Rivers": (4.8242, 7.0336),        # State capital (Port Harcourt)
    "Sokoto": (13.0629, 5.2438),       # State capital (Sokoto)
    "Taraba": (8.8833, 11.3667),       # State capital (Jalingo)
    "Yobe": (11.7483, 11.9639),        # State capital (Damaturu)
    "Zamfara": (12.1704, 6.6641),      # State capital (Gusau)
    "FCT - Abuja": (9.0579, 7.4951),   # Federal capital (Abuja)
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


def initiate_refund(provider, amount, user, transaction_id):
    try:
        if provider == "paystack":
            payload = {"transaction": transaction_id}
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
            notify_user_for_successful_refund(provider, amount, user, transaction_id)
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
            notify_user_for_successful_refund(provider, amount, user, transaction_id)
            return True
    except:
        try:
            notify_admin_for_manual_refund(provider, amount, user, transaction_id)
            return "admin"
        except:
            return False


def notify_admin_for_manual_refund(provider, amount, user, transaction_id):
    if not is_celery_healthy():
        send_refund_email_synchronously(
            provider=provider,
            amount=amount,
            user=user,
            transaction_id=transaction_id,
            reason="Insufficient stock",
            admin_email=admin_email
        )
    else:
        send_manual_refund_notification_email.apply_async(
            kwargs={
                'provider': provider,
                'amount': amount,
                'user_id': user.id,
                'transaction_id': transaction_id,
                'reason': "Insufficient stock",
                'admin_email': admin_email
            }
        )


def notify_user_for_successful_refund(provider, amount, user, transaction_id):
    currency = settings.PAYMENT_CURRENCY

    if not is_celery_healthy():
        send_user_refund_email_synchronously(
            user=user,
            amount=amount,
            provider=provider,
            transaction_id=transaction_id,
            currency=currency,
            admin_email=admin_email
        )
    else:
        send_user_refund_notification_email.apply_async(
            kwargs={
                'user_id': user.id,
                'amount': amount,
                'provider': provider,
                'transaction_id': transaction_id,
                'currency': currency,
                'admin_email': admin_email
            }
        )
