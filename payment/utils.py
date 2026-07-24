import base64
import requests
import logging
from datetime import datetime
from django.conf import settings

logger = logging.getLogger(__name__)


def get_mpesa_access_token():
    url = f"{settings.MPESA_API_URL.rstrip('/')}/oauth/v1/generate?grant_type=client_credentials"
    try:
        response = requests.get(
            url,
            auth=(settings.MPESA_CONSUMER_KEY, settings.MPESA_CONSUMER_SECRET),
            timeout=10,
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        logger.error(f"M-Pesa auth failed: {response.text}")
        return None
    except Exception as e:
        logger.error(f"Error fetching M-Pesa access token: {str(e)}")
        return None


def initiate_mpesa_stk_push(phone_number, amount, reference, description="Tamarind Dhow Booking"):
    access_token = get_mpesa_access_token()
    if not access_token:
        return {"success": False, "message": "Failed to authenticate with M-Pesa"}

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    passkey = settings.MPESA_PASSKEY
    shortcode = settings.MPESA_SHORTCODE
    password = base64.b64encode(f"{shortcode}{passkey}{timestamp}".encode()).decode("utf-8")

    # Format phone number e.g. 0712345678 or +254712345678 -> 254712345678
    formatted_phone = phone_number.replace("+", "").strip()
    if formatted_phone.startswith("0"):
        formatted_phone = "254" + formatted_phone[1:]

    stk_url = f"{settings.MPESA_API_URL.rstrip('/')}/mpesa/stkpush/v1/processrequest"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "BusinessShortCode": shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(amount),
        "PartyA": formatted_phone,
        "PartyB": shortcode,
        "PhoneNumber": formatted_phone,
        "CallBackURL": settings.MPESA_CALLBACK_URL,
        "AccountReference": reference[:12],
        "TransactionDesc": description[:12],
    }

    try:
        response = requests.post(stk_url, json=payload, headers=headers, timeout=15)
        res_data = response.json()
        if response.status_code == 200 and res_data.get("ResponseCode") == "0":
            return {
                "success": True,
                "checkout_request_id": res_data.get("CheckoutRequestID"),
                "merchant_request_id": res_data.get("MerchantRequestID"),
                "data": res_data,
            }
        else:
            logger.error(f"M-Pesa STK Push error: {res_data}")
            return {
                "success": False,
                "message": res_data.get("CustomerMessage", "STK push failed"),
                "data": res_data,
            }
    except Exception as e:
        logger.error(f"Error initiating STK push: {str(e)}")
        return {"success": False, "message": str(e)}
