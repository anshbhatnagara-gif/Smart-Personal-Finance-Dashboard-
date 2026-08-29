"""Action Rules: Deterministic generation of grounded financial action recommendations."""

import hashlib
import json
import uuid
from datetime import date, datetime, timezone, timedelta
from decimal import Decimal
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.models.transaction import Transaction, TransactionType
from app.models.budget import Budget
from app.models.goal import Goal
from app.models.smart_action import ActionTypeEnum, ActionStatusEnum
from app.services.ai.forecasting.forecast_engine import ForecastingEngine
from app.services.ai.risk.risk_engine import RiskEngine
from app.services.ai.goals.goal_calculator import GoalCalculator


class ActionRules:
    """Evaluates verified financial data to synthesize grounded smart action proposals."""

    @staticmethod
    def compute_payload_hash(payload: Dict[str, Any]) -> str:
        """Generate deterministic SHA-256 hash of canonical action payload."""
        canonical_json = json.dumps(payload, sort_keys=True, separators=(',', ':'), default=str)
        return hashlib.sha256(canonical_json.encode('utf-8')).hexdigest()

    @classmethod
    def generate_candidate_actions(cls, user_id: int, db: Session, today: Optional[date] = None) -> List[Dict[str, Any]]:
        """
        Evaluate user financial data across transactions, budgets, goals, forecasts, and risks
        to generate up to 8 prioritized candidate action proposals.
        """
        calc_date = today or date.today()
        now_utc = datetime.now(timezone.utc)
        expires_at = now_utc + timedelta(hours=24)

        fc_engine = ForecastingEngine(user_id, db)
        risk_engine = RiskEngine(user_id, db)

        forecast = fc_engine.get_full_forecast(calc_date)
        risks_report = risk_engine.evaluate_risks(calc_date)

        actions: List[Dict[str, Any]] = []

        # -------------------------------------------------------------
        # 1. BUDGET_ADJUSTMENT: Address budget envelopes projected to overrun
        # -------------------------------------------------------------
        burns = forecast.get("budget_exhaustion_forecast", [])
        for b in burns:
            if b.get("will_exceed_budget") and b.get("projected_overrun_amount", 0.0) > 0:
                cat = b["category"]
                curr_b = b["budget_amount"]
                proj_spent = b["projected_month_end_spending"]
                overrun = b["projected_overrun_amount"]
                suggested_budget = round(proj_spent * 1.05, 2)  # 5% buffer

                payload = {
                    "action": "adjust_budget",
                    "category": cat,
                    "current_budget": curr_b,
                    "new_budget_amount": suggested_budget,
                    "month": calc_date.month,
                    "year": calc_date.year
                }

                actions.append({
                    "action_id": f"act-{uuid.uuid4().hex[:12]}",
                    "action_type": ActionTypeEnum.BUDGET_ADJUSTMENT.value,
                    "title": f"Realign {cat} Budget Envelope",
                    "description": f"Adjust {cat} budget from ₹{curr_b:,.2f} to ₹{suggested_budget:,.2f} to accommodate verified monthly spending velocity.",
                    "verified_evidence": f"Daily spending burn of ₹{b['daily_burn_rate']:,.2f}/day projects month-end spending of ₹{proj_spent:,.2f} (overrun: ₹{overrun:,.2f}).",
                    "financial_amount": Decimal(str(suggested_budget)),
                    "expected_impact": f"Prevents budget failure alert and establishes a realistic cap of ₹{suggested_budget:,.2f}.",
                    "risk_level": "HIGH",
                    "requires_confirmation": True,
                    "status": ActionStatusEnum.PROPOSED.value,
                    "action_payload": json.dumps(payload),
                    "payload_hash": cls.compute_payload_hash(payload),
                    "created_at": now_utc,
                    "expires_at": expires_at
                })

        # -------------------------------------------------------------
        # 2. GOAL_CONTRIBUTION_ADJUSTMENT: Accelerate behind-schedule goals
        # -------------------------------------------------------------
        goals = db.query(Goal).filter(Goal.user_id == user_id).all()
        sav_fc = forecast.get("savings_forecast", {})
        monthly_surplus = Decimal(str(sav_fc.get("projected_value", 0.0)))

        for g in goals:
            prog = GoalCalculator.calculate_progress(g, today=calc_date, monthly_savings_pace=monthly_surplus)
            if (prog["status"] in ["BEHIND", "AT_RISK"] or prog["progress_percentage"] < 50.0) and prog["required_monthly_contribution"] > 0:
                req_c = prog["required_monthly_contribution"]
                suggested_contrib = round(req_c, 2)

                payload = {
                    "action": "adjust_goal_contribution",
                    "goal_id": g.id,
                    "goal_name": g.name,
                    "target_amount": prog["target_amount"],
                    "required_monthly_contribution": suggested_contrib,
                    "target_date": prog["target_date"]
                }

                actions.append({
                    "action_id": f"act-{uuid.uuid4().hex[:12]}",
                    "action_type": ActionTypeEnum.GOAL_CONTRIBUTION_ADJUSTMENT.value,
                    "title": f"Increase Monthly Contribution for '{g.name}'",
                    "description": f"Allocate ₹{suggested_contrib:,.2f}/month towards '{g.name}' to get back on track for deadline {g.target_date}.",
                    "verified_evidence": f"Currently saved ₹{prog['current_amount']:,.2f} of ₹{prog['target_amount']:,.2f} with {prog['days_remaining']} days remaining (status: BEHIND).",
                    "financial_amount": Decimal(str(suggested_contrib)),
                    "expected_impact": f"Ensures goal completion by {g.target_date} without timeline slippage.",
                    "risk_level": "MEDIUM",
                    "requires_confirmation": True,
                    "status": ActionStatusEnum.PROPOSED.value,
                    "action_payload": json.dumps(payload),
                    "payload_hash": cls.compute_payload_hash(payload),
                    "created_at": now_utc,
                    "expires_at": expires_at
                })

        # -------------------------------------------------------------
        # 3. EMERGENCY_FUND_CONTRIBUTION: Fund liquidity safety buffer
        # -------------------------------------------------------------
        ef_goal = next((g for g in goals if g.category == "emergency_fund"), None)
        exp_fc = forecast.get("expense_forecast", {})
        proj_monthly_exp = Decimal(str(exp_fc.get("projected_value", 0.0)))
        target_ef = round(proj_monthly_exp * 3, 2)

        if not ef_goal and proj_monthly_exp > 0:
            suggested_target = float(target_ef) if target_ef > 0 else 100000.0
            initial_contrib = round(float(monthly_surplus * Decimal("0.30")), 2) if monthly_surplus > 0 else 5000.0
            target_dt_str = str(calc_date + timedelta(days=180))

            payload = {
                "action": "create_emergency_fund_goal",
                "name": "3-Month Emergency Fund",
                "target_amount": suggested_target,
                "initial_amount": initial_contrib,
                "target_date": target_dt_str,
                "category": "emergency_fund",
                "priority": "critical"
            }

            actions.append({
                "action_id": f"act-{uuid.uuid4().hex[:12]}",
                "action_type": ActionTypeEnum.EMERGENCY_FUND_CONTRIBUTION.value,
                "title": "Establish 3-Month Emergency Fund Reserve",
                "description": f"Create a dedicated emergency fund goal with target ₹{suggested_target:,.2f} to protect against unforeseen expenses.",
                "verified_evidence": f"Projected monthly expenditures are ₹{float(proj_monthly_exp):,.2f}; benchmark 3-month cushion is ₹{suggested_target:,.2f}.",
                "financial_amount": Decimal(str(suggested_target)),
                "expected_impact": "Builds financial resilience and protects ongoing investments from cashflow shocks.",
                "risk_level": "HIGH",
                "requires_confirmation": True,
                "status": ActionStatusEnum.PROPOSED.value,
                "action_payload": json.dumps(payload),
                "payload_hash": cls.compute_payload_hash(payload),
                "created_at": now_utc,
                "expires_at": expires_at
            })

        # -------------------------------------------------------------
        # 4. SAVINGS_INCREASE: Capitalize on positive monthly surplus
        # -------------------------------------------------------------
        sav_rate = sav_fc.get("projected_savings_rate_percentage", 0.0)
        if monthly_surplus > Decimal("5000.00") and sav_rate < 30.0:
            boost_amt = round(float(monthly_surplus * Decimal("0.20")), 2)
            payload = {
                "action": "boost_monthly_savings",
                "additional_monthly_savings": boost_amt,
                "projected_surplus": float(monthly_surplus)
            }

            actions.append({
                "action_id": f"act-{uuid.uuid4().hex[:12]}",
                "action_type": ActionTypeEnum.SAVINGS_INCREASE.value,
                "title": f"Boost Monthly Savings by ₹{boost_amt:,.2f}",
                "description": f"Direct an extra ₹{boost_amt:,.2f}/month of projected cashflow surplus into high-yield savings.",
                "verified_evidence": f"Projected net monthly surplus is ₹{float(monthly_surplus):,.2f} (savings rate: {sav_rate}%).",
                "financial_amount": Decimal(str(boost_amt)),
                "expected_impact": f"Accelerates net worth growth and lifts savings rate towards 30%+ benchmark.",
                "risk_level": "LOW",
                "requires_confirmation": True,
                "status": ActionStatusEnum.PROPOSED.value,
                "action_payload": json.dumps(payload),
                "payload_hash": cls.compute_payload_hash(payload),
                "created_at": now_utc,
                "expires_at": expires_at
            })

        # -------------------------------------------------------------
        # 5. EXPENSE_REDUCTION: Trim high discretionary spending
        # -------------------------------------------------------------
        cat_fc = exp_fc.get("category_forecasts", {})
        for cat_name, c_data in cat_fc.items():
            if cat_name.lower() in ["shopping", "entertainment", "dining", "food"] and c_data.get("trend_percentage", 0.0) > 15.0:
                cat_spend = c_data.get("projected_spending", 0.0)
                reduction_target = round(cat_spend * 0.15, 2)
                payload = {
                    "action": "reduce_category_expense",
                    "category": cat_name,
                    "current_projected": cat_spend,
                    "target_reduction": reduction_target,
                    "new_target_spending": round(cat_spend - reduction_target, 2)
                }

                actions.append({
                    "action_id": f"act-{uuid.uuid4().hex[:12]}",
                    "action_type": ActionTypeEnum.EXPENSE_REDUCTION.value,
                    "title": f"Trim Discretionary Outflow in {cat_name}",
                    "description": f"Reduce {cat_name} spending by 15% (₹{reduction_target:,.2f}) to counter recent upward velocity (+{c_data.get('trend_percentage'):.1f}%).",
                    "verified_evidence": f"{cat_name} projected spending is ₹{cat_spend:,.2f} with a +{c_data.get('trend_percentage'):.1f}% growth trend.",
                    "financial_amount": Decimal(str(reduction_target)),
                    "expected_impact": f"Unlocks ₹{reduction_target:,.2f}/month in preserved capital for savings or debt reduction.",
                    "risk_level": "LOW",
                    "requires_confirmation": True,
                    "status": ActionStatusEnum.PROPOSED.value,
                    "action_payload": json.dumps(payload),
                    "payload_hash": cls.compute_payload_hash(payload),
                    "created_at": now_utc,
                    "expires_at": expires_at
                })

        # -------------------------------------------------------------
        # 6. FINANCIAL_RISK_MITIGATION: Mitigate critical / high risks
        # -------------------------------------------------------------
        risks = risks_report.get("risks", [])
        for r in risks:
            if r["severity"] in ["CRITICAL", "HIGH"]:
                payload = {
                    "action": "mitigate_risk",
                    "risk_type": r["risk_type"],
                    "affected_amount": r.get("affected_amount", 0.0),
                    "recommended_action": r.get("recommended_action", "")
                }

                actions.append({
                    "action_id": f"act-{uuid.uuid4().hex[:12]}",
                    "action_type": ActionTypeEnum.FINANCIAL_RISK_MITIGATION.value,
                    "title": f"Mitigate {r['title']}",
                    "description": r.get("recommended_action", f"Take proactive corrective measures to resolve {r['risk_type']}."),
                    "verified_evidence": r.get("verified_evidence", r["message"]),
                    "financial_amount": Decimal(str(r.get("affected_amount", 0.0))),
                    "expected_impact": "De-escalates elevated financial stress and stabilizes monthly budget margins.",
                    "risk_level": r["severity"],
                    "requires_confirmation": True,
                    "status": ActionStatusEnum.PROPOSED.value,
                    "action_payload": json.dumps(payload),
                    "payload_hash": cls.compute_payload_hash(payload),
                    "created_at": now_utc,
                    "expires_at": expires_at
                })

        # Sort actions deterministically: CRITICAL > HIGH > MEDIUM > LOW
        severity_weights = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
        actions.sort(
            key=lambda a: (severity_weights.get(a["risk_level"], 0), float(a["financial_amount"])),
            reverse=True
        )

        return actions[:8]
