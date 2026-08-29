"""Proactive AI Financial Insights Engine Package."""

from app.services.ai.insights.insight_engine import InsightEngine
from app.services.ai.insights.insight_rules import InsightRules
from app.services.ai.insights.insight_formatter import InsightFormatter

__all__ = ["InsightEngine", "InsightRules", "InsightFormatter"]
