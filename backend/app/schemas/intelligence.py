"""Pydantic v2 schemas for the Smart Finance Intelligence Engine & Insights API."""

from decimal import Decimal
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class IntelligenceSummary(BaseModel):
    """Monetary summary and cash flow health indicator."""
    total_income: Decimal
    total_expenses: Decimal
    net_savings: Decimal
    savings_rate: float
    current_month: str
    cashflow_status: str = Field(..., description="SURPLUS, BALANCED, DEFICIT")


class CategoryBehaviorItem(BaseModel):
    """Detailed category-level behavior and risk intelligence."""
    category: str
    total_spending: Decimal
    percentage_of_total_spending: float
    transaction_count: int
    average_transaction: Decimal
    current_month_spending: Decimal
    previous_month_spending: Decimal
    month_over_month_percentage_change: float
    budget_amount: Optional[Decimal] = None
    budget_utilization: Optional[float] = None
    risk_level: str = Field(..., description="LOW, MEDIUM, HIGH, CRITICAL")


class TransactionAnomalyItem(BaseModel):
    """Detected unusual or abnormal transaction with reason and severity."""
    transaction_id: int
    category: str
    title: str
    amount: Decimal
    reason: str
    severity: str = Field(..., description="LOW, MEDIUM, HIGH")


class BudgetRiskPredictionItem(BaseModel):
    """Predictive velocity analysis for budget envelopes."""
    category: str
    amount: Decimal
    spent: Decimal
    remaining: Decimal
    utilization: float
    spending_velocity: Decimal
    projected_spend: Decimal
    risk_level: str = Field(..., description="SAFE, WATCH, AT_RISK, LIKELY_OVER_BUDGET")
    explanation: str


class SavingsOpportunityFinding(BaseModel):
    """Actionable potential savings opportunity."""
    category: str
    current_spending: Decimal
    suggested_reduction_percentage: float
    potential_monthly_saving: Decimal
    potential_annual_saving: Decimal
    explanation: str
    priority: str = Field(..., description="HIGH, MEDIUM, LOW")


class HealthScoreDetailedFactor(BaseModel):
    """Individual health score dimension with explanation and actionable recommendation."""
    name: str
    score: int
    weight: str
    explanation: str
    recommendation: str


class FinancialHealthDetail(BaseModel):
    """Explainable 5-factor Financial Health Score."""
    score: int
    status: str
    factors: List[HealthScoreDetailedFactor]


class StructuredRecommendation(BaseModel):
    """High-impact actionable financial recommendation."""
    category: Optional[str] = None
    title: str
    action: str
    potential_monthly_saving: Optional[Decimal] = None
    impact: str = Field(..., description="HIGH, MEDIUM, LOW")


class IntelligenceInsight(BaseModel):
    """Rule-based contextual intelligence item."""
    type: str
    title: str
    message: str
    severity: str = Field(..., description="POSITIVE, INFO, WARNING, CRITICAL")
    category: Optional[str] = None
    metric: Optional[str] = None
    recommendation: Optional[str] = None


class SmartInsightsData(BaseModel):
    """Comprehensive Smart Finance Intelligence response schema."""
    generated_at: str
    summary: IntelligenceSummary
    insights: List[IntelligenceInsight]
    recommendations: List[StructuredRecommendation]
    category_analysis: List[CategoryBehaviorItem]
    anomalies: List[TransactionAnomalyItem]
    budget_risks: List[BudgetRiskPredictionItem]
    savings_opportunities: List[SavingsOpportunityFinding]
    health_score: FinancialHealthDetail

    model_config = ConfigDict(from_attributes=True)


class FinancialContextForAI(BaseModel):
    """Verified structured facts interface for future AI model integration."""
    user_id: int
    as_of: str
    monthly_income: Decimal
    monthly_expenses: Decimal
    net_savings: Decimal
    savings_rate: float
    top_categories: List[Dict[str, Any]]
    budget_risks: List[Dict[str, Any]]
    anomalies: List[Dict[str, Any]]
    savings_opportunities: List[Dict[str, Any]]
    health_score: int
    health_status: str
    insights: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]

    model_config = ConfigDict(from_attributes=True)
