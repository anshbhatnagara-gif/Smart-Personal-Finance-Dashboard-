"""AI Service: Orchestrates financial facts, prompt construction, and provider invocation."""

import logging
from typing import List, Dict, Any, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.schemas.ai import ChatMessage, AIChatResponseData
from app.services.intelligence_service import IntelligenceService
from app.services.ai.prompt_builder import PromptBuilder
from app.services.ai.provider_factory import ProviderFactory

logger = logging.getLogger(__name__)


class AIService:
    """Core coordinator for AI financial queries."""

    @classmethod
    async def chat(
        cls,
        user_id: int,
        message: str,
        history: Optional[List[ChatMessage]],
        db: Session
    ) -> AIChatResponseData:
        """
        Process user question with verified structured financial facts and return safe AI reply.
        """
        cleaned_message = (message or "").strip()
        if not cleaned_message:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Message cannot be empty."
            )

        if len(cleaned_message) > settings.MAX_MESSAGE_LENGTH:
            cleaned_message = cleaned_message[:settings.MAX_MESSAGE_LENGTH]

        # 1. Fetch verified, pre-computed structured financial facts for this user
        financial_context = IntelligenceService.get_financial_context(user_id=user_id, db=db)

        # 2. Fetch proactive insights, goals, forecasts, risks, predictions, and smart actions
        from app.services.ai.insights.insight_engine import InsightEngine
        from app.services.ai.goals.goal_service import GoalService
        from app.services.ai.planning.planning_engine import PlanningEngine
        from app.services.ai.forecasting.forecast_engine import ForecastingEngine
        from app.services.ai.risk.risk_engine import RiskEngine
        from app.services.ai.predictions.predictive_engine import PredictiveEngine
        from app.services.ai.automation.action_engine import SmartActionEngine

        try:
            insight_engine = InsightEngine(user_id=user_id, db=db)
            proactive_insights = insight_engine.generate_insights()
        except Exception:
            proactive_insights = []

        try:
            goals_progress = GoalService.get_all_goals_progress(db=db, user_id=user_id)
        except Exception:
            goals_progress = []

        try:
            planning_engine = PlanningEngine(user_id=user_id, db=db)
            coaching_ctx = planning_engine.get_coaching_context()
        except Exception:
            coaching_ctx = None

        try:
            fc_engine = ForecastingEngine(user_id=user_id, db=db)
            fc_data = fc_engine.get_full_forecast()
        except Exception:
            fc_data = None

        try:
            risk_engine = RiskEngine(user_id=user_id, db=db)
            risk_data = risk_engine.evaluate_risks()
        except Exception:
            risk_data = None

        try:
            pred_engine = PredictiveEngine(user_id=user_id, db=db)
            predictions_data = pred_engine.generate_predictions()
        except Exception:
            predictions_data = None

        try:
            act_engine = SmartActionEngine(user_id=user_id, db=db)
            smart_actions = act_engine.get_or_generate_actions()
        except Exception:
            smart_actions = None

        try:
            from app.services.ai.intelligence.health_score import HealthScoreEngine
            hlth_engine = HealthScoreEngine(user_id=user_id, db=db)
            health_data = hlth_engine.evaluate_health()
        except Exception:
            health_data = None

        try:
            from app.services.ai.explainability.explanation_engine import ExplanationEngine
            exp_engine = ExplanationEngine(user_id=user_id, db=db)
            explanations_data = exp_engine.get_explanations()
        except Exception:
            explanations_data = None

        # 3. Construct safe prompt & system instructions
        system_instruction = PromptBuilder.build_system_prompt()
        prompt = PromptBuilder.build_user_prompt(
            user_message=cleaned_message,
            context=financial_context,
            proactive_insights=proactive_insights,
            goals_progress=goals_progress,
            coaching_context=coaching_ctx,
            forecast_data=fc_data,
            risk_data=risk_data,
            predictions_data=predictions_data,
            smart_actions_data=smart_actions,
            health_data=health_data,
            explanations_data=explanations_data
        )

        # 4. Format bounded conversation history
        raw_history = history or []
        bounded_history = raw_history[-settings.MAX_HISTORY_MESSAGES:]
        history_dicts = [{"role": msg.role, "content": msg.content} for msg in bounded_history]

        # 4. Resolve AI provider
        try:
            provider = ProviderFactory.get_provider()
        except ValueError as exc:
            logger.warning(f"AI Provider configuration issue: {exc}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI service is temporarily unavailable."
            )

        # 5. Generate AI Completion
        try:
            reply_text = await provider.generate_response(
                system_instruction=system_instruction,
                prompt=prompt,
                history=history_dicts
            )
            return AIChatResponseData(
                message=reply_text,
                provider=provider.provider_name,
                model=provider.model_name,
                used_financial_context=True
            )
        except HTTPException:
            raise
        except Exception as exc:
            logger.error(f"AI Generation error: {exc}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI service is temporarily unavailable."
            )
