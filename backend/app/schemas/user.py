"""User Pydantic v2 schemas for request validation, authentication, and responses."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserBase(BaseModel):
    """Base fields shared across user schemas."""
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=100, description="User's full name")


class UserCreate(UserBase):
    """Schema for registering a new user."""
    password: str = Field(..., min_length=8, max_length=128, description="Plaintext password to be hashed")


class UserLogin(BaseModel):
    """Schema for authenticating an existing user."""
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)


class UserUpdate(BaseModel):
    """Schema for updating user profile fields."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8, max_length=128)


class UserResponse(UserBase):
    """Public user schema returned in API responses (password_hash strictly excluded)."""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    """JWT Access Token response envelope."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenPayload(BaseModel):
    """Decoded JWT payload structure."""
    sub: str
    exp: Optional[int] = None
    iat: Optional[int] = None
