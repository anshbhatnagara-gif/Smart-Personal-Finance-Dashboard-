"""FastAPI Router: Protected endpoints for AI Smart Financial Actions & Audit Trail."""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.common import ResponseBase
from app.schemas.ai_actions import (
    SmartActionItem,
    SmartActionResponse,
    SmartActionListResponse,
    ActionConfirmationRequest,
    ActionExecutionResponse,
    ActionRejectionRequest,
    ActionAuditItem,
    ActionHistoryResponse
)
from app.services.ai.automation.action_engine import SmartActionEngine

router = APIRouter(prefix="/ai/actions", tags=["AI Smart Actions"])


@router.get("", response_model=ResponseBase[SmartActionListResponse])
def get_smart_actions(
    refresh: bool = Query(default=False, description="Force re-generation of action proposals"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve verified, active smart action proposals for authenticated user."""
    engine = SmartActionEngine(current_user.id, db)
    proposals = engine.get_or_generate_actions(refresh=refresh)

    items = [
        SmartActionItem(
            action_id=p.action_id,
            action_type=p.action_type,
            title=p.title,
            description=p.description,
            verified_evidence=p.verified_evidence,
            financial_amount=float(p.financial_amount),
            expected_impact=p.expected_impact,
            risk_level=p.risk_level,
            requires_confirmation=p.requires_confirmation,
            status=p.status,
            created_at=p.created_at,
            expires_at=p.expires_at,
            confirmed_at=p.confirmed_at,
            executed_at=p.executed_at,
            rejected_at=p.rejected_at
        )
        for p in proposals
    ]

    return ResponseBase(
        success=True,
        message="Active smart financial actions retrieved successfully.",
        data=SmartActionListResponse(actions=items, total_actions=len(items))
    )


@router.get("/history", response_model=ResponseBase[ActionHistoryResponse])
def get_action_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve immutable audit event trail for authenticated user's smart actions."""
    engine = SmartActionEngine(current_user.id, db)
    audits = engine.get_action_history()

    items = [
        ActionAuditItem(
            id=a.id,
            action_id=a.action_id,
            action_type=a.action_type,
            timestamp=a.timestamp,
            previous_state=a.previous_state,
            resulting_state=a.resulting_state,
            execution_status=a.execution_status,
            financial_amount=float(a.financial_amount),
            reason=a.reason,
            validation_result=a.validation_result
        )
        for a in audits
    ]

    return ResponseBase(
        success=True,
        message="Action audit history retrieved successfully.",
        data=ActionHistoryResponse(items=items, total_records=len(items))
    )


@router.get("/{action_id}", response_model=ResponseBase[SmartActionResponse])
def get_action_details(
    action_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve single smart action proposal by action_id with strict ownership checks."""
    engine = SmartActionEngine(current_user.id, db)
    p = engine.get_action(action_id)

    item = SmartActionItem(
        action_id=p.action_id,
        action_type=p.action_type,
        title=p.title,
        description=p.description,
        verified_evidence=p.verified_evidence,
        financial_amount=float(p.financial_amount),
        expected_impact=p.expected_impact,
        risk_level=p.risk_level,
        requires_confirmation=p.requires_confirmation,
        status=p.status,
        created_at=p.created_at,
        expires_at=p.expires_at,
        confirmed_at=p.confirmed_at,
        executed_at=p.executed_at,
        rejected_at=p.rejected_at
    )

    return ResponseBase(
        success=True,
        message="Action details retrieved successfully.",
        data=SmartActionResponse(action=item)
    )


@router.post("/{action_id}/confirm", response_model=ResponseBase[SmartActionResponse])
def confirm_action(
    action_id: str,
    payload: Optional[ActionConfirmationRequest] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Explicitly confirm an action proposal prior to server-side execution."""
    note = (payload.note or "").strip() if payload else ""
    engine = SmartActionEngine(current_user.id, db)
    p = engine.confirm_action(action_id, note=note)

    item = SmartActionItem(
        action_id=p.action_id,
        action_type=p.action_type,
        title=p.title,
        description=p.description,
        verified_evidence=p.verified_evidence,
        financial_amount=float(p.financial_amount),
        expected_impact=p.expected_impact,
        risk_level=p.risk_level,
        requires_confirmation=p.requires_confirmation,
        status=p.status,
        created_at=p.created_at,
        expires_at=p.expires_at,
        confirmed_at=p.confirmed_at,
        executed_at=p.executed_at,
        rejected_at=p.rejected_at
    )

    return ResponseBase(
        success=True,
        message="Smart action confirmed successfully. Ready for execution.",
        data=SmartActionResponse(action=item)
    )


@router.post("/{action_id}/execute", response_model=ResponseBase[ActionExecutionResponse])
def execute_action(
    action_id: str,
    payload: Optional[ActionConfirmationRequest] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Safely execute a confirmed smart action and record audit log."""
    note = (payload.note or "").strip() if payload else ""
    engine = SmartActionEngine(current_user.id, db)
    res = engine.execute_action(action_id, note=note)

    return ResponseBase(
        success=True,
        message="Smart action executed successfully and recorded in audit log.",
        data=ActionExecutionResponse(
            action_id=res["action_id"],
            action_type=res["action_type"],
            status=res["status"],
            executed_at=res["executed_at"],
            previous_state=res["previous_state"],
            resulting_state=res["resulting_state"],
            audit_logged=res["audit_logged"]
        )
    )


@router.post("/{action_id}/reject", response_model=ResponseBase[SmartActionResponse])
def reject_action(
    action_id: str,
    payload: Optional[ActionRejectionRequest] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reject an action proposal and log rejection in audit trail."""
    reason = (payload.reason or "").strip() if payload else ""
    engine = SmartActionEngine(current_user.id, db)
    p = engine.reject_action(action_id, reason=reason)

    item = SmartActionItem(
        action_id=p.action_id,
        action_type=p.action_type,
        title=p.title,
        description=p.description,
        verified_evidence=p.verified_evidence,
        financial_amount=float(p.financial_amount),
        expected_impact=p.expected_impact,
        risk_level=p.risk_level,
        requires_confirmation=p.requires_confirmation,
        status=p.status,
        created_at=p.created_at,
        expires_at=p.expires_at,
        confirmed_at=p.confirmed_at,
        executed_at=p.executed_at,
        rejected_at=p.rejected_at
    )

    return ResponseBase(
        success=True,
        message="Smart action proposal rejected.",
        data=SmartActionResponse(action=item)
    )
