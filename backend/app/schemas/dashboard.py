"""Dashboard Pydantic v2 schemas for financial aggregation, trends, and health score."""

from decimal import Decimal
from typing import List
from pydantic import BaseModel, ConfigDict

from app.schemas.transaction import TransactionResponse
from app.schemas.budget import BudgetResponse


class MonthComparison(BaseModel):
    """Month-over-month numerical delta and percentage comparison."""
    delta: Decimal
    percentage: float
    is_increase: bool
    text: str


class CategoryBreakdownItem(BaseModel):
    """Spending aggregation per category."""
    category: str
    amount: Decimal
    percentage: float


class MonthlyTrendItem(BaseModel):
    """Historical monthly cash flow point for charts."""
    month_key: str
    month_label: str
    income: Decimal
    expenses: Decimal
    net_savings: Decimal


class HealthFactor(BaseModel):
    """Individual weighted dimension for financial resilience score."""
    name: str
    score: int
    weight: str


class FinancialHealthScore(BaseModel):
    """Calculated 0-100 Financial Health score and factor breakdown."""
    score: int
    status: str
    status_class: str
    factors: List[HealthFactor]


class SmartInsight(BaseModel):
    """Dynamic contextual financial advice card."""
    type: str
    icon: str
    tag: str
    text: str


class DashboardSummaryData(BaseModel):
    """Comprehensive aggregated financial overview for user dashboard."""
    total_income: Decimal
    total_expenses: Decimal
    net_savings: Decimal
    savings_rate: float
    current_month: str
    income_comparison: MonthComparison
    expense_comparison: MonthComparison
    savings_comparison: MonthComparison
    category_breakdown: List[CategoryBreakdownItem]
    trends: List[MonthlyTrendItem]
    health_score: FinancialHealthScore
    insights: List[SmartInsight]
    recent_transactions: List[TransactionResponse]
    budgets: List[BudgetResponse]

    model_config = ConfigDict(from_attributes=True)
