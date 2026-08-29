# Smart Personal Finance Dashboard Backend

Production-ready, deterministic Python backend built with **FastAPI**, **SQLAlchemy 2.x**, **Pydantic v2**, and a **Real AI Financial Assistant** powered by Google Gemini and a deterministic mock provider.

---

## 🚀 Key APIs

### 1. Authentication (`/api/auth`)
- `POST /api/auth/register` — Register new user & issue JWT.
- `POST /api/auth/login` — Authenticate credentials & issue JWT.
- `GET /api/auth/me` — Verify active token and fetch safe profile data.

### 2. Transactions (`/api/transactions`)
- `GET /api/transactions` — Scoped, paginated, searchable, multi-criteria filtered list.
- `POST /api/transactions` — Record new income or expense with Decimal precision.
- `GET /api/transactions/{id}` — Retrieve single transaction.
- `PUT /api/transactions/{id}` — Update existing transaction.
- `DELETE /api/transactions/{id}` — Delete transaction.

### 3. Budgets (`/api/budgets`)
- `GET /api/budgets` — List user envelopes with real-time calculated `spent`, `remaining`, `percentage`, and status (`UNDER_BUDGET`, `ON_TRACK`, `NEAR_LIMIT`, `OVER_BUDGET`).
- `POST /api/budgets` — Create new envelope with unique constraint per period.
- `PUT /api/budgets/{id}` — Adjust envelope limit.
- `DELETE /api/budgets/{id}` — Remove envelope.

### 4. Financial Intelligence Engine (`/api/insights` & `/api/finance/analysis`)
- `GET /api/insights` — Comprehensive intelligence report including category behavior, anomalies, budget risk velocity predictions, savings opportunities, and explainable health score.
- `GET /api/insights/ai-context` — Verified structured financial facts prepared for future LLM integration.
- `GET /api/finance/analysis` — Complete financial analytics report with multi-month cashflow forecasting.

### 5. Real AI Financial Assistant (`/api/ai/chat`)
- `POST /api/ai/chat` — Context-grounded, prompt-injection protected personal finance conversational assistant.
  - **Request**: `{"message": "What is my highest expense?", "history": [...]}`
  - **Response**: `{"success": true, "data": {"message": "...", "provider": "gemini", "model": "gemini-2.5-flash", "used_financial_context": true}}`

---

## 🤖 AI Provider Architecture & Security

```text
Authenticated Request (JWT)
        ↓
Strict User Isolation (current_user.id)
        ↓
Intelligence Layer: get_financial_context(user_id)
        ↓
Verified Structured Financial Facts
        ↓
Prompt Builder (Injection Defense & Delimiters)
        ↓
AI Provider (Gemini / Mock via ProviderFactory)
        ↓
Sanitized, Grounded Assistant Response
```

### Safety & Privacy Guardrails
1. **Zero Database Access for AI**: The AI model never receives direct database connection or credentials. It only receives verified, pre-computed facts.
2. **Prompt Injection Resistance**: All user queries and transaction descriptions are treated strictly as untrusted data strings. Commands like *"ignore previous instructions"* are neutralized.
3. **No Hallucinated Numbers**: Numerical outputs originate from verified Phase 2.4 calculations.
4. **Provider-Independent Factory**: Supports Google Gemini via `google-genai` SDK and a deterministic `MockAIProvider` for test automation.

---

## ⚙️ AI Configuration (`.env`)

```env
# AI Provider Configuration ('gemini' or 'mock')
AI_PROVIDER="mock"
AI_API_KEY="your-gemini-api-key-here"
AI_MODEL="gemini-2.5-flash"
MAX_HISTORY_MESSAGES=10
MAX_MESSAGE_LENGTH=1000
AI_TIMEOUT_SECONDS=30
```

---

## 🧪 Automated Testing
```bash
# Phase 2.5 AI Assistant Test Suite
uv run python scratch/phase_2_5_ai_test.py
# 19/19 Passed (1 Skipped if no live API key)

# Phase 2.4 Intelligence Engine Suite
uv run python scratch/phase_2_4_intelligence_test.py
# 28/28 Passed

# Phase 2.4 Core Analytics Engine Suite
uv run python scratch/phase_2_4_test.py
# 38/38 Passed

# Phase 2.3 Integration Audit
uv run python scratch/phase_2_3_e2e_test.py
# 33/33 Passed

# Phase 2.2 Backend Core Suite
uv run python scratch/phase_2_2_test.py
# 48/48 Passed
```
