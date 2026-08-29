import asyncio
import sys
import os

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, "backend")

from app.core.config import settings
from app.services.ai.provider_factory import ProviderFactory
from app.services.ai.tools.handlers import FinancialToolExecutor

print(f"=== TESTING GROQ AI PROVIDER INTEGRATION ===")
print(f"Provider: {settings.AI_PROVIDER}")
print(f"Model: {settings.AI_MODEL}")

class DummyExecutor:
    def execute(self, tool_name, args):
        print(f"--> Tool executed by Groq: {tool_name} with args {args}")
        if tool_name == "get_transactions":
            return [
                {"id": 1, "title": "Salary", "amount": 85000, "type": "income", "category": "Salary"},
                {"id": 2, "title": "Rent", "amount": 22000, "type": "expense", "category": "Housing & Rent"}
            ]
        elif tool_name == "get_total_balance":
            return {"total_income": 85000, "total_expenses": 22000, "net_savings": 63000}
        return {"status": "success", "result": "sample data"}

async def main():
    provider = ProviderFactory.get_provider()
    print(f"Provider instance created: {provider.provider_name} ({provider.model_name})")

    system_instruction = "You are a professional financial assistant. Use tools when needed to answer questions."
    message = "What were my last transactions?"
    
    print(f"\nSending message: '{message}'")
    result = await provider.chat(
        system_instruction=system_instruction,
        message=message,
        history=[],
        tool_executor=DummyExecutor()
    )
    
    print("\n--- Groq Response Received ---")
    print(f"Provider: {result['provider']}")
    print(f"Model: {result['model']}")
    print(f"Tool Used: {result['tool_used']}")
    print(f"Message:\n{result['message']}")
    print("\n=== GROQ INTEGRATION VERIFIED SUCCESSFULLY! ===")

if __name__ == "__main__":
    asyncio.run(main())
