"""Explanation Rules: Deterministic mathematical explanation generation for forecasts, risks, goals, actions, and scores."""

from decimal import Decimal
from typing import Dict, Any, List, Optional
from datetime import date
from sqlalchemy.orm import Session

from app.services.ai.forecasting.forecast_engine import ForecastingEngine
from app.services.ai.risk.risk_engine import RiskEngine
from app.services.ai.goals.goal_service import GoalService
from app.services.ai.automation.action_engine import SmartActionEngine
from app.services.ai.intelligence.health_rules import HealthRules


class ExplanationRules:
    """Provides grounded mathematical explanations and transparent evidence citations."""

    @classmethod
    def generate_all_explanations(cls, user_id: int, db: Session, today: Optional[date] = None) -> List[Dict[str, Any]]:
        """Synthesize explanations across all active financial domains."""
        calc_date = today or date.today()
        explanations: List[Dict[str, Any]] = []

        # 1. WHY_THIS_HEALTH_SCORE
        health_data = HealthRules.evaluate_all_components(user_id, db, today=calc_date)
        if health_data.get("overall_score") is not None:
            comp_summaries = [
                f"{k}: {v['score']}/100 (Weight: {int(v['weight']*100)}%) — {v['calculation_explanation']}"
                for k, v in health_data.get("components", {}).items()
                if v.get("score") is not None
            ]
            explanations.append({
                "explanation_type": "WHY_THIS_HEALTH_SCORE",
                "label": "EXPLANATION",
                "title": f"Health Score Calculation: {health_data['overall_score']}/100 ({health_data['status']})",
                "summary": health_data["summary"],
                "verified_evidence": "Aggregated over verified monthly cashflow, savings pace, active budgets, and debt outflows.",
                "calculation_basis": "Weighted arithmetic mean across evaluated dimensions: " + "; ".join(comp_summaries),
                "affected_amount": 0.0,
                "confidence": "HIGH",
                "limitations": "Evaluates currently recorded transactions, budget envelopes, and goals within the active workspace."
            })

        # 2. WHY_THIS_FORECAST
        fc_engine = ForecastingEngine(user_id, db)
        fc_data = fc_engine.get_full_forecast(calc_date)
        inc_fc = fc_data.get("income_forecast", {})
        exp_fc = fc_data.get("expense_forecast", {})
        sav_fc = fc_data.get("savings_forecast", {})

        explanations.append({
            "explanation_type": "WHY_THIS_FORECAST",
            "label": "EXPLANATION",
            "title": f"Next-Month Projected Cashflow: ₹{fc_data.get('projected_net_savings', 0.0):,.2f} Surplus",
            "summary": f"Projected Income ₹{inc_fc.get('projected_value', 0.0):,.2f} minus Projected Expenses ₹{exp_fc.get('projected_value', 0.0):,.2f} yields net savings of ₹{sav_fc.get('projected_value', 0.0):,.2f} ({sav_fc.get('projected_savings_rate_percentage', 0.0):.1f}% savings rate).",
            "verified_evidence": f"Income Evidence: {'; '.join(inc_fc.get('evidence', ['Standard historical baseline']))}. Expense Evidence: {'; '.join(exp_fc.get('evidence', ['Historical category averages']))}.",
            "calculation_basis": "Linearly weighted moving average (W_i = i) giving higher weight to recent calendar months with trend slope extrapolation.",
            "affected_amount": float(sav_fc.get("projected_value", 0.0)),
            "confidence": inc_fc.get("confidence", "MEDIUM"),
            "limitations": "Projections assume continuing baseline income velocity and no unforeseen one-off emergency spikes."
        })

        # 3. WHY_THIS_RISK
        risk_engine = RiskEngine(user_id, db)
        risk_data = risk_engine.evaluate_risks(calc_date)
        risks = risk_data.get("risks", [])

        if risks:
            for r in risks[:3]:
                explanations.append({
                    "explanation_type": "WHY_THIS_RISK",
                    "label": "EXPLANATION",
                    "title": f"Risk Explanation: {r['title']} [{r['severity']}]",
                    "summary": r["message"],
                    "verified_evidence": r.get("verified_evidence", r["message"]),
                    "calculation_basis": f"Deterministic rule triggered: {r['risk_type']} evaluated against historical velocity thresholds.",
                    "affected_amount": float(r.get("affected_amount", 0.0)),
                    "confidence": "HIGH",
                    "limitations": "Risk level calculated strictly from recorded database data."
                })
        else:
            explanations.append({
                "explanation_type": "WHY_THIS_RISK",
                "label": "EXPLANATION",
                "title": "Zero Critical Financial Risks Detected",
                "summary": "All 10 deterministic risk evaluators passed within safe operating parameters.",
                "verified_evidence": "Cashflow is positive, savings rate is healthy, and no budget overruns were detected.",
                "calculation_basis": "Evaluated against 10 risk rules (Cashflow, Savings, Budget, Goal, Expense Growth, Debt, Emergency Buffer).",
                "affected_amount": 0.0,
                "confidence": "HIGH",
                "limitations": "Based on current workspace transactions."
            })

        # 4. WHY_THIS_GOAL_STATUS
        goals = GoalService.get_all_goals_progress(db=db, user_id=user_id)
        for g in goals[:2]:
            explanations.append({
                "explanation_type": "WHY_THIS_GOAL_STATUS",
                "label": "EXPLANATION",
                "title": f"Goal Status for '{g['name']}': {g['status']}",
                "summary": f"Saved ₹{g['current_amount']:,.2f} of ₹{g['target_amount']:,.2f} ({g['progress_percentage']:.1f}%). Required pace is ₹{g['required_monthly_contribution']:,.2f}/month with {g['days_remaining']} days remaining.",
                "verified_evidence": f"Target deadline is {g['target_date']}; remaining gap is ₹{g['remaining_amount']:,.2f}.",
                "calculation_basis": f"Progress ratio calculated by comparing elapsed time to date vs target completion timeline.",
                "affected_amount": float(g["remaining_amount"]),
                "confidence": "HIGH",
                "limitations": "Timeline feasibility depends on maintaining required monthly allocation."
            })

        # 5. WHY_THIS_SMART_ACTION
        action_engine = SmartActionEngine(user_id, db)
        proposals = action_engine.get_or_generate_actions(today=calc_date)
        for p in proposals[:2]:
            explanations.append({
                "explanation_type": "WHY_THIS_SMART_ACTION",
                "label": "EXPLANATION",
                "title": f"Smart Action Proposal: {p.title}",
                "summary": p.description,
                "verified_evidence": p.verified_evidence,
                "calculation_basis": f"Action type '{p.action_type}' triggered to achieve: {p.expected_impact}",
                "affected_amount": float(p.financial_amount),
                "confidence": "HIGH",
                "limitations": "Proposal is non-binding and requires explicit user confirmation before execution."
            })

        return explanations
