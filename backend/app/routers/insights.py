"""Insights Router: Smart Finance Intelligence Engine, Behavioral Analytics, and AI Context."""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.transaction import Transaction
from app.models.budget import Budget
from app.schemas.common import ResponseBase
from app.schemas.intelligence import SmartInsightsData, FinancialContextForAI
from app.services.intelligence_service import IntelligenceService

router = APIRouter(prefix="/insights", tags=["Smart Finance Intelligence"])


@router.get(
    "",
    response_model=ResponseBase[SmartInsightsData],
    status_code=status.HTTP_200_OK,
    summary="Get Smart Financial Intelligence Insights"
)
async def get_smart_insights(
    month: Optional[int] = Query(None, ge=1, le=12, description="Target month (default: current month)"),
    year: Optional[int] = Query(None, ge=2000, le=2100, description="Target year (default: current year)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ResponseBase[SmartInsightsData]:
    """
    Execute deterministic financial intelligence analysis strictly for the authenticated user.
    """
    user_transactions = db.query(Transaction).filter(
        Transaction.user_id == current_user.id
    ).order_by(Transaction.transaction_date.desc()).all()

    user_budgets = db.query(Budget).filter(
        Budget.user_id == current_user.id
    ).all()

    insights_data = IntelligenceService.generate_full_insights(
        transactions=user_transactions,
        budgets=user_budgets,
        target_month=month,
        target_year=year
    )

    return ResponseBase(
        success=True,
        message="Financial intelligence insights generated successfully",
        data=insights_data
    )


@router.get(
    "/ai-context",
    response_model=ResponseBase[FinancialContextForAI],
    status_code=status.HTTP_200_OK,
    summary="Get Verified Structured Financial Context for AI"
)
async def get_ai_financial_context(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ResponseBase[FinancialContextForAI]:
    """
    Return verified structured facts for future LLM integration (Phase 2.5/3).
    Ensures future AI agents never query the database directly.
    """
    context = IntelligenceService.get_financial_context(current_user.id, db)
    return ResponseBase(
        success=True,
        message="AI financial context compiled successfully",
        data=context
    )
