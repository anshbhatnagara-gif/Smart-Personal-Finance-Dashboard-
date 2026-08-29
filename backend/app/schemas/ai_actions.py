"""Pydantic v2 Schemas for Smart Financial Actions & Audit Trail."""

from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict, Field


class SmartActionItem(BaseModel):
    """Represents a single smart financial action proposal."""
    model_config = ConfigDict(from_attributes=True)

    action_id: str
    action_type: str
    title: str
    description: str
    verified_evidence: str
    financial_amount: float
    expected_impact: str
    risk_level: str
    requires_confirmation: bool
    status: str
    created_at: datetime
    expires_at: datetime
    confirmed_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None


class SmartActionResponse(BaseModel):
    """Response payload containing a single smart action item."""
    action: SmartActionItem


class SmartActionListResponse(BaseModel):
    """Response payload containing list of active smart action proposals."""
    actions: List[SmartActionItem]
    total_actions: int


class ActionConfirmationRequest(BaseModel):
    """User confirmation request payload."""
    note: Optional[str] = Field(default="", max_length=500, description="Optional user note or rationale for confirmation.")


class ActionExecutionResponse(BaseModel):
    """Response payload detailing server-side execution results."""
    action_id: str
    action_type: str
    status: str
    executed_at: datetime
    previous_state: Dict[str, Any]
    resulting_state: Dict[str, Any]
    audit_logged: bool


class ActionRejectionRequest(BaseModel):
    """User rejection request payload."""
    reason: Optional[str] = Field(default="", max_length=500, description="Optional reason for rejecting the action proposal.")


class ActionAuditItem(BaseModel):
    """Audit log entry for an action lifecycle event."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    action_id: str
    action_type: str
    timestamp: datetime
    previous_state: str
    resulting_state: str
    execution_status: str
    financial_amount: float
    reason: str
    validation_result: str


class ActionHistoryResponse(BaseModel):
    """Response payload containing audit event history."""
    items: List[ActionAuditItem]
    total_records: int
