"""Action Engine: Master coordinator for smart action discovery, lifecycle management, and audit queries."""

import json
from datetime import date, datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.smart_action import SmartActionProposal, ActionAudit, ActionStatusEnum
from app.services.ai.automation.action_rules import ActionRules
from app.services.ai.automation.action_validator import ActionValidator
from app.services.ai.automation.action_executor import ActionExecutor
from app.services.ai.automation.action_formatter import ActionFormatter


class SmartActionEngine:
    """Master orchestrator for user-scoped smart financial actions."""

    def __init__(self, user_id: int, db: Session):
        self.user_id = user_id
        self.db = db

    def get_or_generate_actions(self, today: Optional[date] = None, refresh: bool = False) -> List[SmartActionProposal]:
        """
        Retrieve active proposals for the user. If none exist or refresh requested,
        generate new proposals deterministically from verified data.
        """
        now_utc = datetime.now(timezone.utc)

        # 1. Query existing active (PROPOSED or CONFIRMED) proposals
        existing = (
            self.db.query(SmartActionProposal)
            .filter(
                SmartActionProposal.user_id == self.user_id,
                SmartActionProposal.status.in_([ActionStatusEnum.PROPOSED.value, ActionStatusEnum.CONFIRMED.value])
            )
            .order_by(SmartActionProposal.created_at.desc())
            .all()
        )

        # Filter out expired
        active = []
        for prop in existing:
            if prop.is_expired(now_utc):
                prop.status = ActionStatusEnum.EXPIRED.value
            else:
                active.append(prop)

        if existing:
            self.db.commit()

        if active and not refresh:
            return active

        # 2. Generate candidates from rules
        candidates = ActionRules.generate_candidate_actions(self.user_id, self.db, today=today)
        new_proposals = []

        for c in candidates:
            # Check if identical action type is already pending
            already_pending = any(a.action_type == c["action_type"] and a.title == c["title"] for a in active)
            if not already_pending:
                proposal = SmartActionProposal(
                    action_id=c["action_id"],
                    user_id=self.user_id,
                    action_type=c["action_type"],
                    title=c["title"],
                    description=c["description"],
                    verified_evidence=c["verified_evidence"],
                    financial_amount=c["financial_amount"],
                    expected_impact=c["expected_impact"],
                    risk_level=c["risk_level"],
                    requires_confirmation=c["requires_confirmation"],
                    status=c["status"],
                    action_payload=c["action_payload"],
                    payload_hash=c["payload_hash"],
                    expires_at=c["expires_at"]
                )
                self.db.add(proposal)
                new_proposals.append(proposal)

        if new_proposals:
            self.db.commit()
            for p in new_proposals:
                self.db.refresh(p)

        return active + new_proposals

    def get_action(self, action_id: str) -> SmartActionProposal:
        """Fetch single action proposal strictly validating user ownership."""
        proposal = (
            self.db.query(SmartActionProposal)
            .filter(SmartActionProposal.action_id == action_id)
            .first()
        )
        if not proposal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Smart action '{action_id}' was not found."
            )

        ActionValidator.validate_ownership(proposal, self.user_id)
        return proposal

    def confirm_action(self, action_id: str, note: str = "") -> SmartActionProposal:
        """Confirm a proposed action before execution."""
        proposal = self.get_action(action_id)
        ActionValidator.validate_for_confirmation(proposal, self.user_id)

        now_utc = datetime.now(timezone.utc)
        proposal.status = ActionStatusEnum.CONFIRMED.value
        proposal.confirmed_at = now_utc

        # Record confirmation audit event
        audit = ActionAudit(
            action_id=proposal.action_id,
            user_id=self.user_id,
            action_type=proposal.action_type,
            timestamp=now_utc,
            previous_state=json.dumps({"status": ActionStatusEnum.PROPOSED.value}),
            resulting_state=json.dumps({"status": ActionStatusEnum.CONFIRMED.value, "note": note}),
            execution_status="CONFIRMED",
            financial_amount=proposal.financial_amount,
            reason=note or f"User confirmed {proposal.title}",
            validation_result="CONFIRMATION_VALIDATED"
        )
        self.db.add(audit)
        self.db.commit()
        self.db.refresh(proposal)
        return proposal

    def execute_action(self, action_id: str, note: str = "") -> Dict[str, Any]:
        """Execute a confirmed smart action safely."""
        proposal = self.get_action(action_id)
        return ActionExecutor.execute_action(self.db, proposal, self.user_id, execution_note=note)

    def reject_action(self, action_id: str, reason: str = "") -> SmartActionProposal:
        """Reject an action proposal."""
        proposal = self.get_action(action_id)
        ActionValidator.validate_for_rejection(proposal, self.user_id)

        now_utc = datetime.now(timezone.utc)
        prev_status = proposal.status
        proposal.status = ActionStatusEnum.REJECTED.value
        proposal.rejected_at = now_utc

        audit = ActionAudit(
            action_id=proposal.action_id,
            user_id=self.user_id,
            action_type=proposal.action_type,
            timestamp=now_utc,
            previous_state=json.dumps({"status": prev_status}),
            resulting_state=json.dumps({"status": ActionStatusEnum.REJECTED.value, "reason": reason}),
            execution_status="REJECTED",
            financial_amount=proposal.financial_amount,
            reason=reason or f"User rejected {proposal.title}",
            validation_result="REJECTION_LOGGED"
        )
        self.db.add(audit)
        self.db.commit()
        self.db.refresh(proposal)
        return proposal

    def get_action_history(self) -> List[ActionAudit]:
        """Retrieve audit history for all user actions."""
        return (
            self.db.query(ActionAudit)
            .filter(ActionAudit.user_id == self.user_id)
            .order_by(ActionAudit.timestamp.desc())
            .all()
        )

    def get_formatted_xml(self, today: Optional[date] = None) -> str:
        """Format user's smart actions into prompt-ready XML context."""
        actions = self.get_or_generate_actions(today=today)
        return ActionFormatter.format_actions_xml(actions)
