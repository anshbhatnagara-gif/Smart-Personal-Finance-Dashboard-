"""Budget Pydantic v2 schemas for category spending envelope validation."""

import enum
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class BudgetStatus(str, enum.Enum):
    """Budget utilization classification status."""
    UNDER_BUDGET = "UNDER_BUDGET"
    ON_TRACK = "ON_TRACK"
    NEAR_LIMIT = "NEAR_LIMIT"
    OVER_BUDGET = "OVER_BUDGET"


class BudgetBase(BaseModel):
    """Base fields for category budget validation."""
    category: str = Field(..., min_length=1, max_length=100, description="Expense category")
    amount: Decimal = Field(..., gt=0, decimal_places=2, max_digits=12, description="Budget cap amount (> 0)")
    month: int = Field(..., ge=1, le=12, description="Calendar month index (1 to 12)")
    year: int = Field(..., ge=2000, le=2100, description="Calendar year (e.g. 2026)")


class BudgetCreate(BudgetBase):
    """Schema for setting a new category budget."""
    pass


class BudgetUpdate(BaseModel):
    """Schema for updating an existing category budget limit."""
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    amount: Optional[Decimal] = Field(None, gt=0, decimal_places=2, max_digits=12)
    month: Optional[int] = Field(None, ge=1, le=12)
    year: Optional[int] = Field(None, ge=2000, le=2100)


class BudgetResponse(BudgetBase):
    """Public schema for budget API responses with real-time calculated utilization."""
    id: int
    user_id: int
    spent: Decimal = Decimal("0.00")
    remaining: Decimal = Decimal("0.00")
    percentage: float = 0.0
    status: BudgetStatus = BudgetStatus.UNDER_BUDGET
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
