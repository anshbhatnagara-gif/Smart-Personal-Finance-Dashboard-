"""API Routers package exporting auth, transactions, budgets, dashboard, finance, insights, and ai."""

from app.routers.auth import router as auth_router
from app.routers.transactions import router as transactions_router
from app.routers.budgets import router as budgets_router
from app.routers.dashboard import router as dashboard_router
from app.routers.finance import router as finance_router
from app.routers.insights import router as insights_router
from app.routers.ai import router as ai_router
from app.routers.goals import router as goals_router
from app.routers.actions import router as actions_router

__all__ = [
    "auth_router",
    "transactions_router",
    "budgets_router",
    "dashboard_router",
    "finance_router",
    "insights_router",
    "ai_router",
    "goals_router",
    "actions_router"
]

