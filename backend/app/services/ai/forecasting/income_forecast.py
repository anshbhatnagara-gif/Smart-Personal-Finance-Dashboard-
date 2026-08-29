"""Income Forecast Engine: Projects next-period income based on historical income transactions."""

from datetime import date
from decimal import Decimal
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.models.transaction import Transaction, TransactionType
from app.services.ai.forecasting.forecast_rules import ForecastRules, ForecastConfidence


class IncomeForecastEngine:
    """Calculates deterministic income projections using verified user data."""

    def __init__(self, user_id: int, db: Session):
        self.user_id = user_id
        self.db = db

    def project_income(self, target_date: date = None) -> Dict[str, Any]:
        """
        Generate next-month income forecast.
        Returns structured dictionary with verified facts, projected value, and confidence.
        """
        if not target_date:
            target_date = date.today()

        # Query all historical income transactions
        txs = (
            self.db.query(Transaction)
            .filter(
                Transaction.user_id == self.user_id,
                Transaction.type == TransactionType.INCOME
            )
            .order_by(Transaction.transaction_date.asc())
            .all()
        )

        if not txs:
            return {
                "metric": "Monthly Income",
                "current_value": 0.0,
                "projected_value": 0.0,
                "period": "Next Month",
                "confidence": ForecastConfidence.INSUFFICIENT,
                "methodology": "No historical income records available.",
                "trend_percentage": 0.0,
                "evidence": ["0 verified income transactions in database."],
                "limitations": "Projections require at least 1 recorded income transaction.",
                "is_sufficient_data": False
            }

        # Aggregate monthly totals
        monthly_map: Dict[str, Decimal] = {}
        for t in txs:
            m_key = f"{t.transaction_date.year}-{t.transaction_date.month:02d}"
            monthly_map[m_key] = monthly_map.get(m_key, Decimal("0.00")) + Decimal(str(t.amount))

        sorted_months = sorted(monthly_map.keys())
        monthly_values = [monthly_map[m] for m in sorted_months]
        
        current_value = float(monthly_values[-1])
        projected_decimal = ForecastRules.calculate_weighted_average(monthly_values)
        projected_value = float(projected_decimal)
        trend_pct = ForecastRules.calculate_trend_rate(monthly_values)
        confidence = ForecastRules.calculate_confidence(len(monthly_values), len(txs))

        evidence = [
            f"Analyzed {len(txs)} verified income transaction(s) across {len(monthly_values)} month(s).",
            f"Most recent recorded monthly income: ₹{current_value:,.2f}.",
            f"Weighted historical income baseline: ₹{projected_value:,.2f}."
        ]

        return {
            "metric": "Monthly Income",
            "current_value": round(current_value, 2),
            "projected_value": round(projected_value, 2),
            "period": "Next Month",
            "confidence": confidence,
            "methodology": "Weighted rolling average of verified historical income cycles.",
            "trend_percentage": trend_pct,
            "evidence": evidence,
            "limitations": "Assumes continued recurring income streams without unforeseen disruptions.",
            "is_sufficient_data": True
        }
