"""Safe Planning Formatter: Formats verified goals and planning context into safe XML delimiters."""

import json
from typing import Dict, Any, List
from html import escape


class PlanningFormatter:
    """Formats goal and planning context safely into XML tags for AI reasoning."""

    @staticmethod
    def sanitize_text(text: Any) -> str:
        """Sanitize untrusted user-generated text."""
        if text is None:
            return ""
        s = str(text).replace("\r", " ").replace("\n", " ").strip()
        # Escape XML angle brackets to prevent tag breakouts
        s = s.replace("<", "&lt;").replace(">", "&gt;")
        return s[:150]

    @classmethod
    def format_goals_xml(cls, goals_progress: List[Dict[str, Any]]) -> str:
        """Format active financial goals inside <FINANCIAL_GOALS> delimiters."""
        if not goals_progress:
            return "<FINANCIAL_GOALS>\nNo active financial goals configured.\n</FINANCIAL_GOALS>"

        lines = ["<FINANCIAL_GOALS>"]
        for g in goals_progress:
            safe_name = cls.sanitize_text(g.get("name", "Goal"))
            safe_cat = cls.sanitize_text(g.get("category", "savings"))
            target_amt = g.get("target_amount", 0.0)
            current_amt = g.get("current_amount", 0.0)
            rem_amt = g.get("remaining_amount", 0.0)
            pct = g.get("progress_percentage", 0.0)
            deadline = cls.sanitize_text(g.get("target_date", ""))
            req_monthly = g.get("required_monthly_contribution", 0.0)
            status = cls.sanitize_text(g.get("status", "ON_TRACK"))

            lines.append(
                f"- Goal ID {g.get('goal_id')}: \"{safe_name}\" ({safe_cat}) | Target: ₹{target_amt:,.2f} | "
                f"Saved: ₹{current_amt:,.2f} ({pct}%) | Remaining: ₹{rem_amt:,.2f} | Deadline: {deadline} | "
                f"Required: ₹{req_monthly:,.2f}/month | Status: {status}"
            )
        lines.append("</FINANCIAL_GOALS>")
        return "\n".join(lines)

    @classmethod
    def format_planning_xml(cls, coaching_context: Dict[str, Any]) -> str:
        """Format complete financial planning context inside <PLANNING_CONTEXT> delimiters."""
        cashflow = coaching_context.get("cashflow", {})
        goals_summary = coaching_context.get("goals_summary", {})
        health_score = coaching_context.get("financial_health_score", 70)
        top_cats = coaching_context.get("top_spending_categories", [])

        lines = [
            "<PLANNING_CONTEXT>",
            f"Period: {coaching_context.get('period')}",
            f"Verified Monthly Income: ₹{cashflow.get('monthly_income', 0.0):,.2f}",
            f"Verified Monthly Expenses: ₹{cashflow.get('monthly_expenses', 0.0):,.2f}",
            f"Verified Net Monthly Cash Surplus: ₹{cashflow.get('net_monthly_savings', 0.0):,.2f}",
            f"Savings Rate: {cashflow.get('savings_rate_percentage', 0.0)}%",
            f"Discretionary Spending: ₹{cashflow.get('discretionary_expenses', 0.0):,.2f} ({cashflow.get('discretionary_ratio_percentage', 0.0)}% of expenses)",
            f"Financial Health Score: {health_score}/100",
            f"Active Goals: {goals_summary.get('active_goals_count', 0)} total ({goals_summary.get('goals_on_track_count', 0)} on-track, {goals_summary.get('goals_behind_count', 0)} behind)",
            f"Total Monthly Savings Needed for All Goals: ₹{goals_summary.get('total_required_monthly_savings', 0.0):,.2f}/month"
        ]

        if top_cats:
            lines.append("Top Expense Categories:")
            for tc in top_cats:
                safe_cat = cls.sanitize_text(tc.get("category"))
                lines.append(f"  * {safe_cat}: ₹{tc.get('amount', 0.0):,.2f} ({tc.get('percentage_of_expenses', 0.0)}%)")

        lines.append("</PLANNING_CONTEXT>")
        return "\n".join(lines)
