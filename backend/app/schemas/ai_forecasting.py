"""Pydantic v2 Schemas for AI Financial Forecasting, Risk Detection, and Predictive Insights."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict, Field


class ForecastMetric(BaseModel):
    """Single metric forecast result."""
    metric: str
    current_value: float
    projected_value: float
    period: str = "Next Month"
    confidence: str
    methodology: str
    trend_percentage: float = 0.0
    evidence: List[str] = Field(default_factory=list)
    limitations: str
    is_sufficient_data: bool = True

    model_config = ConfigDict(from_attributes=True)


class CategoryExpenseForecast(BaseModel):
    """Category-specific spending projection."""
    category: str
    current_spending: float
    projected_spending: float
    trend_percentage: float

    model_config = ConfigDict(from_attributes=True)


class ExpenseForecastResponse(BaseModel):
    """Response schema for expense forecasting."""
    metric: str = "Monthly Expenses"
    current_value: float
    projected_value: float
    period: str = "Next Month"
    confidence: str
    methodology: str
    trend_percentage: float = 0.0
    category_forecasts: Dict[str, CategoryExpenseForecast] = Field(default_factory=dict)
    evidence: List[str] = Field(default_factory=list)
    limitations: str
    is_sufficient_data: bool = True

    model_config = ConfigDict(from_attributes=True)


class IncomeForecastResponse(BaseModel):
    """Response schema for income forecasting."""
    metric: str = "Monthly Income"
    current_value: float
    projected_value: float
    period: str = "Next Month"
    confidence: str
    methodology: str
    trend_percentage: float = 0.0
    evidence: List[str] = Field(default_factory=list)
    limitations: str
    is_sufficient_data: bool = True

    model_config = ConfigDict(from_attributes=True)


class CashBalanceTrendItem(BaseModel):
    """Single monthly balance milestone."""
    month_offset: int
    projected_monthly_savings: float
    cumulative_projected_surplus: float

    model_config = ConfigDict(from_attributes=True)


class SavingsForecastResponse(BaseModel):
    """Response schema for savings forecasting."""
    metric: str = "Monthly Net Savings"
    current_value: float
    projected_value: float
    projected_savings_rate_percentage: float
    period: str = "Next Month"
    confidence: str
    methodology: str
    cash_balance_trend_6m: List[CashBalanceTrendItem] = Field(default_factory=list)
    evidence: List[str] = Field(default_factory=list)
    limitations: str
    is_sufficient_data: bool = True

    model_config = ConfigDict(from_attributes=True)


class BudgetExhaustionItem(BaseModel):
    """Projected budget exhaustion metrics."""
    category: str
    budget_amount: float
    current_spent: float
    daily_burn_rate: float
    projected_month_end_spending: float
    projected_exhaustion_day_of_month: Optional[int] = None
    will_exceed_budget: bool
    projected_overrun_amount: float

    model_config = ConfigDict(from_attributes=True)


class GoalCompletionForecastItem(BaseModel):
    """Projected goal timeline metrics."""
    goal_id: int
    name: str
    target_amount: float
    current_amount: float
    remaining_amount: float
    target_date: str
    projected_completion_date: Optional[str] = None
    status: str
    required_monthly_contribution: float
    projected_delay_months: int = 0

    model_config = ConfigDict(from_attributes=True)


class CashflowForecastResponse(BaseModel):
    """Consolidated full cashflow outlook."""
    income_forecast: IncomeForecastResponse
    expense_forecast: ExpenseForecastResponse
    savings_forecast: SavingsForecastResponse
    budget_exhaustion_forecast: List[BudgetExhaustionItem] = Field(default_factory=list)
    goal_completion_forecast: List[GoalCompletionForecastItem] = Field(default_factory=list)
    is_sufficient_data: bool = True

    model_config = ConfigDict(from_attributes=True)


class FinancialRiskItem(BaseModel):
    """Single verified financial risk."""
    risk_type: str
    severity: str
    title: str
    message: str
    verified_evidence: str
    affected_amount: float
    percentage: float
    explanation: str
    recommended_action: str

    model_config = ConfigDict(from_attributes=True)


class FinancialStressSummary(BaseModel):
    """Overall financial stress scoring."""
    overall_risk_level: str
    stress_score: int
    summary: str

    model_config = ConfigDict(from_attributes=True)


class FinancialRiskResponse(BaseModel):
    """Response schema for financial risk report."""
    risks: List[FinancialRiskItem] = Field(default_factory=list)
    total_risks: int
    stress_summary: FinancialStressSummary
    forecast_basis: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class PredictiveInsightItem(BaseModel):
    """Single predictive insight with distinct truth & forecast labels."""
    prediction_type: str
    category: str
    severity: str
    title: str
    verified_fact: str
    forecast: str
    risk: str
    ai_suggestion: str

    model_config = ConfigDict(from_attributes=True)


class PredictiveInsightsResponse(BaseModel):
    """Response schema for predictive insights collection."""
    insights: List[PredictiveInsightItem] = Field(default_factory=list)
    total_insights: int
    generated_at: str

    model_config = ConfigDict(from_attributes=True)
