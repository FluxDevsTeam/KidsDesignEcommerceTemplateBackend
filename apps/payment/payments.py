import uuid
import requests
from rest_framework.response import Response
from django.conf import settings
from datetime import timedelta
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils.timezone import now
import logging

logger = logging.getLogger(__name__)


def generate_confirm_token(user, cart_id):
    try:
        refresh = RefreshToken.for_user(user)
        refresh['cart_id'] = cart_id
        refresh['exp'] = int((now() + timedelta(hours=1)).timestamp())
        return str(refresh.access_token)
    except Exception as e:
        logger.exception("Error generating confirmation token", extra={'user_id': user.id})
        raise


def initiate_flutterwave_payment(amount, email, user, redirect_url):
    try:
        url = "https://api.flutterwave.com/v3/payments"
        headers = {"Authorization": f"Bearer {settings.FLW_SEC_KEY}"}
        first_name = user.first_name or ""
        last_name = user.last_name or ""
        phone_no = user.phone_number or ""

        if not email:
            return Response({"error": "Email is required for payment"}, status=400)

        data = {
            "tx_ref": str(uuid.uuid4()),
            "amount": str(amount),
            "currency": settings.PAYMENT_CURRENCY,
            "redirect_url": redirect_url,
            "meta": {"consumer_id": user.id},
            "customer": {
                "email": email,
                "phonenumber": phone_no,
                "name": f"{last_name} {first_name}".strip()
            },
            "customizations": {
                "title": "ASLUXURY ORIGINALS",
                "logo": "https://th.bing.com/th/id/OIP.YUyvxZV46V46TKoPLtcyjwHaIj?w=183&h=211&c=7&r=0&o=5&pid=1.7"
            }
        }

        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        response_data = response.json()

        payment_link = response_data.get("data", {}).get("link")
        if not payment_link:
            logger.error("Flutterwave payment link missing", extra={'tx_ref': data['tx_ref'], 'user_id': user.id})
            return Response({"error": "Payment processing error. Please try again."}, status=502)
        return Response({
            "message": "Flutterwave payment initiated successfully.",
            "payment_link": payment_link,
            "tx_ref": data["tx_ref"]
        }, status=200)

    except requests.exceptions.RequestException as err:
        logger.error("Flutterwave API error",
                     extra={'error': str(err), 'tx_ref': data.get('tx_ref'), 'user_id': user.id})
        return Response({"error": "Payment service unavailable. Please try again later."}, status=503)
    except Exception as e:
        logger.exception("Unexpected error in Flutterwave payment", extra={'user_id': user.id})
        return Response({"error": "Payment processing failed. Please try again."}, status=500)


def initiate_paystack_payment(amount, email, user, redirect_url):
    try:
        url = "https://api.paystack.co/transaction/initialize"
        headers = {"Authorization": f"Bearer {settings.PAYSTACK_SEC_KEY}", "Content-Type": "application/json"}
        first_name = user.first_name or ""
        last_name = user.last_name or ""
        phone_no = user.phone_number or ""

        if not email:
            return Response({"error": "Email is required for payment"}, status=400)

        data = {
            "amount": int(amount * 100),
            "email": email,
            "currency": settings.PAYMENT_CURRENCY,
            "reference": str(uuid.uuid4()),
            "callback_url": redirect_url,
            "metadata": {"consumer_id": user.id}
        }

        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        response_data = response.json()

        if not response_data.get("status"):
            error_msg = response_data.get("message", "Payment initiation failed")
            logger.error("Paystack error",
                         extra={'error': error_msg, 'reference': data['reference'], 'user_id': user.id})
            return Response({"error": error_msg}, status=response.status_code)

        payment_link = response_data.get("data", {}).get("authorization_url")
        if not payment_link:
            logger.error("Paystack payment link missing", extra={'reference': data['reference'], 'user_id': user.id})
            return Response({"error": "Payment processing error. Please try again."}, status=502)
        return Response({
            "message": "Paystack payment initiated successfully.",
            "payment_link": payment_link,
            "tx_ref": data["reference"]
        }, status=200)

    except requests.exceptions.RequestException as err:
        logger.error("Paystack API error",
                     extra={'error': str(err), 'reference': data.get('reference'), 'user_id': user.id})
        return Response({"error": "Payment service unavailable. Please try again later."}, status=503)
    except Exception as e:
        logger.exception("Unexpected error in Paystack payment", extra={'user_id': user.id})
        return Response({"error": "Payment processing failed. Please try again."}, status=500)
