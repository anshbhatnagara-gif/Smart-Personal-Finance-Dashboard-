"""Phase 4: Production Smoke Test Suite.
Quickly validates core endpoints, database health, security headers, authentication,
financial calculations, AI health score, and simulations on a live deployment.
"""

import sys
import os
from datetime import datetime
import requests

TARGET_URL = os.getenv("SMOKE_TEST_TARGET_URL", "http://127.0.0.1:8000").rstrip("/")
API_URL = f"{TARGET_URL}/api"

PASSED = 0
FAILED = 0


def smoke_assert(condition: bool, name: str):
    global PASSED, FAILED
    if condition:
        PASSED += 1
        print(f"  [PASS] {PASSED:02d}. {name}")
    else:
        FAILED += 1
        print(f"  [FAIL] {name}")
        raise AssertionError(f"Smoke test failed: {name}")


def run_smoke_tests():
    print("=" * 70)
    print(f"PRODUCTION SMOKE TEST: {TARGET_URL}")
    print("=" * 70)

    # 1. Root & Health Probes
    print("\n--- 1. Probes & Security Headers ---")
    r_root = requests.get(f"{TARGET_URL}/")
    smoke_assert(r_root.status_code == 200, "Root endpoint GET / returns 200")

    r_health = requests.get(f"{TARGET_URL}/health")
    smoke_assert(r_health.status_code == 200 and r_health.json().get("database") == "connected", "Health probe GET /health returns DB connected")

    r_live = requests.get(f"{TARGET_URL}/health/live")
    smoke_assert(r_live.status_code == 200 and r_live.json().get("status") == "alive", "Liveness probe GET /health/live returns alive")

    r_ready = requests.get(f"{TARGET_URL}/health/ready")
    smoke_assert(r_ready.status_code == 200 and r_ready.json().get("status") == "ready", "Readiness probe GET /health/ready returns ready")

    headers = r_health.headers
    smoke_assert(headers.get("X-Content-Type-Options") == "nosniff", "Security header X-Content-Type-Options: nosniff")
    smoke_assert(headers.get("X-Frame-Options") == "DENY", "Security header X-Frame-Options: DENY")
    smoke_assert(headers.get("Referrer-Policy") == "strict-origin-when-cross-origin", "Security header Referrer-Policy is present")

    # 2. Authentication & Authorization
    print("\n--- 2. Auth Flow & Session Verification ---")
    ts = int(datetime.now().timestamp())
    smoke_email = f"smoke.{ts}@example.com"
    smoke_pw = "SmokeTestPass123!@#"

    r_reg = requests.post(f"{API_URL}/auth/register", json={
        "name": "Smoke User",
        "email": smoke_email,
        "password": smoke_pw
    })
    smoke_assert(r_reg.status_code in [200, 201], "User registration POST /api/auth/register succeeds")

    r_login = requests.post(f"{API_URL}/auth/login", json={
        "email": smoke_email,
        "password": smoke_pw
    })
    smoke_assert(r_login.status_code == 200, "User login POST /api/auth/login succeeds")
    token = r_login.json().get("data", {}).get("access_token")
    smoke_assert(bool(token), "JWT token received in login response")

    auth_h = {"Authorization": f"Bearer {token}"}

    r_me = requests.get(f"{API_URL}/auth/me", headers=auth_h)
    smoke_assert(r_me.status_code == 200 and r_me.json().get("data", {}).get("email") == smoke_email, "Profile retrieval GET /api/auth/me returns authenticated identity")

    # 3. Core Financial Intelligence Endpoints
    print("\n--- 3. Financial Intelligence & Simulations ---")
    r_hs = requests.get(f"{API_URL}/ai/health-score", headers=auth_h)
    smoke_assert(r_hs.status_code == 200, "Financial health score GET /api/ai/health-score returns 200")

    r_intel = requests.get(f"{API_URL}/ai/intelligence", headers=auth_h)
    smoke_assert(r_intel.status_code == 200 and "health_score" in r_intel.json().get("data", {}), "Unified intelligence GET /api/ai/intelligence returns aggregated data")

    r_sim = requests.post(f"{API_URL}/ai/simulate", headers=auth_h, json={
        "scenario": "INCREASE_SAVINGS",
        "amount": 5000.0
    })
    smoke_assert(r_sim.status_code == 200 and "impact" in r_sim.json().get("data", {}), "In-memory simulation POST /api/ai/simulate executes without mutation")

    r_chat = requests.post(f"{API_URL}/ai/chat", headers=auth_h, json={"message": "What is my current financial status?"})
    smoke_assert(r_chat.status_code == 200, "AI Assistant conversational endpoint POST /api/ai/chat returns 200")

    print("\n" + "=" * 70)
    print(f"SMOKE TEST SUMMARY: {PASSED} PASSED, {FAILED} FAILED (TOTAL {PASSED + FAILED})")
    print("=" * 70)
    return PASSED, FAILED


if __name__ == "__main__":
    passed, failed = run_smoke_tests()
    if failed > 0:
        sys.exit(1)
    sys.exit(0)
