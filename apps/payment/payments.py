import uuid
import requests
from rest_framework.response import Response
from django.conf import settings
import logging

from apps.payment.utils import generate_confirm_token

logger = logging.getLogger(__name__)

base_url = settings.BASE_ROUTE
image_url = settings.PAYMENT_IMAGE_URL


def initiate_flutterwave_payment(confirm_token, amount, user):
    try:
        flutterwave_key = settings.PAYMENT_PROVIDERS["flutterwave"]["secret_key"]
        url = "https://api.flutterwave.com/v3/payments"
        headers = {
            "Authorization": f"Bearer {flutterwave_key}"
        }
        first_name = user.first_name or ""
        last_name = user.last_name or ""
        phone_no = user.phone_number or ""
        reference = str(uuid.uuid4())
        data = {
            "tx_ref": reference,
            "amount": str(amount),
            "currency": settings.PAYMENT_CURRENCY,
            "redirect_url": f"{base_url}/api/v1/payment/verify/?tx_ref={reference}&confirm_token={confirm_token}&provider=flutterwave&amount={int(amount)}&transaction_id={{transaction_id}}",
            "meta": {"consumer_id": user.id},
            "customer": {
                "email": user.email,
                "phonenumber": phone_no,
                "name": f"{last_name} {first_name}"
            },
            "customizations": {
                "title": "Ecommerce Template",
                "logo": image_url
            },
            "configurations": {
                "session_duration": 10,  #minutes
                "max_retry_attempt": 5
            },
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
        }, status=200)

    except requests.exceptions.RequestException as err:
        logger.error("Flutterwave API error",
                     extra={'error': str(err), 'tx_ref': data.get('tx_ref'), 'user_id': user.id})
        return Response({"error": "Payment service unavailable. Please try again later."}, status=503)
    except Exception as e:
        logger.exception("Unexpected error in Flutterwave payment", extra={'user_id': user.id})
        return Response({"error": "Payment processing failed. Please try again."}, status=500)


def initiate_paystack_payment(confirm_token, amount, user):
    try:
        url = "https://api.paystack.co/transaction/initialize"
        paystack_key = settings.PAYMENT_PROVIDERS['paystack']['secret_key']
        headers = {"Authorization": f"Bearer {paystack_key}", "Content-Type": "application/json"}
        first_name = user.first_name or ""
        last_name = user.last_name or ""
        phone_no = user.phone_number or ""
        reference = str(uuid.uuid4())
        data = {
            "amount": int(amount * 100),
            "email": user.email,
            "currency": settings.PAYMENT_CURRENCY,
            "reference": reference,
            "callback_url": f"{base_url}/api/v1/payment/verify/?tx_ref={reference}&confirm_token={confirm_token}&provider=paystack&amount={int(amount)}&transaction_id={{transaction_id}}",
            "metadata": {
                "consumer_id": user.id,
                "image_url": image_url
            }
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
        }, status=200)

    except requests.exceptions.RequestException as err:
        logger.error("Paystack API error",
                     extra={'error': str(err), 'reference': data.get('reference'), 'user_id': user.id})
        return Response({"error": "Payment service unavailable. Please try again later."}, status=503)
    except Exception as e:
        logger.exception("Unexpected error in Paystack payment", extra={'user_id': user.id})
        return Response({"error": "Payment processing failed. Please try again."}, status=500)
