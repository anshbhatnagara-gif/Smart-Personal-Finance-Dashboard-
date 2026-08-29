"""Simulation Rules: Mathematical what-if financial simulation engine."""

from decimal import Decimal
from typing import Dict, Any, List, Optional
from datetime import date, timedelta
from sqlalchemy.orm import Session

from app.models.transaction import Transaction, TransactionType
from app.models.goal import Goal
from app.services.ai.intelligence.health_rules import HealthRules
from app.services.ai.forecasting.forecast_engine import ForecastingEngine
from app.services.ai.goals.goal_calculator import GoalCalculator


class SimulationRules:
    """Computes deterministic what-if delta projections without modifying database state."""

    SUPPORTED_SCENARIOS = [
        "INCREASE_SAVINGS",
        "REDUCE_EXPENSES",
        "INCREASE_EXPENSES",
        "INCOME_REDUCTION",
        "INCOME_INCREASE",
        "GOAL_DEADLINE_CHANGE",
        "MONTHLY_CONTRIBUTION_CHANGE",
        "DEBT_PAYMENT_CHANGE"
    ]

    @classmethod
    def run_simulation(
        cls,
        user_id: int,
        db: Session,
        scenario: str,
        amount: Optional[float] = None,
        percentage: Optional[float] = None,
        months: Optional[int] = None,
        goal_id: Optional[int] = None,
        category: Optional[str] = None,
        today: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Execute in-memory mathematical simulation and return before vs after impact metrics.
        """
        calc_date = today or date.today()
        scenario_upper = scenario.upper()

        if scenario_upper not in cls.SUPPORTED_SCENARIOS:
            raise ValueError(f"Unsupported simulation scenario '{scenario}'. Supported: {', '.join(cls.SUPPORTED_SCENARIOS)}")

        if amount is not None and amount < 0:
            raise ValueError("Simulation amount cannot be negative.")
        if percentage is not None and percentage < 0:
            raise ValueError("Simulation percentage cannot be negative.")

        # 1. Gather baseline metrics
        fc_engine = ForecastingEngine(user_id, db)
        base_fc = fc_engine.get_full_forecast(calc_date)

        base_inc = float(base_fc.get("projected_income", 50000.0))
        base_exp = float(base_fc.get("projected_expenses", 35000.0))
        base_sav = max(0.0, base_inc - base_exp)
        base_rate = (base_sav / base_inc * 100) if base_inc > 0 else 0.0

        base_health = HealthRules.evaluate_all_components(user_id, db, today=calc_date)
        base_score = base_health.get("overall_score") or 70.0

        # Goals baseline
        goals = db.query(Goal).filter(Goal.user_id == user_id).all()
        target_goal = next((g for g in goals if g.id == goal_id), goals[0] if goals else None)

        base_goal_months = 12.0
        if target_goal:
            base_prog = GoalCalculator.calculate_progress(target_goal, today=calc_date, monthly_savings_pace=Decimal(str(base_sav)))
            rem_amt = base_prog.get("remaining_amount", 100000.0)
            base_goal_months = round(rem_amt / max(100.0, base_sav), 1) if base_sav > 0 else 24.0

        # 2. Compute simulated delta
        sim_inc = base_inc
        sim_exp = base_exp
        sim_goal_months = base_goal_months
        impact_summary = ""

        if scenario_upper == "INCREASE_SAVINGS":
            delta_sav = float(amount or (base_inc * (percentage or 10.0) / 100.0))
            sim_exp = max(0.0, base_exp - delta_sav)
            sim_sav = base_inc - sim_exp
            sim_rate = (sim_sav / base_inc * 100) if base_inc > 0 else 0.0
            if target_goal and sim_sav > 0:
                rem_amt = float(target_goal.target_amount - target_goal.current_amount)
                sim_goal_months = round(rem_amt / sim_sav, 1)
            impact_summary = f"Increasing monthly savings by ₹{delta_sav:,.2f} lifts savings rate to {sim_rate:.1f}% and accelerates goal completion by {max(0.0, base_goal_months - sim_goal_months):.1f} months."

        elif scenario_upper == "REDUCE_EXPENSES":
            delta_exp = float(amount or (base_exp * (percentage or 15.0) / 100.0))
            sim_exp = max(0.0, base_exp - delta_exp)
            sim_sav = max(0.0, sim_inc - sim_exp)
            sim_rate = (sim_sav / sim_inc * 100) if sim_inc > 0 else 0.0
            if target_goal and sim_sav > 0:
                rem_amt = float(target_goal.target_amount - target_goal.current_amount)
                sim_goal_months = round(rem_amt / sim_sav, 1)
            impact_summary = f"Trimming monthly expenses by ₹{delta_exp:,.2f} unlocks ₹{delta_exp:,.2f}/month in extra capital (Savings rate: {sim_rate:.1f}%)."

        elif scenario_upper == "INCREASE_EXPENSES":
            delta_exp = float(amount or (base_exp * (percentage or 10.0) / 100.0))
            sim_exp = base_exp + delta_exp
            sim_sav = max(0.0, sim_inc - sim_exp)
            sim_rate = (sim_sav / sim_inc * 100) if sim_inc > 0 else 0.0
            if target_goal and sim_sav > 0:
                rem_amt = float(target_goal.target_amount - target_goal.current_amount)
                sim_goal_months = round(rem_amt / sim_sav, 1)
            else:
                sim_goal_months = base_goal_months + 6.0
            impact_summary = f"Adding ₹{delta_exp:,.2f}/month in expenses reduces monthly surplus to ₹{sim_sav:,.2f} (Savings rate drops to {sim_rate:.1f}%)."

        elif scenario_upper == "INCOME_REDUCTION":
            pct = percentage or 10.0
            delta_inc = float(amount or (base_inc * pct / 100.0))
            sim_inc = max(0.0, base_inc - delta_inc)
            sim_sav = max(0.0, sim_inc - sim_exp)
            sim_rate = (sim_sav / sim_inc * 100) if sim_inc > 0 else 0.0
            impact_summary = f"A {pct:.1f}% income reduction (₹{delta_inc:,.2f}) compresses monthly surplus to ₹{sim_sav:,.2f}."

        elif scenario_upper == "INCOME_INCREASE":
            pct = percentage or 15.0
            delta_inc = float(amount or (base_inc * pct / 100.0))
            sim_inc = base_inc + delta_inc
            sim_sav = max(0.0, sim_inc - sim_exp)
            sim_rate = (sim_sav / sim_inc * 100) if sim_inc > 0 else 0.0
            if target_goal and sim_sav > 0:
                rem_amt = float(target_goal.target_amount - target_goal.current_amount)
                sim_goal_months = round(rem_amt / sim_sav, 1)
            impact_summary = f"A {pct:.1f}% income increase (+₹{delta_inc:,.2f}) expands monthly savings to ₹{sim_sav:,.2f} (Savings rate: {sim_rate:.1f}%)."

        elif scenario_upper == "GOAL_DEADLINE_CHANGE":
            delta_m = months or 3
            if target_goal:
                rem_amt = float(target_goal.target_amount - target_goal.current_amount)
                new_months = max(1.0, base_goal_months + delta_m)
                req_contrib = round(rem_amt / new_months, 2)
                sim_goal_months = new_months
                impact_summary = f"Adjusting deadline by {delta_m:+d} months sets required contribution to ₹{req_contrib:,.2f}/month."
            else:
                impact_summary = "Goal timeline shift evaluated against standard 12-month baseline."

        elif scenario_upper == "MONTHLY_CONTRIBUTION_CHANGE":
            delta_contrib = float(amount or 2000.0)
            if target_goal:
                rem_amt = float(target_goal.target_amount - target_goal.current_amount)
                new_pace = max(500.0, base_sav + delta_contrib)
                sim_goal_months = round(rem_amt / new_pace, 1)
                impact_summary = f"Contributing an extra ₹{delta_contrib:,.2f}/month shortens goal completion to {sim_goal_months:.1f} months."
            else:
                impact_summary = f"Increasing contribution by ₹{delta_contrib:,.2f}/month accelerates goal pace."

        elif scenario_upper == "DEBT_PAYMENT_CHANGE":
            extra_debt_pay = float(amount or 3000.0)
            sim_exp = base_exp + extra_debt_pay
            sim_sav = max(0.0, sim_inc - sim_exp)
            impact_summary = f"Accelerating debt payoff by ₹{extra_debt_pay:,.2f}/month reduces long-term interest burden and de-escalates debt stress."

        # Compute simulated savings & health score
        sim_sav = max(0.0, sim_inc - sim_exp)
        sim_rate = (sim_sav / sim_inc * 100) if sim_inc > 0 else 0.0

        # Heuristic delta for health score
        sav_rate_diff = sim_rate - base_rate
        sim_score = round(min(100.0, max(10.0, base_score + sav_rate_diff * 0.5)), 1)
        sim_status = HealthRules.get_status_label(sim_score)

        return {
            "scenario": scenario_upper,
            "label": "SIMULATION",
            "disclaimer": "SIMULATION ONLY — No modifications were made to your database records.",
            "current_state": {
                "monthly_income": round(base_inc, 2),
                "monthly_expenses": round(base_exp, 2),
                "monthly_savings": round(base_sav, 2),
                "savings_rate_percentage": round(base_rate, 1),
                "health_score": base_score,
                "goal_completion_months": round(base_goal_months, 1)
            },
            "simulated_state": {
                "monthly_income": round(sim_inc, 2),
                "monthly_expenses": round(sim_exp, 2),
                "monthly_savings": round(sim_sav, 2),
                "savings_rate_percentage": round(sim_rate, 1),
                "health_score": sim_score,
                "health_status": sim_status,
                "goal_completion_months": round(sim_goal_months, 1)
            },
            "impact": {
                "delta_monthly_savings": round(sim_sav - base_sav, 2),
                "delta_savings_rate": round(sim_rate - base_rate, 1),
                "delta_health_score": round(sim_score - base_score, 1),
                "timeline_acceleration_months": round(base_goal_months - sim_goal_months, 1),
                "summary": impact_summary
            }
        }
