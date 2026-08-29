"""Goal Projection Engine: Projects completion timelines based on verified savings pace."""

from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, Any, Optional

from app.models.goal import Goal
from app.services.ai.goals.goal_calculator import GoalCalculator


class GoalProjectionEngine:
    """Computes realistic goal completion projections using verified monthly cashflow."""

    @staticmethod
    def project_goal_timeline(
        goal: Goal,
        monthly_savings_pace: Decimal,
        today: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Generate grounded projections comparing current savings pace against required pace.
        """
        if today is None:
            today = date.today()

        progress = GoalCalculator.calculate_progress(goal, today=today, monthly_savings_pace=monthly_savings_pace)
        remaining_amt = Decimal(str(progress["remaining_amount"]))
        req_monthly = Decimal(str(progress["required_monthly_contribution"]))
        target_dt = goal.target_date

        pace_gap = monthly_savings_pace - req_monthly

        if remaining_amt <= Decimal("0.00"):
            projected_months = 0.0
            projected_date = today
            timeline_status = "COMPLETED"
            summary_msg = f"Goal '{goal.name}' is already completed."
        elif monthly_savings_pace <= Decimal("0.00"):
            projected_months = None
            projected_date = None
            timeline_status = "STALLED"
            summary_msg = f"With zero or negative monthly savings, goal '{goal.name}' cannot make progress without budget adjustments."
        else:
            projected_months = float(round(remaining_amt / monthly_savings_pace, 1))
            days_needed = int(projected_months * 30.4375)
            projected_date = today + timedelta(days=days_needed)

            if projected_date <= target_dt:
                months_ahead = round((target_dt - projected_date).days / 30.4375, 1)
                timeline_status = "ON_TRACK" if months_ahead <= 1.0 else "AHEAD"
                summary_msg = (
                    f"At your current pace of ₹{monthly_savings_pace:,.2f}/month, you are on track to complete "
                    f"'{goal.name}' by {projected_date.strftime('%b %Y')} (~{months_ahead} months ahead of deadline)."
                )
            else:
                delay_months = round((projected_date - target_dt).days / 30.4375, 1)
                timeline_status = "BEHIND"
                summary_msg = (
                    f"At your current pace of ₹{monthly_savings_pace:,.2f}/month, completion is projected for "
                    f"{projected_date.strftime('%b %Y')} (~{delay_months} months behind target deadline of {target_dt.strftime('%b %Y')})."
                )

        return {
            "goal_id": goal.id,
            "goal_name": goal.name,
            "target_amount": float(goal.target_amount),
            "current_amount": float(goal.current_amount),
            "remaining_amount": float(remaining_amt),
            "current_monthly_pace": float(monthly_savings_pace),
            "required_monthly_pace": float(req_monthly),
            "pace_gap": float(pace_gap),
            "target_date": str(target_dt),
            "projected_completion_date": str(projected_date) if projected_date else None,
            "projected_months_to_completion": projected_months,
            "timeline_status": timeline_status,
            "summary": summary_msg,
            "verified_facts": [
                f"Goal Target: ₹{goal.target_amount:,.2f}",
                f"Current Saved: ₹{goal.current_amount:,.2f} ({progress['progress_percentage']}%)",
                f"Remaining: ₹{remaining_amt:,.2f}",
                f"Verified Monthly Savings Pace: ₹{monthly_savings_pace:,.2f}"
            ],
            "projections": [
                f"Projected completion date: {projected_date.strftime('%d %b %Y') if projected_date else 'Indefinite'}",
                f"Pace surplus/shortfall: {'+' if pace_gap >= 0 else ''}₹{pace_gap:,.2f}/month"
            ],
            "assumptions": [
                "Assumes average monthly income and living expenses remain consistent.",
                "Assumes no unscheduled lump-sum withdrawals or deposits."
            ]
        }
