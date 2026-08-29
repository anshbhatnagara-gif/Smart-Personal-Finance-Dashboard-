"""Re-export GeminiProvider for backward compatibility."""

from app.services.ai.gemini_provider import GeminiProvider

GeminiAIProvider = GeminiProvider

__all__ = ["GeminiProvider", "GeminiAIProvider"]
