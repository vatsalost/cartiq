"""Authentication request and response schemas."""

from datetime import datetime
import re
from typing import Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field, field_validator


class RegisterRequest(BaseModel):
    """Payload to register a new user account."""

    email: str = Field(..., description="User's valid email address")
    password: str = Field(..., min_length=8, max_length=128, description="Password (at least 8 characters)")

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        clean = v.strip().lower()
        email_regex = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
        if not re.match(email_regex, clean):
            raise ValueError("Invalid email format.")
        return clean

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters.")
        if not any(c.isalpha() for c in v) or not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one letter and one number.")
        return v


class LoginRequest(BaseModel):
    """Payload to authenticate an existing user."""

    email: str = Field(..., description="User email")
    password: str = Field(..., min_length=1, description="Password")

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class DemoLoginRequest(BaseModel):
    """Payload for isolated demo login in development mode."""

    demo_identifier: Optional[str] = Field(None, max_length=64, description="Optional custom identifier for isolated demo session")


class UserSafeProfile(BaseModel):
    """Safe user profile excluding credentials."""

    id: uuid.UUID
    email: str
    status: str = "active"
    is_active: bool = True
    authenticated: bool = True

    model_config = ConfigDict(from_attributes=True)


class AuthResponse(BaseModel):
    """Authentication response returning safe profile and token."""

    user: UserSafeProfile
    token: str
    token_type: str = "bearer"
    expires_at: datetime


class AuthStatusResponse(BaseModel):
    """Public authentication status response."""

    authenticated: bool
    user: Optional[UserSafeProfile] = None


class LogoutResponse(BaseModel):
    """Logout confirmation response."""

    status: str = "logged_out"
    message: str = "Successfully logged out."
