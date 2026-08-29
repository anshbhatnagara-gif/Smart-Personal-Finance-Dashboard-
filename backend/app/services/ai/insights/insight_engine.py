"""Proactive Insight Engine: Rule orchestration, severity prioritization, and user-isolated analysis."""

from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.transaction import Transaction, TransactionType
from app.services.budget_service import BudgetService
from app.services.finance_service import calculate_financial_health_score
from app.services.ai.insights.insight_rules import InsightRules

MAX_PROACTIVE_INSIGHTS: int = 5
SEVERITY_WEIGHTS: Dict[str, int] = {
    "critical": 4,
    "warning": 3,
    "info": 2,
    "positive": 1
}


class InsightEngine:
    """Orchestrates database queries and deterministic insight rules for a specific authenticated user."""

    def __init__(self, user_id: int, db: Session):
        self.user_id = user_id
        self.db = db

    def generate_insights(self, month: Optional[int] = None, year: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Generate, prioritize, and bound proactive financial insights for the authenticated user.
        Strictly user-scoped to self.user_id.
        """
        now = datetime.now()
        cur_month = month or now.month
        cur_year = year or now.year

        # Calculate previous month
        if cur_month == 1:
            prev_month = 12
            prev_year = cur_year - 1
        else:
            prev_month = cur_month - 1
            prev_year = cur_year

        # 1. Fetch current & previous month transactions for self.user_id ONLY
        all_txs = self.db.query(Transaction).filter(
            Transaction.user_id == self.user_id
        ).order_by(Transaction.transaction_date.desc()).all()

        cur_txs = [
            t for t in all_txs
            if t.transaction_date.year == cur_year and t.transaction_date.month == cur_month
        ]
        prev_txs = [
            t for t in all_txs
            if t.transaction_date.year == prev_year and t.transaction_date.month == prev_month
        ]

        # Income & Expenses
        cur_income = sum((t.amount for t in cur_txs if t.type == TransactionType.INCOME), Decimal("0.00"))
        cur_expenses = sum((t.amount for t in cur_txs if t.type == TransactionType.EXPENSE), Decimal("0.00"))

        prev_income = sum((t.amount for t in prev_txs if t.type == TransactionType.INCOME), Decimal("0.00"))
        prev_expenses = sum((t.amount for t in prev_txs if t.type == TransactionType.EXPENSE), Decimal("0.00"))

        # Category spending
        cat_spending_cur: Dict[str, Decimal] = {}
        for t in cur_txs:
            if t.type == TransactionType.EXPENSE:
                cat_spending_cur[t.category] = cat_spending_cur.get(t.category, Decimal("0.00")) + t.amount

        cat_spending_prev: Dict[str, Decimal] = {}
        for t in prev_txs:
            if t.type == TransactionType.EXPENSE:
                cat_spending_prev[t.category] = cat_spending_prev.get(t.category, Decimal("0.00")) + t.amount

        # Category averages
        cat_counts: Dict[str, int] = {}
        cat_totals: Dict[str, Decimal] = {}
        for t in all_txs:
            if t.type == TransactionType.EXPENSE:
                cat_totals[t.category] = cat_totals.get(t.category, Decimal("0.00")) + t.amount
                cat_counts[t.category] = cat_counts.get(t.category, 0) + 1

        cat_averages = {
            cat: cat_totals[cat] / Decimal(str(cat_counts[cat]))
            for cat in cat_totals if cat_counts[cat] > 0
        }

        # Budgets for current user
        budgets = BudgetService.get_budgets(db=self.db, user_id=self.user_id, month=cur_month, year=cur_year)

        # Financial Health Scores
        cur_health = calculate_financial_health_score({
            "income": cur_income,
            "expenses": cur_expenses,
            "prev_expenses": prev_expenses,
            "total_budget": sum((b.amount for b in budgets), Decimal("0.00"))
        })
        cur_health_score = cur_health.score if hasattr(cur_health, "score") else (cur_health.get("score", 70) if isinstance(cur_health, dict) else 70)

        prev_health_score = None
        if len(prev_txs) > 0:
            prev_health = calculate_financial_health_score({
                "income": prev_income,
                "expenses": prev_expenses,
                "prev_expenses": Decimal("0.00"),
                "total_budget": Decimal("0.00")
            })
            prev_health_score = prev_health.score if hasattr(prev_health, "score") else (prev_health.get("score", 70) if isinstance(prev_health, dict) else 70)

        # 2. Collect insights from all 10 rules
        raw_insights: List[Dict[str, Any]] = []

        # Rule 1: Spending Spike
        raw_insights.extend(InsightRules.check_spending_spikes(cat_spending_cur, cat_spending_prev))

        # Rule 2 & 3: Budget Warning & Overspent
        raw_insights.extend(InsightRules.check_budget_warnings(budgets))

        # Rule 4 & 5: Low Savings Rate & Savings Decline
        raw_insights.extend(InsightRules.check_savings_rate(
            income=cur_income,
            expenses=cur_expenses,
            prev_income=prev_income if len(prev_txs) > 0 else None,
            prev_expenses=prev_expenses if len(prev_txs) > 0 else None
        ))

        # Rule 6: Unusual Transaction
        raw_insights.extend(InsightRules.check_unusual_transactions(cur_txs, cat_averages))

        # Rule 7: High Discretionary Spending
        raw_insights.extend(InsightRules.check_high_discretionary_spending(cat_spending_cur, cur_expenses))

        # Rule 8: Recurring High Expense
        raw_insights.extend(InsightRules.check_recurring_high_expense(cat_spending_cur, cur_expenses))

        # Rule 9: Positive Progress
        if len(prev_txs) > 0:
            raw_insights.extend(InsightRules.check_positive_progress(
                income=cur_income,
                expenses=cur_expenses,
                prev_income=prev_income,
                prev_expenses=prev_expenses
            ))

        # Rule 10: Financial Health Change
        raw_insights.extend(InsightRules.check_health_score_change(cur_health_score, prev_health_score))

        # 3. Deterministic Prioritization
        def priority_key(item: Dict[str, Any]):
            sev_weight = SEVERITY_WEIGHTS.get(item.get("severity", "info"), 1)
            amt_impact = float(item.get("amount", 0.0))
            return (sev_weight, amt_impact)

        sorted_insights = sorted(raw_insights, key=priority_key, reverse=True)

        # 4. Bounded to MAX_PROACTIVE_INSIGHTS (5)
        return sorted_insights[:MAX_PROACTIVE_INSIGHTS]
