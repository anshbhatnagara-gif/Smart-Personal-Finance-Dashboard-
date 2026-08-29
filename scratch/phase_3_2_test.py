"""Phase 3.2 — Backend Architecture, Services & Tool Handlers Test Suite."""

import sys
import io
import json
import uuid
from decimal import Decimal
from datetime import date

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, r"c:\Smart Personal Finance Dashboard\smart-personal-finance\backend")
from app.core.config import settings
from app.core.database import SessionLocal, init_db
from app.models.user import User
from app.models.transaction import Transaction
from app.models.budget import Budget
from app.services.intelligence_service import IntelligenceService
from app.services.ai.tools.handlers import FinancialToolExecutor

init_db()

results = {"total": 0, "passed": 0, "failed": 0, "skipped": 0}

def record(name: str, passed: bool, details: str = ""):
    results["total"] += 1
    if passed:
        results["passed"] += 1
        print(f"[PASS] {name} {f'({details})' if details else ''}")
    else:
        results["failed"] += 1
        print(f"[FAIL] {name} {f'({details})' if details else ''}")

def run():
    print("=================================================================")
    print("PHASE 3.2 — SERVICE LAYER & INTELLIGENCE ENGINE SUITE")
    print("=================================================================\n")
    db = SessionLocal()

    try:
        # Seed test user
        run_id = uuid.uuid4().hex[:6]
        user = User(name="Service Test User", email=f"svc.{run_id}@dev.com", password_hash="hash")
        db.add(user)
        db.commit()
        db.refresh(user)

        # Seed test transactions
        t1 = Transaction(user_id=user.id, type="income", title="Salary", amount=Decimal("200000.00"), category="Salary", transaction_date=date(2026, 8, 1))
        t2 = Transaction(user_id=user.id, type="expense", title="Rent", amount=Decimal("50000.00"), category="Rent", transaction_date=date(2026, 8, 2))
        t3 = Transaction(user_id=user.id, type="expense", title="Swiggy", amount=Decimal("15000.00"), category="Food", transaction_date=date(2026, 8, 5))
        db.add_all([t1, t2, t3])
        db.commit()

        # Seed budget
        b1 = Budget(user_id=user.id, category="Food", amount=Decimal("12000.00"), month=8, year=2026)
        db.add(b1)
        db.commit()

        # 1. Test Intelligence Service Cashflow Health
        status = IntelligenceService.calculate_cashflow_health(Decimal("200000.00"), Decimal("65000.00"))
        record("Intelligence: Cashflow health calculated as SURPLUS", status == "SURPLUS", f"status: {status}")

        # 2. Test Tool Executor get_transaction_summary
        executor = FinancialToolExecutor(user_id=user.id, db=db)
        summary = executor.get_transaction_summary(8, 2026)
        record("Tools: get_transaction_summary calculates income=200k, exp=65k, savings=135k", summary["total_income"] == 200000.0 and summary["total_expenses"] == 65000.0 and summary["net_savings"] == 135000.0, f"summary: {summary}")

        # 3. Test Tool Executor get_budget_progress (Overrun Risk)
        b_prog = executor.get_budget_progress(8, 2026)
        food_b = [b for b in b_prog["budgets"] if b["category"] == "Food"][0]
        record("Tools: get_budget_progress identifies Food budget overspend (₹15,000/₹12,000)", food_b["status"] == "OVER_BUDGET" and food_b["risk_level"] == "LIKELY_OVER_BUDGET", f"status: {food_b['status']}")

        # 4. Test Tool Executor get_financial_health
        health = executor.get_financial_health()
        record("Tools: get_financial_health returns 5 factors and score", "score" in health and len(health.get("factors", [])) == 5, f"score: {health.get('score')}")

        # 5. User Data Isolation Test
        other_user = User(name="Other User", email=f"other.{run_id}@dev.com", password_hash="hash")
        db.add(other_user)
        db.commit()
        db.refresh(other_user)
        other_executor = FinancialToolExecutor(user_id=other_user.id, db=db)
        other_summary = other_executor.get_transaction_summary(8, 2026)
        record("Security & Isolation: Tool executor returns 0 transactions for unpopulated user", other_summary["transaction_count"] == 0 and other_summary["total_income"] == 0.0, f"count: {other_summary['transaction_count']}")

    finally:
        assert settings.ENVIRONMENT == "development"
        db.query(Transaction).delete()
        db.query(Budget).delete()
        db.query(User).delete()
        db.commit()
        u_cnt = db.query(User).count()
        record("DB Cleanup: Zero records remaining", u_cnt == 0, f"count: {u_cnt}")
        db.close()

    print("\n=================================================================")
    print(f"PHASE 3.2 SUMMARY — PASSED: {results['passed']}/{results['total']}")
    print("=================================================================\n")
    return results

if __name__ == "__main__":
    res = run()
    sys.exit(0 if res["failed"] == 0 else 1)
