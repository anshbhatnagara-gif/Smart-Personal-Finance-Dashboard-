"""AI Services package exporting ChatService, BaseAIProvider, ProviderFactory, and tools."""

from app.services.ai.base_provider import BaseAIProvider
from app.services.ai.gemini_provider import GeminiProvider
from app.services.ai.mock_provider import MockAIProvider
from app.services.ai.provider_factory import ProviderFactory
from app.services.ai.chat_service import ChatService
from app.services.ai.system_instructions import get_system_instruction
from app.services.ai.tools import FINANCIAL_TOOL_DEFINITIONS, FinancialToolExecutor

__all__ = [
    "BaseAIProvider",
    "GeminiProvider",
    "MockAIProvider",
    "ProviderFactory",
    "ChatService",
    "get_system_instruction",
    "FINANCIAL_TOOL_DEFINITIONS",
    "FinancialToolExecutor"
]
