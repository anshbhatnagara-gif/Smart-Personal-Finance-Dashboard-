"""Finance Router: Smart Finance Engine Intelligence, Analysis, Forecasts, and Alerts."""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.transaction import Transaction
from app.models.budget import Budget
from app.schemas.common import ResponseBase
from app.schemas.finance_analysis import SmartFinanceAnalysisData
from app.services.finance_engine import run_full_financial_analysis

router = APIRouter(prefix="/finance", tags=["Smart Finance Engine"])


@router.get(
    "/analysis",
    response_model=ResponseBase[SmartFinanceAnalysisData],
    status_code=status.HTTP_200_OK,
    summary="Get Deterministic Smart Finance Intelligence Analysis"
)
async def get_financial_analysis(
    month: Optional[int] = Query(None, ge=1, le=12, description="Target month (default: current month)"),
    year: Optional[int] = Query(None, ge=2000, le=2100, description="Target year (default: current year)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ResponseBase[SmartFinanceAnalysisData]:
    """
    Execute full Smart Finance Engine analysis for the authenticated user.
    Strictly scoped to current_user.id (IDOR protection guaranteed).
    """
    # 1. Fetch authenticated user's transactions only
    user_transactions = db.query(Transaction).filter(
        Transaction.user_id == current_user.id
    ).order_by(Transaction.transaction_date.desc()).all()

    # 2. Fetch authenticated user's budgets only
    user_budgets = db.query(Budget).filter(
        Budget.user_id == current_user.id
    ).all()

    # 3. Run pure deterministic financial analytics
    analysis_data = run_full_financial_analysis(
        transactions=user_transactions,
        budgets=user_budgets,
        target_month=month,
        target_year=year
    )

    return ResponseBase(
        success=True,
        message="Smart financial analysis generated successfully",
        data=analysis_data
    )
