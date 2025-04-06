import uuid
import requests
from rest_framework.response import Response
from django.conf import settings

from datetime import timedelta
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils.timezone import now


def generate_confirm_token(user, cart_id):
    """
    Generates a token for payment confirmation.
    """
    refresh = RefreshToken.for_user(user)
    refresh['cart_id'] = cart_id
    refresh['exp'] = now() + timedelta(hours=20)
    return str(refresh.access_token)


def initiate_payment(amount, email, user, redirect_url):
    url = "https://api.flutterwave.com/v3/payments"
    headers = {
        "Authorization": f"Bearer {settings.FLW_SEC_KEY}"
    }
    first_name = user.first_name
    last_name = user.last_name
    phone_no = user.phone_number

    data = {
        "tx_ref": str(uuid.uuid4()),
        "amount": str(amount),
        "currency": "NGN",
        "redirect_url": redirect_url,
        "meta": {
            "consumer_id": user.id,
        },
        "customer": {
            "email": email,
            "phonenumber": phone_no,
            "name": f"{last_name} {first_name}"
        },
        "customizations": {
            "title": "ASLUXURY ORIGINALS",
            "logo": "https://th.bing.com/th/id/OIP.YUyvxZV46V46TKoPLtcyjwHaIj?w=183&h=211&c=7&r=0&o=5&pid=1.7"
        }
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response_data = response.json()

        if response.status_code in [200, 201]:
            payment_link = response_data.get("data", {}).get("link")
            if not payment_link:
                return Response(
                    {"error": "Payment link not found in the response."},
                    status=500
                )
            return Response({
                "message": "Payment initiated successfully.",
                "payment_link": payment_link,
            }, status=200)
        else:
            return Response({
                "error": response_data.get("message", "An error occurred while initiating payment.")
            }, status=response.status_code)

    except requests.exceptions.RequestException as err:
        return Response({"error": str(err)}, status=500)
