"""Phase 2.4 — Budget Envelope & Overrun Prediction Test Suite."""

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
    print("PHASE 2.4 — BUDGET ENVELOPES & OVERRUN PREDICTION SUITE")
    print("=================================================================\n")
    run_id = uuid.uuid4().hex[:6]
    email = f"budget.test.{run_id}@dev.com"
    pwd = "SecurePassword123!"

    st, body = api_call("POST", "/auth/register", {"name": "Budget User", "email": email, "password": pwd})
    token = body.get("data", {}).get("access_token")

    # 1. Create Budget Envelope
    st, body = api_call("POST", "/budgets", {"category": "Food", "amount": "20000.00", "month": 8, "year": 2026}, token=token)
    b_id = body.get("data", {}).get("id") if st == 201 else None
    record("Budgets: Create monthly category budget envelope", st == 201 and bool(b_id), f"id: {b_id}")

    # 2. Get Budget Summary
    st, body = api_call("GET", "/budgets?month=8&year=2026", token=token)
    b_items = body.get("data", []) if st == 200 and isinstance(body.get("data"), list) else []
    record("Budgets: GET /budgets returns active envelopes", st == 200 and len(b_items) == 1, f"count: {len(b_items)}")

    # 3. Add Expense to Check Utilization
    api_call("POST", "/transactions", {"type": "expense", "title": "Groceries", "amount": "15000.00", "category": "Food", "transaction_date": "2026-08-10"}, token=token)
    st, body = api_call("GET", "/budgets?month=8&year=2026", token=token)
    updated_items = body.get("data", []) if st == 200 and isinstance(body.get("data"), list) else []
    spent = updated_items[0].get("spent", 0.0) if updated_items else 0.0
    record("Budgets: Spending utilization calculated correctly (₹15,000/₹20,000)", st == 200 and float(spent) == 15000.0, f"spent: {spent}")

    # Cleanup DB
    assert settings.ENVIRONMENT == "development"
    db = SessionLocal()
    try:
        db.query(Transaction).delete()
        db.query(Budget).delete()
        db.query(User).delete()
        db.commit()
        record("DB Cleanup: Users=0, Budgets=0", db.query(User).count() == 0 and db.query(Budget).count() == 0, "cleaned")
    finally:
        db.close()

    print("\n=================================================================")
    print(f"PHASE 2.4 SUMMARY — PASSED: {results['passed']}/{results['total']}")
    print("=================================================================\n")
    return results

if __name__ == "__main__":
    res = run()
    sys.exit(0 if res["failed"] == 0 else 1)
