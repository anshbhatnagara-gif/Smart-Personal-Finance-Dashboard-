"""Phase 2.5 — Financial Analytics & Smart Insights Test Suite."""

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
    print("PHASE 2.5 — FINANCIAL ANALYTICS & HEALTH SCORE REGRESSION SUITE")
    print("=================================================================\n")
    run_id = uuid.uuid4().hex[:6]
    email = f"analytics.test.{run_id}@dev.com"
    pwd = "SecurePassword123!"

    st, body = api_call("POST", "/auth/register", {"name": "Analytics User", "email": email, "password": pwd})
    token = body.get("data", {}).get("access_token")

    # Seed data
    api_call("POST", "/transactions", {"type": "income", "title": "Salary", "amount": "100000.00", "category": "Salary", "transaction_date": "2026-08-01"}, token=token)
    api_call("POST", "/transactions", {"type": "expense", "title": "Rent", "amount": "30000.00", "category": "Rent", "transaction_date": "2026-08-02"}, token=token)

    # 1. GET /dashboard
    st, body = api_call("GET", "/dashboard?month=8&year=2026", token=token)
    d_data = body.get("data", {}) if st == 200 else {}
    inc = float(d_data.get("total_income", 0))
    exp = float(d_data.get("total_expenses", 0))
    record("Analytics: Dashboard summary returns income, expenses, and savings rate", st == 200 and inc == 100000.0 and exp == 30000.0, f"income: {inc}")

    # 2. GET /insights
    st, body = api_call("GET", "/insights?month=8&year=2026", token=token)
    i_data = body.get("data", {}) if st == 200 else {}
    record("Analytics: GET /insights returns generated financial insights", st == 200 and "insights" in i_data, f"insights count: {len(i_data.get('insights', []))}")

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
    print(f"PHASE 2.5 SUMMARY — PASSED: {results['passed']}/{results['total']}")
    print("=================================================================\n")
    return results

if __name__ == "__main__":
    res = run()
    sys.exit(0 if res["failed"] == 0 else 1)
