"""Forecast Engine: Primary orchestrator for all forecasting services."""

from datetime import date
from typing import Dict, Any
from sqlalchemy.orm import Session

from app.services.ai.forecasting.income_forecast import IncomeForecastEngine
from app.services.ai.forecasting.expense_forecast import ExpenseForecastEngine
from app.services.ai.forecasting.savings_forecast import SavingsForecastEngine
from app.services.ai.forecasting.cashflow_forecast import CashflowForecastEngine
from app.services.ai.forecasting.forecast_formatter import ForecastFormatter


class ForecastingEngine:
    """Master forecasting coordinator for user-scoped predictive calculations."""

    def __init__(self, user_id: int, db: Session):
        self.user_id = user_id
        self.db = db
        self.income_engine = IncomeForecastEngine(user_id, db)
        self.expense_engine = ExpenseForecastEngine(user_id, db)
        self.savings_engine = SavingsForecastEngine(user_id, db)
        self.cashflow_engine = CashflowForecastEngine(user_id, db)

    def get_full_forecast(self, target_date: date = None) -> Dict[str, Any]:
        """Generate comprehensive financial forecast."""
        return self.cashflow_engine.generate_full_forecast(target_date)

    def get_income_forecast(self, target_date: date = None) -> Dict[str, Any]:
        return self.income_engine.project_income(target_date)

    def get_expense_forecast(self, target_date: date = None) -> Dict[str, Any]:
        return self.expense_engine.project_expenses(target_date)

    def get_savings_forecast(self, target_date: date = None) -> Dict[str, Any]:
        return self.savings_engine.project_savings(target_date)

    def get_formatted_xml(self, target_date: date = None) -> str:
        """Format forecast into prompt-ready XML block."""
        data = self.get_full_forecast(target_date)
        return ForecastFormatter.format_forecast_xml(data)
