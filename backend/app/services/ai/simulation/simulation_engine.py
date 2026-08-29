"""Simulation Engine: Master coordinator for hypothetical what-if financial projections."""

from datetime import date
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.services.ai.simulation.simulation_rules import SimulationRules


class SimulationEngine:
    """Master evaluator for what-if simulations with zero database mutations."""

    def __init__(self, user_id: int, db: Session):
        self.user_id = user_id
        self.db = db

    def simulate(
        self,
        scenario: str,
        amount: Optional[float] = None,
        percentage: Optional[float] = None,
        months: Optional[int] = None,
        goal_id: Optional[int] = None,
        category: Optional[str] = None,
        today: Optional[date] = None
    ) -> Dict[str, Any]:
        """Run in-memory simulation for authenticated user."""
        return SimulationRules.run_simulation(
            user_id=self.user_id,
            db=self.db,
            scenario=scenario,
            amount=amount,
            percentage=percentage,
            months=months,
            goal_id=goal_id,
            category=category,
            today=today
        )

    def get_preset_examples(self) -> List[Dict[str, Any]]:
        """Return recommended preset scenario simulations for one-click user exploration."""
        return [
            {
                "scenario": "INCREASE_SAVINGS",
                "title": "Increase Monthly Savings by ₹5,000",
                "description": "Evaluate impact on goal completion velocity and savings rate.",
                "payload": {"scenario": "INCREASE_SAVINGS", "amount": 5000.0}
            },
            {
                "scenario": "REDUCE_EXPENSES",
                "title": "Trim Discretionary Outflows by 15%",
                "description": "Simulate monthly cashflow surplus unlocked by optimizing spending.",
                "payload": {"scenario": "REDUCE_EXPENSES", "percentage": 15.0}
            },
            {
                "scenario": "INCOME_INCREASE",
                "title": "Simulate 10% Salary Increment",
                "description": "Project expanded investment capacity and financial health score improvement.",
                "payload": {"scenario": "INCOME_INCREASE", "percentage": 10.0}
            },
            {
                "scenario": "GOAL_DEADLINE_CHANGE",
                "title": "Accelerate Goal Deadline by 3 Months",
                "description": "Calculate required monthly pace adjustment to finish goals earlier.",
                "payload": {"scenario": "GOAL_DEADLINE_CHANGE", "months": -3}
            }
        ]
