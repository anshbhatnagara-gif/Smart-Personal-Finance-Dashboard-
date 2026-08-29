import json
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import extract

from app.models.transaction import Transaction, TransactionType
from app.models.budget import Budget
from app.services.finance_service import (
    calculate_savings,
    calculate_savings_rate,
    analyze_categories,
    calculate_financial_health_score,
    generate_smart_insights
)
from app.services.intelligence_service import IntelligenceService
from app.services.ai.insights.insight_engine import InsightEngine
from app.services.ai.goals.goal_service import GoalService
from app.services.ai.goals.goal_calculator import GoalCalculator
from app.services.ai.planning.planning_engine import PlanningEngine
from app.services.ai.planning.goal_projection import GoalProjectionEngine
from app.services.ai.planning.affordability_engine import AffordabilityEngine
from app.services.ai.planning.scenario_engine import ScenarioEngine
from app.services.ai.forecasting.forecast_engine import ForecastingEngine
from app.services.ai.risk.risk_engine import RiskEngine
from app.services.ai.predictions.predictive_engine import PredictiveEngine
from app.services.ai.automation.action_engine import SmartActionEngine
from app.services.ai.intelligence.health_score import HealthScoreEngine
from app.services.ai.intelligence.intelligence_engine import UnifiedIntelligenceEngine
from app.services.ai.explainability.explanation_engine import ExplanationEngine
from app.services.ai.simulation.simulation_engine import SimulationEngine


class FinancialToolExecutor:
    """Safely executes read-only financial tools scoped to authenticated user_id."""

    def __init__(self, user_id: int, db: Session):
        self.user_id = user_id
        self.db = db

    def execute(self, tool_name: str, arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Dispatch requested tool by name with parameter validation."""
        args = arguments or {}

        handlers = {
            "get_transactions": self.get_transactions,
            "get_transaction_summary": self.get_transaction_summary,
            "get_budget_progress": self.get_budget_progress,
            "get_dashboard": self.get_dashboard,
            "get_category_spending": self.get_category_spending,
            "get_monthly_cashflow": self.get_monthly_cashflow,
            "get_spending_analysis": self.get_spending_analysis,
            "get_savings_opportunities": self.get_savings_opportunities,
            "get_financial_health": self.get_financial_health,
            "get_proactive_insights": self.get_proactive_insights,
            "get_spending_alerts": self.get_spending_alerts,
            "get_financial_changes": self.get_financial_changes,
            "get_financial_goals": self.get_financial_goals,
            "get_goal_progress": self.get_goal_progress,
            "calculate_goal_plan": self.calculate_goal_plan,
            "calculate_affordability": self.calculate_affordability,
            "run_financial_scenario": self.run_financial_scenario,
            "get_coaching_context": self.get_coaching_context,
            "get_financial_forecast": self.get_financial_forecast,
            "get_cashflow_forecast": self.get_cashflow_forecast,
            "get_expense_forecast": self.get_expense_forecast,
            "get_income_forecast": self.get_income_forecast,
            "get_savings_forecast": self.get_savings_forecast,
            "get_financial_risks": self.get_financial_risks,
            "get_predictive_insights": self.get_predictive_insights,
            "get_forecast_explanation": self.get_forecast_explanation,
            "get_smart_actions": self.get_smart_actions,
            "get_action_details": self.get_action_details,
            "propose_financial_action": self.propose_financial_action,
            "confirm_financial_action": self.confirm_financial_action,
            "execute_financial_action": self.execute_financial_action,
            "reject_financial_action": self.reject_financial_action,
            "get_action_history": self.get_action_history,
            "get_financial_health_score": self.get_financial_health_score,
            "get_financial_intelligence": self.get_financial_intelligence,
            "explain_financial_forecast": self.explain_financial_forecast,
            "explain_financial_risk": self.explain_financial_risk,
            "explain_goal_status": self.explain_goal_status,
            "explain_smart_action": self.explain_smart_action,
            "run_financial_simulation": self.run_financial_simulation,
            "explain_health_score": self.explain_health_score,
        }

        handler = handlers.get(tool_name)
        if not handler:
            return {"error": f"Tool '{tool_name}' is not recognized or supported."}

        try:
            return handler(**args)
        except TypeError as e:
            return {"error": f"Invalid arguments for tool '{tool_name}': {str(e)}"}
        except Exception as e:
            return {"error": f"Tool execution failed: {str(e)}"}

    def get_transactions(
        self,
        category: Optional[str] = None,
        transaction_type: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """Fetch transactions strictly scoped by authenticated user_id."""
        query = self.db.query(Transaction).filter(Transaction.user_id == self.user_id)

        if category and category.strip():
            query = query.filter(Transaction.category.ilike(f"%{category.strip()}%"))

        if transaction_type and transaction_type.lower() in ["income", "expense"]:
            query = query.filter(Transaction.type == TransactionType(transaction_type.lower()))

        if start_date:
            try:
                s_date = datetime.strptime(start_date, "%Y-%m-%d").date()
                query = query.filter(Transaction.transaction_date >= s_date)
            except ValueError:
                pass

        if end_date:
            try:
                e_date = datetime.strptime(end_date, "%Y-%m-%d").date()
                query = query.filter(Transaction.transaction_date <= e_date)
            except ValueError:
                pass

        safe_limit = max(1, min(limit, 50))
        txs = query.order_by(Transaction.transaction_date.desc()).limit(safe_limit).all()

        return {
            "count": len(txs),
            "transactions": [
                {
                    "id": t.id,
                    "title": t.title,
                    "amount": float(t.amount),
                    "type": t.type.value,
                    "category": t.category,
                    "date": t.transaction_date.isoformat(),
                    "description": t.description
                }
                for t in txs
            ]
        }

    def get_transaction_summary(
        self,
        month: Optional[int] = None,
        year: Optional[int] = None
    ) -> Dict[str, Any]:
        """Calculate total income, expenses, and net savings for user in specified period."""
        now = datetime.now()
        target_month = month if (month and 1 <= month <= 12) else now.month
        target_year = year if (year and 2000 <= year <= 2100) else now.year

        txs = self.db.query(Transaction).filter(
            Transaction.user_id == self.user_id,
            extract("month", Transaction.transaction_date) == target_month,
            extract("year", Transaction.transaction_date) == target_year
        ).all()

        total_income = sum((t.amount for t in txs if t.type == TransactionType.INCOME), Decimal("0.00"))
        total_expenses = sum((t.amount for t in txs if t.type == TransactionType.EXPENSE), Decimal("0.00"))
        net_savings = calculate_savings(total_income, total_expenses)
        savings_rate = calculate_savings_rate(total_income, total_expenses)

        return {
            "month": target_month,
            "year": target_year,
            "total_income": float(total_income),
            "total_expenses": float(total_expenses),
            "net_savings": float(net_savings),
            "savings_rate_percentage": savings_rate,
            "transaction_count": len(txs)
        }

    def get_budget_progress(
        self,
        month: Optional[int] = None,
        year: Optional[int] = None
    ) -> Dict[str, Any]:
        """Fetch budget envelopes and calculate live utilization and risk predictions."""
        now = datetime.now()
        target_month = month if (month and 1 <= month <= 12) else now.month
        target_year = year if (year and 2000 <= year <= 2100) else now.year

        budgets = self.db.query(Budget).filter(
            Budget.user_id == self.user_id,
            Budget.month == target_month,
            Budget.year == target_year
        ).all()

        all_txs = self.db.query(Transaction).filter(
            Transaction.user_id == self.user_id,
            Transaction.type == TransactionType.EXPENSE
        ).all()

        predictions = IntelligenceService.calculate_budget_risk(
            transactions=all_txs,
            budgets=budgets,
            current_month=target_month,
            current_year=target_year
        )

        items = [
            {
                "category": p.category,
                "allocated": float(p.amount),
                "spent": float(p.spent),
                "remaining": float(p.remaining),
                "percentage_used": p.utilization,
                "velocity_per_day": float(p.spending_velocity),
                "projected_month_end": float(p.projected_spend),
                "status": "OVER_BUDGET" if p.spent > p.amount else ("NEAR_LIMIT" if p.utilization >= 80.0 else "ON_TRACK"),
                "risk_level": p.risk_level,
                "explanation": p.explanation
            }
            for p in predictions
        ]

        return {
            "month": target_month,
            "year": target_year,
            "budgets": items,
            "count": len(items)
        }

    def get_category_spending(
        self,
        month: Optional[int] = None,
        year: Optional[int] = None
    ) -> Dict[str, Any]:
        """Calculate categorized spending breakdown and top outflow drivers."""
        now = datetime.now()
        target_month = month if (month and 1 <= month <= 12) else now.month
        target_year = year if (year and 2000 <= year <= 2100) else now.year

        expense_txs = self.db.query(Transaction).filter(
            Transaction.user_id == self.user_id,
            Transaction.type == TransactionType.EXPENSE,
            extract("month", Transaction.transaction_date) == target_month,
            extract("year", Transaction.transaction_date) == target_year
        ).all()

        raw_categories = analyze_categories(expense_txs)
        categories = [
            {
                "category": c.category,
                "amount": float(c.amount),
                "percentage": float(c.percentage)
            }
            for c in raw_categories
        ]

        return {
            "month": target_month,
            "year": target_year,
            "categories": categories,
            "top_category": categories[0]["category"] if categories else None
        }

    def get_monthly_cashflow(self, months: int = 6) -> Dict[str, Any]:
        """Compile multi-month income and expense trends for user."""
        safe_months = max(1, min(months, 12))
        now = datetime.now()
        history = []

        for i in range(safe_months - 1, -1, -1):
            m = (now.month - i - 1) % 12 + 1
            y = now.year + (now.month - i - 1) // 12

            txs = self.db.query(Transaction).filter(
                Transaction.user_id == self.user_id,
                extract("month", Transaction.transaction_date) == m,
                extract("year", Transaction.transaction_date) == y
            ).all()

            income = sum((t.amount for t in txs if t.type == TransactionType.INCOME), Decimal("0.00"))
            expenses = sum((t.amount for t in txs if t.type == TransactionType.EXPENSE), Decimal("0.00"))
            savings = income - expenses

            history.append({
                "month": m,
                "year": y,
                "month_name": date(y, m, 1).strftime("%b %Y"),
                "income": float(income),
                "expenses": float(expenses),
                "savings": float(savings)
            })

        return {"cashflow_history": history}

    def get_spending_analysis(
        self,
        month: Optional[int] = None,
        year: Optional[int] = None
    ) -> Dict[str, Any]:
        """Perform deep spending behavior analysis including MoM deltas and anomalies."""
        now = datetime.now()
        target_month = month if (month and 1 <= month <= 12) else now.month
        target_year = year if (year and 2000 <= year <= 2100) else now.year

        txs = self.db.query(Transaction).filter(Transaction.user_id == self.user_id).all()
        budgets = self.db.query(Budget).filter(
            Budget.user_id == self.user_id,
            Budget.month == target_month,
            Budget.year == target_year
        ).all()

        behavior = IntelligenceService.analyze_category_behavior(
            transactions=txs,
            budgets=budgets,
            current_month=target_month,
            current_year=target_year
        )

        anomalies = IntelligenceService.detect_unusual_transactions(
            transactions=txs
        )

        return {
            "month": target_month,
            "year": target_year,
            "category_behavior": [
                {
                    "category": b.category,
                    "current_spending": float(b.current_month_spending),
                    "previous_spending": float(b.previous_month_spending),
                    "mom_growth_percentage": b.month_over_month_percentage_change,
                    "percentage_of_total": b.percentage_of_total_spending,
                    "risk_level": b.risk_level
                }
                for b in behavior
            ],
            "unusual_transactions": [
                {
                    "title": a.title,
                    "category": a.category,
                    "amount": float(a.amount),
                    "severity": a.severity,
                    "reason": a.reason
                }
                for a in anomalies
            ]
        }

    def get_savings_opportunities(self) -> Dict[str, Any]:
        """Identify actionable data-derived savings opportunities."""
        txs = self.db.query(Transaction).filter(Transaction.user_id == self.user_id).all()
        now = datetime.now()
        budgets = self.db.query(Budget).filter(
            Budget.user_id == self.user_id,
            Budget.month == now.month,
            Budget.year == now.year
        ).all()

        summary = self.get_transaction_summary(now.month, now.year)
        income_dec = Decimal(str(summary["total_income"]))

        findings = IntelligenceService.calculate_savings_opportunity(
            transactions=txs,
            income=income_dec,
            budgets=budgets
        )

        total_potential_monthly = sum((f.potential_monthly_saving for f in findings), Decimal("0.00"))
        total_potential_annual = total_potential_monthly * 12

        return {
            "opportunities": [
                {
                    "category": f.category,
                    "current_spending": float(f.current_spending),
                    "suggested_reduction_percentage": f.suggested_reduction_percentage,
                    "potential_monthly_saving": float(f.potential_monthly_saving),
                    "potential_annual_saving": float(f.potential_annual_saving),
                    "priority": f.priority,
                    "explanation": f.explanation
                }
                for f in findings
            ],
            "total_potential_monthly_saving": float(total_potential_monthly),
            "total_potential_annual_saving": float(total_potential_annual)
        }

    def get_financial_health(self) -> Dict[str, Any]:
        """Retrieve 5-factor health score with detailed factor breakdown."""
        now = datetime.now()
        summary = self.get_transaction_summary(now.month, now.year)

        prev_month = 12 if now.month == 1 else now.month - 1
        prev_year = now.year - 1 if now.month == 1 else now.year
        prev_summary = self.get_transaction_summary(prev_month, prev_year)

        budgets = self.db.query(Budget).filter(
            Budget.user_id == self.user_id,
            Budget.month == now.month,
            Budget.year == now.year
        ).all()

        total_budget = sum((b.amount for b in budgets), Decimal("0.00"))

        health_detail = IntelligenceService.calculate_health_score_detail(
            income=Decimal(str(summary["total_income"])),
            expenses=Decimal(str(summary["total_expenses"])),
            prev_expenses=Decimal(str(prev_summary["total_expenses"])),
            total_budget=total_budget
        )

        return {
            "score": health_detail.score,
            "status": health_detail.status,
            "factors": [
                {
                    "name": f.name,
                    "score": f.score,
                    "weight": f.weight,
                    "explanation": f.explanation,
                    "recommendation": f.recommendation
                }
                for f in health_detail.factors
            ]
        }

    def get_dashboard(
        self,
        month: Optional[int] = None,
        year: Optional[int] = None
    ) -> Dict[str, Any]:
        """Aggregate full dashboard data for authenticated user."""
        summary = self.get_transaction_summary(month, year)
        cat_data = self.get_category_spending(month, year)
        budget_prog = self.get_budget_progress(month, year)

        health = calculate_financial_health_score({
            "income": Decimal(str(summary["total_income"])),
            "expenses": Decimal(str(summary["total_expenses"])),
            "total_budget": Decimal(str(sum((b["allocated"] for b in budget_prog["budgets"]), 0.0)))
        })

        expense_txs = self.db.query(Transaction).filter(
            Transaction.user_id == self.user_id,
            Transaction.type == TransactionType.EXPENSE,
            extract("month", Transaction.transaction_date) == summary["month"],
            extract("year", Transaction.transaction_date) == summary["year"]
        ).all()

        insights = generate_smart_insights({
            "income": Decimal(str(summary["total_income"])),
            "expenses": Decimal(str(summary["total_expenses"])),
            "transactions": expense_txs,
            "budgets": []
        })

        insights_list = [
            {
                "title": i.tag,
                "description": i.text,
                "type": i.type
            }
            for i in insights
        ]

        return {
            "summary": summary,
            "category_breakdown": cat_data["categories"],
            "budgets": budget_prog["budgets"],
            "health_score": {
                "score": health.score,
                "status": health.status
            },
            "insights": insights_list
        }

    def get_proactive_insights(
        self,
        month: Optional[int] = None,
        year: Optional[int] = None
    ) -> Dict[str, Any]:
        """Retrieve prioritized proactive financial insights for current user."""
        engine = InsightEngine(user_id=self.user_id, db=self.db)
        insights = engine.generate_insights(month=month, year=year)
        return {
            "count": len(insights),
            "insights": insights
        }

    def get_spending_alerts(
        self,
        month: Optional[int] = None,
        year: Optional[int] = None
    ) -> Dict[str, Any]:
        """Retrieve high-priority spending alerts for current user."""
        engine = InsightEngine(user_id=self.user_id, db=self.db)
        all_insights = engine.generate_insights(month=month, year=year)
        alerts = [
            i for i in all_insights
            if i.get("type") in ["SPENDING_SPIKE", "BUDGET_OVERSPENT", "BUDGET_WARNING", "UNUSUAL_TRANSACTION"]
        ]
        return {
            "count": len(alerts),
            "alerts": alerts
        }

    def get_financial_changes(
        self,
        month: Optional[int] = None,
        year: Optional[int] = None
    ) -> Dict[str, Any]:
        """Retrieve period-over-period financial changes for current user."""
        engine = InsightEngine(user_id=self.user_id, db=self.db)
        all_insights = engine.generate_insights(month=month, year=year)
        changes = [
            i for i in all_insights
            if i.get("type") in ["FINANCIAL_HEALTH_CHANGE", "SAVINGS_DECLINE", "POSITIVE_PROGRESS", "SPENDING_SPIKE"]
        ]
        return {
            "count": len(changes),
            "changes": changes
        }

    def get_financial_goals(self) -> Dict[str, Any]:
        """Retrieve active financial goals for the authenticated user."""
        planning = PlanningEngine(self.user_id, self.db)
        coaching = planning.generate_coaching_context()
        monthly_pace = Decimal(str(coaching["cashflow"]["net_monthly_savings"]))

        progress_list = GoalService.get_all_goals_progress(self.db, self.user_id, monthly_pace=monthly_pace)
        return {
            "count": len(progress_list),
            "goals": progress_list
        }

    def get_goal_progress(self, goal_id: Optional[int] = None) -> Dict[str, Any]:
        """Retrieve progress metrics for a specific goal or all goals."""
        planning = PlanningEngine(self.user_id, self.db)
        coaching = planning.generate_coaching_context()
        monthly_pace = Decimal(str(coaching["cashflow"]["net_monthly_savings"]))

        if goal_id is not None:
            prog = GoalService.get_goal_progress(self.db, self.user_id, goal_id, monthly_pace=monthly_pace)
            if not prog:
                return {"error": f"Goal ID {goal_id} not found."}
            return {"goal_progress": prog}
        else:
            all_prog = GoalService.get_all_goals_progress(self.db, self.user_id, monthly_pace=monthly_pace)
            return {
                "count": len(all_prog),
                "goals": all_prog
            }

    def calculate_goal_plan(self, goal_id: int) -> Dict[str, Any]:
        """Calculate required monthly/weekly contributions and timeline projection."""
        goal = GoalService.get_goal(self.db, self.user_id, goal_id)
        if not goal:
            return {"error": f"Goal ID {goal_id} not found."}

        planning = PlanningEngine(self.user_id, self.db)
        coaching = planning.generate_coaching_context()
        monthly_pace = Decimal(str(coaching["cashflow"]["net_monthly_savings"]))

        return GoalProjectionEngine.project_goal_timeline(goal, monthly_savings_pace=monthly_pace)

    def calculate_affordability(
        self,
        required_monthly_amount: Optional[float] = None,
        goal_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Evaluate whether a goal or monthly contribution is affordable."""
        planning = PlanningEngine(self.user_id, self.db)
        coaching = planning.generate_coaching_context()
        income = Decimal(str(coaching["cashflow"]["monthly_income"]))
        expenses = Decimal(str(coaching["cashflow"]["monthly_expenses"]))
        discretionary = Decimal(str(coaching["cashflow"]["discretionary_expenses"]))

        req_amount = Decimal(str(required_monthly_amount)) if required_monthly_amount is not None else Decimal("0.00")
        goal_name = None

        if goal_id is not None:
            goal = GoalService.get_goal(self.db, self.user_id, goal_id)
            if goal:
                goal_name = goal.name
                prog = GoalCalculator.calculate_progress(goal)
                if required_monthly_amount is None:
                    req_amount = Decimal(str(prog["required_monthly_contribution"]))

        return AffordabilityEngine.evaluate_affordability(
            required_monthly_amount=req_amount,
            monthly_income=income,
            monthly_expenses=expenses,
            discretionary_expenses=discretionary,
            goal_name=goal_name
        )

    def run_financial_scenario(
        self,
        scenario_type: str,
        goal_id: Optional[int] = None,
        amount: Optional[float] = None,
        percentage: Optional[float] = None,
        category: Optional[str] = None,
        months_delta: Optional[int] = None
    ) -> Dict[str, Any]:
        """Run deterministic 'What-If' simulation for current user."""
        goal = GoalService.get_goal(self.db, self.user_id, goal_id) if goal_id else None

        planning = PlanningEngine(self.user_id, self.db)
        coaching = planning.generate_coaching_context()
        income = Decimal(str(coaching["cashflow"]["monthly_income"]))
        expenses = Decimal(str(coaching["cashflow"]["monthly_expenses"]))

        # Build category spending map
        txs = self.db.query(Transaction).filter(
            Transaction.user_id == self.user_id,
            Transaction.type == TransactionType.EXPENSE
        ).all()
        cat_spending = {}
        for t in txs:
            cat_spending[t.category] = cat_spending.get(t.category, Decimal("0.00")) + t.amount

        params = {
            "monthly_savings_delta": amount,
            "reduction_amount": amount,
            "reduction_percentage": percentage,
            "increase_amount": amount,
            "increase_percentage": percentage,
            "category": category,
            "months_delta": months_delta,
            "monthly_contribution": amount
        }

        try:
            return ScenarioEngine.run_scenario(
                scenario_type=scenario_type,
                goal=goal,
                baseline_income=income,
                baseline_expenses=expenses,
                category_spending=cat_spending,
                params=params
            )
        except ValueError as e:
            return {"error": str(e)}

    def get_coaching_context(
        self,
        month: Optional[int] = None,
        year: Optional[int] = None
    ) -> Dict[str, Any]:
        """Retrieve complete personalized coaching context for current user."""
        planning = PlanningEngine(self.user_id, self.db)
        return planning.generate_coaching_context(month=month, year=year)

    def get_financial_forecast(self) -> Dict[str, Any]:
        """Retrieve full next-month cashflow, category, budget burn, and goal completion forecast."""
        engine = ForecastingEngine(self.user_id, self.db)
        return engine.get_full_forecast()

    def get_cashflow_forecast(self) -> Dict[str, Any]:
        """Retrieve cashflow forecast outlook, trend rates, and 6-month projected balance trajectory."""
        engine = ForecastingEngine(self.user_id, self.db)
        return engine.get_full_forecast()

    def get_expense_forecast(self) -> Dict[str, Any]:
        """Retrieve projected next-month total expenses with category-level breakdowns."""
        engine = ForecastingEngine(self.user_id, self.db)
        return engine.get_expense_forecast()

    def get_income_forecast(self) -> Dict[str, Any]:
        """Retrieve verified next-month projected income and trend confidence."""
        engine = ForecastingEngine(self.user_id, self.db)
        return engine.get_income_forecast()

    def get_savings_forecast(self) -> Dict[str, Any]:
        """Retrieve projected next-month net savings, projected savings rate percentage, and 6-month trajectory."""
        engine = ForecastingEngine(self.user_id, self.db)
        return engine.get_savings_forecast()

    def get_financial_risks(self) -> Dict[str, Any]:
        """Evaluate 10 deterministic financial risk rules and return prioritized risk report."""
        engine = RiskEngine(self.user_id, self.db)
        return engine.evaluate_risks()

    def get_predictive_insights(self) -> Dict[str, Any]:
        """Retrieve top prioritized predictive insights combining forecasts, risks, and suggestions."""
        engine = PredictiveEngine(self.user_id, self.db)
        insights = engine.generate_predictions()
        return {
            "insights": insights,
            "total_insights": len(insights)
        }

    def get_forecast_explanation(self, forecast_type: Optional[str] = "all") -> Dict[str, Any]:
        """Retrieve mathematical explanations, methodologies, and limitations for projections."""
        engine = ForecastingEngine(self.user_id, self.db)
        fc = engine.get_full_forecast()
        inc = fc.get("income_forecast", {})
        exp = fc.get("expense_forecast", {})
        sav = fc.get("savings_forecast", {})

        return {
            "methodology": "Linearly weighted moving average with recurring monthly frequency analysis.",
            "income_model": {
                "methodology": inc.get("methodology"),
                "confidence": inc.get("confidence"),
                "limitations": inc.get("limitations"),
                "evidence": inc.get("evidence", [])
            },
            "expense_model": {
                "methodology": exp.get("methodology"),
                "confidence": exp.get("confidence"),
                "limitations": exp.get("limitations"),
                "evidence": exp.get("evidence", [])
            },
            "savings_model": {
                "methodology": sav.get("methodology"),
                "confidence": sav.get("confidence"),
                "limitations": sav.get("limitations"),
                "evidence": sav.get("evidence", [])
            }
        }

    def get_smart_actions(self, refresh: Optional[bool] = False) -> Dict[str, Any]:
        """Retrieve active smart financial action recommendations."""
        engine = SmartActionEngine(self.user_id, self.db)
        proposals = engine.get_or_generate_actions(refresh=bool(refresh))
        return {
            "actions": [
                {
                    "action_id": p.action_id,
                    "action_type": p.action_type,
                    "title": p.title,
                    "description": p.description,
                    "verified_evidence": p.verified_evidence,
                    "financial_amount": float(p.financial_amount),
                    "expected_impact": p.expected_impact,
                    "risk_level": p.risk_level,
                    "requires_confirmation": p.requires_confirmation,
                    "status": p.status,
                    "expires_at": str(p.expires_at)
                }
                for p in proposals
            ],
            "total_actions": len(proposals)
        }

    def get_action_details(self, action_id: str) -> Dict[str, Any]:
        """Retrieve details of a specific smart action proposal."""
        engine = SmartActionEngine(self.user_id, self.db)
        p = engine.get_action(action_id)
        return {
            "action_id": p.action_id,
            "action_type": p.action_type,
            "title": p.title,
            "description": p.description,
            "verified_evidence": p.verified_evidence,
            "financial_amount": float(p.financial_amount),
            "expected_impact": p.expected_impact,
            "risk_level": p.risk_level,
            "requires_confirmation": p.requires_confirmation,
            "status": p.status,
            "created_at": str(p.created_at),
            "expires_at": str(p.expires_at),
            "confirmed_at": str(p.confirmed_at) if p.confirmed_at else None,
            "executed_at": str(p.executed_at) if p.executed_at else None,
            "rejected_at": str(p.rejected_at) if p.rejected_at else None
        }

    def propose_financial_action(
        self,
        action_type: str,
        title: str,
        description: str,
        financial_amount: Optional[float] = 0.0
    ) -> Dict[str, Any]:
        """Propose a new smart financial action (status PROPOSED, requires confirmation before execution)."""
        import uuid
        from datetime import datetime, timezone, timedelta
        from app.models.smart_action import SmartActionProposal, ActionStatusEnum
        from app.services.ai.automation.action_rules import ActionRules

        now_utc = datetime.now(timezone.utc)
        payload = {
            "action": "user_or_ai_custom_action",
            "action_type": action_type,
            "title": title,
            "description": description,
            "financial_amount": float(financial_amount or 0.0)
        }
        payload_hash = ActionRules.compute_payload_hash(payload)

        prop = SmartActionProposal(
            action_id=f"act-{uuid.uuid4().hex[:12]}",
            user_id=self.user_id,
            action_type=action_type,
            title=title,
            description=description,
            verified_evidence=f"Proposed by user/assistant analysis with parameter amount ₹{float(financial_amount or 0.0):,.2f}.",
            financial_amount=Decimal(str(financial_amount or 0.0)),
            expected_impact="Awaiting user confirmation before applying server-side modifications.",
            risk_level="MEDIUM",
            requires_confirmation=True,
            status=ActionStatusEnum.PROPOSED.value,
            action_payload=json.dumps(payload),
            payload_hash=payload_hash,
            expires_at=now_utc + timedelta(hours=24)
        )
        self.db.add(prop)
        self.db.commit()
        self.db.refresh(prop)

        return {
            "action_id": prop.action_id,
            "action_type": prop.action_type,
            "title": prop.title,
            "status": prop.status,
            "requires_confirmation": True,
            "message": "Action proposal created with status PROPOSED. Must be confirmed by user before execution."
        }

    def confirm_financial_action(self, action_id: str, note: Optional[str] = "") -> Dict[str, Any]:
        """Confirm an action proposal."""
        engine = SmartActionEngine(self.user_id, self.db)
        p = engine.confirm_action(action_id, note=note or "")
        return {
            "action_id": p.action_id,
            "action_type": p.action_type,
            "status": p.status,
            "confirmed_at": str(p.confirmed_at),
            "message": "Action confirmed successfully. Ready for execution."
        }

    def execute_financial_action(self, action_id: str, note: Optional[str] = "") -> Dict[str, Any]:
        """Execute a confirmed smart action safely."""
        engine = SmartActionEngine(self.user_id, self.db)
        return engine.execute_action(action_id, note=note or "")

    def reject_financial_action(self, action_id: str, reason: Optional[str] = "") -> Dict[str, Any]:
        """Reject an action proposal."""
        engine = SmartActionEngine(self.user_id, self.db)
        p = engine.reject_action(action_id, reason=reason or "")
        return {
            "action_id": p.action_id,
            "action_type": p.action_type,
            "status": p.status,
            "rejected_at": str(p.rejected_at),
            "message": "Action proposal rejected and logged in audit history."
        }

    def get_action_history(self) -> Dict[str, Any]:
        """Retrieve audit history for user actions."""
        engine = SmartActionEngine(self.user_id, self.db)
        audits = engine.get_action_history()
        return {
            "history": [
                {
                    "id": a.id,
                    "action_id": a.action_id,
                    "action_type": a.action_type,
                    "timestamp": str(a.timestamp),
                    "execution_status": a.execution_status,
                    "financial_amount": float(a.financial_amount),
                    "reason": a.reason,
                    "validation_result": a.validation_result
                }
                for a in audits
            ],
            "total_records": len(audits)
        }

    # ----------------------------------------------------------------------
    # PHASE 3.9 TOOL HANDLERS
    # ----------------------------------------------------------------------

    def get_financial_health_score(self) -> Dict[str, Any]:
        """Evaluate 7-factor financial health score (0-100)."""
        engine = HealthScoreEngine(self.user_id, self.db)
        return engine.evaluate_health()

    def get_financial_intelligence(self) -> Dict[str, Any]:
        """Retrieve unified master financial intelligence payload."""
        engine = UnifiedIntelligenceEngine(self.user_id, self.db)
        raw = engine.get_unified_intelligence()
        # Convert objects to serializable dicts
        return {
            "health_score": raw["health_score"],
            "forecast": raw["forecast"],
            "risks": raw["risks"],
            "goals": raw["goals"],
            "smart_actions": [a.action_id for a in raw.get("smart_actions", [])] if hasattr(raw.get("smart_actions", [None])[0], "action_id") else raw.get("smart_actions", []),
            "explanations": raw["explanations"],
            "as_of_date": raw["as_of_date"]
        }

    def explain_financial_forecast(self) -> Dict[str, Any]:
        """Explain mathematical methodology behind next-month forecasts."""
        engine = ExplanationEngine(self.user_id, self.db)
        return engine.get_explanation_by_type("WHY_THIS_FORECAST")

    def explain_financial_risk(self) -> Dict[str, Any]:
        """Explain reasons behind active risk flags."""
        engine = ExplanationEngine(self.user_id, self.db)
        return engine.get_explanation_by_type("WHY_THIS_RISK")

    def explain_goal_status(self, goal_id: Optional[int] = None) -> Dict[str, Any]:
        """Explain goal progress velocity and timeline."""
        engine = ExplanationEngine(self.user_id, self.db)
        return engine.get_explanation_by_type("WHY_THIS_GOAL_STATUS")

    def explain_smart_action(self, action_id: Optional[str] = None) -> Dict[str, Any]:
        """Explain reasons and expected impact for a Smart Action."""
        engine = ExplanationEngine(self.user_id, self.db)
        return engine.get_explanation_by_type("WHY_THIS_SMART_ACTION")

    def run_financial_simulation(
        self,
        scenario: str,
        amount: Optional[float] = None,
        percentage: Optional[float] = None,
        months: Optional[int] = None,
        goal_id: Optional[int] = None,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute hypothetical what-if simulation (zero DB writes)."""
        engine = SimulationEngine(self.user_id, self.db)
        return engine.simulate(
            scenario=scenario,
            amount=amount,
            percentage=percentage,
            months=months,
            goal_id=goal_id,
            category=category
        )

    def explain_health_score(self) -> Dict[str, Any]:
        """Explain the exact breakdown and component scoring for Financial Health."""
        engine = ExplanationEngine(self.user_id, self.db)
        return engine.get_explanation_by_type("WHY_THIS_HEALTH_SCORE")




