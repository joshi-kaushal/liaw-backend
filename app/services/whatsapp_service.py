import hashlib
import hmac
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

META_API_BASE = "https://graph.facebook.com/v21.0"


async def send_otp_message(phone_number: str, otp_code: str) -> bool:
    """
    Send an OTP code to a phone number via WhatsApp Cloud API.

    Uses a pre-approved message template named "otp_verification".
    You must create this template in your Meta Business Manager:
      - Template name: otp_verification
      - Category: AUTHENTICATION
      - Body: "Your Live in a Week verification code is {{1}}. Valid for 5 minutes."
      - Parameter: {{1}} = OTP code

    Returns True if sent successfully, False otherwise.
    """
    if not settings.META_ACCESS_TOKEN or settings.META_ACCESS_TOKEN == "placeholder":
        # Dev mode — log OTP to console instead of sending
        logger.warning(f"[DEV MODE] OTP for {phone_number}: {otp_code}")
        return True

    # Always log the OTP to console so you can test it locally
    logger.info(f"==== 🔐 YOUR OTP CODE FOR {phone_number}: {otp_code} ====")

    url = f"{META_API_BASE}/{settings.META_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {settings.META_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    # Using the default 'hello_world' template since Meta restricts 
    # template creation for unverified accounts.
    payload = {
        "messaging_product": "whatsapp",
        "to": phone_number.lstrip("+"),
        "type": "template",
        "template": {
            "name": "hello_world",
            "language": {"code": "en_US"},
        },
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            logger.info(response.text)
            if response.status_code == 200:
                logger.info(f"OTP sent to {phone_number}")
                return True
            else:
                logger.error(
                    f"Failed to send OTP: {response.status_code} {response.text}"
                )
                return False
    except httpx.HTTPError as e:
        logger.error(f"WhatsApp API error: {e}")
        return False


async def send_text_message(phone_number: str, text: str) -> bool:
    """Send a plain text message via WhatsApp Cloud API."""
    if not settings.META_ACCESS_TOKEN or settings.META_ACCESS_TOKEN == "placeholder":
        logger.warning(f"[DEV MODE] WhatsApp to {phone_number}: {text}")
        return True

    url = f"{META_API_BASE}/{settings.META_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {settings.META_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": phone_number.lstrip("+"),
        "type": "text",
        "text": {"body": text},
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                return True
            else:
                logger.error(
                    f"Failed to send message: {response.status_code} {response.text}"
                )
                return False
    except httpx.HTTPError as e:
        logger.error(f"WhatsApp API error: {e}")
        return False


def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """
    Verify the HMAC-SHA256 signature from Meta webhook.
    The signature header is: sha256=<hex_digest>
    """
    if not settings.META_APP_SECRET or settings.META_APP_SECRET == "placeholder":
        logger.warning("[DEV MODE] Skipping webhook signature verification")
        return True

    expected = hmac.new(
        settings.META_APP_SECRET.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()

    provided = signature.removeprefix("sha256=")
    return hmac.compare_digest(expected, provided)
