"""Provider Factory: Resolve AI Provider implementation dynamically."""

from app.core.config import settings
from app.services.ai.base_provider import BaseAIProvider
from app.services.ai.gemini_provider import GeminiProvider
from app.services.ai.mock_provider import MockAIProvider


class ProviderFactory:
    """Factory to instantiate configured AI provider instance."""

    @classmethod
    def get_provider(cls) -> BaseAIProvider:
        """Return configured BaseAIProvider instance."""
        provider_name = (settings.AI_PROVIDER or "mock").lower().strip()

        if provider_name == "gemini":
            if not settings.AI_API_KEY or settings.AI_API_KEY.strip() in ["", "your-gemini-api-key-here", "None"]:
                raise ValueError("Gemini AI provider selected but AI_API_KEY is not configured in .env.")
            return GeminiProvider(
                api_key=settings.AI_API_KEY,
                model_name=settings.AI_MODEL,
                timeout_seconds=settings.AI_TIMEOUT_SECONDS
            )
        elif provider_name == "mock":
            return MockAIProvider(model_name="mock-finance-engine-v1")
        else:
            raise ValueError(f"Unsupported AI_PROVIDER '{provider_name}'. Supported: 'gemini', 'mock'.")
