"""Planning Engine: Synthesizes goals, progress, cashflow, and proactive insights for coaching."""

from datetime import datetime, date
from decimal import Decimal
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.models.transaction import Transaction, TransactionType
from app.services.budget_service import BudgetService
from app.services.finance_service import calculate_financial_health_score
from app.services.ai.goals.goal_service import GoalService
from app.services.ai.goals.goal_calculator import GoalCalculator
from app.services.ai.insights.insight_engine import InsightEngine
from app.services.ai.insights.insight_rules import DISCRETIONARY_CATEGORIES


class PlanningEngine:
    """Orchestrates comprehensive personalized financial coaching data for the authenticated user."""

    def __init__(self, user_id: int, db: Session):
        self.user_id = user_id
        self.db = db

    def generate_coaching_context(
        self,
        month: Optional[int] = None,
        year: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate complete verified coaching profile:
        - Cashflow & Savings Pace
        - Active Goals & Status Breakdown
        - Largest Expense Categories
        - Discretionary Ratio
        - Proactive Financial Insights
        - Health Score
        """
        now = datetime.now()
        cur_month = month or now.month
        cur_year = year or now.year

        # 1. Fetch user transactions
        all_txs = self.db.query(Transaction).filter(
            Transaction.user_id == self.user_id
        ).order_by(Transaction.transaction_date.desc()).all()

        cur_txs = [
            t for t in all_txs
            if t.transaction_date.year == cur_year and t.transaction_date.month == cur_month
        ]

        cur_income = sum((t.amount for t in cur_txs if t.type == TransactionType.INCOME), Decimal("0.00"))
        cur_expenses = sum((t.amount for t in cur_txs if t.type == TransactionType.EXPENSE), Decimal("0.00"))
        net_savings = cur_income - cur_expenses
        savings_rate = float((net_savings / cur_income) * 100) if cur_income > 0 else 0.0

        # Category spending
        cat_spending: Dict[str, Decimal] = {}
        for t in cur_txs:
            if t.type == TransactionType.EXPENSE:
                cat_spending[t.category] = cat_spending.get(t.category, Decimal("0.00")) + t.amount

        # Discretionary spending
        discretionary_total = sum(
            (cat_spending[c] for c in cat_spending if c in DISCRETIONARY_CATEGORIES),
            Decimal("0.00")
        )
        discretionary_ratio = float((discretionary_total / cur_expenses) * 100) if cur_expenses > 0 else 0.0

        # Top 3 expense categories
        sorted_cats = sorted(cat_spending.items(), key=lambda x: x[1], reverse=True)
        top_categories = [
            {
                "category": cat,
                "amount": float(amt),
                "percentage_of_expenses": round(float((amt / cur_expenses) * 100), 1) if cur_expenses > 0 else 0.0
            }
            for cat, amt in sorted_cats[:3]
        ]

        # 2. Fetch Active Goals & Progress
        goals = GoalService.get_goals(self.db, self.user_id)
        goals_progress = [
            GoalCalculator.calculate_progress(g, monthly_savings_pace=net_savings)
            for g in goals
        ]

        total_goal_target = sum((Decimal(str(g.target_amount)) for g in goals), Decimal("0.00"))
        total_goal_saved = sum((Decimal(str(g.current_amount)) for g in goals), Decimal("0.00"))
        total_goal_remaining = sum((Decimal(str(p["remaining_amount"])) for p in goals_progress), Decimal("0.00"))
        total_monthly_required = sum((Decimal(str(p["required_monthly_contribution"])) for p in goals_progress), Decimal("0.00"))

        # Goals status summary
        goals_on_track = sum(1 for p in goals_progress if p["status"] in ("ON_TRACK", "AHEAD", "COMPLETED"))
        goals_behind = sum(1 for p in goals_progress if p["status"] == "BEHIND")

        # 3. Budgets & Health Score
        budgets = BudgetService.get_budgets(self.db, self.user_id, month=cur_month, year=cur_year)
        total_budget = sum((b.amount for b in budgets), Decimal("0.00"))

        health_res = calculate_financial_health_score({
            "income": cur_income,
            "expenses": cur_expenses,
            "prev_expenses": Decimal("0.00"),
            "total_budget": total_budget
        })
        health_score = health_res.score if hasattr(health_res, "score") else 70

        # 4. Proactive Insights
        insight_engine = InsightEngine(self.user_id, self.db)
        proactive_insights = insight_engine.generate_insights(month=cur_month, year=cur_year)

        return {
            "user_id": self.user_id,
            "period": f"{cur_year}-{cur_month:02d}",
            "cashflow": {
                "monthly_income": float(cur_income),
                "monthly_expenses": float(cur_expenses),
                "net_monthly_savings": float(net_savings),
                "savings_rate_percentage": round(savings_rate, 1),
                "discretionary_expenses": float(discretionary_total),
                "discretionary_ratio_percentage": round(discretionary_ratio, 1)
            },
            "top_spending_categories": top_categories,
            "goals_summary": {
                "active_goals_count": len(goals),
                "goals_on_track_count": goals_on_track,
                "goals_behind_count": goals_behind,
                "total_target_amount": float(total_goal_target),
                "total_saved_amount": float(total_goal_saved),
                "total_remaining_amount": float(total_goal_remaining),
                "total_required_monthly_savings": float(round(total_monthly_required, 2)),
                "goals": goals_progress
            },
            "financial_health_score": health_score,
            "proactive_insights": proactive_insights
        }
