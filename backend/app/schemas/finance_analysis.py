"""Pydantic v2 schemas for the Smart Finance Engine analysis & intelligence API."""

from decimal import Decimal
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class MetricDelta(BaseModel):
    """Numerical delta and percentage comparison for a monetary metric."""
    delta: Decimal
    percentage: float
    is_increase: bool
    text: str


class CategorySpendingItem(BaseModel):
    """Spending metrics for a single category."""
    category: str
    amount: Decimal
    percentage: float
    transaction_count: int = 0
    previous_amount: Optional[Decimal] = None
    growth_percentage: Optional[float] = None


class SpendingAnalysis(BaseModel):
    """Detailed category breakdown and spending concentration analysis."""
    total_spending: Decimal
    top_categories: List[CategorySpendingItem]
    highest_expense_category: Optional[CategorySpendingItem] = None
    spending_concentration_top1: float
    spending_concentration_top3: float
    significant_increases: List[Dict[str, Any]]
    unusually_high_categories: List[Dict[str, Any]]


class UnusualSpendingAlert(BaseModel):
    """Statistical anomaly alert for abnormal category spending."""
    category: str
    current_amount: Decimal
    historical_baseline: Decimal
    percentage_difference: float
    z_score: Optional[float] = None
    severity: str = Field(..., description="LOW, MEDIUM, HIGH")
    explanation: str


class BudgetRecommendationItem(BaseModel):
    """Intelligent budget recommendation based on historical trends."""
    category: str
    average_monthly_spending: Decimal
    recent_trend: str = Field(..., description="increasing, decreasing, stable")
    suggested_budget: Decimal
    current_budget: Optional[Decimal] = None
    recommended_adjustment: Optional[Decimal] = None
    safety_buffer_percentage: float
    explanation: str
    affordability_flag: bool = True


class SavingsOpportunityItem(BaseModel):
    """Actionable savings opportunity based on discretionary and growing spending."""
    category: str
    current_spending: Decimal
    suggested_reduction_percentage: float
    estimated_monthly_saving: Decimal
    estimated_annual_saving: Decimal
    explanation: str
    priority: str = Field(..., description="HIGH, MEDIUM, LOW")


class ForecastMonthItem(BaseModel):
    """Projected cash flow for a future month."""
    month_offset: int
    month_label: str
    estimated_income: Decimal
    estimated_expenses: Decimal
    estimated_net_savings: Decimal
    estimated_savings_rate: float


class CashflowForecast(BaseModel):
    """Deterministic multi-month cash flow forecast."""
    forecast_months: List[ForecastMonthItem]
    confidence_level: str = Field(..., description="HIGH, MEDIUM, LOW")
    confidence_score: int
    methodology: str = "Weighted Moving Average (WMA)"


class HealthScoreFactorDetail(BaseModel):
    """Individual weighted health factor breakdown."""
    score: int
    weight: str
    weight_percentage: int
    label: str
    description: str


class FinancialHealthAnalysis(BaseModel):
    """5-Factor Financial Health Score with explainable details."""
    score: int
    status: str
    status_class: str
    factors: Dict[str, HealthScoreFactorDetail]
    explanations: List[str]


class SmartInsightItem(BaseModel):
    """Structured actionable financial insight."""
    type: str = Field(..., description="HIGH_SAVER, BUDGET_WARNING, SPENDING_SPIKE, etc.")
    title: str
    message: str
    severity: str = Field(..., description="INFO, POSITIVE, WARNING, CRITICAL")
    category: Optional[str] = None
    metric: Optional[str] = None
    recommendation: Optional[str] = None


class FinancialAlertItem(BaseModel):
    """Prioritized financial warning or alert."""
    severity: str = Field(..., description="HIGH, MEDIUM, LOW")
    type: str
    title: str
    message: str
    action_required: bool = True


class FinancialSummary(BaseModel):
    """High-level monetary metrics overview."""
    total_income: Decimal
    total_expenses: Decimal
    net_savings: Decimal
    savings_rate: float
    current_month: str
    income_growth: MetricDelta
    expense_growth: MetricDelta
    savings_growth: MetricDelta


class BudgetAnalysisSummary(BaseModel):
    """Envelope budget overview and utilization metrics."""
    total_budget_envelope: Decimal
    total_budget_spent: Decimal
    total_budget_remaining: Decimal
    overall_utilization_percentage: float
    over_budget_categories_count: int
    near_limit_categories_count: int
    recommendations: List[BudgetRecommendationItem]


class SmartFinanceAnalysisData(BaseModel):
    """Complete comprehensive Smart Finance Engine output schema."""
    summary: FinancialSummary
    spending_analysis: SpendingAnalysis
    budget_analysis: BudgetAnalysisSummary
    savings_opportunities: List[SavingsOpportunityItem]
    unusual_spending: List[UnusualSpendingAlert]
    cashflow_forecast: CashflowForecast
    financial_health: FinancialHealthAnalysis
    insights: List[SmartInsightItem]
    alerts: List[FinancialAlertItem]

    model_config = ConfigDict(from_attributes=True)
