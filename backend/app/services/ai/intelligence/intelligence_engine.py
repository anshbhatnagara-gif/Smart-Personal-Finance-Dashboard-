"""Unified AI Financial Intelligence Engine: Master aggregator for all AI intelligence subsystems."""

from datetime import date
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.services.ai.intelligence.health_rules import HealthRules
from app.services.ai.forecasting.forecast_engine import ForecastingEngine
from app.services.ai.risk.risk_engine import RiskEngine
from app.services.ai.goals.goal_service import GoalService
from app.services.ai.automation.action_engine import SmartActionEngine
from app.services.ai.explainability.explanation_engine import ExplanationEngine
from app.services.ai.insights.insight_engine import InsightEngine


class UnifiedIntelligenceEngine:
    """Master single source of truth coordinating all deterministic intelligence providers."""

    def __init__(self, user_id: int, db: Session):
        self.user_id = user_id
        self.db = db

    def get_unified_intelligence(self, today: Optional[date] = None) -> Dict[str, Any]:
        """
        Aggregate all verified financial intelligence data for authenticated user.
        """
        calc_date = today or date.today()

        # 1. Health score
        health = HealthRules.evaluate_all_components(self.user_id, self.db, today=calc_date)

        # 2. Forecasts
        fc_engine = ForecastingEngine(self.user_id, self.db)
        forecast = fc_engine.get_full_forecast(calc_date)

        # 3. Risks
        risk_engine = RiskEngine(self.user_id, self.db)
        risks = risk_engine.evaluate_risks(calc_date)

        # 4. Goals
        goals = GoalService.get_all_goals_progress(db=self.db, user_id=self.user_id)

        # 5. Smart Actions
        action_engine = SmartActionEngine(self.user_id, self.db)
        raw_actions = action_engine.get_or_generate_actions(today=calc_date)
        actions = []
        for a in raw_actions:
            if hasattr(a, "action_id"):
                actions.append({
                    "action_id": a.action_id,
                    "action_type": a.action_type,
                    "title": a.title,
                    "description": a.description,
                    "verified_evidence": a.verified_evidence,
                    "financial_amount": float(a.financial_amount),
                    "expected_impact": a.expected_impact,
                    "risk_level": a.risk_level,
                    "requires_confirmation": a.requires_confirmation,
                    "status": a.status,
                    "created_at": a.created_at.isoformat() if a.created_at else None,
                    "expires_at": a.expires_at.isoformat() if a.expires_at else None,
                    "confirmed_at": a.confirmed_at.isoformat() if a.confirmed_at else None,
                    "executed_at": a.executed_at.isoformat() if a.executed_at else None,
                    "rejected_at": a.rejected_at.isoformat() if a.rejected_at else None,
                })
            elif isinstance(a, dict):
                actions.append(a)

        # 6. Explanations
        exp_engine = ExplanationEngine(self.user_id, self.db)
        explanations = exp_engine.get_explanations(today=calc_date)

        # 7. Proactive Insights
        insight_engine = InsightEngine(self.user_id, self.db)
        proactive_insights = insight_engine.generate_insights(month=calc_date.month, year=calc_date.year)

        return {
            "health_score": health,
            "forecast": forecast,
            "risks": risks,
            "goals": goals,
            "smart_actions": actions,
            "explanations": explanations,
            "proactive_insights": proactive_insights,
            "as_of_date": str(calc_date)
        }
