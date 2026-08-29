"""Pydantic schemas package."""

from app.schemas.common import (
    ResponseBase,
    PaginatedData,
    PaginatedResponse,
    RootResponse,
    HealthResponse
)
from app.schemas.user import (
    UserBase,
    UserCreate,
    UserLogin,
    UserUpdate,
    UserResponse,
    TokenResponse,
    TokenPayload
)
from app.schemas.transaction import (
    TransactionType,
    TransactionBase,
    TransactionCreate,
    TransactionUpdate,
    TransactionResponse
)
from app.schemas.budget import (
    BudgetStatus,
    BudgetBase,
    BudgetCreate,
    BudgetUpdate,
    BudgetResponse
)
from app.schemas.dashboard import (
    MonthComparison,
    CategoryBreakdownItem,
    MonthlyTrendItem,
    HealthFactor,
    FinancialHealthScore,
    SmartInsight,
    DashboardSummaryData
)

__all__ = [
    "ResponseBase",
    "PaginatedData",
    "PaginatedResponse",
    "RootResponse",
    "HealthResponse",
    "UserBase",
    "UserCreate",
    "UserLogin",
    "UserUpdate",
    "UserResponse",
    "TokenResponse",
    "TokenPayload",
    "TransactionType",
    "TransactionBase",
    "TransactionCreate",
    "TransactionUpdate",
    "TransactionResponse",
    "BudgetStatus",
    "BudgetBase",
    "BudgetCreate",
    "BudgetUpdate",
    "BudgetResponse",
    "MonthComparison",
    "CategoryBreakdownItem",
    "MonthlyTrendItem",
    "HealthFactor",
    "FinancialHealthScore",
    "SmartInsight",
    "DashboardSummaryData"
]
