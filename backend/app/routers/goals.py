"""FastAPI Router for Financial Goals, Progress Tracking, and What-If Scenarios."""

from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.routers.auth import get_current_user
from app.services.ai.goals.goal_service import GoalService
from app.services.ai.planning.planning_engine import PlanningEngine
from app.services.ai.planning.scenario_engine import ScenarioEngine
from app.schemas.ai_goals import (
    GoalCreate,
    GoalUpdate,
    GoalResponse,
    GoalProgressResponse,
    GoalListResponse
)
from app.schemas.ai_planning import (
    GoalScenarioRequest,
    GoalScenarioResponse
)
from app.schemas.common import ResponseBase

router = APIRouter(prefix="/ai/goals", tags=["Financial Goals & Planning"])


@router.get("", response_model=ResponseBase[GoalListResponse])
def get_user_goals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all financial goals for the authenticated user with progress metrics."""
    planning = PlanningEngine(current_user.id, db)
    coaching = planning.generate_coaching_context()
    monthly_pace = Decimal(str(coaching["cashflow"]["net_monthly_savings"]))

    goals_progress = GoalService.get_all_goals_progress(db, current_user.id, monthly_pace=monthly_pace)

    total_target = sum((p["target_amount"] for p in goals_progress), 0.0)
    total_saved = sum((p["current_amount"] for p in goals_progress), 0.0)
    total_remaining = sum((p["remaining_amount"] for p in goals_progress), 0.0)

    return ResponseBase(
        success=True,
        message="Financial goals retrieved successfully.",
        data=GoalListResponse(
            goals=[GoalProgressResponse(**p) for p in goals_progress],
            total_goals=len(goals_progress),
            total_target_amount=total_target,
            total_saved_amount=total_saved,
            total_remaining_amount=total_remaining
        )
    )


@router.post("", response_model=ResponseBase[GoalProgressResponse], status_code=status.HTTP_201_CREATED)
def create_user_goal(
    payload: GoalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new financial goal strictly scoped to the authenticated user."""
    try:
        goal = GoalService.create_goal(db, current_user.id, payload.model_dump())
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )

    progress = GoalService.get_goal_progress(db, current_user.id, goal.id)
    return ResponseBase(
        success=True,
        message="Financial goal created successfully.",
        data=GoalProgressResponse(**progress)
    )


@router.get("/{goal_id}", response_model=ResponseBase[GoalProgressResponse])
def get_user_goal(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get single goal details with verified progress metrics."""
    progress = GoalService.get_goal_progress(db, current_user.id, goal_id)
    if not progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Financial goal not found or access denied."
        )

    return ResponseBase(
        success=True,
        message="Financial goal retrieved successfully.",
        data=GoalProgressResponse(**progress)
    )


@router.patch("/{goal_id}", response_model=ResponseBase[GoalProgressResponse])
def update_user_goal(
    goal_id: int,
    payload: GoalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update goal targets, dates, or saved amounts with ownership check."""
    update_data = {k: v for k, v in payload.model_dump().items() if v is not None}
    try:
        goal = GoalService.update_goal(db, current_user.id, goal_id, update_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )

    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Financial goal not found or access denied."
        )

    progress = GoalService.get_goal_progress(db, current_user.id, goal.id)
    return ResponseBase(
        success=True,
        message="Financial goal updated successfully.",
        data=GoalProgressResponse(**progress)
    )


@router.delete("/{goal_id}", response_model=ResponseBase[dict])
def delete_user_goal(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a financial goal with strict ownership verification."""
    deleted = GoalService.delete_goal(db, current_user.id, goal_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Financial goal not found or access denied."
        )

    return ResponseBase(
        success=True,
        message="Financial goal deleted successfully.",
        data={"deleted_goal_id": goal_id}
    )


@router.get("/{goal_id}/progress", response_model=ResponseBase[GoalProgressResponse])
def get_user_goal_progress(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed contribution breakdown and completion estimates for a goal."""
    planning = PlanningEngine(current_user.id, db)
    coaching = planning.generate_coaching_context()
    monthly_pace = Decimal(str(coaching["cashflow"]["net_monthly_savings"]))

    progress = GoalService.get_goal_progress(db, current_user.id, goal_id, monthly_pace=monthly_pace)
    if not progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Financial goal not found or access denied."
        )

    return ResponseBase(
        success=True,
        message="Goal progress calculated successfully.",
        data=GoalProgressResponse(**progress)
    )


@router.post("/{goal_id}/scenario", response_model=ResponseBase[GoalScenarioResponse])
def run_user_goal_scenario(
    goal_id: int,
    payload: GoalScenarioRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Run a deterministic 'What-If' simulation for a specific goal."""
    goal = GoalService.get_goal(db, current_user.id, goal_id)
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Financial goal not found or access denied."
        )

    planning = PlanningEngine(current_user.id, db)
    coaching = planning.generate_coaching_context()
    income = Decimal(str(coaching["cashflow"]["monthly_income"]))
    expenses = Decimal(str(coaching["cashflow"]["monthly_expenses"]))

    try:
        res = ScenarioEngine.run_scenario(
            scenario_type=payload.scenario_type,
            goal=goal,
            baseline_income=income,
            baseline_expenses=expenses,
            params=payload.model_dump()
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )

    return ResponseBase(
        success=True,
        message="Scenario simulation calculated successfully.",
        data=GoalScenarioResponse(**res)
    )
