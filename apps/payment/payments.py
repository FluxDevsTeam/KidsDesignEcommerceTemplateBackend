import uuid
import requests
from rest_framework.response import Response
from django.conf import settings
from .variables import backend_base_route, brand_logo
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# had to make them functions so it wot crash when i newly create project
def get_base_url():
    return backend_base_route


def get_image_url():
    return brand_logo


def get_webhook_url():
    return f"{get_base_url()}/api/v1/payment/webhook/"


def initiate_flutterwave_payment(confirm_token, amount, user):
    print("1")
    print("1")
    print("1")
    print("1")
    image = get_image_url()
    image_path = os.path.join(BASE_DIR, 'image')
    print(image_path)
    print("1")
    print("1")
    print("1")
    print("1")
    try:
        flutterwave_key = settings.PAYMENT_PROVIDERS["flutterwave"]["secret_key"]
        url = "https://api.flutterwave.com/v3/payments"
        headers = {"Authorization": f"Bearer {flutterwave_key}"}
        first_name = user.first_name or ""
        last_name = user.last_name or ""
        phone_no = user.phone_number or ""
        reference = str(uuid.uuid4())
        base_url = get_base_url()
        image_url = image_path
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
                "session_duration": 10,
                "max_retry_attempt": 5
            },
        }

        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        response_data = response.json()

        payment_link = response_data.get("data", {}).get("link")
        if not payment_link:
            return Response({"error": "Payment processing error. Please try again."}, status=502)
        return Response({
            "message": "Flutterwave payment initiated successfully.",
            "payment_link": payment_link,
        }, status=200)

    except requests.exceptions.RequestException as err:
        return Response({"error": "Payment service unavailable. Please try again later."}, status=503)
    except Exception as e:
        return Response({"error": "Payment processing failed. Please try again."}, status=500)


def initiate_paystack_payment(confirm_token, amount, user):
    try:
        paystack_key = settings.PAYMENT_PROVIDERS['paystack']['secret_key']
        headers = {"Authorization": f"Bearer {paystack_key}", "Content-Type": "application/json"}
        url = "https://api.paystack.co/transaction/initialize"
        first_name = user.first_name or ""
        last_name = user.last_name or ""
        phone_no = user.phone_number or ""
        reference = str(uuid.uuid4())
        base_url = get_base_url()
        image_url = get_image_url()
        data = {
            "amount": int(amount * 100),
            "email": user.email,
            "currency": settings.PAYMENT_CURRENCY,
            "reference": reference,
            "callback_url": f"{base_url}/api/v1/payment/verify/?tx_ref={reference}&confirm_token={confirm_token}&provider=paystack&amount={int(amount)}",
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
            return Response({"error": error_msg}, status=response.status_code)

        payment_link = response_data.get("data", {}).get("authorization_url")
        if not payment_link:
            return Response({"error": "Payment processing error. Please try again."}, status=502)
        return Response({
            "message": "Paystack payment initiated successfully.",
            "payment_link": payment_link,
        }, status=200)

    except requests.exceptions.RequestException as err:

        return Response({"error": "Payment service unavailable. Please try again later."}, status=503)
    except Exception as e:
        return Response({"error": "Payment processing failed. Please try again."}, status=500)
