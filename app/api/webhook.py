import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.bot.handler import handle_whatsapp_message

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook/whatsapp", tags=["Webhook"])


class OdysseyWebhookPayload(BaseModel):
    """Flat payload sent by Odyssey for every routed WhatsApp message."""

    # 'from' is a Python keyword, so Pydantic's alias is used here.
    from_: str = Field(..., alias="from")
    raw_text: str
    intent: str
    app: str
    entities: dict[str, str] = {}
    timestamp: str
    push_name: str | None = None

    model_config = {"populate_by_name": True}


@router.post("")
async def receive_message(
    payload: OdysseyWebhookPayload,
    db: Annotated[AsyncSession, Depends(get_db)],
    x_gateway_secret: Annotated[str | None, Header()] = None,
):
    """
    Receives a routed WhatsApp message from the Odyssey gateway.
    Authenticates via a shared x-gateway-secret header, then dispatches
    to the bot handler which contains all command/reply logic.
    """
    if settings.ODYSSEY_WEBHOOK_SECRET:
        # Reject calls that don't carry the correct pre-shared secret.
        # This prevents any party other than Odyssey from triggering bot actions.
        if x_gateway_secret != settings.ODYSSEY_WEBHOOK_SECRET:
            raise HTTPException(status_code=401, detail="Invalid gateway secret")

    logger.info(
        "Received Odyssey webhook",
        extra={"from": payload.from_, "intent": payload.intent},
    )
    print("[DEBUG] Receive Message Payload: ", payload)
    await handle_whatsapp_message(db, payload.from_, payload.raw_text, payload.push_name)

    return {"status": "ok"}
