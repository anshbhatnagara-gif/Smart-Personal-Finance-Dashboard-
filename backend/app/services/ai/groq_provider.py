"""Groq AI Provider supporting multi-turn function calling and tools with high-throughput inference."""

import asyncio
import json
from typing import List, Dict, Any, Optional
import httpx

from app.services.ai.base_provider import BaseAIProvider
from app.services.ai.tools.handlers import FinancialToolExecutor
from app.services.ai.tools.definitions import FINANCIAL_TOOL_DEFINITIONS


def _convert_schema_to_json_schema(schema: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively convert uppercase types in definitions (e.g. OBJECT) to JSON schema lowercase (e.g. object)."""
    if not isinstance(schema, dict):
        return schema
    res = {}
    for k, v in schema.items():
        if k == "type" and isinstance(v, str):
            res[k] = v.lower()
        elif isinstance(v, dict):
            res[k] = _convert_schema_to_json_schema(v)
        elif isinstance(v, list):
            res[k] = [_convert_schema_to_json_schema(item) if isinstance(item, dict) else item for item in v]
        else:
            res[k] = v
    return res


class GroqProvider(BaseAIProvider):
    """Groq AI integration supporting function calling and low-latency reasoning."""

    GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(
        self,
        api_key: Optional[str],
        model_name: str = "openai/gpt-oss-120b",
        timeout_seconds: int = 30
    ):
        if not api_key or api_key.strip() in ["", "your-groq-api-key-here", "None"]:
            raise ValueError("AI_API_KEY is not configured for Groq provider.")

        self._api_key = api_key.strip()
        self._model_name = model_name or "openai/gpt-oss-120b"
        self._timeout = timeout_seconds
        self._tools = self._build_groq_tools()

    @property
    def provider_name(self) -> str:
        return "groq"

    @property
    def model_name(self) -> str:
        return self._model_name

    def _build_groq_tools(self) -> List[Dict[str, Any]]:
        """Convert tool declarations into OpenAI/Groq compatible tools format."""
        tools = []
        for defn in FINANCIAL_TOOL_DEFINITIONS:
            params = _convert_schema_to_json_schema(defn.get("parameters", {}))
            tools.append({
                "type": "function",
                "function": {
                    "name": defn["name"],
                    "description": defn.get("description", ""),
                    "parameters": params
                }
            })
        return tools

    async def chat(
        self,
        system_instruction: str,
        message: str,
        history: List[Dict[str, str]],
        tool_executor: FinancialToolExecutor
    ) -> Dict[str, Any]:
        """
        Execute multi-turn chat interaction with function calling and tool execution via Groq.
        """
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json"
        }

        # Format messages according to OpenAI / Groq standard
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": system_instruction}
        ]

        for msg in history:
            role = "assistant" if msg.get("role") in ["model", "assistant"] else "user"
            messages.append({"role": role, "content": msg.get("content", "")})

        messages.append({"role": "user", "content": message})

        tool_used = False

        async with httpx.AsyncClient(timeout=float(self._timeout)) as client:
            # 1. First Turn: Call Groq with available financial tools
            payload: Dict[str, Any] = {
                "model": self._model_name,
                "messages": messages,
                "temperature": 0.2,
                "max_completion_tokens": 1200
            }
            if self._tools:
                payload["tools"] = self._tools
                payload["tool_choice"] = "auto"

            try:
                response = await client.post(self.GROQ_API_URL, headers=headers, json=payload)
                if response.status_code == 429:
                    # Rate limit retry with 2.5s backoff
                    await asyncio.sleep(2.5)
                    response = await client.post(self.GROQ_API_URL, headers=headers, json=payload)

                if response.status_code != 200:
                    error_msg = response.text
                    try:
                        err_json = response.json()
                        error_msg = err_json.get("error", {}).get("message", error_msg)
                    except Exception:
                        pass
                    raise RuntimeError(f"Groq API Error ({response.status_code}): {error_msg}")

                res_data = response.json()
                choice = res_data.get("choices", [{}])[0]
                res_message = choice.get("message", {})

                # Check if Groq called any tools
                tool_calls = res_message.get("tool_calls")
                if tool_calls:
                    tool_used = True
                    # Append assistant's tool calls to message history
                    messages.append(res_message)

                    for call in tool_calls:
                        fn = call.get("function", {})
                        fn_name = fn.get("name")
                        try:
                            fn_args = json.loads(fn.get("arguments", "{}"))
                        except Exception:
                            fn_args = {}

                        # Execute the tool safely within authenticated context
                        tool_result = tool_executor.execute(fn_name, fn_args)

                        # Append tool execution result
                        messages.append({
                            "role": "tool",
                            "tool_call_id": call.get("id"),
                            "content": json.dumps(tool_result, default=str)
                        })

                    # 2. Second Turn: Let model produce grounded natural language answer
                    second_payload = {
                        "model": self._model_name,
                        "messages": messages,
                        "temperature": 0.2,
                        "max_completion_tokens": 1200
                    }
                    second_res = await client.post(self.GROQ_API_URL, headers=headers, json=second_payload)
                    if second_res.status_code == 429:
                        await asyncio.sleep(2.5)
                        second_res = await client.post(self.GROQ_API_URL, headers=headers, json=second_payload)

                    if second_res.status_code != 200:
                        raise RuntimeError(f"Groq tool response formulation failed: {second_res.text}")

                    second_data = second_res.json()
                    final_choice = second_data.get("choices", [{}])[0]
                    reply_text = final_choice.get("message", {}).get("content", "")

                else:
                    reply_text = res_message.get("content", "")

                return {
                    "message": (reply_text or "I have processed your financial request.").strip(),
                    "provider": self.provider_name,
                    "model": self.model_name,
                    "tool_used": tool_used
                }

            except httpx.TimeoutException:
                raise TimeoutError("Groq AI request timed out. Please try again.")
            except Exception as e:
                raise RuntimeError(f"Groq AI Service Error: {str(e)}")

    async def generate_response(
        self,
        system_instruction: str,
        prompt: str,
        history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """Direct text-to-text generation."""
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json"
        }
        messages: List[Dict[str, str]] = [
            {"role": "system", "content": system_instruction}
        ]
        if history:
            for msg in history:
                role = "assistant" if msg.get("role") in ["model", "assistant"] else "user"
                messages.append({"role": role, "content": msg.get("content", "")})
        messages.append({"role": "user", "content": prompt})

        async with httpx.AsyncClient(timeout=float(self._timeout)) as client:
            res = await client.post(
                self.GROQ_API_URL,
                headers=headers,
                json={
                    "model": self._model_name,
                    "messages": messages,
                    "temperature": 0.2,
                    "max_completion_tokens": 1000
                }
            )
            if res.status_code != 200:
                raise RuntimeError(f"Groq generation error: {res.text}")
            return res.json()["choices"][0]["message"]["content"].strip()
