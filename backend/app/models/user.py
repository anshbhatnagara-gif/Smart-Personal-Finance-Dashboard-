"""SQLAlchemy 2.x User Model."""

from datetime import datetime
from typing import List, TYPE_CHECKING
from sqlalchemy import String, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.transaction import Transaction
    from app.models.budget import Budget
    from app.models.goal import Goal
    from app.models.smart_action import SmartActionProposal, ActionAudit


class User(Base):
    """User entity representing an account holder."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relationships
    transactions: Mapped[List["Transaction"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="Transaction.transaction_date.desc()"
    )
    budgets: Mapped[List["Budget"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )
    goals: Mapped[List["Goal"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="Goal.target_date.asc()"
    )
    smart_actions: Mapped[List["SmartActionProposal"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="SmartActionProposal.created_at.desc()"
    )
    action_audits: Mapped[List["ActionAudit"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="ActionAudit.timestamp.desc()"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', name='{self.name}')>"
