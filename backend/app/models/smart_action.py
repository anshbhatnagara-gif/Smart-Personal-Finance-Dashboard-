"""SQLAlchemy 2.x Models for Smart Actions and Action Audit Trail."""

import enum
from datetime import datetime, timezone, timedelta
from typing import Optional, TYPE_CHECKING
from decimal import Decimal
from sqlalchemy import String, Integer, Numeric, DateTime, Boolean, Text, ForeignKey, func, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class ActionTypeEnum(str, enum.Enum):
    """Supported smart financial action types."""
    BUDGET_ADJUSTMENT = "BUDGET_ADJUSTMENT"
    SAVINGS_INCREASE = "SAVINGS_INCREASE"
    GOAL_CONTRIBUTION_ADJUSTMENT = "GOAL_CONTRIBUTION_ADJUSTMENT"
    EXPENSE_REDUCTION = "EXPENSE_REDUCTION"
    RECURRING_EXPENSE_REVIEW = "RECURRING_EXPENSE_REVIEW"
    EMERGENCY_FUND_CONTRIBUTION = "EMERGENCY_FUND_CONTRIBUTION"
    DEBT_PAYMENT_REVIEW = "DEBT_PAYMENT_REVIEW"
    FINANCIAL_RISK_MITIGATION = "FINANCIAL_RISK_MITIGATION"


class ActionStatusEnum(str, enum.Enum):
    """Lifecycle status for smart financial actions."""
    PROPOSED = "PROPOSED"
    CONFIRMED = "CONFIRMED"
    EXECUTED = "EXECUTED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class SmartActionProposal(Base):
    """Stores AI-proposed smart actions awaiting user confirmation."""

    __tablename__ = "smart_action_proposals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    action_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    action_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    verified_evidence: Mapped[str] = mapped_column(Text, nullable=False)
    financial_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    expected_impact: Mapped[str] = mapped_column(Text, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), default="MEDIUM", nullable=False)
    requires_confirmation: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="PROPOSED", nullable=False, index=True)

    action_payload: Mapped[str] = mapped_column(Text, nullable=False)  # JSON payload string
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)  # SHA-256 for tamper prevention

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    executed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="smart_actions")

    def is_expired(self, current_time: Optional[datetime] = None) -> bool:
        """Check if action proposal has expired."""
        now = current_time or datetime.now(timezone.utc)
        if self.expires_at.tzinfo is None:
            # Handle naive datetime from SQLite
            return self.expires_at < now.replace(tzinfo=None)
        return self.expires_at < now

    def __repr__(self) -> str:
        return f"<SmartActionProposal(action_id='{self.action_id}', type='{self.action_type}', status='{self.status}')>"


class ActionAudit(Base):
    """Immutable audit trail for all action lifecycle events."""

    __tablename__ = "action_audits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    action_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    action_type: Mapped[str] = mapped_column(String(50), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    previous_state: Mapped[str] = mapped_column(Text, nullable=False)  # JSON or text
    resulting_state: Mapped[str] = mapped_column(Text, nullable=False)  # JSON or text
    execution_status: Mapped[str] = mapped_column(String(30), nullable=False)
    financial_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    validation_result: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="action_audits")

    def __repr__(self) -> str:
        return f"<ActionAudit(action_id='{self.action_id}', status='{self.execution_status}', time='{self.timestamp}')>"
