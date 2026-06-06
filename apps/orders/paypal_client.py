import base64
import requests
from django.conf import settings


def _base_url():
    if settings.PAYPAL_MODE == 'sandbox':
        return 'https://api-m.sandbox.paypal.com'
    return 'https://api-m.paypal.com'


def _get_access_token():
    credentials = base64.b64encode(
        f"{settings.PAYPAL_CLIENT_ID}:{settings.PAYPAL_CLIENT_SECRET}".encode()
    ).decode()
    response = requests.post(
        f"{_base_url()}/v1/oauth2/token",
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data="grant_type=client_credentials",
        timeout=10,
    )
    response.raise_for_status()
    return response.json()['access_token']


def create_order(amount, currency, order_id, return_url=None, cancel_url=None):
    access_token = _get_access_token()
    payload = {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "reference_id": f"order_{order_id}",
                "amount": {
                    "currency_code": currency,
                    "value": str(amount),
                },
            }
        ],
    }
    if return_url and cancel_url:
        payload["application_context"] = {
            "return_url": return_url,
            "cancel_url": cancel_url,
        }
    response = requests.post(
        f"{_base_url()}/v2/checkout/orders",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def capture_order(paypal_order_id):
    access_token = _get_access_token()
    response = requests.post(
        f"{_base_url()}/v2/checkout/orders/{paypal_order_id}/capture",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        timeout=10,
    )
    response.raise_for_status()
    return response.json()
