from pydantic import BaseModel, Field
import uuid
from datetime import datetime


class OTPRequest(BaseModel):
    """Request to send an OTP to a phone number."""
    phone_number: str = Field(
        ...,
        pattern=r"^\+[1-9]\d{6,14}$",
        description="Phone number in E.164 format, e.g. +919876543210",
        examples=["+919876543210"],
    )


class OTPVerify(BaseModel):
    """Request to verify an OTP and get a JWT."""
    phone_number: str = Field(
        ...,
        pattern=r"^\+[1-9]\d{6,14}$",
        description="Phone number in E.164 format",
    )
    code: str = Field(
        ...,
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$",
        description="6-digit OTP code",
    )


class TokenResponse(BaseModel):
    """JWT token response after successful OTP verification."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Token expiry in seconds")
    user: "UserResponse"


class UserResponse(BaseModel):
    """Public user profile."""
    id: uuid.UUID
    phone_number: str
    display_name: str | None = None
    profile_picture_url: str | None = None
    is_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    """Fields the user can update on their profile."""
    display_name: str | None = Field(None, max_length=100)
    profile_picture_url: str | None = Field(None, max_length=500)


class RefreshRequest(BaseModel):
    """Request to refresh a JWT token."""
    access_token: str
