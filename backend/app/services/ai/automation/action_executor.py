"""Action Executor: Safe server-side execution of confirmed smart financial actions."""

import json
from datetime import datetime, timezone, date
from decimal import Decimal
from typing import Dict, Any
from sqlalchemy.orm import Session

from app.models.budget import Budget
from app.models.goal import Goal
from app.models.smart_action import SmartActionProposal, ActionAudit, ActionStatusEnum
from app.services.ai.automation.action_validator import ActionValidator


class ActionExecutor:
    """Safely executes confirmed smart actions and logs immutable audit records."""

    @classmethod
    def execute_action(
        cls,
        db: Session,
        proposal: SmartActionProposal,
        authenticated_user_id: int,
        execution_note: str = ""
    ) -> Dict[str, Any]:
        """
        Execute confirmed action, update database state, write audit log, and return results.
        """
        # 1. Run all strict validation checks
        payload = ActionValidator.validate_for_execution(proposal, authenticated_user_id)

        now_utc = datetime.now(timezone.utc)
        action_name = payload.get("action", "")
        previous_state: Dict[str, Any] = {}
        resulting_state: Dict[str, Any] = {}

        try:
            # 2. Execute concrete business operation
            if action_name == "adjust_budget":
                cat = payload.get("category", "")
                new_amt = Decimal(str(payload.get("new_budget_amount", "0.00")))
                m = payload.get("month", now_utc.month)
                y = payload.get("year", now_utc.year)

                existing_b = (
                    db.query(Budget)
                    .filter(
                        Budget.user_id == authenticated_user_id,
                        Budget.category == cat,
                        Budget.month == m,
                        Budget.year == y
                    )
                    .first()
                )

                if existing_b:
                    previous_state = {
                        "budget_id": existing_b.id,
                        "category": existing_b.category,
                        "amount": float(existing_b.amount),
                        "month": existing_b.month,
                        "year": existing_b.year
                    }
                    existing_b.amount = new_amt
                    db.flush()
                    resulting_state = {
                        "budget_id": existing_b.id,
                        "category": existing_b.category,
                        "amount": float(existing_b.amount),
                        "month": existing_b.month,
                        "year": existing_b.year,
                        "status": "UPDATED"
                    }
                else:
                    new_b = Budget(
                        user_id=authenticated_user_id,
                        category=cat,
                        amount=new_amt,
                        month=m,
                        year=y
                    )
                    db.add(new_b)
                    db.flush()
                    previous_state = {"status": "NONE"}
                    resulting_state = {
                        "budget_id": new_b.id,
                        "category": new_b.category,
                        "amount": float(new_b.amount),
                        "month": new_b.month,
                        "year": new_b.year,
                        "status": "CREATED"
                    }

            elif action_name == "adjust_goal_contribution":
                goal_id = payload.get("goal_id")
                goal = db.query(Goal).filter(Goal.id == goal_id, Goal.user_id == authenticated_user_id).first()
                if goal:
                    previous_state = {
                        "goal_id": goal.id,
                        "name": goal.name,
                        "target_amount": float(goal.target_amount),
                        "current_amount": float(goal.current_amount),
                        "target_date": str(goal.target_date)
                    }
                    # Resulting state reflects the confirmed monthly contribution plan
                    resulting_state = {
                        "goal_id": goal.id,
                        "name": goal.name,
                        "confirmed_monthly_contribution": float(payload.get("required_monthly_contribution", 0.0)),
                        "target_amount": float(goal.target_amount),
                        "target_date": str(goal.target_date),
                        "status": "CONTRIBUTION_SCHEDULE_CONFIRMED"
                    }
                else:
                    previous_state = {"error": "Goal not found"}
                    resulting_state = {"status": "SKIPPED"}

            elif action_name == "create_emergency_fund_goal":
                from datetime import datetime as dt
                t_date = dt.strptime(payload.get("target_date"), "%Y-%m-%d").date() if isinstance(payload.get("target_date"), str) else payload.get("target_date")
                new_goal = Goal(
                    user_id=authenticated_user_id,
                    name=payload.get("name", "Emergency Fund"),
                    target_amount=Decimal(str(payload.get("target_amount", "100000.00"))),
                    current_amount=Decimal(str(payload.get("initial_amount", "0.00"))),
                    target_date=t_date,
                    category=payload.get("category", "emergency_fund"),
                    priority=payload.get("priority", "critical")
                )
                db.add(new_goal)
                db.flush()
                previous_state = {"emergency_fund_goal": "NONE"}
                resulting_state = {
                    "goal_id": new_goal.id,
                    "name": new_goal.name,
                    "target_amount": float(new_goal.target_amount),
                    "current_amount": float(new_goal.current_amount),
                    "target_date": str(new_goal.target_date),
                    "status": "GOAL_CREATED"
                }

            elif action_name in ["boost_monthly_savings", "reduce_category_expense", "mitigate_risk"]:
                previous_state = {"action_type": proposal.action_type, "status": "PENDING"}
                resulting_state = {
                    "action_type": proposal.action_type,
                    "status": "EXECUTED",
                    "parameters": payload,
                    "execution_timestamp": str(now_utc)
                }

            else:
                previous_state = {"status": "UNKNOWN_ACTION"}
                resulting_state = {"status": "GENERIC_EXECUTION", "action": action_name}

            # 3. Mark proposal executed
            proposal.status = ActionStatusEnum.EXECUTED.value
            proposal.executed_at = now_utc

            # 4. Create immutable audit record
            audit = ActionAudit(
                action_id=proposal.action_id,
                user_id=authenticated_user_id,
                action_type=proposal.action_type,
                timestamp=now_utc,
                previous_state=json.dumps(previous_state, default=str),
                resulting_state=json.dumps(resulting_state, default=str),
                execution_status="SUCCESS",
                financial_amount=proposal.financial_amount,
                reason=execution_note or proposal.title,
                validation_result="ALL_PRECONDITIONS_VERIFIED"
            )
            db.add(audit)
            db.commit()

            return {
                "action_id": proposal.action_id,
                "action_type": proposal.action_type,
                "status": ActionStatusEnum.EXECUTED.value,
                "executed_at": now_utc,
                "previous_state": previous_state,
                "resulting_state": resulting_state,
                "audit_logged": True
            }

        except Exception as exc:
            db.rollback()
            # Record failed audit attempt
            failed_audit = ActionAudit(
                action_id=proposal.action_id,
                user_id=authenticated_user_id,
                action_type=proposal.action_type,
                timestamp=now_utc,
                previous_state=json.dumps(previous_state, default=str),
                resulting_state=json.dumps({"error": str(exc)}, default=str),
                execution_status="FAILED",
                financial_amount=proposal.financial_amount,
                reason=f"Execution error: {str(exc)}",
                validation_result="EXECUTION_FAILED"
            )
            db.add(failed_audit)
            db.commit()
            raise RuntimeError(f"Server-side action execution failed: {str(exc)}")
