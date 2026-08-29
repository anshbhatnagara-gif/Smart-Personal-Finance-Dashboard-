"""Savings Forecast Engine: Projects next-period savings, savings rate, and 6-month cash trajectory."""

from datetime import date
from decimal import Decimal
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.services.ai.forecasting.income_forecast import IncomeForecastEngine
from app.services.ai.forecasting.expense_forecast import ExpenseForecastEngine
from app.services.ai.forecasting.forecast_rules import ForecastConfidence


class SavingsForecastEngine:
    """Calculates deterministic savings projections, rates, and cash balance trends."""

    def __init__(self, user_id: int, db: Session):
        self.user_id = user_id
        self.db = db
        self.income_engine = IncomeForecastEngine(user_id, db)
        self.expense_engine = ExpenseForecastEngine(user_id, db)

    def project_savings(self, target_date: date = None) -> Dict[str, Any]:
        """
        Generate next-month net savings forecast and 6-month balance trend projection.
        """
        inc_data = self.income_engine.project_income(target_date)
        exp_data = self.expense_engine.project_expenses(target_date)

        if not inc_data["is_sufficient_data"] and not exp_data["is_sufficient_data"]:
            return {
                "metric": "Monthly Net Savings",
                "current_value": 0.0,
                "projected_value": 0.0,
                "projected_savings_rate_percentage": 0.0,
                "period": "Next Month",
                "confidence": ForecastConfidence.INSUFFICIENT,
                "methodology": "No historical transactions available.",
                "cash_balance_trend_6m": [],
                "evidence": ["0 verified transactions available for cashflow extrapolation."],
                "limitations": "Projections require recorded financial transactions.",
                "is_sufficient_data": False
            }

        curr_inc = Decimal(str(inc_data["current_value"]))
        curr_exp = Decimal(str(exp_data["current_value"]))
        current_savings = float(curr_inc - curr_exp)

        proj_inc = Decimal(str(inc_data["projected_value"]))
        proj_exp = Decimal(str(exp_data["projected_value"]))
        projected_savings = float(proj_inc - proj_exp)

        # Projected savings rate
        if proj_inc > Decimal("0.00"):
            proj_savings_rate = float(round((Decimal(str(projected_savings)) / proj_inc) * Decimal("100.0"), 2))
        else:
            proj_savings_rate = 0.0

        # Confidence is minimum of income and expense confidence
        if inc_data["confidence"] == ForecastConfidence.HIGH and exp_data["confidence"] == ForecastConfidence.HIGH:
            confidence = ForecastConfidence.HIGH
        elif inc_data["confidence"] == ForecastConfidence.INSUFFICIENT or exp_data["confidence"] == ForecastConfidence.INSUFFICIENT:
            confidence = ForecastConfidence.LOW
        else:
            confidence = ForecastConfidence.MEDIUM

        # 6-Month cumulative cash balance trend
        trend_6m: List[Dict[str, Any]] = []
        cumulative = Decimal("0.00")
        monthly_net = Decimal(str(projected_savings))

        for month_offset in range(1, 7):
            cumulative += monthly_net
            trend_6m.append({
                "month_offset": month_offset,
                "projected_monthly_savings": round(float(monthly_net), 2),
                "cumulative_projected_surplus": round(float(cumulative), 2)
            })

        evidence = [
            f"Projected Monthly Income: ₹{float(proj_inc):,.2f}.",
            f"Projected Monthly Expenses: ₹{float(proj_exp):,.2f}.",
            f"Projected Net Monthly Savings: ₹{projected_savings:,.2f} ({proj_savings_rate}% savings rate)."
        ]

        return {
            "metric": "Monthly Net Savings",
            "current_value": round(current_savings, 2),
            "projected_value": round(projected_savings, 2),
            "projected_savings_rate_percentage": proj_savings_rate,
            "period": "Next Month",
            "confidence": confidence,
            "methodology": "Synthesized net residual cashflow (Projected Income - Projected Expenses).",
            "cash_balance_trend_6m": trend_6m,
            "evidence": evidence,
            "limitations": "Assumes consistent monthly income and no unforeseen emergency expenditures.",
            "is_sufficient_data": True
        }
