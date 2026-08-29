"""Transaction Pydantic v2 schemas for financial validation."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

from app.models.transaction import TransactionType


class TransactionBase(BaseModel):
    """Base fields for transaction validation."""
    type: TransactionType
    title: str = Field(..., min_length=1, max_length=255, description="Short title or payee")
    description: Optional[str] = Field(None, max_length=500, description="Detailed notes")
    amount: Decimal = Field(..., gt=0, decimal_places=2, max_digits=12, description="Monetary value (> 0)")
    category: str = Field(..., min_length=1, max_length=100, description="Category name")
    transaction_date: date = Field(..., description="Date transaction occurred")


class TransactionCreate(TransactionBase):
    """Schema for creating a new transaction record."""
    pass


class TransactionUpdate(BaseModel):
    """Schema for updating an existing transaction."""
    type: Optional[TransactionType] = None
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    amount: Optional[Decimal] = Field(None, gt=0, decimal_places=2, max_digits=12)
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    transaction_date: Optional[date] = None


class TransactionResponse(TransactionBase):
    """Public schema for transaction API responses."""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
