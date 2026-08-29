"""Transactions Router: Filtered retrieval, creation, updates, and deletion."""

from datetime import date
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, Path, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.transaction import TransactionType
from app.schemas.common import ResponseBase, PaginatedData
from app.schemas.transaction import (
    TransactionCreate,
    TransactionUpdate,
    TransactionResponse
)
from app.services.transaction_service import TransactionService

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.get(
    "",
    response_model=ResponseBase[PaginatedData[TransactionResponse]],
    status_code=status.HTTP_200_OK,
    summary="List Scoped Transactions"
)
async def list_transactions(
    search: Optional[str] = Query(None, description="Search keyword in title, description, or category"),
    category: Optional[str] = Query(None, description="Category filter (e.g. Food, Salary)"),
    type: Optional[TransactionType] = Query(None, description="Filter by type (income or expense)"),
    date_from: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    sort_by: str = Query("date", pattern="^(date|amount|category|title)$", description="Field to sort by"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort direction"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ResponseBase[PaginatedData[TransactionResponse]]:
    """Retrieve filtered, sorted, and paginated transactions belonging to the authenticated user."""
    items, total, total_pages = TransactionService.get_transactions(
        db=db,
        user_id=current_user.id,
        search=search,
        category=category,
        type_=type,
        date_from=date_from,
        date_to=date_to,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size
    )

    serialized_items = [TransactionResponse.model_validate(t) for t in items]
    paginated_data = PaginatedData[TransactionResponse](
        items=serialized_items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

    return ResponseBase(
        success=True,
        message=f"Retrieved {len(serialized_items)} transactions",
        data=paginated_data
    )


@router.post(
    "",
    response_model=ResponseBase[TransactionResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create New Transaction"
)
async def create_transaction(
    tx_in: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ResponseBase[TransactionResponse]:
    """Create a new transaction record associated with the authenticated user."""
    tx = TransactionService.create_transaction(db, current_user.id, tx_in)
    return ResponseBase(
        success=True,
        message="Transaction recorded successfully",
        data=TransactionResponse.model_validate(tx)
    )


@router.get(
    "/{id}",
    response_model=ResponseBase[TransactionResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Transaction by ID"
)
async def get_transaction(
    id: int = Path(..., ge=1, description="Transaction ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ResponseBase[TransactionResponse]:
    """Retrieve a single transaction ensuring ownership."""
    tx = TransactionService.get_transaction_by_id(db, id, current_user.id)
    return ResponseBase(
        success=True,
        message="Transaction retrieved",
        data=TransactionResponse.model_validate(tx)
    )


@router.put(
    "/{id}",
    response_model=ResponseBase[TransactionResponse],
    status_code=status.HTTP_200_OK,
    summary="Update Transaction"
)
async def update_transaction(
    tx_update: TransactionUpdate,
    id: int = Path(..., ge=1, description="Transaction ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ResponseBase[TransactionResponse]:
    """Update fields of an existing transaction owned by user."""
    tx = TransactionService.update_transaction(db, id, current_user.id, tx_update)
    return ResponseBase(
        success=True,
        message="Transaction updated successfully",
        data=TransactionResponse.model_validate(tx)
    )


@router.delete(
    "/{id}",
    response_model=ResponseBase[dict],
    status_code=status.HTTP_200_OK,
    summary="Delete Transaction"
)
async def delete_transaction(
    id: int = Path(..., ge=1, description="Transaction ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ResponseBase[dict]:
    """Delete a transaction owned by user."""
    TransactionService.delete_transaction(db, id, current_user.id)
    return ResponseBase(
        success=True,
        message=f"Transaction with ID {id} deleted successfully",
        data={"deleted_id": id}
    )
