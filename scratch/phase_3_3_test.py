"""Phase 3.3 — AI Assistant Architecture & Tool Function Calling Test Suite."""

import sys
import io
import json
import uuid
import urllib.request
import urllib.error

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, r"c:\Smart Personal Finance Dashboard\smart-personal-finance\backend")
from app.core.config import settings
from app.core.database import SessionLocal, init_db
from app.models.user import User
from app.models.transaction import Transaction
from app.models.budget import Budget
from app.services.ai.tools.definitions import FINANCIAL_TOOL_DEFINITIONS

init_db()
BACKEND_URL = "http://127.0.0.1:8000/api"

results = {"total": 0, "passed": 0, "failed": 0, "skipped": 0}

def record(name: str, passed: bool, details: str = ""):
    results["total"] += 1
    if passed:
        results["passed"] += 1
        print(f"[PASS] {name} {f'({details})' if details else ''}")
    else:
        results["failed"] += 1
        print(f"[FAIL] {name} {f'({details})' if details else ''}")

def api_call(method: str, endpoint: str, data: dict = None, token: str = None):
    url = f"{BACKEND_URL}{endpoint}"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if token: headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body_text = e.read().decode("utf-8")
        try: b_json = json.loads(body_text)
        except Exception: b_json = body_text
        return e.code, b_json
    except Exception as exc:
        return 0, str(exc)

def run():
    print("=================================================================")
    print("PHASE 3.3 — AI ASSISTANT ARCHITECTURE & TOOL CALLING SUITE")
    print("=================================================================\n")

    # 1. Tool Declarations
    record("AI Tools: Financial tools registered in tool definitions (>= 9)", len(FINANCIAL_TOOL_DEFINITIONS) >= 9, f"registered tools: {len(FINANCIAL_TOOL_DEFINITIONS)}")

    # 2. AI Status
    st, body = api_call("GET", "/ai/status")
    data = body.get("data", {}) if st == 200 else {}
    record("AI Status: GET /api/ai/status active", st == 200 and "provider" in data, f"provider: {data.get('provider')}")

    # 3. Authenticated AI Chat Execution
    run_id = uuid.uuid4().hex[:6]
    st, body = api_call("POST", "/auth/register", {"name": "AI User 3.3", "email": f"ai33.{run_id}@dev.com", "password": "Password123!"})
    token = body.get("data", {}).get("access_token")

    st, body = api_call("POST", "/ai/chat", {"message": "How am I doing financially?"}, token=token)
    msg = body.get("data", {}).get("message", "") if st == 200 else ""
    record("AI Chat: POST /api/ai/chat returns grounded response", st == 200 and len(msg) > 20, f"msg length: {len(msg)}")

    # Cleanup DB
    assert settings.ENVIRONMENT == "development"
    db = SessionLocal()
    try:
        db.query(Transaction).delete()
        db.query(Budget).delete()
        db.query(User).delete()
        db.commit()
        record("DB Cleanup: Zero records remaining", db.query(User).count() == 0, "cleaned")
    finally:
        db.close()

    print("\n=================================================================")
    print(f"PHASE 3.3 SUMMARY — PASSED: {results['passed']}/{results['total']}")
    print("=================================================================\n")
    return results

if __name__ == "__main__":
    res = run()
    sys.exit(0 if res["failed"] == 0 else 1)
