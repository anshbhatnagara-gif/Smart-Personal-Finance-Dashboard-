"""Deterministic Proactive Financial Insight Rules and Threshold Constants."""

from decimal import Decimal
from typing import List, Dict, Any, Optional, Set
from datetime import date

# Documented Threshold Constants
SPENDING_SPIKE_THRESHOLD_PERCENT: float = 30.0
BUDGET_WARNING_MIN_PERCENT: float = 80.0
BUDGET_WARNING_MAX_PERCENT: float = 100.0
BUDGET_OVERSPENT_MIN_PERCENT: float = 100.0
LOW_SAVINGS_RATE_THRESHOLD_PERCENT: float = 20.0
SAVINGS_DECLINE_THRESHOLD_PERCENT: float = 10.0
UNUSUAL_TRANSACTION_MULTIPLIER: float = 2.0
UNUSUAL_TRANSACTION_MIN_AMOUNT: float = 5000.0
HIGH_DISCRETIONARY_SPENDING_PERCENT: float = 40.0
DISCRETIONARY_CATEGORIES: Set[str] = {"Shopping", "Entertainment", "Food", "Travel", "Dining", "Luxury"}
RECURRING_HIGH_EXPENSE_PERCENT: float = 30.0
FINANCIAL_HEALTH_CHANGE_DELTA: int = 5


class InsightRules:
    """Collection of 10 deterministic financial event detection rules."""

    @staticmethod
    def check_spending_spikes(
        category_spending_current: Dict[str, Decimal],
        category_spending_previous: Dict[str, Decimal]
    ) -> List[Dict[str, Any]]:
        """1. SPENDING_SPIKE: Category spending >= 30% MoM increase."""
        insights = []
        for cat, cur_amt in category_spending_current.items():
            prev_amt = category_spending_previous.get(cat, Decimal("0.00"))
            if prev_amt > 0:
                growth = float((cur_amt - prev_amt) / prev_amt * 100)
                if growth >= SPENDING_SPIKE_THRESHOLD_PERCENT:
                    insights.append({
                        "type": "SPENDING_SPIKE",
                        "severity": "warning",
                        "title": f"Spending Spike in {cat}",
                        "message": f"{cat} spending increased by {growth:.1f}% (₹{cur_amt:,.2f} vs ₹{prev_amt:,.2f} last month).",
                        "category": cat,
                        "amount": float(cur_amt),
                        "percentage": round(growth, 1),
                        "recommendation": f"Review recent {cat} transactions to understand the spending surge.",
                        "evidence": {
                            "current_spending": float(cur_amt),
                            "previous_spending": float(prev_amt),
                            "difference": float(cur_amt - prev_amt),
                            "growth_percentage": round(growth, 1)
                        }
                    })
        return insights

    @staticmethod
    def check_budget_warnings(budgets: List[Any]) -> List[Dict[str, Any]]:
        """2. BUDGET_WARNING & 3. BUDGET_OVERSPENT."""
        insights = []
        for b in budgets:
            category = getattr(b, "category", "")
            amount = Decimal(str(getattr(b, "amount", 0)))
            spent = Decimal(str(getattr(b, "spent", 0)))
            if amount <= 0:
                continue
            utilization = float((spent / amount) * 100)

            if utilization > BUDGET_OVERSPENT_MIN_PERCENT:
                insights.append({
                    "type": "BUDGET_OVERSPENT",
                    "severity": "critical",
                    "title": f"Budget Overspent: {category}",
                    "message": f"{category} has exceeded its budget cap by ₹{spent - amount:,.2f} ({utilization:.1f}% utilized).",
                    "category": category,
                    "amount": float(spent),
                    "percentage": round(utilization, 1),
                    "recommendation": f"Pause optional {category} purchases for the rest of the month.",
                    "evidence": {
                        "budget_amount": float(amount),
                        "spent_amount": float(spent),
                        "overspend_amount": float(spent - amount),
                        "utilization_percentage": round(utilization, 1)
                    }
                })
            elif utilization >= BUDGET_WARNING_MIN_PERCENT:
                insights.append({
                    "type": "BUDGET_WARNING",
                    "severity": "warning",
                    "title": f"Approaching Budget Limit: {category}",
                    "message": f"{category} budget is at {utilization:.1f}% utilization (₹{spent:,.2f} of ₹{amount:,.2f}).",
                    "category": category,
                    "amount": float(spent),
                    "percentage": round(utilization, 1),
                    "recommendation": f"Only ₹{amount - spent:,.2f} remains in your {category} envelope.",
                    "evidence": {
                        "budget_amount": float(amount),
                        "spent_amount": float(spent),
                        "remaining_buffer": float(amount - spent),
                        "utilization_percentage": round(utilization, 1)
                    }
                })
        return insights

    @staticmethod
    def check_savings_rate(
        income: Decimal,
        expenses: Decimal,
        prev_income: Optional[Decimal] = None,
        prev_expenses: Optional[Decimal] = None
    ) -> List[Dict[str, Any]]:
        """4. LOW_SAVINGS_RATE & 5. SAVINGS_DECLINE."""
        insights = []
        if income <= 0:
            return insights

        savings = income - expenses
        savings_rate = float((savings / income) * 100)

        # Rule 4: Low Savings Rate
        if savings_rate < LOW_SAVINGS_RATE_THRESHOLD_PERCENT:
            insights.append({
                "type": "LOW_SAVINGS_RATE",
                "severity": "warning",
                "title": "Low Savings Rate Alert",
                "message": f"Your current savings rate is {savings_rate:.1f}%, which is below the recommended 20% benchmark.",
                "category": "Savings",
                "amount": float(savings),
                "percentage": round(savings_rate, 1),
                "recommendation": "Identify 1-2 non-essential expense categories to trim and rebuild your cash buffer.",
                "evidence": {
                    "income": float(income),
                    "expenses": float(expenses),
                    "net_savings": float(savings),
                    "savings_rate_percentage": round(savings_rate, 1)
                }
            })

        # Rule 5: Savings Decline MoM
        if prev_income is not None and prev_expenses is not None and prev_income > 0:
            prev_savings = prev_income - prev_expenses
            prev_savings_rate = float((prev_savings / prev_income) * 100)

            # Check if savings amount or rate declined by >= 10%
            rate_decline = prev_savings_rate - savings_rate
            if rate_decline >= SAVINGS_DECLINE_THRESHOLD_PERCENT or (prev_savings > 0 and savings < prev_savings * Decimal("0.90")):
                insights.append({
                    "type": "SAVINGS_DECLINE",
                    "severity": "warning",
                    "title": "Savings Rate Deterioration",
                    "message": f"Savings rate dropped to {savings_rate:.1f}% compared to {prev_savings_rate:.1f}% last month.",
                    "category": "Savings",
                    "amount": float(savings),
                    "percentage": round(rate_decline, 1),
                    "recommendation": "Review recent monthly outflow surges to prevent ongoing savings erosion.",
                    "evidence": {
                        "current_savings_rate": round(savings_rate, 1),
                        "previous_savings_rate": round(prev_savings_rate, 1),
                        "decline_percentage": round(rate_decline, 1)
                    }
                })
        return insights

    @staticmethod
    def check_unusual_transactions(
        transactions: List[Any],
        category_averages: Dict[str, Decimal]
    ) -> List[Dict[str, Any]]:
        """6. UNUSUAL_TRANSACTION: >= 2.0x category average and >= ₹5,000."""
        insights = []
        for t in transactions:
            if isinstance(t, dict):
                raw_type = t.get("type", "")
                amt = Decimal(str(t.get("amount", 0)))
                cat = str(t.get("category", ""))
                title = str(t.get("title", "Transaction"))
            else:
                raw_type = getattr(t, "type", "")
                amt = Decimal(str(getattr(t, "amount", 0)))
                cat = str(getattr(t, "category", ""))
                title = str(getattr(t, "title", "Transaction"))

            tx_type = str(raw_type.value if hasattr(raw_type, "value") else raw_type).lower()
            if "expense" not in tx_type:
                continue
            avg = category_averages.get(cat, Decimal("0.00"))

            if avg > 0 and amt >= Decimal(str(UNUSUAL_TRANSACTION_MIN_AMOUNT)) and amt >= (avg * Decimal(str(UNUSUAL_TRANSACTION_MULTIPLIER))):
                multiple = float(amt / avg)
                insights.append({
                    "type": "UNUSUAL_TRANSACTION",
                    "severity": "critical",
                    "title": f"Unusual High Transaction: {cat}",
                    "message": f"Transaction '{title}' of ₹{amt:,.2f} is {multiple:.1f}x higher than your average {cat} purchase.",
                    "category": cat,
                    "amount": float(amt),
                    "percentage": round(multiple * 100, 1),
                    "recommendation": "Verify this large charge to confirm it was expected.",
                    "evidence": {
                        "transaction_title": title,
                        "amount": float(amt),
                        "category_average": float(avg),
                        "multiplier": round(multiple, 1)
                    }
                })
        return insights

    @staticmethod
    def check_high_discretionary_spending(
        category_spending: Dict[str, Decimal],
        total_expenses: Decimal
    ) -> List[Dict[str, Any]]:
        """7. HIGH_DISCRETIONARY_SPENDING: Discretionary categories >= 40% of total expenses."""
        insights = []
        if total_expenses <= 0:
            return insights

        discretionary_total = Decimal("0.00")
        for cat, amt in category_spending.items():
            if cat in DISCRETIONARY_CATEGORIES:
                discretionary_total += amt

        disc_percent = float((discretionary_total / total_expenses) * 100)
        if disc_percent >= HIGH_DISCRETIONARY_SPENDING_PERCENT:
            insights.append({
                "type": "HIGH_DISCRETIONARY_SPENDING",
                "severity": "warning",
                "title": "High Discretionary Spending",
                "message": f"Discretionary purchases (Food, Shopping, Travel, etc.) represent {disc_percent:.1f}% of total outflow (₹{discretionary_total:,.2f}).",
                "category": "Discretionary",
                "amount": float(discretionary_total),
                "percentage": round(disc_percent, 1),
                "recommendation": "Trimming discretionary spending by 15% could unlock significant monthly savings.",
                "evidence": {
                    "discretionary_total": float(discretionary_total),
                    "total_expenses": float(total_expenses),
                    "discretionary_percentage": round(disc_percent, 1)
                }
            })
        return insights

    @staticmethod
    def check_recurring_high_expense(
        category_spending: Dict[str, Decimal],
        total_expenses: Decimal
    ) -> List[Dict[str, Any]]:
        """8. RECURRING_HIGH_EXPENSE: One category >= 30% of total expenses."""
        insights = []
        if total_expenses <= 0:
            return insights

        for cat, amt in category_spending.items():
            pct = float((amt / total_expenses) * 100)
            if pct >= RECURRING_HIGH_EXPENSE_PERCENT:
                insights.append({
                    "type": "RECURRING_HIGH_EXPENSE",
                    "severity": "info",
                    "title": f"Dominant Expense Category: {cat}",
                    "message": f"{cat} consumes {pct:.1f}% of your entire monthly expenses (₹{amt:,.2f}).",
                    "category": cat,
                    "amount": float(amt),
                    "percentage": round(pct, 1),
                    "recommendation": f"Monitor {cat} closely as it represents your single largest cash outflow.",
                    "evidence": {
                        "category": cat,
                        "amount": float(amt),
                        "percentage_of_total": round(pct, 1)
                    }
                })
        return insights

    @staticmethod
    def check_positive_progress(
        income: Decimal,
        expenses: Decimal,
        prev_income: Decimal,
        prev_expenses: Decimal
    ) -> List[Dict[str, Any]]:
        """9. POSITIVE_PROGRESS: Spending decreased or savings rate improved."""
        insights = []
        if prev_expenses > 0 and expenses < prev_expenses:
            exp_drop_pct = float((prev_expenses - expenses) / prev_expenses * 100)
            if exp_drop_pct >= 5.0:
                insights.append({
                    "type": "POSITIVE_PROGRESS",
                    "severity": "positive",
                    "title": "Expense Reduction Progress",
                    "message": f"Great job! Total monthly expenses decreased by {exp_drop_pct:.1f}% compared to last month.",
                    "category": "Progress",
                    "amount": float(prev_expenses - expenses),
                    "percentage": round(exp_drop_pct, 1),
                    "recommendation": "Keep up the great spending control momentum!",
                    "evidence": {
                        "current_expenses": float(expenses),
                        "previous_expenses": float(prev_expenses),
                        "saved_amount": float(prev_expenses - expenses)
                    }
                })

        if income > 0 and prev_income > 0:
            cur_sr = float((income - expenses) / income * 100)
            prev_sr = float((prev_income - prev_expenses) / prev_income * 100)
            if cur_sr > prev_sr + 5.0:
                insights.append({
                    "type": "POSITIVE_PROGRESS",
                    "severity": "positive",
                    "title": "Savings Rate Growth",
                    "message": f"Your savings rate improved to {cur_sr:.1f}% (up from {prev_sr:.1f}% last month).",
                    "category": "Progress",
                    "amount": float(income - expenses),
                    "percentage": round(cur_sr - prev_sr, 1),
                    "recommendation": "Consider routing the additional surplus directly into an emergency fund.",
                    "evidence": {
                        "current_savings_rate": round(cur_sr, 1),
                        "previous_savings_rate": round(prev_sr, 1)
                    }
                })
        return insights

    @staticmethod
    def check_health_score_change(
        current_score: int,
        previous_score: Optional[int]
    ) -> List[Dict[str, Any]]:
        """10. FINANCIAL_HEALTH_CHANGE: Health score changed >= 5 points."""
        insights = []
        if previous_score is not None:
            delta = current_score - previous_score
            if abs(delta) >= FINANCIAL_HEALTH_CHANGE_DELTA:
                direction = "improved" if delta > 0 else "declined"
                severity = "positive" if delta > 0 else "warning"
                insights.append({
                    "type": "FINANCIAL_HEALTH_CHANGE",
                    "severity": severity,
                    "title": f"Health Score {direction.capitalize()}",
                    "message": f"Your Financial Health Score {direction} by {abs(delta)} points (now {current_score}/100).",
                    "category": "Health",
                    "amount": float(current_score),
                    "percentage": float(delta),
                    "recommendation": f"Review factor breakdown to maintain or boost your score.",
                    "evidence": {
                        "current_score": current_score,
                        "previous_score": previous_score,
                        "delta": delta,
                        "direction": direction
                    }
                })
        return insights
