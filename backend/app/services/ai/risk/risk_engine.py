"""Risk Engine: Main orchestrator for evaluating financial risk rules against verified user data."""

from datetime import date
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.services.ai.forecasting.cashflow_forecast import CashflowForecastEngine
from app.services.ai.risk.risk_rules import RiskRules, RiskSeverity
from app.services.ai.risk.risk_formatter import RiskFormatter


class RiskEngine:
    """Evaluates all deterministic risk rules and aggregates stress scores."""

    SEVERITY_ORDER = {
        RiskSeverity.CRITICAL: 1,
        RiskSeverity.HIGH: 2,
        RiskSeverity.MEDIUM: 3,
        RiskSeverity.LOW: 4,
        RiskSeverity.NONE: 5
    }

    def __init__(self, user_id: int, db: Session):
        self.user_id = user_id
        self.db = db
        self.forecast_engine = CashflowForecastEngine(user_id, db)

    def evaluate_risks(self, target_date: date = None) -> Dict[str, Any]:
        """
        Evaluate all 10 risk rules and return prioritized risk report.
        """
        if not target_date:
            target_date = date.today()

        forecast_data = self.forecast_engine.generate_full_forecast(target_date)

        detected_risks: List[Dict[str, Any]] = []

        # Execute 9 rule evaluators
        rule_evaluators = [
            RiskRules.evaluate_cashflow_risk,
            RiskRules.evaluate_savings_risk,
            RiskRules.evaluate_budget_risk,
            RiskRules.evaluate_goal_risk,
            RiskRules.evaluate_expense_growth_risk,
            RiskRules.evaluate_income_decline_risk,
            RiskRules.evaluate_emergency_buffer_risk,
            RiskRules.evaluate_discretionary_risk,
            RiskRules.evaluate_debt_pressure_risk
        ]

        for ev in rule_evaluators:
            res = ev(forecast_data)
            if res:
                detected_risks.append(res)

        # Sort risks deterministically by severity then affected amount
        detected_risks.sort(
            key=lambda r: (
                self.SEVERITY_ORDER.get(r["severity"], 99),
                -r.get("affected_amount", 0.0)
            )
        )

        stress_summary = RiskRules.calculate_overall_stress(detected_risks)

        return {
            "risks": detected_risks,
            "total_risks": len(detected_risks),
            "stress_summary": stress_summary,
            "forecast_basis": {
                "projected_income": forecast_data.get("income_forecast", {}).get("projected_value", 0.0),
                "projected_expenses": forecast_data.get("expense_forecast", {}).get("projected_value", 0.0),
                "projected_savings": forecast_data.get("savings_forecast", {}).get("projected_value", 0.0),
                "confidence": forecast_data.get("savings_forecast", {}).get("confidence", "INSUFFICIENT_DATA")
            }
        }

    def get_formatted_xml(self, target_date: date = None) -> str:
        """Format risks into XML block for prompt builder."""
        data = self.evaluate_risks(target_date)
        return RiskFormatter.format_risks_xml(data)
