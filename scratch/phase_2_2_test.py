"""Phase 2.2 — Authentication & JWT Security Test Suite."""

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
    print("PHASE 2.2 — AUTHENTICATION & JWT SECURITY REGRESSION SUITE")
    print("=================================================================\n")
    run_id = uuid.uuid4().hex[:6]
    email = f"auth.test.{run_id}@dev.com"
    pwd = "SecurePassword123!"

    # 1. User Registration
    st, body = api_call("POST", "/auth/register", {"name": "Test User", "email": email, "password": pwd})
    token = body.get("data", {}).get("access_token") if st == 201 else None
    record("Auth: Register new user", st == 201 and bool(token), f"status: {st}")

    # 2. Duplicate Registration Rejection
    st, _ = api_call("POST", "/auth/register", {"name": "Dup User", "email": email, "password": pwd})
    record("Auth: Duplicate email registration rejected (400)", st == 400, f"status: {st}")

    # 3. User Login
    st, body = api_call("POST", "/auth/login", {"email": email, "password": pwd})
    login_token = body.get("data", {}).get("access_token") if st == 200 else None
    record("Auth: Login with valid credentials", st == 200 and bool(login_token), f"status: {st}")

    # 4. Invalid Login Rejection
    st, _ = api_call("POST", "/auth/login", {"email": email, "password": "WrongPassword!"})
    record("Auth: Login with invalid password rejected (401)", st == 401, f"status: {st}")

    # 5. Protected Endpoint Access with Valid Token
    st, body = api_call("GET", "/auth/me", token=token)
    u_data = body.get("data", {}) if st == 200 else {}
    record("Auth: GET /auth/me returns authenticated profile", st == 200 and u_data.get("email") == email, f"email: {u_data.get('email')}")
    record("Security: Password hash not exposed in user profile", "password_hash" not in str(u_data), "zero secret leak")

    # 6. Unauthenticated Access Rejection
    st, _ = api_call("GET", "/auth/me")
    record("Auth: GET /auth/me without token rejected (401)", st == 401, f"status: {st}")

    # Cleanup DB
    assert settings.ENVIRONMENT == "development"
    db = SessionLocal()
    try:
        db.query(Transaction).delete()
        db.query(Budget).delete()
        db.query(User).delete()
        db.commit()
        u_cnt = db.query(User).count()
        record("DB Cleanup: Users count = 0", u_cnt == 0, f"count: {u_cnt}")
    finally:
        db.close()

    print("\n=================================================================")
    print(f"PHASE 2.2 SUMMARY — PASSED: {results['passed']}/{results['total']}")
    print("=================================================================\n")
    return results

if __name__ == "__main__":
    res = run()
    sys.exit(0 if res["failed"] == 0 else 1)
