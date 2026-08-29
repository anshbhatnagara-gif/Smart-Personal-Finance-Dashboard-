"""Budgets Router: Category envelope creation, utilization tracking, and updates."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Path, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.common import ResponseBase
from app.schemas.budget import BudgetCreate, BudgetUpdate, BudgetResponse
from app.services.budget_service import BudgetService

router = APIRouter(prefix="/budgets", tags=["Budgets"])


@router.get(
    "",
    response_model=ResponseBase[List[BudgetResponse]],
    status_code=status.HTTP_200_OK,
    summary="List User Budgets with Live Utilization"
)
async def list_budgets(
    month: Optional[int] = Query(None, ge=1, le=12, description="Month filter (1-12)"),
    year: Optional[int] = Query(None, ge=2000, le=2100, description="Year filter (e.g. 2026)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ResponseBase[List[BudgetResponse]]:
    """Retrieve all budget envelopes for the user with live calculated spent amount, remaining buffer, and status."""
    budgets = BudgetService.get_budgets(
        db=db,
        user_id=current_user.id,
        month=month,
        year=year
    )
    return ResponseBase(
        success=True,
        message=f"Retrieved {len(budgets)} budget envelopes",
        data=budgets
    )


@router.post(
    "",
    response_model=ResponseBase[BudgetResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create Category Budget Envelope"
)
async def create_budget(
    budget_in: BudgetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ResponseBase[BudgetResponse]:
    """Create a new category budget limit for a specific month and year."""
    budget = BudgetService.create_budget(db, current_user.id, budget_in)
    return ResponseBase(
        success=True,
        message=f"Budget for '{budget.category}' set to {budget.amount}",
        data=budget
    )


@router.put(
    "/{id}",
    response_model=ResponseBase[BudgetResponse],
    status_code=status.HTTP_200_OK,
    summary="Update Category Budget"
)
async def update_budget(
    budget_update: BudgetUpdate,
    id: int = Path(..., ge=1, description="Budget ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ResponseBase[BudgetResponse]:
    """Update limit, category, or period for an existing budget envelope."""
    budget = BudgetService.update_budget(db, id, current_user.id, budget_update)
    return ResponseBase(
        success=True,
        message="Budget updated successfully",
        data=budget
    )


@router.delete(
    "/{id}",
    response_model=ResponseBase[dict],
    status_code=status.HTTP_200_OK,
    summary="Delete Budget Envelope"
)
async def delete_budget(
    id: int = Path(..., ge=1, description="Budget ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ResponseBase[dict]:
    """Delete a budget envelope owned by user."""
    BudgetService.delete_budget(db, id, current_user.id)
    return ResponseBase(
        success=True,
        message=f"Budget with ID {id} deleted successfully",
        data={"deleted_id": id}
    )
