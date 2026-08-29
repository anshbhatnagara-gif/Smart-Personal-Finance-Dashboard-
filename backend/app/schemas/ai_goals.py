"""Pydantic v2 schemas for Financial Goals API and Progress Breakdowns."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class GoalBase(BaseModel):
    """Base fields for financial goals."""
    name: str = Field(..., min_length=1, max_length=150, description="Display name for the goal")
    target_amount: Decimal = Field(..., gt=Decimal("0.00"), description="Target amount in INR")
    current_amount: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"), description="Current amount saved in INR")
    target_date: date = Field(..., description="Target completion date (YYYY-MM-DD)")
    category: str = Field(default="savings", description="Goal category type")
    priority: str = Field(default="medium", description="Priority level: low, medium, high, critical")


class GoalCreate(GoalBase):
    """Payload for creating a new financial goal."""
    pass


class GoalUpdate(BaseModel):
    """Payload for updating an existing financial goal."""
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    target_amount: Optional[Decimal] = Field(None, gt=Decimal("0.00"))
    current_amount: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    target_date: Optional[date] = None
    category: Optional[str] = None
    priority: Optional[str] = None


class GoalResponse(BaseModel):
    """Goal entity response schema."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    name: str
    target_amount: float
    current_amount: float
    target_date: str
    category: str
    priority: str
    created_at: str
    updated_at: str


class GoalProgressResponse(BaseModel):
    """Progress metrics and contribution requirements for a goal."""
    goal_id: int
    name: str
    target_amount: float
    current_amount: float
    remaining_amount: float
    progress_percentage: float
    target_date: str
    days_remaining: int
    months_remaining: float
    required_monthly_contribution: float
    required_weekly_contribution: float
    status: str
    projected_completion_date: Optional[str] = None
    category: str
    priority: str


class GoalListResponse(BaseModel):
    """List response envelope for financial goals."""
    goals: List[GoalProgressResponse]
    total_goals: int
    total_target_amount: float
    total_saved_amount: float
    total_remaining_amount: float
