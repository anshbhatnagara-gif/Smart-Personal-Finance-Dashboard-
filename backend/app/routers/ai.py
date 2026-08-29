"""AI Router: Production AI Financial Assistant, Status, and Proactive Insights endpoints."""

from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.common import ResponseBase
from app.schemas.ai import AIChatRequest, AIChatResponseData
from app.schemas.ai_insights import ProactiveInsightsResponseData, ProactiveInsightItem
from app.schemas.ai_forecasting import (
    CashflowForecastResponse,
    ExpenseForecastResponse,
    IncomeForecastResponse,
    SavingsForecastResponse,
    FinancialRiskResponse,
    PredictiveInsightsResponse,
    PredictiveInsightItem,
    FinancialRiskItem,
    FinancialStressSummary
)
from app.schemas.ai_intelligence import (
    FinancialHealthScoreResponse,
    FinancialExplanationResponse,
    FinancialExplanationItem,
    SimulationRequest,
    SimulationResponse,
    SimulationExamplesResponse,
    FinancialIntelligenceResponse
)
from app.services.ai.chat_service import ChatService
from app.services.ai.insights.insight_engine import InsightEngine
from app.services.ai.forecasting.forecast_engine import ForecastingEngine
from app.services.ai.risk.risk_engine import RiskEngine
from app.services.ai.predictions.predictive_engine import PredictiveEngine
from app.services.ai.intelligence.health_score import HealthScoreEngine
from app.services.ai.intelligence.intelligence_engine import UnifiedIntelligenceEngine
from app.services.ai.explainability.explanation_engine import ExplanationEngine
from app.services.ai.simulation.simulation_engine import SimulationEngine

router = APIRouter(prefix="/ai", tags=["AI Financial Assistant"])


@router.post(
    "/chat",
    response_model=ResponseBase[AIChatResponseData],
    status_code=status.HTTP_200_OK,
    summary="Chat with Smart Personal Finance Assistant"
)
async def chat_with_ai(
    payload: AIChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ResponseBase[AIChatResponseData]:
    """
    Execute tool-enabled natural language financial query strictly scoped to the authenticated user.
    """
    response_data = await ChatService.process_chat(
        user_id=current_user.id,
        message=payload.message,
        history=payload.history,
        db=db
    )

    return ResponseBase(
        success=True,
        message="AI response generated successfully",
        data=response_data
    )


@router.get(
    "/insights",
    response_model=ResponseBase[ProactiveInsightsResponseData],
    status_code=status.HTTP_200_OK,
    summary="Get Proactive AI Financial Insights and Alerts"
)
async def get_proactive_insights(
    month: Optional[int] = Query(None, ge=1, le=12, description="Target month (default: current month)"),
    year: Optional[int] = Query(None, ge=2000, le=2100, description="Target year (default: current year)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ResponseBase[ProactiveInsightsResponseData]:
    """
    Fetch prioritized proactive financial insights, spending alerts, and progress indicators.
    Identity is strictly derived from the authenticated JWT token.
    """
    engine = InsightEngine(user_id=current_user.id, db=db)
    raw_insights = engine.generate_insights(month=month, year=year)

    items = [ProactiveInsightItem.model_validate(i) for i in raw_insights]
    return ResponseBase(
        success=True,
        message="Proactive insights retrieved successfully",
        data=ProactiveInsightsResponseData(
            generated_at=datetime.utcnow().isoformat() + "Z",
            insights=items,
            count=len(items)
        )
    )


@router.get(
    "/status",
    response_model=ResponseBase[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="Get AI Service Configuration Status"
)
async def get_ai_status() -> ResponseBase[Dict[str, Any]]:
    """
    Return active AI provider and model metadata without exposing sensitive credentials.
    """
    has_api_key = bool(
        settings.AI_API_KEY and
        settings.AI_API_KEY.strip() not in ["", "your-gemini-api-key-here", "None"]
    )

    return ResponseBase(
        success=True,
        message="AI status retrieved successfully",
        data={
            "provider": settings.AI_PROVIDER,
            "configured": has_api_key if settings.AI_PROVIDER == "gemini" else True,
            "model": settings.AI_MODEL,
            "max_history": settings.MAX_HISTORY_MESSAGES
        }
    )


@router.get(
    "/forecast",
    response_model=ResponseBase[CashflowForecastResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Full Deterministic Cashflow Forecast"
)
async def get_financial_forecast(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ResponseBase[CashflowForecastResponse]:
    """Get synthesized next-month cashflow, category spending, budget burn, and goal timelines."""
    engine = ForecastingEngine(user_id=current_user.id, db=db)
    raw = engine.get_full_forecast()
    return ResponseBase(
        success=True,
        message="Financial forecast generated successfully",
        data=CashflowForecastResponse.model_validate(raw)
    )


@router.get(
    "/forecast/cashflow",
    response_model=ResponseBase[CashflowForecastResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Full Cashflow Forecast Outlook"
)
async def get_cashflow_forecast_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ResponseBase[CashflowForecastResponse]:
    """Alias for /forecast providing complete cashflow outlook."""
    engine = ForecastingEngine(user_id=current_user.id, db=db)
    raw = engine.get_full_forecast()
    return ResponseBase(
        success=True,
        message="Cashflow forecast generated successfully",
        data=CashflowForecastResponse.model_validate(raw)
    )


@router.get(
    "/forecast/expenses",
    response_model=ResponseBase[ExpenseForecastResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Next-Month Expense and Category Forecast"
)
async def get_expense_forecast_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ResponseBase[ExpenseForecastResponse]:
    """Get overall expense and category-specific projections."""
    engine = ForecastingEngine(user_id=current_user.id, db=db)
    raw = engine.get_expense_forecast()
    return ResponseBase(
        success=True,
        message="Expense forecast generated successfully",
        data=ExpenseForecastResponse.model_validate(raw)
    )


@router.get(
    "/forecast/income",
    response_model=ResponseBase[IncomeForecastResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Next-Month Income Forecast"
)
async def get_income_forecast_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ResponseBase[IncomeForecastResponse]:
    """Get verified next-month income projection."""
    engine = ForecastingEngine(user_id=current_user.id, db=db)
    raw = engine.get_income_forecast()
    return ResponseBase(
        success=True,
        message="Income forecast generated successfully",
        data=IncomeForecastResponse.model_validate(raw)
    )


@router.get(
    "/forecast/savings",
    response_model=ResponseBase[SavingsForecastResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Next-Month Savings and 6-Month Trajectory"
)
async def get_savings_forecast_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ResponseBase[SavingsForecastResponse]:
    """Get net savings projection, savings rate, and 6-month trajectory."""
    engine = ForecastingEngine(user_id=current_user.id, db=db)
    raw = engine.get_savings_forecast()
    return ResponseBase(
        success=True,
        message="Savings forecast generated successfully",
        data=SavingsForecastResponse.model_validate(raw)
    )


@router.get(
    "/risks",
    response_model=ResponseBase[FinancialRiskResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Deterministic Financial Risk Report"
)
async def get_financial_risks_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ResponseBase[FinancialRiskResponse]:
    """Evaluate 10 deterministic financial risk rules and return prioritized risk report."""
    engine = RiskEngine(user_id=current_user.id, db=db)
    raw = engine.evaluate_risks()
    return ResponseBase(
        success=True,
        message="Financial risk report generated successfully",
        data=FinancialRiskResponse.model_validate(raw)
    )


@router.get(
    "/predictions",
    response_model=ResponseBase[PredictiveInsightsResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Top Prioritized Predictive Insights"
)
async def get_predictions_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ResponseBase[PredictiveInsightsResponse]:
    """Synthesize forecasts and risks into top 5 predictive insights with labeled fact/forecast/risk/suggestion."""
    engine = PredictiveEngine(user_id=current_user.id, db=db)
    raw_list = engine.generate_predictions()
    items = [PredictiveInsightItem.model_validate(p) for p in raw_list]
    return ResponseBase(
        success=True,
        message="Predictive insights generated successfully",
        data=PredictiveInsightsResponse(
            insights=items,
            total_insights=len(items),
            generated_at=datetime.utcnow().isoformat() + "Z"
        )
    )


# ----------------------------------------------------------------------
# PHASE 3.9: AI FINANCIAL INTELLIGENCE, EXPLAINABILITY & SIMULATION
# ----------------------------------------------------------------------

@router.get(
    "/intelligence",
    response_model=ResponseBase[FinancialIntelligenceResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Unified Master Financial Intelligence"
)
async def get_financial_intelligence_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ResponseBase[FinancialIntelligenceResponse]:
    """Retrieve complete aggregated intelligence payload strictly scoped to authenticated user."""
    engine = UnifiedIntelligenceEngine(user_id=current_user.id, db=db)
    raw = engine.get_unified_intelligence()
    return ResponseBase(
        success=True,
        message="Unified financial intelligence generated successfully",
        data=FinancialIntelligenceResponse.model_validate(raw)
    )


@router.get(
    "/health-score",
    response_model=ResponseBase[FinancialHealthScoreResponse],
    status_code=status.HTTP_200_OK,
    summary="Get 7-Factor Financial Health Score"
)
async def get_health_score_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ResponseBase[FinancialHealthScoreResponse]:
    """Evaluate deterministic 7-factor financial health score (0-100) with transparent component explanations."""
    engine = HealthScoreEngine(user_id=current_user.id, db=db)
    raw = engine.evaluate_health()
    return ResponseBase(
        success=True,
        message="Financial health score evaluated successfully",
        data=FinancialHealthScoreResponse.model_validate(raw)
    )


@router.get(
    "/explanations",
    response_model=ResponseBase[FinancialExplanationResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Grounded AI Explanations"
)
async def get_explanations_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ResponseBase[FinancialExplanationResponse]:
    """Retrieve all structured mathematical explanations across forecasts, risks, goals, and actions."""
    engine = ExplanationEngine(user_id=current_user.id, db=db)
    raw_list = engine.get_explanations()
    items = [FinancialExplanationItem.model_validate(e) for e in raw_list]
    return ResponseBase(
        success=True,
        message="Grounded explanations retrieved successfully",
        data=FinancialExplanationResponse(
            explanations=items,
            total_count=len(items),
            as_of_date=datetime.utcnow().strftime("%Y-%m-%d")
        )
    )


@router.get(
    "/explanations/{explanation_type}",
    response_model=ResponseBase[FinancialExplanationItem],
    status_code=status.HTTP_200_OK,
    summary="Get Specific Explanation by Category"
)
async def get_explanation_by_type_endpoint(
    explanation_type: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ResponseBase[FinancialExplanationItem]:
    """Fetch structured explanation for a specific domain (e.g. WHY_THIS_HEALTH_SCORE)."""
    engine = ExplanationEngine(user_id=current_user.id, db=db)
    raw = engine.get_explanation_by_type(explanation_type)
    return ResponseBase(
        success=True,
        message=f"Explanation for '{explanation_type}' retrieved successfully",
        data=FinancialExplanationItem.model_validate(raw)
    )


@router.post(
    "/simulate",
    response_model=ResponseBase[SimulationResponse],
    status_code=status.HTTP_200_OK,
    summary="Run What-If Financial Decision Simulation"
)
async def run_simulation_endpoint(
    payload: SimulationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ResponseBase[SimulationResponse]:
    """Execute hypothetical in-memory simulation with zero database mutations."""
    engine = SimulationEngine(user_id=current_user.id, db=db)
    raw = engine.simulate(
        scenario=payload.scenario,
        amount=payload.amount,
        percentage=payload.percentage,
        months=payload.months,
        goal_id=payload.goal_id,
        category=payload.category
    )
    return ResponseBase(
        success=True,
        message="What-if financial simulation executed successfully",
        data=SimulationResponse.model_validate(raw)
    )


@router.get(
    "/simulation/examples",
    response_model=ResponseBase[SimulationExamplesResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Preset Simulation Scenarios"
)
async def get_simulation_examples_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ResponseBase[SimulationExamplesResponse]:
    """Get preset scenario templates for interactive one-click what-if simulation."""
    engine = SimulationEngine(user_id=current_user.id, db=db)
    examples = engine.get_preset_examples()
    return ResponseBase(
        success=True,
        message="Simulation preset examples retrieved successfully",
        data=SimulationExamplesResponse(
            examples=examples,
            total_count=len(examples)
        )
    )


