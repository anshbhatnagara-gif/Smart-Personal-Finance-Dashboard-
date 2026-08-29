"""Pydantic v2 schemas for Financial Planning, Affordability, and What-If Scenarios."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class GoalScenarioRequest(BaseModel):
    """Request payload for running a what-if scenario simulation."""
    scenario_type: str = Field(
        ...,
        description="Type: increased_savings, reduced_spending, increased_expenses, income_reduction, goal_deadline_change, monthly_contribution_change"
    )
    monthly_savings_delta: Optional[float] = Field(None, description="Additional monthly savings amount")
    reduction_percentage: Optional[float] = Field(None, description="Percentage reduction in expenses")
    reduction_amount: Optional[float] = Field(None, description="Direct INR reduction amount")
    increase_percentage: Optional[float] = Field(None, description="Percentage increase in expenses")
    increase_amount: Optional[float] = Field(None, description="Direct INR increase in expenses")
    category: Optional[str] = Field(None, description="Target category for spending adjustments")
    months_delta: Optional[int] = Field(None, description="Number of months to extend/shorten deadline")
    new_target_date: Optional[str] = Field(None, description="New target date in YYYY-MM-DD format")
    monthly_contribution: Optional[float] = Field(None, description="Custom monthly contribution amount")


class GoalScenarioResponse(BaseModel):
    """Response envelope for scenario simulation results."""
    scenario_type: str
    goal_name: str
    summary: str
    baseline_monthly_surplus: Optional[float] = None
    simulated_monthly_surplus: Optional[float] = None
    monthly_savings_increase: Optional[float] = None
    annual_savings_increase: Optional[float] = None
    baseline_months_to_completion: Optional[float] = None
    simulated_months_to_completion: Optional[float] = None
    time_saved_months: Optional[float] = None
    simulated_required_monthly: Optional[float] = None
    original_required_monthly: Optional[float] = None
    monthly_required_relief: Optional[float] = None
    projected_completion_date: Optional[str] = None
    assumptions: List[str] = []


class AffordabilityResponse(BaseModel):
    """Response schema for goal affordability analysis."""
    affordability_status: str
    required_monthly_amount: float
    suggested_monthly_amount: float
    monthly_income: float
    monthly_expenses: float
    net_monthly_surplus: float
    discretionary_expenses: float
    savings_rate_percentage: float
    reasoning: str
    verified_facts: List[str]
    recommendation: str
    assumptions: List[str]


class FinancialPlanningResponse(BaseModel):
    """Complete personalized financial coaching profile."""
    user_id: int
    period: str
    cashflow: Dict[str, Any]
    top_spending_categories: List[Dict[str, Any]]
    goals_summary: Dict[str, Any]
    financial_health_score: int
    proactive_insights: List[Dict[str, Any]]
