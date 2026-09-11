"""Groq AI Provider supporting multi-turn function calling and tools with high-throughput inference."""

import asyncio
import json
import logging
from typing import List, Dict, Any, Optional
import httpx

logger = logging.getLogger(__name__)

from app.services.ai.base_provider import BaseAIProvider
from app.services.ai.tools.handlers import FinancialToolExecutor
from app.services.ai.tools.definitions import FINANCIAL_TOOL_DEFINITIONS


CORE_TOOL_NAMES = {
    "get_dashboard",
    "get_transactions",
    "get_transaction_summary",
    "get_budget_progress",
    "get_spending_alerts",
    "get_category_spending",
    "get_spending_analysis",
    "get_savings_opportunities",
    "get_financial_health",
    "get_proactive_insights",
    "get_financial_forecast",
    "get_financial_risks",
    "get_financial_goals",
    "get_smart_actions",
}


def _convert_tool_parameters(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Convert Gemini-style uppercase tool parameters into OpenAI/Groq compatible JSON schema."""
    if not isinstance(parameters, dict):
        return {}

    required_keys = set(parameters.get("required") or [])
    properties = parameters.get("properties") or {}
    converted_properties = {}

    for prop_name, prop_def in properties.items():
        if not isinstance(prop_def, dict):
            converted_properties[prop_name] = prop_def
            continue

        raw_type = (prop_def.get("type") or "string").lower()
        type_mapping = {
            "string": "string",
            "integer": "integer",
            "number": "number",
            "boolean": "boolean",
            "array": "array",
            "object": "object"
        }
        param_type = type_mapping.get(raw_type, "string")

        prop_entry: Dict[str, Any] = {
            "description": prop_def.get("description", "")
        }

        # If parameter is optional, allow null so Groq/OpenAI JSON schema validation
        # doesn't reject explicit null arguments sent by LLMs (e.g. {"month": null, "year": null})
        if prop_name not in required_keys:
            prop_entry["type"] = [param_type, "null"]
        else:
            prop_entry["type"] = param_type

        converted_properties[prop_name] = prop_entry

    return {
        "type": "object",
        "properties": converted_properties,
        "required": list(required_keys)
    }


class GroqProvider(BaseAIProvider):
    """Groq AI provider implementing high-speed inference with function calling support."""

    GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(self, api_key: str, model_name: Optional[str] = None, timeout_seconds: int = 30):
        if not api_key or not api_key.strip():
            raise ValueError("Groq API key cannot be empty.")

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
        """Convert core tool declarations into OpenAI/Groq compatible tools format."""
        tools = []
        for defn in FINANCIAL_TOOL_DEFINITIONS:
            # Filter to core financial tools to respect Groq's 8000 TPM limit
            if defn["name"] not in CORE_TOOL_NAMES:
                continue
            params = _convert_tool_parameters(defn.get("parameters", {}))
            tools.append({
                "type": "function",
                "function": {
                    "name": defn["name"],
                    "description": defn.get("description", ""),
                    "parameters": params
                }
            })
        return tools

    async def _post_with_retry(
        self,
        client: httpx.AsyncClient,
        headers: Dict[str, str],
        payload: Dict[str, Any],
        max_attempts: int = 3
    ) -> httpx.Response:
        """Send request to Groq API with smart 429 rate limit backoff and network recovery."""
        import re
        last_response = None
        for attempt in range(max_attempts):
            try:
                response = await client.post(self.GROQ_API_URL, headers=headers, json=payload)
                last_response = response
            except httpx.RequestError as net_err:
                if attempt < max_attempts - 1:
                    logger.warning(f"Groq network retryable error ({type(net_err).__name__}). Retrying in 2.0s...")
                    await asyncio.sleep(2.0)
                    continue
                raise

            if response.status_code == 429 and attempt < max_attempts - 1:
                wait_seconds = 2.0
                try:
                    err_text = response.text
                    match = re.search(r"try again in ([\d\.]+)s", err_text)
                    if match:
                        wait_seconds = float(match.group(1)) + 0.5
                except Exception:
                    pass
                logger.warning(f"Groq 429 TPM backoff: waiting {wait_seconds:.2f}s (attempt {attempt+1}/{max_attempts})")
                await asyncio.sleep(wait_seconds)
                continue

            break

        return last_response

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
        reply_text = ""

        async with httpx.AsyncClient(timeout=float(self._timeout)) as client:
            try:
                max_turns = 3
                turn = 0
                tool_used = False
                reply_text = ""

                while turn < max_turns:
                    turn += 1
                    payload: Dict[str, Any] = {
                        "model": self._model_name,
                        "messages": messages,
                        "temperature": 0.2,
                        "max_completion_tokens": 1200,
                        "tools": self._tools
                    }

                    response = await self._post_with_retry(client, headers, payload)
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
                    tool_calls = res_message.get("tool_calls")

                    if tool_calls and turn < max_turns:
                        tool_used = True
                        messages.append(res_message)

                        for call in tool_calls:
                            fn = call.get("function", {})
                            fn_name = fn.get("name")
                            try:
                                fn_args = json.loads(fn.get("arguments", "{}"))
                            except Exception:
                                fn_args = {}

                            cleaned_args = {k: v for k, v in fn_args.items() if v is not None}
                            tool_result = tool_executor.execute(fn_name, cleaned_args)

                            messages.append({
                                "role": "tool",
                                "tool_call_id": call.get("id"),
                                "content": json.dumps(tool_result, default=str)
                            })
                    else:
                        reply_text = res_message.get("content") or ""
                        if not reply_text and res_message.get("reasoning"):
                            reply_text = res_message.get("reasoning")
                        break

                if not reply_text:
                    reply_text = "I have analyzed your financial records and active metrics. Please review your dashboard insights and category envelope balances."

                return {
                    "message": reply_text.strip(),
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
