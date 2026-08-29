"""Common Pydantic v2 schemas for standard API responses, pagination, and health checks."""

from typing import Generic, Optional, TypeVar, List, Any
from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class ResponseBase(BaseModel, Generic[T]):
    """Standard generic API response envelope."""
    success: bool = True
    message: Optional[str] = None
    data: Optional[T] = None

    model_config = ConfigDict(from_attributes=True)


class PaginatedData(BaseModel, Generic[T]):
    """Pagination envelope for data collections."""
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int

    model_config = ConfigDict(from_attributes=True)


class PaginatedResponse(ResponseBase[PaginatedData[T]], Generic[T]):
    """API Response containing paginated items."""
    pass


class RootResponse(BaseModel):
    """Response model for API root endpoint."""
    success: bool = True
    message: str = "Smart Personal Finance API is running"


class HealthResponse(BaseModel):
    """Response model for service and database health check."""
    success: bool = True
    status: str = "ok"
    database: str = "connected"
    details: Optional[dict[str, Any]] = None
