"""Chat Service: Orchestrates message validation, tool binding, and AI provider execution."""

import logging
from typing import List, Dict, Any, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.schemas.ai import ChatMessage, AIChatResponseData
from app.services.ai.tools.handlers import FinancialToolExecutor
from app.services.ai.system_instructions import get_system_instruction
from app.services.ai.provider_factory import ProviderFactory

logger = logging.getLogger("uvicorn.error")


class ChatService:
    """Coordinates tool execution and AI completions for authenticated users."""

    @classmethod
    async def process_chat(
        cls,
        user_id: int,
        message: str,
        history: Optional[List[ChatMessage]],
        db: Session
    ) -> AIChatResponseData:
        """
        Process chat query with strict user isolation, tool execution, and provider invocation.
        """
        cleaned_message = (message or "").strip()
        if not cleaned_message:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Message cannot be empty."
            )

        if len(cleaned_message) > settings.MAX_MESSAGE_LENGTH:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Message exceeds maximum allowed length of {settings.MAX_MESSAGE_LENGTH} characters."
            )

        # 1. Instantiate tool executor bound exclusively to this authenticated user_id
        tool_executor = FinancialToolExecutor(user_id=user_id, db=db)

        # 2. Limit and format conversation history
        raw_history = history or []
        bounded_history = raw_history[-settings.MAX_HISTORY_MESSAGES:]
        history_dicts = [{"role": msg.role, "content": msg.content} for msg in bounded_history]

        # 3. System instruction persona
        system_instruction = get_system_instruction()

        # 4. Resolve AI provider
        try:
            provider = ProviderFactory.get_provider()
        except ValueError as exc:
            logger.warning(f"AI Provider configuration unavailable: {exc}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI service is temporarily unavailable."
            )

        # 5. Execute chat with tool calling
        try:
            result = await provider.chat(
                system_instruction=system_instruction,
                message=cleaned_message,
                history=history_dicts,
                tool_executor=tool_executor
            )

            return AIChatResponseData(
                message=result.get("message", ""),
                provider=result.get("provider", provider.provider_name),
                model=result.get("model", provider.model_name),
                used_financial_context=result.get("tool_used", True)
            )

        except HTTPException:
            raise
        except Exception as exc:
            logger.error(f"AI Chat error: {exc}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI service is temporarily unavailable."
            )
