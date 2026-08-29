"""Financial Health Rules: Deterministic 7-factor mathematical evaluation of financial health."""

from decimal import Decimal
from typing import Dict, Any, List, Optional
from datetime import date, timedelta
from sqlalchemy.orm import Session

from app.models.transaction import Transaction, TransactionType
from app.models.budget import Budget
from app.models.goal import Goal
from app.services.ai.goals.goal_calculator import GoalCalculator


class HealthRules:
    """Evaluates 7 weighted financial health dimensions with deterministic calculations."""

    COMPONENT_WEIGHTS = {
        "CASHFLOW_HEALTH": 0.20,
        "SAVINGS_HEALTH": 0.15,
        "BUDGET_HEALTH": 0.15,
        "GOAL_HEALTH": 0.15,
        "EMERGENCY_BUFFER_HEALTH": 0.15,
        "DEBT_HEALTH": 0.10,
        "EXPENSE_STABILITY": 0.10
    }

    @staticmethod
    def get_status_label(score: float) -> str:
        """Classify a 0-100 score into status tiers."""
        if score >= 81.0:
            return "EXCELLENT"
        elif score >= 61.0:
            return "GOOD"
        elif score >= 41.0:
            return "FAIR"
        elif score >= 21.0:
            return "POOR"
        else:
            return "CRITICAL"

    @classmethod
    def evaluate_all_components(cls, user_id: int, db: Session, today: Optional[date] = None) -> Dict[str, Any]:
        """
        Evaluate all 7 health dimensions and calculate weighted overall financial health score.
        """
        calc_date = today or date.today()
        cur_m, cur_y = calc_date.month, calc_date.year

        # 1. Gather historical transaction data for current and previous month
        txs_cur = (
            db.query(Transaction)
            .filter(
                Transaction.user_id == user_id,
                Transaction.transaction_date <= calc_date,
                Transaction.transaction_date >= date(cur_y, cur_m, 1)
            )
            .all()
        )

        prev_date = (calc_date.replace(day=1) - timedelta(days=1))
        prev_m, prev_y = prev_date.month, prev_date.year
        txs_prev = (
            db.query(Transaction)
            .filter(
                Transaction.user_id == user_id,
                Transaction.transaction_date >= date(prev_y, prev_m, 1),
                Transaction.transaction_date <= prev_date
            )
            .all()
        )

        all_txs = db.query(Transaction).filter(Transaction.user_id == user_id).all()

        inc_cur = sum(Decimal(str(t.amount)) for t in txs_cur if t.type == TransactionType.INCOME)
        exp_cur = sum(Decimal(str(t.amount)) for t in txs_cur if t.type == TransactionType.EXPENSE)

        inc_prev = sum(Decimal(str(t.amount)) for t in txs_prev if t.type == TransactionType.INCOME)
        exp_prev = sum(Decimal(str(t.amount)) for t in txs_prev if t.type == TransactionType.EXPENSE)

        # Fallback to overall monthly averages if current month has 0 income
        if inc_cur == 0 and all_txs:
            tot_inc = sum(Decimal(str(t.amount)) for t in all_txs if t.type == TransactionType.INCOME)
            distinct_months = max(1, len(set((t.transaction_date.year, t.transaction_date.month) for t in all_txs)))
            inc_cur = tot_inc / Decimal(str(distinct_months))

        components: Dict[str, Dict[str, Any]] = {}

        # -------------------------------------------------------------
        # 1. CASHFLOW_HEALTH (Weight: 20%)
        # -------------------------------------------------------------
        if not all_txs or (inc_cur == 0 and exp_cur == 0):
            components["CASHFLOW_HEALTH"] = {
                "name": "Cashflow Health",
                "weight": cls.COMPONENT_WEIGHTS["CASHFLOW_HEALTH"],
                "score": None,
                "status": "INSUFFICIENT_DATA",
                "verified_evidence": "No transactions recorded for the evaluation period.",
                "calculation_explanation": "Operating surplus cannot be computed without verified income or expenses."
            }
        else:
            surplus = inc_cur - exp_cur
            ratio = float(surplus / inc_cur) if inc_cur > 0 else (-1.0 if exp_cur > 0 else 0.0)

            if ratio >= 0.30:
                cf_score = 100.0
            elif ratio >= 0.20:
                cf_score = 85.0 + (ratio - 0.20) * 150.0
            elif ratio >= 0.10:
                cf_score = 70.0 + (ratio - 0.10) * 150.0
            elif ratio >= 0.00:
                cf_score = 50.0 + ratio * 200.0
            else:
                cf_score = max(0.0, 50.0 + ratio * 100.0)

            cf_score = round(min(100.0, max(0.0, cf_score)), 1)
            components["CASHFLOW_HEALTH"] = {
                "name": "Cashflow Health",
                "weight": cls.COMPONENT_WEIGHTS["CASHFLOW_HEALTH"],
                "score": cf_score,
                "status": cls.get_status_label(cf_score),
                "verified_evidence": f"Monthly Income: ₹{float(inc_cur):,.2f}, Expenses: ₹{float(exp_cur):,.2f}, Net Surplus: ₹{float(surplus):,.2f} ({ratio*100:.1f}% margin).",
                "calculation_explanation": f"Surplus margin of {ratio*100:.1f}% maps to cashflow score of {cf_score}/100."
            }

        # -------------------------------------------------------------
        # 2. SAVINGS_HEALTH (Weight: 15%)
        # -------------------------------------------------------------
        if not all_txs or inc_cur == 0:
            components["SAVINGS_HEALTH"] = {
                "name": "Savings Health",
                "weight": cls.COMPONENT_WEIGHTS["SAVINGS_HEALTH"],
                "score": None,
                "status": "INSUFFICIENT_DATA",
                "verified_evidence": "No verified income transactions available to compute savings rate.",
                "calculation_explanation": "Savings rate requires positive verified monthly cash inflow."
            }
        else:
            net_saved = max(Decimal("0.00"), inc_cur - exp_cur)
            sav_rate = float((net_saved / inc_cur) * 100)

            if sav_rate >= 30.0:
                sav_score = 100.0
            elif sav_rate >= 20.0:
                sav_score = 80.0 + (sav_rate - 20.0) * 2.0
            elif sav_rate >= 10.0:
                sav_score = 60.0 + (sav_rate - 10.0) * 2.0
            elif sav_rate > 0.0:
                sav_score = 40.0 + sav_rate * 2.0
            else:
                sav_score = 20.0

            sav_score = round(min(100.0, max(0.0, sav_score)), 1)
            components["SAVINGS_HEALTH"] = {
                "name": "Savings Health",
                "weight": cls.COMPONENT_WEIGHTS["SAVINGS_HEALTH"],
                "score": sav_score,
                "status": cls.get_status_label(sav_score),
                "verified_evidence": f"Net savings: ₹{float(net_saved):,.2f} on income ₹{float(inc_cur):,.2f} (Savings Rate: {sav_rate:.1f}%).",
                "calculation_explanation": f"Savings rate of {sav_rate:.1f}% against 20%+ target maps to {sav_score}/100."
            }

        # -------------------------------------------------------------
        # 3. BUDGET_HEALTH (Weight: 15%)
        # -------------------------------------------------------------
        budgets = (
            db.query(Budget)
            .filter(Budget.user_id == user_id, Budget.month == cur_m, Budget.year == cur_y)
            .all()
        )

        if not budgets:
            components["BUDGET_HEALTH"] = {
                "name": "Budget Health",
                "weight": cls.COMPONENT_WEIGHTS["BUDGET_HEALTH"],
                "score": 75.0,
                "status": "GOOD",
                "verified_evidence": "No active category budget envelopes set for the current month.",
                "calculation_explanation": "Neutral baseline score (75.0) assigned in the absence of category overruns."
            }
        else:
            b_scores = []
            ev_list = []
            for b in budgets:
                cat_spent = sum(
                    Decimal(str(t.amount))
                    for t in txs_cur
                    if t.type == TransactionType.EXPENSE and t.category.lower() == b.category.lower()
                )
                b_limit = Decimal(str(b.amount))
                if b_limit > 0:
                    pct = float((cat_spent / b_limit) * 100)
                    if pct <= 80.0:
                        b_score = 100.0
                    elif pct <= 100.0:
                        b_score = 100.0 - (pct - 80.0) * 1.0  # 80-100% -> 100 to 80
                    else:
                        over_pct = pct - 100.0
                        b_score = max(10.0, 80.0 - over_pct * 1.5)
                    b_scores.append(b_score)
                    ev_list.append(f"{b.category}: ₹{float(cat_spent):,.2f}/₹{float(b_limit):,.2f} ({pct:.0f}%)")

            avg_b_score = round(sum(b_scores) / len(b_scores), 1) if b_scores else 75.0
            components["BUDGET_HEALTH"] = {
                "name": "Budget Health",
                "weight": cls.COMPONENT_WEIGHTS["BUDGET_HEALTH"],
                "score": avg_b_score,
                "status": cls.get_status_label(avg_b_score),
                "verified_evidence": "; ".join(ev_list),
                "calculation_explanation": f"Average envelope adherence score across {len(budgets)} budgets is {avg_b_score}/100."
            }

        # -------------------------------------------------------------
        # 4. GOAL_HEALTH (Weight: 15%)
        # -------------------------------------------------------------
        goals = db.query(Goal).filter(Goal.user_id == user_id).all()
        if not goals:
            components["GOAL_HEALTH"] = {
                "name": "Goal Health",
                "weight": cls.COMPONENT_WEIGHTS["GOAL_HEALTH"],
                "score": 75.0,
                "status": "GOOD",
                "verified_evidence": "No active financial goals established.",
                "calculation_explanation": "Neutral baseline score (75.0) assigned."
            }
        else:
            g_scores = []
            ev_list = []
            for g in goals:
                prog = GoalCalculator.calculate_progress(g, today=calc_date, monthly_savings_pace=max(Decimal("0.00"), inc_cur - exp_cur))
                st = prog["status"]
                if st == "COMPLETED":
                    gs = 100.0
                elif st == "AHEAD":
                    gs = 95.0
                elif st == "ON_TRACK":
                    gs = 85.0
                elif st == "AT_RISK":
                    gs = 55.0
                else:  # BEHIND
                    gs = 35.0
                g_scores.append(gs)
                ev_list.append(f"{g.name}: {prog['progress_percentage']:.1f}% ({st})")

            avg_g_score = round(sum(g_scores) / len(g_scores), 1)
            components["GOAL_HEALTH"] = {
                "name": "Goal Health",
                "weight": cls.COMPONENT_WEIGHTS["GOAL_HEALTH"],
                "score": avg_g_score,
                "status": cls.get_status_label(avg_g_score),
                "verified_evidence": "; ".join(ev_list),
                "calculation_explanation": f"Weighted trajectory score across {len(goals)} active goals is {avg_g_score}/100."
            }

        # -------------------------------------------------------------
        # 5. EMERGENCY_BUFFER_HEALTH (Weight: 15%)
        # -------------------------------------------------------------
        if exp_cur == 0 and not all_txs:
            components["EMERGENCY_BUFFER_HEALTH"] = {
                "name": "Emergency Buffer Health",
                "weight": cls.COMPONENT_WEIGHTS["EMERGENCY_BUFFER_HEALTH"],
                "score": None,
                "status": "INSUFFICIENT_DATA",
                "verified_evidence": "No expenditure baseline to evaluate emergency liquidity coverage.",
                "calculation_explanation": "Emergency reserve requires verified monthly expenditure run-rate."
            }
        else:
            monthly_burn = exp_cur if exp_cur > 0 else (exp_prev if exp_prev > 0 else Decimal("30000.00"))
            ef_goal = next((g for g in goals if g.category == "emergency_fund"), None)
            cur_savings = ef_goal.current_amount if ef_goal else max(Decimal("0.00"), inc_cur - exp_cur)
            months_covered = float(cur_savings / monthly_burn) if monthly_burn > 0 else 3.0

            if months_covered >= 6.0:
                eb_score = 100.0
            elif months_covered >= 3.0:
                eb_score = 80.0 + (months_covered - 3.0) * 6.6
            elif months_covered >= 1.0:
                eb_score = 50.0 + (months_covered - 1.0) * 15.0
            else:
                eb_score = max(10.0, months_covered * 50.0)

            eb_score = round(min(100.0, max(0.0, eb_score)), 1)
            components["EMERGENCY_BUFFER_HEALTH"] = {
                "name": "Emergency Buffer Health",
                "weight": cls.COMPONENT_WEIGHTS["EMERGENCY_BUFFER_HEALTH"],
                "score": eb_score,
                "status": cls.get_status_label(eb_score),
                "verified_evidence": f"Estimated liquid safety reserve of ₹{float(cur_savings):,.2f} provides {months_covered:.1f} months of coverage (monthly burn: ₹{float(monthly_burn):,.2f}).",
                "calculation_explanation": f"{months_covered:.1f} months of liquidity coverage against 3-6 month target maps to {eb_score}/100."
            }

        # -------------------------------------------------------------
        # 6. DEBT_HEALTH (Weight: 10%)
        # -------------------------------------------------------------
        debt_spent = sum(
            Decimal(str(t.amount))
            for t in txs_cur
            if t.type == TransactionType.EXPENSE and t.category.lower() in ["debt", "loan", "emi", "mortgage", "credit card"]
        )

        if inc_cur > 0:
            debt_ratio = float((debt_spent / inc_cur) * 100)
            if debt_ratio == 0:
                debt_score = 100.0
            elif debt_ratio <= 15.0:
                debt_score = 90.0
            elif debt_ratio <= 30.0:
                debt_score = 75.0
            elif debt_ratio <= 45.0:
                debt_score = 50.0
            else:
                debt_score = max(10.0, 100.0 - debt_ratio * 1.5)

            debt_score = round(min(100.0, max(0.0, debt_score)), 1)
            components["DEBT_HEALTH"] = {
                "name": "Debt Health",
                "weight": cls.COMPONENT_WEIGHTS["DEBT_HEALTH"],
                "score": debt_score,
                "status": cls.get_status_label(debt_score),
                "verified_evidence": f"Debt servicing outflow: ₹{float(debt_spent):,.2f} ({debt_ratio:.1f}% of income).",
                "calculation_explanation": f"Debt-to-income ratio of {debt_ratio:.1f}% maps to {debt_score}/100."
            }
        else:
            components["DEBT_HEALTH"] = {
                "name": "Debt Health",
                "weight": cls.COMPONENT_WEIGHTS["DEBT_HEALTH"],
                "score": 90.0 if debt_spent == 0 else 40.0,
                "status": "EXCELLENT" if debt_spent == 0 else "POOR",
                "verified_evidence": f"Debt expenditures: ₹{float(debt_spent):,.2f}.",
                "calculation_explanation": "Score evaluated on debt outflow scale."
            }

        # -------------------------------------------------------------
        # 7. EXPENSE_STABILITY (Weight: 10%)
        # -------------------------------------------------------------
        if exp_prev > 0 and exp_cur > 0:
            growth_pct = float(((exp_cur - exp_prev) / exp_prev) * 100)
            if growth_pct <= 0.0:
                st_score = 95.0
            elif growth_pct <= 10.0:
                st_score = 85.0
            elif growth_pct <= 20.0:
                st_score = 65.0
            else:
                st_score = max(20.0, 100.0 - growth_pct * 2.0)

            st_score = round(min(100.0, max(0.0, st_score)), 1)
            components["EXPENSE_STABILITY"] = {
                "name": "Expense Stability",
                "weight": cls.COMPONENT_WEIGHTS["EXPENSE_STABILITY"],
                "score": st_score,
                "status": cls.get_status_label(st_score),
                "verified_evidence": f"Month-over-month expenditure shift: {growth_pct:+.1f}% (Previous: ₹{float(exp_prev):,.2f}, Current: ₹{float(exp_cur):,.2f}).",
                "calculation_explanation": f"MoM expense growth of {growth_pct:+.1f}% maps to stability score of {st_score}/100."
            }
        else:
            components["EXPENSE_STABILITY"] = {
                "name": "Expense Stability",
                "weight": cls.COMPONENT_WEIGHTS["EXPENSE_STABILITY"],
                "score": 80.0,
                "status": "GOOD",
                "verified_evidence": "Single-period baseline observed; stable expenditure velocity.",
                "calculation_explanation": "Standard stability baseline (80.0) applied."
            }

        # -------------------------------------------------------------
        # Compute Overall Weighted Health Score
        # -------------------------------------------------------------
        valid_scores = [c for c in components.values() if c["score"] is not None]

        if not valid_scores:
            overall_score = None
            overall_status = "INSUFFICIENT_DATA"
            summary = "Not enough verified financial data is available to determine an overall health score."
        else:
            total_weight = sum(c["weight"] for c in valid_scores)
            weighted_sum = sum(c["score"] * c["weight"] for c in valid_scores)
            overall_score = round(min(100.0, max(0.0, weighted_sum / total_weight)), 1)
            overall_status = cls.get_status_label(overall_score)
            summary = f"Your overall financial health is rated {overall_status} ({overall_score}/100) based on {len(valid_scores)} evaluated dimensions."

        return {
            "overall_score": overall_score,
            "status": overall_status,
            "summary": summary,
            "components": components,
            "as_of_date": str(calc_date)
        }
