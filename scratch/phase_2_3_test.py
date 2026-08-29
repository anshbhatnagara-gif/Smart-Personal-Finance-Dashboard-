"""Phase 2.3 — Transaction Management & Category Analytics Test Suite."""

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
    print("PHASE 2.3 — TRANSACTION MANAGEMENT & ANALYTICS REGRESSION SUITE")
    print("=================================================================\n")
    run_id = uuid.uuid4().hex[:6]
    email = f"tx.test.{run_id}@dev.com"
    pwd = "SecurePassword123!"

    st, body = api_call("POST", "/auth/register", {"name": "Tx User", "email": email, "password": pwd})
    token = body.get("data", {}).get("access_token")

    # 1. Create Income Transaction
    st, body = api_call("POST", "/transactions", {"type": "income", "title": "Base Salary", "amount": "150000.00", "category": "Salary", "transaction_date": "2026-08-01"}, token=token)
    t_id1 = body.get("data", {}).get("id") if st == 201 else None
    record("Transactions: Create income transaction", st == 201 and bool(t_id1), f"id: {t_id1}")

    # 2. Create Expense Transaction
    st, body = api_call("POST", "/transactions", {"type": "expense", "title": "Groceries", "amount": "15000.00", "category": "Food", "transaction_date": "2026-08-05"}, token=token)
    t_id2 = body.get("data", {}).get("id") if st == 201 else None
    record("Transactions: Create expense transaction", st == 201 and bool(t_id2), f"id: {t_id2}")

    # 3. Get All Transactions
    st, body = api_call("GET", "/transactions", token=token)
    txs = body.get("data", {}).get("items", []) if st == 200 else []
    record("Transactions: GET /transactions returns list", st == 200 and len(txs) == 2, f"count: {len(txs)}")

    # 4. Filter Transactions by Category
    st, body = api_call("GET", "/transactions?category=Food", token=token)
    food_txs = body.get("data", {}).get("items", []) if st == 200 else []
    record("Transactions: Category filter works", st == 200 and len(food_txs) == 1 and food_txs[0]["category"] == "Food", f"count: {len(food_txs)}")

    # 5. Delete Transaction
    st, _ = api_call("DELETE", f"/transactions/{t_id2}", token=token)
    record("Transactions: DELETE /transactions/{id} succeeds", st == 200 or st == 204, f"status: {st}")

    # Cleanup DB
    assert settings.ENVIRONMENT == "development"
    db = SessionLocal()
    try:
        db.query(Transaction).delete()
        db.query(Budget).delete()
        db.query(User).delete()
        db.commit()
        record("DB Cleanup: Users=0, Txs=0", db.query(User).count() == 0 and db.query(Transaction).count() == 0, "cleaned")
    finally:
        db.close()

    print("\n=================================================================")
    print(f"PHASE 2.3 SUMMARY — PASSED: {results['passed']}/{results['total']}")
    print("=================================================================\n")
    return results

if __name__ == "__main__":
    
    res = run()
    sys.exit(0 if res["failed"] == 0 else 1)
