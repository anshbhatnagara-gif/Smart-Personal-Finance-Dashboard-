"""Services package exporting business and financial logic handlers."""

from app.services.auth_service import AuthService
from app.services.transaction_service import TransactionService
from app.services.budget_service import BudgetService
from app.services.finance_service import (
    calculate_savings,
    calculate_savings_rate,
    compare_months,
    analyze_categories,
    detect_overspending,
    calculate_budget_usage,
    calculate_financial_health_score,
    generate_smart_insights,
    format_currency_inr
)
from app.services import finance_engine
from app.services.intelligence_service import IntelligenceService

__all__ = [
    "AuthService",
    "TransactionService",
    "BudgetService",
    "calculate_savings",
    "calculate_savings_rate",
    "compare_months",
    "analyze_categories",
    "detect_overspending",
    "calculate_budget_usage",
    "calculate_financial_health_score",
    "generate_smart_insights",
    "format_currency_inr",
    "finance_engine",
    "IntelligenceService"
]
