"""What-If Scenario Engine: Deterministic financial simulations for goals and cashflow."""

from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, Any, Optional

from app.models.goal import Goal
from app.services.ai.goals.goal_calculator import GoalCalculator


class ScenarioEngine:
    """Computes deterministic projections for 'What-If' financial decisions."""

    @staticmethod
    def run_scenario(
        scenario_type: str,
        goal: Optional[Goal] = None,
        baseline_income: Decimal = Decimal("0.00"),
        baseline_expenses: Decimal = Decimal("0.00"),
        category_spending: Optional[Dict[str, Decimal]] = None,
        params: Optional[Dict[str, Any]] = None,
        today: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Execute deterministic scenario simulation.
        Supported scenario_types:
          1. increased_savings
          2. reduced_spending
          3. increased_expenses
          4. income_reduction
          5. goal_deadline_change
          6. monthly_contribution_change
        """
        if params is None:
            params = {}
        if today is None:
            today = date.today()
        if category_spending is None:
            category_spending = {}

        baseline_surplus = baseline_income - baseline_expenses
        remaining_amt = Decimal("0.00")
        target_dt = today + timedelta(days=365)
        goal_name = "Overall Finances"

        if goal:
            goal_name = goal.name
            target_dt = goal.target_date
            remaining_amt = max(Decimal("0.00"), Decimal(str(goal.target_amount)) - Decimal(str(goal.current_amount)))

        # 1. Scenario: Increased Savings
        if scenario_type == "increased_savings":
            delta = Decimal(str(params.get("monthly_savings_delta", params.get("amount", 5000))))
            new_surplus = baseline_surplus + delta
            new_expenses = max(Decimal("0.00"), baseline_expenses - delta)

            baseline_months = float(round(remaining_amt / max(Decimal("1.0"), baseline_surplus), 1)) if baseline_surplus > 0 and remaining_amt > 0 else None
            new_months = float(round(remaining_amt / max(Decimal("1.0"), new_surplus), 1)) if new_surplus > 0 and remaining_amt > 0 else None
            time_saved_months = round(baseline_months - new_months, 1) if (baseline_months and new_months) else None

            summary = (
                f"Saving an additional ₹{delta:,.2f}/month increases your monthly surplus to ₹{new_surplus:,.2f}. "
                + (f"This could help complete '{goal_name}' ~{time_saved_months} months earlier." if time_saved_months and time_saved_months > 0 else "This accelerates your total savings pace.")
            )

            return {
                "scenario_type": scenario_type,
                "goal_name": goal_name,
                "parameter_used": f"+₹{delta:,.2f}/month savings",
                "baseline_monthly_surplus": float(baseline_surplus),
                "simulated_monthly_surplus": float(new_surplus),
                "monthly_savings_increase": float(delta),
                "annual_savings_increase": float(delta * 12),
                "baseline_months_to_completion": baseline_months,
                "simulated_months_to_completion": new_months,
                "time_saved_months": time_saved_months,
                "summary": summary,
                "assumptions": ["Assumes regular additional savings every month without withdrawals."]
            }

        # 2. Scenario: Reduced Spending
        elif scenario_type == "reduced_spending":
            cat = params.get("category")
            pct = Decimal(str(params.get("reduction_percentage", 20.0)))
            amt_param = params.get("reduction_amount")

            if amt_param is not None:
                reduction = Decimal(str(amt_param))
            elif cat and cat in category_spending:
                cat_amt = category_spending[cat]
                reduction = cat_amt * (pct / Decimal("100.0"))
            else:
                reduction = baseline_expenses * (pct / Decimal("100.0"))

            new_expenses = max(Decimal("0.00"), baseline_expenses - reduction)
            new_surplus = baseline_income - new_expenses
            annual_saved = reduction * 12

            baseline_months = float(round(remaining_amt / max(Decimal("1.0"), baseline_surplus), 1)) if baseline_surplus > 0 and remaining_amt > 0 else None
            new_months = float(round(remaining_amt / max(Decimal("1.0"), new_surplus), 1)) if new_surplus > 0 and remaining_amt > 0 else None
            time_saved_months = round(baseline_months - new_months, 1) if (baseline_months and new_months) else None

            cat_note = f"in {cat} " if cat else ""
            summary = (
                f"Reducing spending {cat_note}by {pct}% saves ₹{reduction:,.2f}/month (₹{annual_saved:,.2f}/year), "
                f"increasing your monthly cash surplus to ₹{new_surplus:,.2f}."
            )

            return {
                "scenario_type": scenario_type,
                "goal_name": goal_name,
                "parameter_used": f"{cat_note}reduction of {pct}% (₹{reduction:,.2f})",
                "baseline_monthly_expenses": float(baseline_expenses),
                "simulated_monthly_expenses": float(new_expenses),
                "monthly_savings_increase": float(reduction),
                "annual_savings_increase": float(annual_saved),
                "baseline_months_to_completion": baseline_months,
                "simulated_months_to_completion": new_months,
                "time_saved_months": time_saved_months,
                "summary": summary,
                "assumptions": [f"Assumes category spending {cat_note}remains capped at the reduced level."]
            }

        # 3. Scenario: Increased Expenses
        elif scenario_type == "increased_expenses":
            pct = Decimal(str(params.get("increase_percentage", 10.0)))
            amt_param = params.get("increase_amount")

            if amt_param is not None:
                increase = Decimal(str(amt_param))
            else:
                increase = baseline_expenses * (pct / Decimal("100.0"))

            new_expenses = baseline_expenses + increase
            new_surplus = baseline_income - new_expenses

            summary = (
                f"A {pct}% increase in monthly expenses (+₹{increase:,.2f}) reduces your monthly surplus "
                f"from ₹{baseline_surplus:,.2f} down to ₹{new_surplus:,.2f}."
            )

            return {
                "scenario_type": scenario_type,
                "goal_name": goal_name,
                "parameter_used": f"+{pct}% expense increase (+₹{increase:,.2f})",
                "baseline_monthly_expenses": float(baseline_expenses),
                "simulated_monthly_expenses": float(new_expenses),
                "baseline_monthly_surplus": float(baseline_surplus),
                "simulated_monthly_surplus": float(new_surplus),
                "monthly_surplus_impact": float(-increase),
                "summary": summary,
                "assumptions": ["Assumes lifestyle inflation or higher recurring bills without income growth."]
            }

        # 4. Scenario: Income Reduction
        elif scenario_type == "income_reduction":
            pct = Decimal(str(params.get("reduction_percentage", 15.0)))
            amt_param = params.get("reduction_amount")

            if amt_param is not None:
                drop = Decimal(str(amt_param))
            else:
                drop = baseline_income * (pct / Decimal("100.0"))

            new_income = max(Decimal("0.00"), baseline_income - drop)
            new_surplus = new_income - baseline_expenses

            summary = (
                f"If monthly income decreases by {pct}% (-₹{drop:,.2f}), your new income is ₹{new_income:,.2f} "
                f"leaving a net monthly surplus of ₹{new_surplus:,.2f}."
            )

            return {
                "scenario_type": scenario_type,
                "goal_name": goal_name,
                "parameter_used": f"-{pct}% income reduction (-₹{drop:,.2f})",
                "baseline_monthly_income": float(baseline_income),
                "simulated_monthly_income": float(new_income),
                "baseline_monthly_surplus": float(baseline_surplus),
                "simulated_monthly_surplus": float(new_surplus),
                "monthly_surplus_impact": float(-drop),
                "summary": summary,
                "assumptions": ["Assumes living expenses remain unchanged despite lower earnings."]
            }

        # 5. Scenario: Goal Deadline Change
        elif scenario_type == "goal_deadline_change":
            months_delta = int(params.get("months_delta", 6))
            new_dt_str = params.get("new_target_date")

            if new_dt_str:
                new_target_dt = date.fromisoformat(new_dt_str)
            else:
                new_target_dt = target_dt + timedelta(days=int(months_delta * 30.4375))

            new_days = max(1, (new_target_dt - today).days)
            new_months = max(Decimal("1.0"), Decimal(str(new_days)) / Decimal("30.4375"))
            new_req_monthly = remaining_amt / new_months

            orig_days = max(1, (target_dt - today).days)
            orig_months = max(Decimal("1.0"), Decimal(str(orig_days)) / Decimal("30.4375"))
            orig_req_monthly = remaining_amt / orig_months

            monthly_diff = orig_req_monthly - new_req_monthly

            summary = (
                f"Extending the deadline for '{goal_name}' to {new_target_dt.strftime('%b %Y')} (~{months_delta} months) "
                f"lowers your required monthly contribution from ₹{orig_req_monthly:,.2f} to ₹{new_req_monthly:,.2f}/month (saving ₹{monthly_diff:,.2f}/month in required cashflow)."
            )

            return {
                "scenario_type": scenario_type,
                "goal_name": goal_name,
                "original_target_date": str(target_dt),
                "simulated_target_date": str(new_target_dt),
                "original_required_monthly": float(round(orig_req_monthly, 2)),
                "simulated_required_monthly": float(round(new_req_monthly, 2)),
                "monthly_required_relief": float(round(monthly_diff, 2)),
                "summary": summary,
                "assumptions": ["Assumes goal target amount remains unchanged over the extended duration."]
            }

        # 6. Scenario: Monthly Contribution Change
        elif scenario_type == "monthly_contribution_change":
            new_contrib = Decimal(str(params.get("monthly_contribution", 10000)))
            new_months = float(round(remaining_amt / max(Decimal("1.0"), new_contrib), 1)) if new_contrib > 0 and remaining_amt > 0 else 0.0
            new_date = today + timedelta(days=int(new_months * 30.4375))

            summary = (
                f"Contributing ₹{new_contrib:,.2f}/month towards '{goal_name}' will complete the remaining ₹{remaining_amt:,.2f} "
                f"in ~{new_months} months (projected {new_date.strftime('%b %Y')})."
            )

            return {
                "scenario_type": scenario_type,
                "goal_name": goal_name,
                "simulated_monthly_contribution": float(new_contrib),
                "remaining_amount": float(remaining_amt),
                "simulated_months_to_completion": new_months,
                "projected_completion_date": str(new_date),
                "summary": summary,
                "assumptions": ["Assumes contribution is made consistently every single month."]
            }

        else:
            raise ValueError(f"Unknown scenario_type '{scenario_type}'. Supported: increased_savings, reduced_spending, increased_expenses, income_reduction, goal_deadline_change, monthly_contribution_change.")
