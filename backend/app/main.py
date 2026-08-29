"""Smart Personal Finance API - Main Application Entrypoint."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, Depends, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import init_db, get_db
from app.schemas.common import RootResponse, HealthResponse
from app.routers import (
    auth_router,
    transactions_router,
    budgets_router,
    dashboard_router,
    finance_router,
    insights_router,
    ai_router,
    goals_router,
    actions_router
)

logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifecycle manager: initializes database schema on startup."""
    init_db()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Production-ready FastAPI backend for Smart Personal Finance Dashboard.",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Global Production Exception Handler to prevent stack trace leaks
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all exception handler to return safe, standardized error envelopes in production."""
    logger.error(f"Unhandled Exception on {request.method} {request.url.path}: {exc}", exc_info=settings.DEBUG)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "Internal server error. Please try again later.",
            "detail": str(exc) if settings.DEBUG else None
        }
    )

# Configure Cross-Origin Resource Sharing (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers under /api prefix
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(transactions_router, prefix=settings.API_V1_STR)
app.include_router(budgets_router, prefix=settings.API_V1_STR)
app.include_router(dashboard_router, prefix=settings.API_V1_STR)
app.include_router(finance_router, prefix=settings.API_V1_STR)
app.include_router(insights_router, prefix=settings.API_V1_STR)
app.include_router(ai_router, prefix=settings.API_V1_STR)
app.include_router(goals_router, prefix=settings.API_V1_STR)
app.include_router(actions_router, prefix=settings.API_V1_STR)


@app.get(
    "/",
    response_model=RootResponse,
    tags=["General"],
    summary="API Root Status"
)
async def root() -> RootResponse:
    """Return root status verifying the API service is active."""
    return RootResponse(
        success=True,
        message="Smart Personal Finance API is running"
    )


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Service & Database Health Verification"
)
async def health_check(db: Session = Depends(get_db)) -> HealthResponse:
    """Genuinely verify database connectivity by executing a test query."""
    try:
        db.execute(text("SELECT 1"))
        return HealthResponse(
            success=True,
            status="ok",
            database="connected"
        )
    except Exception as exc:
        logger.error(f"Database health check failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "success": False,
                "status": "unhealthy",
                "database": "disconnected"
            }
        )
