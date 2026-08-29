"""Expense Forecast Engine: Projects next-period spending overall and by category."""

from datetime import date
from decimal import Decimal
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.models.transaction import Transaction, TransactionType
from app.services.ai.forecasting.forecast_rules import ForecastRules, ForecastConfidence


class ExpenseForecastEngine:
    """Calculates deterministic expense projections overall and per category."""

    def __init__(self, user_id: int, db: Session):
        self.user_id = user_id
        self.db = db

    def project_expenses(self, target_date: date = None) -> Dict[str, Any]:
        """
        Generate next-month expense forecast overall and broken down by category.
        """
        if not target_date:
            target_date = date.today()

        # Query all historical expense transactions
        txs = (
            self.db.query(Transaction)
            .filter(
                Transaction.user_id == self.user_id,
                Transaction.type == TransactionType.EXPENSE
            )
            .order_by(Transaction.transaction_date.asc())
            .all()
        )

        if not txs:
            return {
                "metric": "Monthly Expenses",
                "current_value": 0.0,
                "projected_value": 0.0,
                "period": "Next Month",
                "confidence": ForecastConfidence.INSUFFICIENT,
                "methodology": "No historical expense records available.",
                "trend_percentage": 0.0,
                "category_forecasts": {},
                "evidence": ["0 verified expense transactions in database."],
                "limitations": "Requires at least 1 recorded expense transaction.",
                "is_sufficient_data": False
            }

        # Monthly total mapping & category mapping
        monthly_total_map: Dict[str, Decimal] = {}
        category_monthly_map: Dict[str, Dict[str, Decimal]] = {}

        for t in txs:
            m_key = f"{t.transaction_date.year}-{t.transaction_date.month:02d}"
            amt = Decimal(str(t.amount))
            cat = t.category.title()

            monthly_total_map[m_key] = monthly_total_map.get(m_key, Decimal("0.00")) + amt
            if cat not in category_monthly_map:
                category_monthly_map[cat] = {}
            category_monthly_map[cat][m_key] = category_monthly_map[cat].get(m_key, Decimal("0.00")) + amt

        sorted_months = sorted(monthly_total_map.keys())
        monthly_values = [monthly_total_map[m] for m in sorted_months]

        current_value = float(monthly_values[-1])
        projected_decimal = ForecastRules.calculate_weighted_average(monthly_values)
        projected_value = float(projected_decimal)
        trend_pct = ForecastRules.calculate_trend_rate(monthly_values)
        confidence = ForecastRules.calculate_confidence(len(sorted_months), len(txs))

        # Category forecasts
        category_forecasts: Dict[str, Dict[str, Any]] = {}
        for cat, m_dict in category_monthly_map.items():
            cat_vals = [m_dict.get(m, Decimal("0.00")) for m in sorted_months]
            cat_proj = float(ForecastRules.calculate_weighted_average(cat_vals))
            cat_curr = float(cat_vals[-1])
            cat_trend = ForecastRules.calculate_trend_rate(cat_vals)
            category_forecasts[cat] = {
                "category": cat,
                "current_spending": round(cat_curr, 2),
                "projected_spending": round(cat_proj, 2),
                "trend_percentage": cat_trend
            }

        evidence = [
            f"Analyzed {len(txs)} verified expense transaction(s) across {len(sorted_months)} month(s).",
            f"Most recent monthly spending: ₹{current_value:,.2f}.",
            f"Projected baseline outflow for next month: ₹{projected_value:,.2f} across {len(category_forecasts)} categories."
        ]

        return {
            "metric": "Monthly Expenses",
            "current_value": round(current_value, 2),
            "projected_value": round(projected_value, 2),
            "period": "Next Month",
            "confidence": confidence,
            "methodology": "Linearly weighted rolling average with category component breakdown.",
            "trend_percentage": trend_pct,
            "category_forecasts": category_forecasts,
            "evidence": evidence,
            "limitations": "Excludes irregular one-off capital expenditures and assumes consistent recurring habits.",
            "is_sufficient_data": True
        }
