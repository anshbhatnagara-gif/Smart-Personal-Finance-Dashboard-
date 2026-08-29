"""Action Validator: Strict server-side validation against tampering, stale state, and unauthorized execution."""

import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from fastapi import HTTPException, status

from app.models.smart_action import SmartActionProposal, ActionStatusEnum
from app.services.ai.automation.action_rules import ActionRules


class ActionValidator:
    """Enforces strict security, identity ownership, and lifecycle state constraints."""

    @staticmethod
    def validate_ownership(proposal: SmartActionProposal, authenticated_user_id: int) -> None:
        """Ensure the proposal belongs strictly to the authenticated user."""
        if proposal.user_id != authenticated_user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Action proposal not found."
            )

    @staticmethod
    def validate_not_expired(proposal: SmartActionProposal, current_time: Optional[datetime] = None) -> None:
        """Ensure proposal has not exceeded its validity TTL."""
        if proposal.is_expired(current_time):
            proposal.status = ActionStatusEnum.EXPIRED.value
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This action proposal has expired and can no longer be confirmed or executed."
            )

    @classmethod
    def validate_payload_integrity(cls, proposal: SmartActionProposal) -> Dict[str, Any]:
        """Verify action payload has not been tampered with and matches its SHA-256 digest."""
        try:
            payload = json.loads(proposal.action_payload)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Action payload is corrupted."
            )

        calculated_hash = ActionRules.compute_payload_hash(payload)
        if calculated_hash != proposal.payload_hash:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Action payload integrity violation: parameter tampering detected."
            )

        return payload

    @classmethod
    def validate_for_confirmation(cls, proposal: SmartActionProposal, authenticated_user_id: int) -> Dict[str, Any]:
        """Validate all preconditions before confirming an action proposal."""
        cls.validate_ownership(proposal, authenticated_user_id)
        cls.validate_not_expired(proposal)

        if proposal.status == ActionStatusEnum.CONFIRMED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Action is already confirmed."
            )
        if proposal.status == ActionStatusEnum.EXECUTED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Action has already been executed."
            )
        if proposal.status == ActionStatusEnum.REJECTED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Action has been rejected and cannot be confirmed."
            )
        if proposal.status != ActionStatusEnum.PROPOSED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid action status for confirmation: {proposal.status}."
            )

        return cls.validate_payload_integrity(proposal)

    @classmethod
    def validate_for_execution(cls, proposal: SmartActionProposal, authenticated_user_id: int) -> Dict[str, Any]:
        """Validate all preconditions before server-side execution."""
        cls.validate_ownership(proposal, authenticated_user_id)
        cls.validate_not_expired(proposal)

        if proposal.status == ActionStatusEnum.EXECUTED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Action has already been executed (replay prevented)."
            )
        if proposal.status == ActionStatusEnum.REJECTED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Action was rejected and cannot be executed."
            )
        if proposal.status != ActionStatusEnum.CONFIRMED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Action must be explicitly confirmed by the user before execution."
            )

        return cls.validate_payload_integrity(proposal)

    @classmethod
    def validate_for_rejection(cls, proposal: SmartActionProposal, authenticated_user_id: int) -> None:
        """Validate preconditions before rejecting an action proposal."""
        cls.validate_ownership(proposal, authenticated_user_id)

        if proposal.status == ActionStatusEnum.EXECUTED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Executed actions cannot be rejected."
            )
        if proposal.status == ActionStatusEnum.REJECTED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Action is already rejected."
            )
