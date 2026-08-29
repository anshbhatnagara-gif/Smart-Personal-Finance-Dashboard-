"""Pydantic v2 schemas for AI Financial Intelligence, Health Scoring, Explainability, and Simulations."""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class FinancialHealthComponent(BaseModel):
    """Component evaluation within 7-factor financial health score."""
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., description="Human-readable component name")
    weight: float = Field(..., ge=0.0, le=1.0, description="Component weight in overall score")
    score: Optional[float] = Field(None, ge=0.0, le=100.0, description="Component score from 0-100 or None if insufficient data")
    status: str = Field(..., description="Status tier: EXCELLENT, GOOD, FAIR, POOR, CRITICAL, INSUFFICIENT_DATA")
    verified_evidence: str = Field(..., description="Fact-checked evidence string from database")
    calculation_explanation: str = Field(..., description="Deterministic calculation description")


class FinancialHealthScoreResponse(BaseModel):
    """Full financial health score evaluation response."""
    model_config = ConfigDict(from_attributes=True)

    overall_score: Optional[float] = Field(None, ge=0.0, le=100.0, description="Overall weighted score 0-100")
    status: str = Field(..., description="Overall health classification")
    summary: str = Field(..., description="Executive summary of user financial health")
    components: Dict[str, FinancialHealthComponent] = Field(..., description="7 individual dimension evaluations")
    as_of_date: str = Field(..., description="Evaluation date YYYY-MM-DD")


class FinancialExplanationItem(BaseModel):
    """Structured transparent explanation item."""
    model_config = ConfigDict(from_attributes=True)

    explanation_type: str = Field(..., description="Category: WHY_THIS_FORECAST, WHY_THIS_RISK, WHY_THIS_GOAL_STATUS, WHY_THIS_SMART_ACTION, WHY_THIS_HEALTH_SCORE")
    label: str = Field("EXPLANATION", description="Strict label EXPLANATION")
    title: str = Field(..., description="Headline of explanation")
    summary: str = Field(..., description="Core narrative explanation")
    verified_evidence: str = Field(..., description="Direct citation of database metrics")
    calculation_basis: str = Field(..., description="Formula or rule logic applied")
    affected_amount: float = Field(0.0, ge=0.0, description="Monetary impact amount in INR")
    confidence: str = Field("HIGH", description="Confidence tier: HIGH, MEDIUM, LOW")
    limitations: str = Field(..., description="Scope and constraint limitations")


class FinancialExplanationResponse(BaseModel):
    """Response containing list of grounded explanations."""
    model_config = ConfigDict(from_attributes=True)

    explanations: List[FinancialExplanationItem] = Field(..., description="Active explanations")
    total_count: int = Field(..., ge=0, description="Total active explanations")
    as_of_date: str = Field(..., description="Calculation date")


class SimulationRequest(BaseModel):
    """Payload to trigger what-if financial simulation."""
    model_config = ConfigDict(extra="ignore")

    scenario: str = Field(..., description="Scenario type: INCREASE_SAVINGS, REDUCE_EXPENSES, INCREASE_EXPENSES, INCOME_REDUCTION, INCOME_INCREASE, GOAL_DEADLINE_CHANGE, MONTHLY_CONTRIBUTION_CHANGE, DEBT_PAYMENT_CHANGE")
    amount: Optional[float] = Field(None, ge=0.0, description="Monetary delta amount (must be positive)")
    percentage: Optional[float] = Field(None, ge=0.0, le=100.0, description="Percentage shift (0-100)")
    months: Optional[int] = Field(None, description="Timeline delta in months")
    goal_id: Optional[int] = Field(None, description="Specific goal target ID")
    category: Optional[str] = Field(None, description="Expense category target")


class SimulationState(BaseModel):
    """Financial state snapshot before or after simulation."""
    monthly_income: float = Field(..., ge=0.0)
    monthly_expenses: float = Field(..., ge=0.0)
    monthly_savings: float = Field(..., ge=0.0)
    savings_rate_percentage: float = Field(..., ge=0.0, le=100.0)
    health_score: float = Field(..., ge=0.0, le=100.0)
    health_status: Optional[str] = Field(None)
    goal_completion_months: float = Field(..., ge=0.0)


class SimulationImpact(BaseModel):
    """Delta impact between current and simulated outcomes."""
    delta_monthly_savings: float = Field(...)
    delta_savings_rate: float = Field(...)
    delta_health_score: float = Field(...)
    timeline_acceleration_months: float = Field(...)
    summary: str = Field(...)


class SimulationResponse(BaseModel):
    """Complete what-if simulation response."""
    scenario: str = Field(..., description="Scenario simulated")
    label: str = Field("SIMULATION", description="Strict label SIMULATION")
    disclaimer: str = Field("SIMULATION ONLY — No modifications were made to your database records.")
    current_state: SimulationState = Field(...)
    simulated_state: SimulationState = Field(...)
    impact: SimulationImpact = Field(...)


class SimulationExampleItem(BaseModel):
    """Preset scenario template for one-click exploration."""
    scenario: str = Field(...)
    title: str = Field(...)
    description: str = Field(...)
    payload: Dict[str, Any] = Field(...)


class SimulationExamplesResponse(BaseModel):
    """Response containing list of preset simulation examples."""
    examples: List[SimulationExampleItem] = Field(...)
    total_count: int = Field(...)


class FinancialIntelligenceResponse(BaseModel):
    """Unified master intelligence response."""
    health_score: FinancialHealthScoreResponse = Field(...)
    forecast: Dict[str, Any] = Field(...)
    risks: Dict[str, Any] = Field(...)
    goals: List[Dict[str, Any]] = Field(...)
    smart_actions: List[Dict[str, Any]] = Field(...)
    explanations: List[FinancialExplanationItem] = Field(...)
    as_of_date: str = Field(...)
