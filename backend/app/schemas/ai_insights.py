"""Pydantic v2 Schemas for Proactive Financial Insights & Alerts API."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class ProactiveInsightItem(BaseModel):
    """Structured proactive financial insight/alert model."""
    type: str = Field(..., description="Rule identifier (SPENDING_SPIKE, BUDGET_WARNING, etc.)")
    severity: str = Field(..., description="Severity level: critical, warning, info, positive")
    title: str = Field(..., description="Concise insight title")
    message: str = Field(..., description="Data-grounded explanation message")
    category: str = Field(..., description="Financial category or domain")
    amount: float = Field(..., description="Associated monetary value in INR")
    percentage: float = Field(..., description="Associated percentage metric or utilization")
    recommendation: str = Field(..., description="Actionable informational suggestion")
    evidence: Dict[str, Any] = Field(default_factory=dict, description="Supporting mathematical calculation facts")

    model_config = ConfigDict(from_attributes=True)


class ProactiveInsightsResponseData(BaseModel):
    """Response payload for GET /api/ai/insights."""
    generated_at: str
    insights: List[ProactiveInsightItem]
    count: int

    model_config = ConfigDict(from_attributes=True)
