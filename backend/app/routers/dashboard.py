"""Dashboard Router: Aggregated metrics, cash flow trends, health score, and insights."""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import extract

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.transaction import Transaction, TransactionType
from app.schemas.common import ResponseBase
from app.schemas.transaction import TransactionResponse
from app.schemas.dashboard import (
    DashboardSummaryData,
    MonthlyTrendItem
)
from app.services.budget_service import BudgetService
from app.services.finance_service import (
    calculate_savings,
    calculate_savings_rate,
    compare_months,
    analyze_categories,
    calculate_financial_health_score,
    generate_smart_insights
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get(
    "",
    response_model=ResponseBase[DashboardSummaryData],
    status_code=status.HTTP_200_OK,
    summary="Get Aggregated Financial Dashboard"
)
async def get_dashboard_summary(
    month: Optional[int] = Query(None, ge=1, le=12, description="Target month (default: current month)"),
    year: Optional[int] = Query(None, ge=2000, le=2100, description="Target year (default: current year)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ResponseBase[DashboardSummaryData]:
    """Compile comprehensive financial metrics, comparisons, health score, and smart insights."""
    now = datetime.now()
    cur_month = month or now.month
    cur_year = year or now.year

    # Previous Month calculation
    if cur_month == 1:
        prev_month = 12
        prev_year = cur_year - 1
    else:
        prev_month = cur_month - 1
        prev_year = cur_year

    month_str = f"{cur_year}-{cur_month:02d}"

    # 1. Fetch all user transactions
    all_transactions = db.query(Transaction).filter(
        Transaction.user_id == current_user.id
    ).order_by(Transaction.transaction_date.desc()).all()

    # Current month transactions
    cur_transactions = [
        t for t in all_transactions
        if t.transaction_date.year == cur_year and t.transaction_date.month == cur_month
    ]

    # Previous month transactions
    prev_transactions = [
        t for t in all_transactions
        if t.transaction_date.year == prev_year and t.transaction_date.month == prev_month
    ]

    # 2. Current Month Aggregations
    cur_income = sum(
        (t.amount for t in cur_transactions if t.type == TransactionType.INCOME),
        Decimal("0.00")
    )
    cur_expenses = sum(
        (t.amount for t in cur_transactions if t.type == TransactionType.EXPENSE),
        Decimal("0.00")
    )
    cur_savings = calculate_savings(cur_income, cur_expenses)
    cur_savings_rate = calculate_savings_rate(cur_income, cur_expenses)

    # 3. Previous Month Aggregations
    prev_income = sum(
        (t.amount for t in prev_transactions if t.type == TransactionType.INCOME),
        Decimal("0.00")
    )
    prev_expenses = sum(
        (t.amount for t in prev_transactions if t.type == TransactionType.EXPENSE),
        Decimal("0.00")
    )
    prev_savings = calculate_savings(prev_income, prev_expenses)

    # 4. MoM Comparisons
    income_comp = compare_months(cur_income, prev_income)
    expense_comp = compare_months(cur_expenses, prev_expenses)
    savings_comp = compare_months(cur_savings, prev_savings)

    # 5. Category Breakdown
    cat_breakdown = analyze_categories(cur_transactions)

    # 6. Fetch User Budgets
    budgets_list = BudgetService.get_budgets(
        db=db,
        user_id=current_user.id,
        month=cur_month,
        year=cur_year
    )
    total_budget_envelope = sum((b.amount for b in budgets_list), Decimal("0.00"))

    # 7. Multi-Month Trend Points (Last 6 Months)
    trend_items: List[MonthlyTrendItem] = []
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    for i in range(5, -1, -1):
        # Calculate target month/year going backwards
        m = cur_month - i
        y = cur_year
        while m <= 0:
            m += 12
            y -= 1

        m_txs = [
            t for t in all_transactions
            if t.transaction_date.year == y and t.transaction_date.month == m
        ]
        m_inc = sum((t.amount for t in m_txs if t.type == TransactionType.INCOME), Decimal("0.00"))
        m_exp = sum((t.amount for t in m_txs if t.type == TransactionType.EXPENSE), Decimal("0.00"))
        m_sav = calculate_savings(m_inc, m_exp)

        trend_items.append(MonthlyTrendItem(
            month_key=f"{y}-{m:02d}",
            month_label=month_names[m - 1],
            income=m_inc,
            expenses=m_exp,
            net_savings=m_sav
        ))

    # 8. Financial Health Score
    health_score = calculate_financial_health_score({
        "income": cur_income,
        "expenses": cur_expenses,
        "prev_expenses": prev_expenses,
        "total_budget": total_budget_envelope
    })

    # 9. Smart Insights
    insights = generate_smart_insights({
        "income": cur_income,
        "expenses": cur_expenses,
        "prev_income": prev_income,
        "prev_expenses": prev_expenses,
        "transactions": cur_transactions,
        "budgets": budgets_list
    })

    # 10. Recent Transactions (Top 5)
    recent_txs = [TransactionResponse.model_validate(t) for t in all_transactions[:5]]

    summary_data = DashboardSummaryData(
        total_income=cur_income,
        total_expenses=cur_expenses,
        net_savings=cur_savings,
        savings_rate=cur_savings_rate,
        current_month=month_str,
        income_comparison=income_comp,
        expense_comparison=expense_comp,
        savings_comparison=savings_comp,
        category_breakdown=cat_breakdown,
        trends=trend_items,
        health_score=health_score,
        insights=insights,
        recent_transactions=recent_txs,
        budgets=budgets_list
    )

    return ResponseBase(
        success=True,
        message="Dashboard summary compiled successfully",
        data=summary_data
    )
