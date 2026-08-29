"""AI Forecasting package: deterministic predictive projections based on verified transaction data."""

from app.services.ai.forecasting.forecast_rules import ForecastRules, ForecastConfidence
from app.services.ai.forecasting.income_forecast import IncomeForecastEngine
from app.services.ai.forecasting.expense_forecast import ExpenseForecastEngine
from app.services.ai.forecasting.savings_forecast import SavingsForecastEngine
from app.services.ai.forecasting.cashflow_forecast import CashflowForecastEngine
from app.services.ai.forecasting.forecast_formatter import ForecastFormatter
from app.services.ai.forecasting.forecast_engine import ForecastingEngine

__all__ = [
    "ForecastRules",
    "ForecastConfidence",
    "IncomeForecastEngine",
    "ExpenseForecastEngine",
    "SavingsForecastEngine",
    "CashflowForecastEngine",
    "ForecastFormatter",
    "ForecastingEngine"
]
