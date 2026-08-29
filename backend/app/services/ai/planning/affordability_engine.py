"""Affordability Engine: Evaluates goal and purchase feasibility against verified cashflow."""

from decimal import Decimal
from typing import Dict, Any, Optional


class AffordabilityEngine:
    """Evaluates whether a planned financial goal or monthly contribution is affordable."""

    @staticmethod
    def evaluate_affordability(
        required_monthly_amount: Decimal,
        monthly_income: Decimal,
        monthly_expenses: Decimal,
        discretionary_expenses: Decimal = Decimal("0.00"),
        goal_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluate affordability based on verified income, expenses, and discretionary cushion.
        """
        net_surplus = monthly_income - monthly_expenses
        savings_rate = float((net_surplus / monthly_income * 100)) if monthly_income > 0 else 0.0

        target_label = f"goal '{goal_name}'" if goal_name else "planned commitment"

        if required_monthly_amount <= Decimal("0.00"):
            status = "affordable"
            suggested_amount = Decimal("0.00")
            reasoning = "No additional monthly contribution is required."
        elif net_surplus >= (required_monthly_amount * Decimal("1.25")):
            status = "affordable"
            suggested_amount = required_monthly_amount
            reasoning = (
                f"Fully affordable. Your verified monthly surplus of ₹{net_surplus:,.2f} comfortably covers "
                f"the required ₹{required_monthly_amount:,.2f}/month while preserving a cash safety cushion."
            )
        elif net_surplus >= required_monthly_amount:
            status = "affordable"
            suggested_amount = required_monthly_amount
            reasoning = (
                f"Affordable with minimal buffer. Your monthly surplus of ₹{net_surplus:,.2f} meets the required "
                f"₹{required_monthly_amount:,.2f}/month, utilizing {float(required_monthly_amount/net_surplus*100):.1f}% of your free cashflow."
            )
        elif (net_surplus + discretionary_expenses) >= required_monthly_amount:
            status = "potentially_affordable"
            gap = required_monthly_amount - net_surplus
            suggested_amount = net_surplus
            reasoning = (
                f"Potentially affordable with spending adjustments. Your current surplus is ₹{net_surplus:,.2f}, leaving a "
                f"shortfall of ₹{gap:,.2f}/month. You have ₹{discretionary_expenses:,.2f} in discretionary spending that can be trimmed."
            )
        else:
            status = "not_affordable"
            suggested_amount = max(Decimal("0.00"), net_surplus)
            total_capacity = net_surplus + discretionary_expenses
            reasoning = (
                f"Currently not affordable under current spending patterns. Required ₹{required_monthly_amount:,.2f}/month exceeds "
                f"your total available surplus plus discretionary cushion (₹{total_capacity:,.2f}). Extending the deadline is recommended."
            )

        return {
            "affordability_status": status,
            "required_monthly_amount": float(required_monthly_amount),
            "suggested_monthly_amount": float(suggested_amount),
            "monthly_income": float(monthly_income),
            "monthly_expenses": float(monthly_expenses),
            "net_monthly_surplus": float(net_surplus),
            "discretionary_expenses": float(discretionary_expenses),
            "savings_rate_percentage": round(savings_rate, 1),
            "reasoning": reasoning,
            "verified_facts": [
                f"Monthly Income: ₹{monthly_income:,.2f}",
                f"Monthly Expenses: ₹{monthly_expenses:,.2f}",
                f"Net Monthly Cash Surplus: ₹{net_surplus:,.2f}",
                f"Discretionary Category Outflows: ₹{discretionary_expenses:,.2f}"
            ],
            "recommendation": (
                "Allocate your monthly surplus to a dedicated high-yield savings account."
                if status == "affordable"
                else "Identify 1-2 discretionary categories to reduce or consider extending the goal completion date."
            ),
            "assumptions": [
                "Assumes baseline income and fixed expenses remain stable.",
                "Assumes no unforeseen major emergency expenditures occur."
            ]
        }
