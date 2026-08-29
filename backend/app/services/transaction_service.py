"""Transaction Service: Database queries, scoping, filtering, sorting, pagination, and CRUD."""

from datetime import date
from math import ceil
from typing import Optional, List, Tuple
from fastapi import HTTPException, status
from sqlalchemy import or_, desc, asc
from sqlalchemy.orm import Session

from app.models.transaction import Transaction, TransactionType
from app.schemas.transaction import TransactionCreate, TransactionUpdate


class TransactionService:
    """Service managing scoped transaction records with IDOR protection."""

    @staticmethod
    def get_transactions(
        db: Session,
        user_id: int,
        search: Optional[str] = None,
        category: Optional[str] = None,
        type_: Optional[TransactionType] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        sort_by: str = "date",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 10
    ) -> Tuple[List[Transaction], int, int]:
        """Fetch filtered, sorted, and paginated transactions strictly scoped to user_id."""
        query = db.query(Transaction).filter(Transaction.user_id == user_id)

        # 1. Search Filter (title or description)
        if search and search.strip():
            term = f"%{search.strip().lower()}%"
            query = query.filter(
                or_(
                    Transaction.title.ilike(term),
                    Transaction.description.ilike(term),
                    Transaction.category.ilike(term)
                )
            )

        # 2. Category Filter
        if category and category.upper() != "ALL":
            query = query.filter(Transaction.category.ilike(category.strip()))

        # 3. Type Filter
        if type_:
            query = query.filter(Transaction.type == type_)

        # 4. Date Range Filter
        if date_from:
            query = query.filter(Transaction.transaction_date >= date_from)
        if date_to:
            query = query.filter(Transaction.transaction_date <= date_to)

        # Total Count before pagination
        total_count = query.count()
        total_pages = ceil(total_count / page_size) if total_count > 0 else 1

        # 5. Sorting
        order_fn = desc if sort_order.lower() == "desc" else asc
        if sort_by == "amount":
            query = query.order_by(order_fn(Transaction.amount), desc(Transaction.transaction_date))
        elif sort_by == "category":
            query = query.order_by(order_fn(Transaction.category), desc(Transaction.transaction_date))
        elif sort_by == "title":
            query = query.order_by(order_fn(Transaction.title), desc(Transaction.transaction_date))
        else:  # Default to date
            query = query.order_by(order_fn(Transaction.transaction_date), order_fn(Transaction.id))

        # 6. Pagination
        safe_page = max(1, page)
        safe_page_size = max(1, min(100, page_size))
        offset = (safe_page - 1) * safe_page_size
        items = query.offset(offset).limit(safe_page_size).all()

        return items, total_count, total_pages

    @staticmethod
    def get_transaction_by_id(db: Session, transaction_id: int, user_id: int) -> Transaction:
        """Fetch a single transaction ensuring ownership (prevents IDOR)."""
        tx = db.query(Transaction).filter(
            Transaction.id == transaction_id,
            Transaction.user_id == user_id
        ).first()

        if not tx:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Transaction with ID {transaction_id} not found"
            )
        return tx

    @staticmethod
    def create_transaction(db: Session, user_id: int, tx_in: TransactionCreate) -> Transaction:
        """Create a new transaction for the authenticated user."""
        tx = Transaction(
            user_id=user_id,
            type=tx_in.type,
            title=tx_in.title.strip(),
            description=tx_in.description.strip() if tx_in.description else None,
            amount=tx_in.amount,
            category=tx_in.category.strip(),
            transaction_date=tx_in.transaction_date
        )
        db.add(tx)
        db.commit()
        db.refresh(tx)
        return tx

    @classmethod
    def update_transaction(
        cls,
        db: Session,
        transaction_id: int,
        user_id: int,
        tx_update: TransactionUpdate
    ) -> Transaction:
        """Update an existing transaction owned by user."""
        tx = cls.get_transaction_by_id(db, transaction_id, user_id)

        update_data = tx_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "title" and value:
                setattr(tx, field, value.strip())
            elif field == "description" and value:
                setattr(tx, field, value.strip())
            elif field == "category" and value:
                setattr(tx, field, value.strip())
            else:
                setattr(tx, field, value)

        db.commit()
        db.refresh(tx)
        return tx

    @classmethod
    def delete_transaction(cls, db: Session, transaction_id: int, user_id: int) -> None:
        """Delete a transaction owned by user."""
        tx = cls.get_transaction_by_id(db, transaction_id, user_id)
        db.delete(tx)
        db.commit()
