"""Base Provider Interface for AI Providers with Function Calling and Generation Support."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from app.services.ai.tools.handlers import FinancialToolExecutor


class BaseAIProvider(ABC):
    """Abstract interface for all AI provider adapters."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Identifier name of the provider (e.g. 'gemini', 'mock')."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Active model identifier."""
        pass

    @abstractmethod
    async def chat(
        self,
        system_instruction: str,
        message: str,
        history: List[Dict[str, str]],
        tool_executor: FinancialToolExecutor
    ) -> Dict[str, Any]:
        """
        Execute chat interaction with function calling and tool execution.
        """
        raise NotImplementedError

    async def generate_response(
        self,
        system_instruction: str,
        prompt: str,
        history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Direct text-to-text generation for backward compatibility with Phase 2.5 prompt pipeline.
        """
        raise NotImplementedError
