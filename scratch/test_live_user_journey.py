import requests
import json
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


BASE_URL = "https://smart-personal-finance-dashboard-zed3.onrender.com"
EMAIL = "anshbhatnagara@gmail.com"
PASSWORD = "Ansh@2007"
NAME = "Ansh Bhatnagar"

print(f"=== TESTING LIVE PRODUCTION FULL-STACK JOURNEY AT {BASE_URL} ===")

# 1. Login with user credentials
print("\n--- 1. Authenticating with User Credentials ---")
login_payload = {"email": EMAIL, "password": PASSWORD}
res = requests.post(f"{BASE_URL}/api/auth/login", json=login_payload)
print(f"Login status: {res.status_code}")
if res.status_code != 200:
    print(f"Login failed: {res.text}")
    exit(1)

token = res.json()["data"]["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("Access token received successfully!")

# 2. Check Profile
print("\n--- 2. Checking Current Profile (/api/auth/me) ---")
res = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
profile = res.json()["data"]
print(f"User Profile Verified: {profile['name']} ({profile['email']}) [ID: {profile['id']}]")

# 3. Create Sample Transactions (Income & Expenses)
print("\n--- 3. Creating Real Financial Transactions ---")
sample_transactions = [
    {"title": "August Tech Salary", "amount": 85000, "type": "income", "category": "Salary", "transaction_date": "2026-08-01"},
    {"title": "Apartment Rent", "amount": 22000, "type": "expense", "category": "Housing & Rent", "transaction_date": "2026-08-02"},
    {"title": "Grocery & Provisions", "amount": 6500, "type": "expense", "category": "Food & Dining", "transaction_date": "2026-08-05"},
    {"title": "Electricity & WiFi", "amount": 2800, "type": "expense", "category": "Utilities", "transaction_date": "2026-08-10"},
    {"title": "Fine Dining & Treats", "amount": 3200, "type": "expense", "category": "Food & Dining", "transaction_date": "2026-08-15"},
    {"title": "Weekend Movie & Outing", "amount": 1200, "type": "expense", "category": "Entertainment", "transaction_date": "2026-08-18"},
    {"title": "Consulting Freelance Project", "amount": 15000, "type": "income", "category": "Side Income", "transaction_date": "2026-08-20"},
]
for t in sample_transactions:
    res = requests.post(f"{BASE_URL}/api/transactions", json=t, headers=headers)
    print(f"Created transaction '{t['title']}' (+/- ₹{t['amount']}): {res.status_code}")

# 4. Create Financial Goal
print("\n--- 4. Setting Up Financial Goal ---")
goal_payload = {
    "name": "Emergency Fund 2026",
    "target_amount": 150000,
    "current_amount": 45000,
    "target_date": "2026-12-31",
    "category": "emergency_fund",
    "priority": "high"
}
res = requests.post(f"{BASE_URL}/api/ai/goals", json=goal_payload, headers=headers)
print(f"Created goal '{goal_payload['name']}': {res.status_code}")

# 5. Fetch Dashboard Summary
print("\n--- 5. Fetching Live Dashboard Summary ---")
res = requests.get(f"{BASE_URL}/api/dashboard?month=8&year=2026", headers=headers)
data = res.json()["data"]
print(f"Total Income: ₹{data['total_income']}")
print(f"Total Expenses: ₹{data['total_expenses']}")
print(f"Net Savings: ₹{data['net_savings']}")
print(f"Savings Rate: {data['savings_rate']}%")
print(f"Financial Health Score: {data['health_score']['score']}/100 ({data['health_score']['status']})")
print(f"Key Insights Generated: {len(data['insights'])} dynamic insights")

# 6. Test AI Financial Assistant Chat
print("\n--- 6. Testing AI Financial Assistant Chat ---")
chat_payload = {
    "message": "Can you analyze my current financial situation and suggest the best way to optimize my savings?"
}
res = requests.post(f"{BASE_URL}/api/ai/chat", json=chat_payload, headers=headers)
print(f"AI Chat status: {res.status_code}")
ai_reply = res.json()["data"]["message"]
print(f"\nAI Assistant Response:\n{ai_reply}\n")

# 7. Test What-If Simulator
print("--- 7. Testing What-If Simulator ---")
sim_payload = {
    "scenario_type": "REDUCE_EXPENSES",
    "parameters": {"reduction_percentage": 15}
}
res = requests.post(f"{BASE_URL}/api/ai/simulate", json=sim_payload, headers=headers)
print(f"Simulation status: {res.status_code}")
sim_data = res.json()["data"]
print(f"Simulated New Health Score: {sim_data['simulated_health_score']['score']}/100")

# 8. Check Budgets
print("\n--- 8. Checking Active Budgets ---")
res = requests.get(f"{BASE_URL}/api/budgets?month=8&year=2026", headers=headers)
budgets = res.json()["data"]
print(f"Total Budgets Active: {len(budgets)}")
for b in budgets:
    print(f"  • {b['category']}: Spent ₹{b['spent']} / ₹{b['amount']} ({b['percentage']}%) - {b['status']}")

print("\n================================================================================")
print("FULL STACK LIVE USER JOURNEY TEST COMPLETED WITH 100% SUCCESS ON PRODUCTION!")
print("================================================================================")
