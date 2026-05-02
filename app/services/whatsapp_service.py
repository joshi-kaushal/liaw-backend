import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


async def send_text_message(phone_number: str, text: str) -> bool:
    """
    Send a plain text message to a WhatsApp user via the Odyssey gateway.

    Odyssey expects plain phone numbers (no + prefix) and handles the
    JID normalisation internally before calling Baileys.
    """
    # Strip the + prefix that the bot handler adds — Odyssey takes bare numbers.
    to = phone_number.lstrip("+")

    if not settings.ODYSSEY_URL or not settings.ODYSSEY_API_KEY:
        # Dev mode — log to console when Odyssey isn't configured.
        logger.warning("[DEV MODE] WhatsApp reply to %s: %s", to, text)
        return True

    url = f"{settings.ODYSSEY_URL}/send"
    headers = {
        "x-api-key": settings.ODYSSEY_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {"to": to, "text": text}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                return True
            logger.error(
                "Odyssey /send failed: %s %s", response.status_code, response.text
            )
            return False
    except httpx.HTTPError as exc:
        logger.error("Odyssey /send HTTP error: %s", exc)
        return False


# ---------------------------------------------------------------------------
# COMMENTED OUT — Meta Cloud API send functions (archived alongside
# whatsapp-metacloudapi.py). OTP is now sent as a plain text message via
# send_text_message() → Odyssey /send, which is handled in bot/handler.py.
# ---------------------------------------------------------------------------

# META_API_BASE = "https://graph.facebook.com/v21.0"
#
# async def send_otp_message(phone_number: str, otp_code: str) -> bool:
#     """
#     Send an OTP code to a phone number via WhatsApp Cloud API.
#     Template: otp_verification (AUTHENTICATION category).
#     """
#     if not settings.META_ACCESS_TOKEN or settings.META_ACCESS_TOKEN == "placeholder":
#         logger.warning(f"[DEV MODE] OTP for {phone_number}: {otp_code}")
#         return True
#
#     url = f"{META_API_BASE}/{settings.META_PHONE_NUMBER_ID}/messages"
#     headers = {
#         "Authorization": f"Bearer {settings.META_ACCESS_TOKEN}",
#         "Content-Type": "application/json",
#     }
#     payload = {
#         "messaging_product": "whatsapp",
#         "to": phone_number.lstrip("+"),
#         "type": "template",
#         "template": {"name": "hello_world", "language": {"code": "en_US"}},
#     }
#     try:
#         async with httpx.AsyncClient(timeout=10.0) as client:
#             response = await client.post(url, headers=headers, json=payload)
#             if response.status_code == 200:
#                 return True
#             logger.error(f"Failed to send OTP: {response.status_code} {response.text}")
#             return False
#     except httpx.HTTPError as e:
#         logger.error(f"WhatsApp API error: {e}")
#         return False
#
# async def send_text_message_meta(phone_number: str, text: str) -> bool:
#     """Send a plain text message via WhatsApp Cloud API (Meta)."""
#     if not settings.META_ACCESS_TOKEN or settings.META_ACCESS_TOKEN == "placeholder":
#         logger.warning(f"[DEV MODE] WhatsApp to {phone_number}: {text}")
#         return True
#
#     url = f"{META_API_BASE}/{settings.META_PHONE_NUMBER_ID}/messages"
#     headers = {
#         "Authorization": f"Bearer {settings.META_ACCESS_TOKEN}",
#         "Content-Type": "application/json",
#     }
#     payload = {
#         "messaging_product": "whatsapp",
#         "to": phone_number.lstrip("+"),
#         "type": "text",
#         "text": {"body": text},
#     }
#     try:
#         async with httpx.AsyncClient(timeout=10.0) as client:
#             response = await client.post(url, headers=headers, json=payload)
#             if response.status_code == 200:
#                 return True
#             logger.error(f"Failed to send message: {response.status_code} {response.text}")
#             return False
#     except httpx.HTTPError as e:
#         logger.error(f"WhatsApp API error: {e}")
#         return False
#
# def verify_webhook_signature(payload: bytes, signature: str) -> bool:
#     """Verify the HMAC-SHA256 signature from Meta webhook."""
#     import hashlib, hmac as _hmac
#     if not settings.META_APP_SECRET or settings.META_APP_SECRET == "placeholder":
#         logger.warning("[DEV MODE] Skipping webhook signature verification")
#         return True
#     expected = _hmac.new(
#         settings.META_APP_SECRET.encode(), payload, hashlib.sha256
#     ).hexdigest()
#     provided = signature.removeprefix("sha256=")
#     return _hmac.compare_digest(expected, provided)
