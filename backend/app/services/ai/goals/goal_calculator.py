"""Goal Calculator: Deterministic financial calculations for goal progress and timelines."""

from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, Any, Optional

from app.models.goal import Goal


class GoalCalculator:
    """Performs deterministic financial math for goal progress, contributions, and status."""

    @staticmethod
    def calculate_progress(
        goal: Goal,
        today: Optional[date] = None,
        monthly_savings_pace: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """
        Calculate progress, remaining amounts, monthly/weekly contributions,
        completion projection, and status for a goal.
        """
        if today is None:
            today = date.today()

        target_amt = Decimal(str(goal.target_amount))
        current_amt = Decimal(str(goal.current_amount))
        target_dt = goal.target_date

        # 1. Progress percentage
        if target_amt > Decimal("0.00"):
            progress_pct = float(min(Decimal("100.0"), (current_amt / target_amt) * Decimal("100.0")))
        else:
            progress_pct = 0.0
        progress_pct = round(progress_pct, 1)

        # 2. Remaining amount
        remaining_amt = max(Decimal("0.00"), target_amt - current_amt)

        # 3. Days & Months remaining
        days_remaining = max(0, (target_dt - today).days)
        # Approximate months (30.4375 days per month)
        if days_remaining <= 0:
            months_remaining = Decimal("0.0")
            weeks_remaining = Decimal("0.0")
        else:
            months_remaining = max(Decimal("0.1"), Decimal(str(days_remaining)) / Decimal("30.4375"))
            weeks_remaining = max(Decimal("0.1"), Decimal(str(days_remaining)) / Decimal("7.0"))

        # 4. Required Contributions
        if remaining_amt <= Decimal("0.00"):
            req_monthly = Decimal("0.00")
            req_weekly = Decimal("0.00")
        elif months_remaining > Decimal("0.0"):
            req_monthly = remaining_amt / max(Decimal("1.0"), months_remaining)
            req_weekly = remaining_amt / max(Decimal("1.0"), weeks_remaining)
        else:
            req_monthly = remaining_amt
            req_weekly = remaining_amt

        # 5. Goal Status determination
        created_dt = goal.created_at.date() if hasattr(goal, "created_at") and goal.created_at else (target_dt - timedelta(days=90))
        total_duration_days = max(1, (target_dt - created_dt).days)
        elapsed_days = max(0, (today - created_dt).days)

        if current_amt >= target_amt:
            status = "COMPLETED"
        elif days_remaining == 0:
            status = "BEHIND"
        else:
            # Expected progress ratio by today
            expected_ratio = min(Decimal("1.0"), Decimal(str(elapsed_days)) / Decimal(str(total_duration_days)))
            expected_amount = target_amt * expected_ratio
            if expected_amount == Decimal("0.00"):
                status = "ON_TRACK" if current_amt > Decimal("0.00") else "ON_TRACK"
            elif current_amt >= (expected_amount * Decimal("1.10")):
                status = "AHEAD"
            elif current_amt >= (expected_amount * Decimal("0.85")):
                status = "ON_TRACK"
            else:
                status = "BEHIND"

        # 6. Projected completion date based on pace
        projected_completion_date = None
        if remaining_amt <= Decimal("0.00"):
            projected_completion_date = str(today)
        elif monthly_savings_pace is not None and monthly_savings_pace > Decimal("0.00"):
            months_needed = float(remaining_amt / monthly_savings_pace)
            days_needed = int(months_needed * 30.4375)
            projected_completion_date = str(today + timedelta(days=days_needed))
        else:
            # Fallback projection based on target date
            projected_completion_date = str(target_dt)

        return {
            "goal_id": goal.id,
            "name": goal.name,
            "target_amount": float(target_amt),
            "current_amount": float(current_amt),
            "remaining_amount": float(remaining_amt),
            "progress_percentage": progress_pct,
            "target_date": str(target_dt),
            "days_remaining": days_remaining,
            "months_remaining": round(float(months_remaining), 1),
            "required_monthly_contribution": round(float(req_monthly), 2),
            "required_weekly_contribution": round(float(req_weekly), 2),
            "status": status,
            "projected_completion_date": projected_completion_date,
            "category": goal.category,
            "priority": goal.priority
        }
