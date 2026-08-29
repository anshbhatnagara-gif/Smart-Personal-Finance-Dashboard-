"""Gemini AI Provider supporting function calling and tools using Google GenAI SDK."""

import asyncio
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types
from google.genai.errors import APIError

from app.services.ai.base_provider import BaseAIProvider
from app.services.ai.tools.handlers import FinancialToolExecutor
from app.services.ai.tools.definitions import FINANCIAL_TOOL_DEFINITIONS


class GeminiProvider(BaseAIProvider):
    """Google Gemini integration with multi-turn function calling."""

    def __init__(self, api_key: Optional[str], model_name: str = "gemini-2.5-flash", timeout_seconds: int = 30):
        if not api_key or api_key.strip() in ["", "your-gemini-api-key-here", "None"]:
            raise ValueError("AI_API_KEY is not configured for Gemini provider.")

        self._api_key = api_key.strip()
        self._model_name = model_name
        self._timeout = timeout_seconds
        self._client = genai.Client(api_key=self._api_key)

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def model_name(self) -> str:
        return self._model_name

    def _build_gemini_tools(self) -> List[types.Tool]:
        """Convert tool declarations into Gemini types.Tool."""
        declarations = []
        for defn in FINANCIAL_TOOL_DEFINITIONS:
            declarations.append(types.FunctionDeclaration(
                name=defn["name"],
                description=defn["description"],
                parameters=defn.get("parameters")
            ))
        return [types.Tool(function_declarations=declarations)]

    async def chat(
        self,
        system_instruction: str,
        message: str,
        history: List[Dict[str, str]],
        tool_executor: FinancialToolExecutor
    ) -> Dict[str, Any]:
        """
        Send user message to Gemini, execute requested tool if any, and return grounded response.
        """
        tools = self._build_gemini_tools()

        # Build message history
        contents: List[types.Content] = []
        for msg in history:
            role = "user" if msg.get("role") == "user" else "model"
            contents.append(types.Content(
                role=role,
                parts=[types.Part.from_text(text=msg.get("content", ""))]
            ))

        # Add current user message
        contents.append(types.Content(
            role="user",
            parts=[types.Part.from_text(text=message)]
        ))

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.2,
            max_output_tokens=1000,
            tools=tools
        )

        def _generate(current_contents):
            return self._client.models.generate_content(
                model=self._model_name,
                contents=current_contents,
                config=config
            )

        tool_used = False

        try:
            # 1. First turn: Model may return text or a function_call
            response = await asyncio.wait_for(
                asyncio.to_thread(_generate, contents),
                timeout=float(self._timeout)
            )

            # Check if Gemini requested function calling
            if response.function_calls:
                tool_used = True
                call = response.function_calls[0]
                tool_name = call.name
                tool_args = call.args or {}

                # Execute tool using the authenticated context
                tool_result = tool_executor.execute(tool_name, tool_args)

                # Append model's function call to conversation history
                contents.append(types.Content(
                    role="model",
                    parts=[types.Part.from_function_call(name=tool_name, args=tool_args)]
                ))

                # Append function response to conversation history
                contents.append(types.Content(
                    role="user",
                    parts=[types.Part.from_function_response(name=tool_name, response={"result": tool_result})]
                ))

                # 2. Second turn: Model processes tool output and produces final answer
                final_response = await asyncio.wait_for(
                    asyncio.to_thread(_generate, contents),
                    timeout=float(self._timeout)
                )

                reply_text = final_response.text or "I processed your financial data, but could not formulate a response."
            else:
                reply_text = response.text or "I processed your query."

            return {
                "message": reply_text.strip(),
                "provider": self.provider_name,
                "model": self.model_name,
                "tool_used": tool_used
            }

        except asyncio.TimeoutError:
            raise TimeoutError("Gemini AI request timed out. Please try again.")
        except APIError as e:
            raise RuntimeError(f"Gemini API Error: {e.message or 'Service error'}")
        except Exception as e:
            raise RuntimeError(f"AI Service Error: {str(e)}")
