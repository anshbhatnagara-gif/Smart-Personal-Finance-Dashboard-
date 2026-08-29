"""Goal Service: Database persistence, scoped queries, and goal calculations."""

from decimal import Decimal
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.goal import Goal
from app.services.ai.goals.goal_validator import GoalValidator
from app.services.ai.goals.goal_calculator import GoalCalculator


class GoalService:
    """Service layer managing Goal entities with strict user-id scoping."""

    @staticmethod
    def create_goal(db: Session, user_id: int, goal_data: Dict[str, Any]) -> Goal:
        """Create a new financial goal strictly owned by authenticated user_id."""
        cleaned = GoalValidator.validate_goal_data(goal_data, is_update=False)
        goal = Goal(
            user_id=user_id,
            name=cleaned["name"],
            target_amount=cleaned["target_amount"],
            current_amount=cleaned.get("current_amount", Decimal("0.00")),
            target_date=cleaned["target_date"],
            category=cleaned.get("category", "savings"),
            priority=cleaned.get("priority", "medium")
        )
        db.add(goal)
        db.commit()
        db.refresh(goal)
        return goal

    @staticmethod
    def get_goals(db: Session, user_id: int) -> List[Goal]:
        """Fetch all financial goals owned by user_id."""
        return db.query(Goal).filter(
            Goal.user_id == user_id
        ).order_by(Goal.target_date.asc(), Goal.priority.desc()).all()

    @staticmethod
    def get_goal(db: Session, user_id: int, goal_id: int) -> Optional[Goal]:
        """Fetch a specific financial goal with strict ownership verification."""
        return db.query(Goal).filter(
            Goal.id == goal_id,
            Goal.user_id == user_id
        ).first()

    @staticmethod
    def update_goal(
        db: Session,
        user_id: int,
        goal_id: int,
        update_data: Dict[str, Any]
    ) -> Optional[Goal]:
        """Update an existing financial goal with validation and ownership check."""
        goal = GoalService.get_goal(db, user_id, goal_id)
        if not goal:
            return None

        cleaned = GoalValidator.validate_goal_data(update_data, is_update=True)

        if "name" in cleaned:
            goal.name = cleaned["name"]
        if "target_amount" in cleaned:
            goal.target_amount = cleaned["target_amount"]
        if "current_amount" in cleaned:
            goal.current_amount = cleaned["current_amount"]
        if "target_date" in cleaned:
            goal.target_date = cleaned["target_date"]
        if "category" in cleaned:
            goal.category = cleaned["category"]
        if "priority" in cleaned:
            goal.priority = cleaned["priority"]

        db.commit()
        db.refresh(goal)
        return goal

    @staticmethod
    def delete_goal(db: Session, user_id: int, goal_id: int) -> bool:
        """Delete a financial goal owned by user_id."""
        goal = GoalService.get_goal(db, user_id, goal_id)
        if not goal:
            return False
        db.delete(goal)
        db.commit()
        return True

    @staticmethod
    def get_goal_progress(
        db: Session,
        user_id: int,
        goal_id: int,
        monthly_pace: Optional[Decimal] = None
    ) -> Optional[Dict[str, Any]]:
        """Get calculated progress breakdown for a single goal."""
        goal = GoalService.get_goal(db, user_id, goal_id)
        if not goal:
            return None
        return GoalCalculator.calculate_progress(goal, monthly_savings_pace=monthly_pace)

    @staticmethod
    def get_all_goals_progress(
        db: Session,
        user_id: int,
        monthly_pace: Optional[Decimal] = None
    ) -> List[Dict[str, Any]]:
        """Get progress breakdowns for all active goals owned by user_id."""
        goals = GoalService.get_goals(db, user_id)
        return [
            GoalCalculator.calculate_progress(g, monthly_savings_pace=monthly_pace)
            for g in goals
        ]
