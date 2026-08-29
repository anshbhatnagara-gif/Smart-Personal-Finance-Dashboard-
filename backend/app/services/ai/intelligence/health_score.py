"""Health Score Engine: Coordinator for deterministic financial health assessment."""

from datetime import date
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.services.ai.intelligence.health_rules import HealthRules


class HealthScoreEngine:
    """Master evaluator for user financial health scoring."""

    def __init__(self, user_id: int, db: Session):
        self.user_id = user_id
        self.db = db

    def evaluate_health(self, today: Optional[date] = None) -> Dict[str, Any]:
        """
        Evaluate full 7-dimension financial health score strictly for authenticated user.
        """
        return HealthRules.evaluate_all_components(self.user_id, self.db, today=today)
