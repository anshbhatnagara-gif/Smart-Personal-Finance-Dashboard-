"""Cashflow Forecast Engine: Comprehensive financial outlook integrating cashflow, budgets, and goals."""

from datetime import date
from decimal import Decimal
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.models.budget import Budget
from app.models.goal import Goal
from app.models.transaction import Transaction, TransactionType
from app.services.ai.forecasting.income_forecast import IncomeForecastEngine
from app.services.ai.forecasting.expense_forecast import ExpenseForecastEngine
from app.services.ai.forecasting.savings_forecast import SavingsForecastEngine
from app.services.ai.goals.goal_calculator import GoalCalculator


class CashflowForecastEngine:
    """Consolidates complete deterministic financial forecasts including budget burn and goal timelines."""

    def __init__(self, user_id: int, db: Session):
        self.user_id = user_id
        self.db = db
        self.income_engine = IncomeForecastEngine(user_id, db)
        self.expense_engine = ExpenseForecastEngine(user_id, db)
        self.savings_engine = SavingsForecastEngine(user_id, db)

    def generate_full_forecast(self, target_date: date = None, today: date = None) -> Dict[str, Any]:
        """
        Synthesize complete predictive forecast model.
        """
        calc_date = today or target_date or date.today()

        income_fc = self.income_engine.project_income(calc_date)
        expense_fc = self.expense_engine.project_expenses(calc_date)
        savings_fc = self.savings_engine.project_savings(calc_date)

        # Budget exhaustion projections
        budget_burn = self._calculate_budget_exhaustion(calc_date)

        # Goal completion projections
        monthly_pace = Decimal(str(savings_fc.get("projected_value", 0.0)))
        goal_projections = self._calculate_goal_projections(monthly_pace, calc_date)

        return {
            "income_forecast": income_fc,
            "expense_forecast": expense_fc,
            "savings_forecast": savings_fc,
            "budget_exhaustion_forecast": budget_burn,
            "goal_completion_forecast": goal_projections,
            "is_sufficient_data": income_fc["is_sufficient_data"] or expense_fc["is_sufficient_data"]
        }

    def _calculate_budget_exhaustion(self, today: date) -> List[Dict[str, Any]]:
        """Calculate daily spending burn rate and projected budget exhaustion day."""
        import calendar
        month_days = calendar.monthrange(today.year, today.month)[1]
        days_elapsed = max(today.day, 1)
        days_remaining = max(month_days - days_elapsed, 0)

        budgets = (
            self.db.query(Budget)
            .filter(
                Budget.user_id == self.user_id,
                Budget.month == today.month,
                Budget.year == today.year
            )
            .all()
        )

        results = []
        for b in budgets:
            spent_txs = (
                self.db.query(Transaction)
                .filter(
                    Transaction.user_id == self.user_id,
                    Transaction.type == TransactionType.EXPENSE,
                    Transaction.category == b.category,
                    Transaction.transaction_date >= date(today.year, today.month, 1),
                    Transaction.transaction_date <= today
                )
                .all()
            )
            spent_total = sum((Decimal(str(t.amount)) for t in spent_txs), Decimal("0.00"))
            b_amt = Decimal(str(b.amount))

            daily_burn = spent_total / Decimal(str(days_elapsed))
            projected_month_end = spent_total + (daily_burn * Decimal(str(days_remaining)))

            exhaustion_day = None
            if daily_burn > Decimal("0.00") and spent_total < b_amt:
                days_to_exhaust = int((b_amt - spent_total) / daily_burn)
                exhaustion_day = days_elapsed + days_to_exhaust
                if exhaustion_day > month_days:
                    exhaustion_day = None

            will_exceed = projected_month_end > b_amt or spent_total >= b_amt

            results.append({
                "category": b.category,
                "budget_amount": float(b_amt),
                "current_spent": float(spent_total),
                "daily_burn_rate": float(round(daily_burn, 2)),
                "projected_month_end_spending": float(round(projected_month_end, 2)),
                "projected_exhaustion_day_of_month": exhaustion_day,
                "will_exceed_budget": will_exceed,
                "projected_overrun_amount": float(max(projected_month_end - b_amt, Decimal("0.00")))
            })

        return results

    def _calculate_goal_projections(self, monthly_pace: Decimal, today: date) -> List[Dict[str, Any]]:
        """Project goal completion timelines with allocated savings pace."""
        goals = (
            self.db.query(Goal)
            .filter(Goal.user_id == self.user_id)
            .order_by(Goal.target_date.asc())
            .all()
        )

        projections = []
        for g in goals:
            prog = GoalCalculator.calculate_progress(g, today=today, monthly_savings_pace=monthly_pace)
            projections.append({
                "goal_id": g.id,
                "name": g.name,
                "target_amount": float(g.target_amount),
                "current_amount": float(g.current_amount),
                "remaining_amount": prog["remaining_amount"],
                "target_date": str(g.target_date),
                "projected_completion_date": prog.get("projected_completion_date"),
                "status": prog["status"],
                "required_monthly_contribution": prog["required_monthly_contribution"],
                "projected_delay_months": prog.get("projected_delay_months", 0)
            })

        return projections
