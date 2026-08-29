"""Pydantic v2 schemas for the AI Financial Assistant."""

from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class ChatMessage(BaseModel):
    """Single message in conversation history."""
    role: str = Field(..., description="'user' or 'assistant'")
    content: str = Field(..., min_length=1, max_length=2000)


class AIChatRequest(BaseModel):
    """Request payload for AI assistant chat."""
    message: str = Field(..., min_length=1, max_length=1000, description="User question or financial query")
    history: Optional[List[ChatMessage]] = Field(default_factory=list, description="Recent conversation history")


class AIChatResponseData(BaseModel):
    """Structured response payload from AI assistant."""
    message: str = Field(..., description="Assistant reply message")
    provider: str = Field(..., description="Active AI provider (e.g. gemini, mock)")
    model: str = Field(..., description="Active model identifier")
    used_financial_context: bool = Field(True, description="Indicates verified user financial facts were provided to AI")

    model_config = ConfigDict(from_attributes=True)
