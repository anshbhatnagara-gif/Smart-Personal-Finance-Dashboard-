"""SQLAlchemy 2.x Goal Model with target dates, category types, and user relationships."""

from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING
from sqlalchemy import (
    String,
    Integer,
    Numeric,
    DateTime,
    Date,
    ForeignKey,
    Enum as SQLEnum,
    func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class GoalCategoryEnum(str, Enum):
    """Supported financial goal categories."""
    EMERGENCY_FUND = "emergency_fund"
    SAVINGS = "savings"
    TRAVEL = "travel"
    EDUCATION = "education"
    VEHICLE = "vehicle"
    HOME = "home"
    INVESTMENT = "investment"
    DEBT_PAYMENT = "debt_payment"
    DEBT_PAYOFF = "debt_payoff"
    PURCHASE = "purchase"
    RETIREMENT = "retirement"
    OTHER = "other"


class GoalPriorityEnum(str, Enum):
    """Goal prioritization levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Goal(Base):
    """Financial goal tracking target savings, deadlines, and progress."""

    __tablename__ = "goals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    target_amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=12, scale=2, asdecimal=True),
        nullable=False
    )
    current_amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=12, scale=2, asdecimal=True),
        default=Decimal("0.00"),
        nullable=False
    )
    target_date: Mapped[date] = mapped_column(Date, nullable=False)
    category: Mapped[str] = mapped_column(String(50), default=GoalCategoryEnum.SAVINGS.value, nullable=False)
    priority: Mapped[str] = mapped_column(String(20), default=GoalPriorityEnum.MEDIUM.value, nullable=False)

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
    user: Mapped["User"] = relationship(back_populates="goals")

    def __repr__(self) -> str:
        return (
            f"<Goal(id={self.id}, user_id={self.user_id}, name='{self.name}', "
            f"target={self.target_amount}, current={self.current_amount}, "
            f"target_date='{self.target_date}')>"
        )
