import secrets
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import User, OTPCode


async def get_or_create_user(db: AsyncSession, phone_number: str) -> User:
    """Find existing user by phone or create a new unverified user."""
    stmt = select(User).where(User.phone_number == phone_number)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            id=uuid.uuid4(),
            phone_number=phone_number,
            is_verified=False,
        )
        db.add(user)
        await db.flush()

    return user


def generate_otp_code() -> str:
    """Generate a cryptographically secure 6-digit OTP."""
    return f"{secrets.randbelow(1000000):06d}"


async def create_otp(db: AsyncSession, user_id: uuid.UUID) -> str:
    """Create a new OTP for a user (5-minute expiry)."""
    code = generate_otp_code()
    otp = OTPCode(
        id=uuid.uuid4(),
        user_id=user_id,
        code=code,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
        is_used=False,
    )
    db.add(otp)
    await db.flush()
    return code


async def verify_otp(
    db: AsyncSession, phone_number: str, code: str
) -> User | None:
    """
    Verify an OTP for a phone number.
    Returns the user if valid, None if invalid/expired/used.
    Marks the OTP as used on success.
    """
    # Find the user
    stmt = select(User).where(User.phone_number == phone_number)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if user is None:
        return None

    # Find the latest valid OTP for this user
    stmt = (
        select(OTPCode)
        .where(
            OTPCode.user_id == user.id,
            OTPCode.code == code,
            OTPCode.is_used == False,  # noqa: E712
            OTPCode.expires_at > datetime.now(timezone.utc),
        )
        .order_by(OTPCode.created_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    otp = result.scalar_one_or_none()

    if otp is None:
        return None

    # Mark OTP as used and user as verified
    otp.is_used = True
    user.is_verified = True
    await db.flush()

    return user


def create_access_token(user_id: uuid.UUID) -> tuple[str, int]:
    """
    Create a JWT access token for a user.
    Returns (token_string, expiry_seconds).
    """
    expiry_seconds = settings.JWT_EXPIRY_HOURS * 3600
    payload = {
        "sub": str(user_id),
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRY_HOURS),
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token, expiry_seconds


def decode_access_token(token: str) -> dict | None:
    """
    Decode and validate a JWT token.
    Returns the payload dict if valid, None if invalid/expired.
    """
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except jwt.PyJWTError:
        return None
