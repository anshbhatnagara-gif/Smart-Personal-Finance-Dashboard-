"""Phase 3.1 — Security, Rate Limiting & Production Infrastructure Test Suite."""

import sys
import io
import json
import urllib.request
import urllib.error

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, r"c:\Smart Personal Finance Dashboard\smart-personal-finance\backend")
from app.core.config import settings

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
    url = f"{BACKEND_URL}{endpoint}" if not endpoint.startswith("http") else endpoint
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
    print("PHASE 3.1 — PRODUCTION SECURITY & VALIDATION SUITE")
    print("=================================================================\n")

    # 1. Health check
    st, body = api_call("GET", "http://127.0.0.1:8000/health")
    record("Infrastructure: GET /health returns status ok", st == 200 and body.get("status") in ["ok", "healthy"], f"status: {st}")

    # 2. OpenApi spec
    st, body = api_call("GET", "http://127.0.0.1:8000/openapi.json")
    record("Infrastructure: GET /openapi.json accessible", st == 200 and "paths" in body, f"status: {st}")

    # 3. Invalid Route 404
    st, _ = api_call("GET", "/non-existent-route")
    record("Security: Non-existent endpoint returns 404", st == 404, f"status: {st}")

    # 4. Method Not Allowed 405
    st, _ = api_call("PUT", "/auth/login", {"data": "test"})
    record("Security: Disallowed method returns 405/404", st in [404, 405], f"status: {st}")

    print("\n=================================================================")
    print(f"PHASE 3.1 SUMMARY — PASSED: {results['passed']}/{results['total']}")
    print("=================================================================\n")
    return results

if __name__ == "__main__":
    res = run()
    sys.exit(0 if res["failed"] == 0 else 1)
