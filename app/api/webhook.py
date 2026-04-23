import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.bot.handler import handle_whatsapp_message
from app.services.whatsapp_service import verify_webhook_signature

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook/whatsapp", tags=["Webhook"])


@router.get("")
async def verify_webhook(
    request: Request,
):
    """
    Webhook verification endpoint required by Meta.
    Meta sends a GET request with hub.mode, hub.challenge, and hub.verify_token.
    We must echo back hub.challenge if the token matches.
    """
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode and token:
        if mode == "subscribe" and token == settings.META_VERIFY_TOKEN:
            logger.info("Webhook verified successfully!")
            return Response(content=challenge, media_type="text/plain")
        else:
            raise HTTPException(status_code=403, detail="Invalid verify token")
            
    raise HTTPException(status_code=400, detail="Missing parameters")


@router.post("")
async def receive_message(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Handles incoming messages from WhatsApp.
    Validates HMAC signature and passes message to the bot handler.
    """
    # 1. Verify signature
    payload_body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")
    
    if not signature:
        logger.warning("Missing X-Hub-Signature-256 header")
        raise HTTPException(status_code=401, detail="Missing signature")
        
    if not verify_webhook_signature(payload_body, signature):
        logger.warning("Invalid webhook signature")
        raise HTTPException(status_code=401, detail="Invalid signature")

    # 2. Parse payload
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # Meta webhook payload is deeply nested
    try:
        # Check if this is a message event
        entry = data.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])
        
        if not messages:
            # Not a message (could be a status update, like "delivered" or "read")
            return {"status": "ok"}
            
        message = messages[0]
        
        # Only handle text messages for now
        if message.get("type") == "text":
            phone_number = message.get("from")  # WhatsApp ID of sender
            text = message.get("text", {}).get("body", "")
            
            # Fire and forget the handler so we don't block the webhook response
            # Note: For production, consider using BackgroundTasks to avoid holding up the HTTP response
            await handle_whatsapp_message(db, phone_number, text)
            
    except (IndexError, KeyError) as e:
        logger.error(f"Error parsing webhook payload: {e}")
        # Return 200 anyway so Meta doesn't retry
        
    return {"status": "ok"}
