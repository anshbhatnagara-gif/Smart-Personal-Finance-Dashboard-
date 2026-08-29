"""Predictive Engine: Synthesizes forecasts, risks, goals, and proactive rules into prioritized predictive insights."""

from datetime import date
from decimal import Decimal
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.services.ai.forecasting.forecast_engine import ForecastingEngine
from app.services.ai.risk.risk_engine import RiskEngine
from app.services.ai.risk.risk_rules import RiskSeverity
from app.services.ai.predictions.prediction_formatter import PredictionFormatter


class PredictiveEngine:
    """Combines deterministic forecasts, active risk signals, and planning metrics into top 5 predictive insights."""

    MAX_PREDICTIVE_INSIGHTS = 5

    def __init__(self, user_id: int, db: Session):
        self.user_id = user_id
        self.db = db
        self.forecasting = ForecastingEngine(user_id, db)
        self.risk_engine = RiskEngine(user_id, db)

    def generate_predictions(self, target_date: date = None) -> List[Dict[str, Any]]:
        """
        Generate bounded, prioritized predictive insights.
        Each insight explicitly separates:
        - VERIFIED_FACT
        - FORECAST
        - RISK
        - AI_SUGGESTION
        """
        if not target_date:
            target_date = date.today()

        forecast_data = self.forecasting.get_full_forecast(target_date)
        risk_data = self.risk_engine.evaluate_risks(target_date)

        insights: List[Dict[str, Any]] = []

        # 1. Generate predictions from detected risks
        for r in risk_data.get("risks", []):
            insights.append({
                "prediction_type": r.get("risk_type"),
                "category": r.get("risk_type").replace("_RISK", "").replace("_", " ").title(),
                "severity": r.get("severity"),
                "title": r.get("title"),
                "verified_fact": r.get("verified_evidence"),
                "forecast": r.get("message"),
                "risk": r.get("explanation"),
                "ai_suggestion": r.get("recommended_action"),
                "priority_weight": self._severity_weight(r.get("severity"))
            })

        # 2. Generate budget exhaustion predictions (if not already included as a risk)
        for b in forecast_data.get("budget_exhaustion_forecast", []):
            if b.get("will_exceed_budget") and not any(i["prediction_type"] == "BUDGET_RISK" and b["category"] in i["title"] for i in insights):
                insights.append({
                    "prediction_type": "BUDGET_EXHAUSTION_PREDICTION",
                    "category": b["category"],
                    "severity": RiskSeverity.HIGH if b["projected_overrun_amount"] > 3000.0 else RiskSeverity.MEDIUM,
                    "title": f"Projected Budget Exhaustion in {b['category']}",
                    "verified_fact": f"Current spend is ₹{b['current_spent']:,.2f} of ₹{b['budget_amount']:,.2f} monthly budget.",
                    "forecast": f"At daily burn of ₹{b['daily_burn_rate']:,.2f}/day, spending will reach ₹{b['projected_month_end_spending']:,.2f}.",
                    "risk": f"Projected overrun of approximately ₹{b['projected_overrun_amount']:,.2f} before month end.",
                    "ai_suggestion": f"Limit further {b['category']} transactions to prevent exceeding your budget allocation.",
                    "priority_weight": 25
                })

        # 3. Positive predictive progress (e.g. strong savings rate or goal ahead)
        sav = forecast_data.get("savings_forecast", {})
        if sav.get("is_sufficient_data") and sav.get("projected_savings_rate_percentage", 0.0) >= 30.0:
            insights.append({
                "prediction_type": "POSITIVE_SAVINGS_TRAJECTORY",
                "category": "Savings",
                "severity": "POSITIVE",
                "title": "Strong Projected Savings Momentum",
                "verified_fact": f"Projected net monthly surplus is ₹{sav.get('projected_value', 0.0):,.2f}.",
                "forecast": f"Savings rate is projected to maintain a healthy {sav.get('projected_savings_rate_percentage', 0.0):.1f}% pace.",
                "risk": "Minimal risk if recurring expenses remain stable.",
                "ai_suggestion": "Consider channeling a portion of this projected surplus toward accelerated goal funding or emergency reserves.",
                "priority_weight": 5
            })

        # Sort insights by priority weight descending
        insights.sort(key=lambda x: -x["priority_weight"])

        # Cap at MAX_PREDICTIVE_INSIGHTS (5)
        return insights[:self.MAX_PREDICTIVE_INSIGHTS]

    def _severity_weight(self, severity: str) -> int:
        weights = {
            RiskSeverity.CRITICAL: 100,
            RiskSeverity.HIGH: 75,
            RiskSeverity.MEDIUM: 50,
            RiskSeverity.LOW: 20,
            "POSITIVE": 10
        }
        return weights.get(severity, 0)

    def get_formatted_xml(self, target_date: date = None) -> str:
        """Format predictive insights into XML block."""
        predictions = self.generate_predictions(target_date)
        return PredictionFormatter.format_predictions_xml(predictions)
