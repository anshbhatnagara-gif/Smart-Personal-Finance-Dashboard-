"""Explanation Engine: Coordinator for structured AI explainability."""

from datetime import date
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.services.ai.explainability.explanation_rules import ExplanationRules


class ExplanationEngine:
    """Master evaluator for grounded mathematical explanations."""

    def __init__(self, user_id: int, db: Session):
        self.user_id = user_id
        self.db = db

    def get_explanations(self, today: Optional[date] = None) -> List[Dict[str, Any]]:
        """Retrieve all active explanations across financial domains."""
        return ExplanationRules.generate_all_explanations(self.user_id, self.db, today=today)

    def get_explanation_by_type(self, explanation_type: str, today: Optional[date] = None) -> Dict[str, Any]:
        """Fetch explanation matching a specific category (e.g. WHY_THIS_HEALTH_SCORE)."""
        all_exp = self.get_explanations(today=today)
        target = next((e for e in all_exp if e["explanation_type"].upper() == explanation_type.upper()), None)
        if not target:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Explanation for type '{explanation_type}' not found."
            )
        return target
