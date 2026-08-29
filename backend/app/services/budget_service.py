"""Budget Service: Envelope management, expense tracking, and status calculations."""

from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import extract

from app.models.budget import Budget
from app.models.transaction import Transaction, TransactionType
from app.schemas.budget import BudgetCreate, BudgetUpdate, BudgetResponse
from app.services.finance_service import calculate_budget_usage


class BudgetService:
    """Service managing budget envelopes with live spending calculations."""

    @staticmethod
    def get_budgets(
        db: Session,
        user_id: int,
        month: Optional[int] = None,
        year: Optional[int] = None
    ) -> List[BudgetResponse]:
        """Fetch all budgets for a user with calculated spending and utilization status."""
        query = db.query(Budget).filter(Budget.user_id == user_id)
        if month:
            query = query.filter(Budget.month == month)
        if year:
            query = query.filter(Budget.year == year)

        budgets = query.order_by(Budget.category.asc()).all()

        # Gather transactions for the user to compute spent amounts per category
        tx_query = db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.type == TransactionType.EXPENSE
        )
        if month:
            tx_query = tx_query.filter(extract("month", Transaction.transaction_date) == month)
        if year:
            tx_query = tx_query.filter(extract("year", Transaction.transaction_date) == year)

        expense_transactions = tx_query.all()

        # Aggregate expenses by category
        spent_map: dict[str, Decimal] = {}
        for tx in expense_transactions:
            cat_key = tx.category.lower().strip()
            spent_map[cat_key] = spent_map.get(cat_key, Decimal("0.00")) + tx.amount

        # Build responses with computed fields
        results: List[BudgetResponse] = []
        for b in budgets:
            spent = spent_map.get(b.category.lower().strip(), Decimal("0.00"))
            pct, remaining, b_status = calculate_budget_usage(spent, b.amount)

            results.append(BudgetResponse(
                id=b.id,
                user_id=b.user_id,
                category=b.category,
                amount=b.amount,
                month=b.month,
                year=b.year,
                spent=spent,
                remaining=remaining,
                percentage=pct,
                status=b_status,
                created_at=b.created_at,
                updated_at=b.updated_at
            ))

        return results

    @classmethod
    def get_budget_by_id(cls, db: Session, budget_id: int, user_id: int) -> Budget:
        """Fetch budget ensuring ownership (prevents IDOR)."""
        budget = db.query(Budget).filter(
            Budget.id == budget_id,
            Budget.user_id == user_id
        ).first()

        if not budget:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Budget with ID {budget_id} not found"
            )
        return budget

    @classmethod
    def create_budget(cls, db: Session, user_id: int, budget_in: BudgetCreate) -> BudgetResponse:
        """Create a new category budget envelope enforcing unique constraint."""
        cat_clean = budget_in.category.strip()
        existing = db.query(Budget).filter(
            Budget.user_id == user_id,
            Budget.category.ilike(cat_clean),
            Budget.month == budget_in.month,
            Budget.year == budget_in.year
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A budget for '{cat_clean}' in {budget_in.year}-{budget_in.month:02d} already exists"
            )

        budget = Budget(
            user_id=user_id,
            category=cat_clean,
            amount=budget_in.amount,
            month=budget_in.month,
            year=budget_in.year
        )
        db.add(budget)
        db.commit()
        db.refresh(budget)

        # Calculate initial spending
        tx_spent = db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.type == TransactionType.EXPENSE,
            Transaction.category.ilike(cat_clean),
            extract("month", Transaction.transaction_date) == budget.month,
            extract("year", Transaction.transaction_date) == budget.year
        ).all()
        spent = sum((t.amount for t in tx_spent), Decimal("0.00"))
        pct, remaining, b_status = calculate_budget_usage(spent, budget.amount)

        return BudgetResponse(
            id=budget.id,
            user_id=budget.user_id,
            category=budget.category,
            amount=budget.amount,
            month=budget.month,
            year=budget.year,
            spent=spent,
            remaining=remaining,
            percentage=pct,
            status=b_status,
            created_at=budget.created_at,
            updated_at=budget.updated_at
        )

    @classmethod
    def update_budget(
        cls,
        db: Session,
        budget_id: int,
        user_id: int,
        budget_update: BudgetUpdate
    ) -> BudgetResponse:
        """Update an existing category budget with conflict verification."""
        budget = cls.get_budget_by_id(db, budget_id, user_id)

        update_data = budget_update.model_dump(exclude_unset=True)
        new_category = update_data.get("category", budget.category).strip()
        new_month = update_data.get("month", budget.month)
        new_year = update_data.get("year", budget.year)

        # Verify uniqueness if key dimensions are changing
        if (
            new_category.lower() != budget.category.lower()
            or new_month != budget.month
            or new_year != budget.year
        ):
            conflict = db.query(Budget).filter(
                Budget.user_id == user_id,
                Budget.id != budget_id,
                Budget.category.ilike(new_category),
                Budget.month == new_month,
                Budget.year == new_year
            ).first()
            if conflict:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Another budget for '{new_category}' in {new_year}-{new_month:02d} already exists"
                )

        for field, value in update_data.items():
            if field == "category" and value:
                setattr(budget, field, value.strip())
            else:
                setattr(budget, field, value)

        db.commit()
        db.refresh(budget)

        # Recalculate spent
        tx_spent = db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.type == TransactionType.EXPENSE,
            Transaction.category.ilike(budget.category),
            extract("month", Transaction.transaction_date) == budget.month,
            extract("year", Transaction.transaction_date) == budget.year
        ).all()
        spent = sum((t.amount for t in tx_spent), Decimal("0.00"))
        pct, remaining, b_status = calculate_budget_usage(spent, budget.amount)

        return BudgetResponse(
            id=budget.id,
            user_id=budget.user_id,
            category=budget.category,
            amount=budget.amount,
            month=budget.month,
            year=budget.year,
            spent=spent,
            remaining=remaining,
            percentage=pct,
            status=b_status,
            created_at=budget.created_at,
            updated_at=budget.updated_at
        )

    @classmethod
    def delete_budget(cls, db: Session, budget_id: int, user_id: int) -> None:
        """Delete a category budget owned by user."""
        budget = cls.get_budget_by_id(db, budget_id, user_id)
        db.delete(budget)
        db.commit()
