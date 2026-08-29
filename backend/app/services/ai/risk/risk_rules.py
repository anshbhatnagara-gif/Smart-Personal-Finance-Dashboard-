"""Financial Risk Rules: Deterministic risk detection algorithms and stress scoring."""

from datetime import date
from decimal import Decimal
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.models.transaction import Transaction, TransactionType
from app.models.budget import Budget
from app.models.goal import Goal
from app.services.ai.forecasting.cashflow_forecast import CashflowForecastEngine


class RiskSeverity:
    """Standard risk severity hierarchy."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NONE = "NONE"


class RiskType:
    """Standardized financial risk types."""
    CASHFLOW_RISK = "CASHFLOW_RISK"
    SAVINGS_RISK = "SAVINGS_RISK"
    BUDGET_RISK = "BUDGET_RISK"
    GOAL_RISK = "GOAL_RISK"
    EXPENSE_GROWTH_RISK = "EXPENSE_GROWTH_RISK"
    INCOME_DECLINE_RISK = "INCOME_DECLINE_RISK"
    EMERGENCY_BUFFER_RISK = "EMERGENCY_BUFFER_RISK"
    DISCRETIONARY_RISK = "DISCRETIONARY_RISK"
    DEBT_PRESSURE_RISK = "DEBT_PRESSURE_RISK"
    FINANCIAL_STRESS = "FINANCIAL_STRESS"


class RiskRules:
    """Evaluates individual risk conditions deterministically."""

    @staticmethod
    def evaluate_cashflow_risk(forecast_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """1. CASHFLOW_RISK: Projected expenses exceed projected income."""
        inc = forecast_data.get("income_forecast", {})
        exp = forecast_data.get("expense_forecast", {})
        if not inc.get("is_sufficient_data") or not exp.get("is_sufficient_data"):
            return None

        proj_inc = inc.get("projected_value", 0.0)
        proj_exp = exp.get("projected_value", 0.0)

        if proj_exp > proj_inc and proj_inc > 0.0:
            deficit = proj_exp - proj_inc
            deficit_pct = (deficit / proj_inc) * 100.0
            return {
                "risk_type": RiskType.CASHFLOW_RISK,
                "severity": RiskSeverity.CRITICAL,
                "title": "Projected Cashflow Deficit",
                "message": f"Projected monthly expenses (₹{proj_exp:,.2f}) exceed projected income (₹{proj_inc:,.2f}) by ₹{deficit:,.2f}.",
                "verified_evidence": f"Baseline Income: ₹{proj_inc:,.2f} vs Baseline Expenses: ₹{proj_exp:,.2f}.",
                "affected_amount": round(deficit, 2),
                "percentage": round(deficit_pct, 2),
                "explanation": "Outflows are outpacing verified incoming cash flow, leading to potential balance drawdown if unadjusted.",
                "recommended_action": "Review non-essential discretionary categories to eliminate the monthly shortfall."
            }
        return None

    @staticmethod
    def evaluate_savings_risk(forecast_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """2. SAVINGS_RISK: Projected savings rate falls below 20%."""
        sav = forecast_data.get("savings_forecast", {})
        inc = forecast_data.get("income_forecast", {})
        if not sav.get("is_sufficient_data") or inc.get("projected_value", 0.0) <= 0.0:
            return None

        rate = sav.get("projected_savings_rate_percentage", 0.0)
        proj_sav = sav.get("projected_value", 0.0)

        if rate < 20.0 and rate >= 0.0:
            return {
                "risk_type": RiskType.SAVINGS_RISK,
                "severity": RiskSeverity.HIGH if rate < 10.0 else RiskSeverity.MEDIUM,
                "title": "Sub-Optimal Projected Savings Rate",
                "message": f"Your projected savings rate is {rate:.1f}%, which is below the 20% healthy benchmark.",
                "verified_evidence": f"Projected Monthly Savings: ₹{proj_sav:,.2f} ({rate:.1f}% of income).",
                "affected_amount": round(max(proj_sav, 0.0), 2),
                "percentage": round(rate, 2),
                "explanation": "Maintaining a savings rate below 20% limits financial cushion building and delays target goal completions.",
                "recommended_action": "Target a 20%+ savings buffer by trimming 5-10% from discretionary expenditures."
            }
        return None

    @staticmethod
    def evaluate_budget_risk(forecast_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """3. BUDGET_RISK: Current spending pace predicts budget exhaustion before month end."""
        burn_list = forecast_data.get("budget_exhaustion_forecast", [])
        exceeded = [b for b in burn_list if b.get("will_exceed_budget")]

        if exceeded:
            worst = max(exceeded, key=lambda x: x.get("projected_overrun_amount", 0.0))
            overrun = worst.get("projected_overrun_amount", 0.0)
            cat = worst.get("category", "")
            return {
                "risk_type": RiskType.BUDGET_RISK,
                "severity": RiskSeverity.HIGH if overrun >= 5000.0 else RiskSeverity.MEDIUM,
                "title": f"Budget Exhaustion Risk in {cat}",
                "message": f"At current burn pace, your {cat} budget is projected to overrun by ₹{overrun:,.2f} before month-end.",
                "verified_evidence": f"{cat} Budget: ₹{worst['budget_amount']:,.2f}, Projected Outflow: ₹{worst['projected_month_end_spending']:,.2f}.",
                "affected_amount": round(overrun, 2),
                "percentage": round((worst['projected_month_end_spending'] / worst['budget_amount'] * 100.0) if worst['budget_amount'] > 0 else 0.0, 2),
                "explanation": f"Daily spending rate in {cat} is tracking faster than your allocated monthly limit.",
                "recommended_action": f"Slow daily {cat} spend to avoid exceeding your budget ceiling."
            }
        return None

    @staticmethod
    def evaluate_goal_risk(forecast_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """4. GOAL_RISK: Current savings pace cannot reach goal target by target date."""
        goals = forecast_data.get("goal_completion_forecast", [])
        behind = [g for g in goals if g.get("status") == "BEHIND" or g.get("projected_delay_months", 0) > 0]

        if behind:
            target_goal = behind[0]
            delay = target_goal.get("projected_delay_months", 0)
            req = target_goal.get("required_monthly_contribution", 0.0)
            rem = target_goal.get("remaining_amount", 0.0)
            return {
                "risk_type": RiskType.GOAL_RISK,
                "severity": RiskSeverity.MEDIUM,
                "title": f"Timeline Delay for {target_goal['name']}",
                "message": f"Current monthly savings pace projects a {delay}-month delay reaching your {target_goal['name']} target.",
                "verified_evidence": f"Remaining target: ₹{rem:,.2f} | Required pace: ₹{req:,.2f}/mo.",
                "affected_amount": round(rem, 2),
                "percentage": round(delay, 1),
                "explanation": "Allocated surplus is insufficient to reach the full target amount by the chosen deadline.",
                "recommended_action": f"Increase monthly contribution to ₹{req:,.2f}/mo or consider extending the target deadline."
            }
        return None

    @staticmethod
    def evaluate_expense_growth_risk(forecast_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """5. EXPENSE_GROWTH_RISK: Expenses consistently increasing over multiple periods (>= 15%)."""
        exp = forecast_data.get("expense_forecast", {})
        trend = exp.get("trend_percentage", 0.0)
        curr = exp.get("current_value", 0.0)

        if trend >= 15.0 and curr > 0.0:
            return {
                "risk_type": RiskType.EXPENSE_GROWTH_RISK,
                "severity": RiskSeverity.HIGH if trend >= 25.0 else RiskSeverity.MEDIUM,
                "title": "Accelerating Expense Surge",
                "message": f"Monthly expenses have grown at an average trend of +{trend:.1f}% period-over-period.",
                "verified_evidence": f"Historical expense trend rate: +{trend:.1f}%.",
                "affected_amount": round(curr, 2),
                "percentage": round(trend, 2),
                "explanation": "Sustained upward expense momentum reduces long-term net savings accumulation.",
                "recommended_action": "Audit recent month-over-month category expansions to curb lifestyle inflation."
            }
        return None

    @staticmethod
    def evaluate_income_decline_risk(forecast_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """6. INCOME_DECLINE_RISK: Income declining materially (>= 10%) vs previous periods."""
        inc = forecast_data.get("income_forecast", {})
        trend = inc.get("trend_percentage", 0.0)
        curr = inc.get("current_value", 0.0)

        if trend <= -10.0 and curr > 0.0:
            return {
                "risk_type": RiskType.INCOME_DECLINE_RISK,
                "severity": RiskSeverity.HIGH,
                "title": "Material Income Contraction",
                "message": f"Verified income has contracted by {trend:.1f}% compared to prior periods.",
                "verified_evidence": f"Income trend rate: {trend:.1f}%.",
                "affected_amount": round(curr, 2),
                "percentage": round(abs(trend), 2),
                "explanation": "Lower incoming cash flow tightens disposable margin and increases budget vulnerability.",
                "recommended_action": "Realign recurring monthly budgets to match the reduced income baseline."
            }
        return None

    @staticmethod
    def evaluate_emergency_buffer_risk(forecast_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """7. EMERGENCY_BUFFER_RISK: Available surplus is insufficient (< 10%) relative to recurring expenses."""
        sav = forecast_data.get("savings_forecast", {})
        exp = forecast_data.get("expense_forecast", {})
        if not sav.get("is_sufficient_data") or not exp.get("is_sufficient_data"):
            return None

        proj_sav = sav.get("projected_value", 0.0)
        proj_exp = exp.get("projected_value", 0.0)

        if proj_exp > 0.0 and (proj_sav / proj_exp) < 0.10:
            buffer_pct = (proj_sav / proj_exp) * 100.0
            return {
                "risk_type": RiskType.EMERGENCY_BUFFER_RISK,
                "severity": RiskSeverity.HIGH if proj_sav <= 0.0 else RiskSeverity.MEDIUM,
                "title": "Thin Monthly Cash Buffer",
                "message": f"Your projected monthly surplus of ₹{proj_sav:,.2f} provides less than 10% ({buffer_pct:.1f}%) cushion over monthly expenses.",
                "verified_evidence": f"Projected Expenses: ₹{proj_exp:,.2f} vs Projected Surplus: ₹{proj_sav:,.2f}.",
                "affected_amount": round(max(proj_sav, 0.0), 2),
                "percentage": round(buffer_pct, 2),
                "explanation": "A narrow cushion leaves little room for unexpected medical or maintenance emergencies.",
                "recommended_action": "Build a liquid cash reserve to absorb unplanned cost variations."
            }
        return None

    @staticmethod
    def evaluate_discretionary_risk(forecast_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """8. DISCRETIONARY_RISK: Discretionary expenses projected to become disproportionately high (> 40%)."""
        exp = forecast_data.get("expense_forecast", {})
        cats = exp.get("category_forecasts", {})
        total_exp = exp.get("projected_value", 0.0)

        if total_exp <= 0.0:
            return None

        discretionary_names = {"shopping", "food", "dining", "travel", "entertainment", "leisure", "hobbies"}
        disc_total = 0.0
        for name, c_data in cats.items():
            if name.lower() in discretionary_names:
                disc_total += c_data.get("projected_spending", 0.0)

        disc_ratio = (disc_total / total_exp) * 100.0
        if disc_ratio > 40.0:
            return {
                "risk_type": RiskType.DISCRETIONARY_RISK,
                "severity": RiskSeverity.MEDIUM,
                "title": "Elevated Discretionary Outflow",
                "message": f"Discretionary spending is projected at {disc_ratio:.1f}% (₹{disc_total:,.2f}) of total monthly expenses.",
                "verified_evidence": f"Discretionary spending: ₹{disc_total:,.2f} / ₹{total_exp:,.2f}.",
                "affected_amount": round(disc_total, 2),
                "percentage": round(disc_ratio, 2),
                "explanation": "Non-essential outflows occupy a large portion of cashflow that could otherwise accelerate savings.",
                "recommended_action": "Consider capping discretionary purchases to 30% of total expenses."
            }
        return None

    @staticmethod
    def evaluate_debt_pressure_risk(forecast_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """9. DEBT_PRESSURE_RISK: Debt-related payments consuming high share of income (> 30%)."""
        exp = forecast_data.get("expense_forecast", {})
        inc = forecast_data.get("income_forecast", {})
        cats = exp.get("category_forecasts", {})
        total_inc = inc.get("projected_value", 0.0)

        if total_inc <= 0.0:
            return None

        debt_names = {"debt", "loan", "emi", "credit card", "mortgage", "debt_payment", "debt_payoff"}
        debt_total = 0.0
        for name, c_data in cats.items():
            if any(dn in name.lower() for dn in debt_names):
                debt_total += c_data.get("projected_spending", 0.0)

        debt_ratio = (debt_total / total_inc) * 100.0
        if debt_ratio > 30.0:
            return {
                "risk_type": RiskType.DEBT_PRESSURE_RISK,
                "severity": RiskSeverity.HIGH,
                "title": "High Debt-to-Income Pressure",
                "message": f"Debt servicing payments constitute {debt_ratio:.1f}% (₹{debt_total:,.2f}) of projected monthly income.",
                "verified_evidence": f"Debt Outflow: ₹{debt_total:,.2f} / Income: ₹{total_inc:,.2f}.",
                "affected_amount": round(debt_total, 2),
                "percentage": round(debt_ratio, 2),
                "explanation": "High debt commitments restrict financial flexibility and cashflow liquidity.",
                "recommended_action": "Focus surplus cashflow toward high-interest debt amortization."
            }
        return None

    @staticmethod
    def calculate_overall_stress(risks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """10. FINANCIAL_STRESS: Aggregate overall financial stress rating."""
        if not risks:
            return {
                "overall_risk_level": RiskSeverity.NONE,
                "stress_score": 10,
                "summary": "No critical financial risks detected. Projections indicate a stable financial position."
            }

        crit_count = sum(1 for r in risks if r["severity"] == RiskSeverity.CRITICAL)
        high_count = sum(1 for r in risks if r["severity"] == RiskSeverity.HIGH)
        med_count = sum(1 for r in risks if r["severity"] == RiskSeverity.MEDIUM)

        if crit_count >= 1:
            level = RiskSeverity.CRITICAL
            score = 90
            summary = "Critical financial risks detected requiring immediate budget and cashflow realignment."
        elif high_count >= 2:
            level = RiskSeverity.HIGH
            score = 75
            summary = "Multiple high financial risks detected. Cashflow and spending buffers should be reinforced."
        elif high_count == 1 or med_count >= 2:
            level = RiskSeverity.MEDIUM
            score = 50
            summary = "Moderate financial risks detected. Monitoring discretionary burn and goal pacing is recommended."
        else:
            level = RiskSeverity.LOW
            score = 25
            summary = "Minor financial risks detected. Overall financial outlook remains generally stable."

        return {
            "overall_risk_level": level,
            "stress_score": score,
            "summary": summary
        }
