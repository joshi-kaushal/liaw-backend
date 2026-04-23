import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.auth import (
    OTPRequest,
    OTPVerify,
    TokenResponse,
    UserResponse,
    UserUpdate,
)
from app.services.auth_service import (
    get_or_create_user,
    create_otp,
    verify_otp,
    create_access_token,
)
from app.services.whatsapp_service import send_otp_message

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/request-otp",
    status_code=status.HTTP_200_OK,
    summary="Request an OTP",
    description="Sends a 6-digit OTP to the given phone number via WhatsApp.",
)
async def request_otp(
    body: OTPRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # Get or create user
    user = await get_or_create_user(db, body.phone_number)

    # Generate OTP
    code = await create_otp(db, user.id)

    # Send OTP via WhatsApp
    sent = await send_otp_message(body.phone_number, code)
    if not sent:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to send OTP via WhatsApp. Please try again.",
        )
    logger.info(sent)
    return {"message": "OTP sent successfully", "phone_number": body.phone_number}


@router.post(
    "/verify-otp",
    response_model=TokenResponse,
    summary="Verify OTP and get JWT",
    description="Verifies the OTP and returns a JWT access token.",
)
async def verify_otp_endpoint(
    body: OTPVerify,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    user = await verify_otp(db, body.phone_number, body.code)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired OTP",
        )

    token, expires_in = create_access_token(user.id)

    return TokenResponse(
        access_token=token,
        expires_in=expires_in,
        user=UserResponse.model_validate(user),
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
):
    return UserResponse.model_validate(current_user)


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Update current user profile",
)
async def update_me(
    body: UserUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if body.display_name is not None:
        current_user.display_name = body.display_name
    if body.profile_picture_url is not None:
        current_user.profile_picture_url = body.profile_picture_url

    await db.flush()
    return UserResponse.model_validate(current_user)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh JWT token",
    description="Issues a new JWT token for an authenticated user.",
)
async def refresh_token(
    current_user: Annotated[User, Depends(get_current_user)],
):
    token, expires_in = create_access_token(current_user.id)

    return TokenResponse(
        access_token=token,
        expires_in=expires_in,
        user=UserResponse.model_validate(current_user),
    )
