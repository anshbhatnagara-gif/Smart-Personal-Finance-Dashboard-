# 🚀 Smart Personal Finance Dashboard

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-D71F00.svg?style=flat&logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![Chart.js](https://img.shields.io/badge/Chart.js-4.4+-FF6384.svg?style=flat&logo=chartdotjs&logoColor=white)](https://www.chartjs.org/)
[![Tests](https://img.shields.io/badge/Tests-355%20Passed%20(100%25)-brightgreen.svg)](#-test-suite--verification)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

An intelligent, full-stack personal finance application built with a **Vanilla HTML5/CSS3/JavaScript (ES6+)** frontend and a high-performance **Python FastAPI + SQLAlchemy 2.x** backend. Features a **7-Factor Financial Health Score Engine**, **Deterministic AI Explainability**, **What-If Decision Simulator**, **User-Confirmed Smart Actions Automation**, **Linear Forecasting & Risk Detection**, **Goal Tracking with Personalized AI Coaching**, and a **Context-Grounded 41-Tool AI Assistant** (supporting Google Gemini 2.5 Flash and offline mock providers).

---

## 📑 Table of Contents

- [Key Architecture & Capabilities](#-key-architecture--capabilities)
  - [1. 7-Dimension Financial Health Score Engine](#1-7-dimension-financial-health-score-engine)
  - [2. AI Explainability Engine](#2-ai-explainability-engine)
  - [3. What-If Financial Decision Simulator](#3-what-if-financial-decision-simulator)
  - [4. AI Financial Automation & Smart Actions](#4-ai-financial-automation--smart-actions)
  - [5. Forecasting & Predictive Risk Detection](#5-forecasting--predictive-risk-detection)
  - [6. Financial Goals & Personalized AI Coaching](#6-financial-goals--personalized-ai-coaching)
  - [7. 41-Tool AI Financial Assistant](#7-41-tool-ai-financial-assistant)
- [System Architecture](#-system-architecture)
- [Directory Structure](#-directory-structure)
- [API Endpoints Reference](#-api-endpoints-reference)
- [Security & Anti-Hallucination Design](#-security--anti-hallucination-design)
- [Quick Start Guide](#-quick-start-guide)
  - [Prerequisites](#prerequisites)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
- [Test Suite & Verification](#-test-suite--verification)

---

## 🌟 Key Architecture & Capabilities

### 1. 7-Dimension Financial Health Score Engine
Evaluates algorithmic financial resilience on a deterministic **0–100 score** across 7 weighted dimensions:
- **Cashflow Health (20%)**: Operating monthly surplus margin.
- **Savings Health (15%)**: Savings rate compared to benchmark 20%+ target.
- **Budget Health (15%)**: Envelope adherence and overrun penalties.
- **Goal Health (15%)**: Aggregate goal completion velocity and timeline gap.
- **Emergency Buffer (15%)**: Months of expenditure coverage against 3–6 month target.
- **Debt Health (10%)**: Debt-to-income ratio (DTI).
- **Expense Stability (10%)**: Month-over-month spending volatility.
- **Status Classification**: `EXCELLENT` (85–100), `GOOD` (70–84), `FAIR` (50–69), `POOR` (30–49), `CRITICAL` (<30), or `INSUFFICIENT_DATA`.

### 2. AI Explainability Engine
Eliminates opaque AI responses by synthesizing **6 structured explanation models** with verified database evidence citations, mathematical calculation basis, and explicit limitations:
- `WHY_THIS_HEALTH_SCORE`
- `WHY_THIS_FORECAST`
- `WHY_THIS_RISK`
- `WHY_THIS_GOAL_STATUS`
- `WHY_THIS_SMART_ACTION`
- `WHY_THIS_SUGGESTION`

### 3. What-If Financial Decision Simulator
Enables interactive hypothetical projections across **8 financial scenarios** with **zero database mutations**:
- `INCREASE_SAVINGS`: Project compound growth and runway expansion.
- `REDUCE_EXPENSES`: Trim discretionary budget allocations.
- `INCREASE_EXPENSES`: Test lifestyle inflation impacts.
- `INCOME_REDUCTION` / `INCOME_INCREASE`: Stress-test cashflow against career or salary changes.
- `GOAL_DEADLINE_CHANGE`: Adjust target completion timelines.
- `MONTHLY_CONTRIBUTION_CHANGE`: Recalculate goal velocity.
- `DEBT_PAYMENT_CHANGE`: Accelerate debt paydown.

### 4. AI Financial Automation & Smart Actions
Transforms passive recommendations into **safe, user-confirmed actions** using a strict state machine:
- Lifecycle: `PROPOSED` $\rightarrow$ `CONFIRMED` $\rightarrow$ `EXECUTED` (or `REJECTED` / `EXPIRED`).
- **Zero Autonomous Writes**: AI cannot directly modify the database without explicit user confirmation.
- **SHA-256 Tamper Detection**: Proposal payloads are cryptographically hashed to prevent modification.
- **Immutable Audit Trail**: All confirmations, executions, and rejections are permanently logged to the `action_audits` table.

### 5. Forecasting & Predictive Risk Detection
- **Deterministic Linear Regression**: Evaluates multi-month expenditure trends and predicts next month cashflow.
- **Early Overrun Warnings**: Flags category envelope overrun probabilities.
- **Multi-Risk Classifications**: Evaluates cashflow depletion risks, low savings velocity, and discretionary spikes.

### 6. Financial Goals & Personalized AI Coaching
- **Goal Management**: Scoped creation, update, progress tracking, and priority tagging (`low`, `medium`, `high`, `critical`).
- **Required Pace Calculation**: Automatically calculates monthly savings required to hit target dates.
- **AI Coaching Prompts**: Generates tailored step-by-step advice grounded in active financial records.

### 7. 41-Tool AI Financial Assistant
- **Dual Provider Support**:
  - `gemini`: Live Google Gemini 2.5 Flash with structured function calling.
  - `mock`: Deterministic offline intent matching with verified calculations.
- **Strict XML Context Pipeline**: Injects verified data using `<FINANCIAL_HEALTH_SCORE>`, `<FINANCIAL_EXPLANATIONS>`, `<SIMULATION_CONTEXT>`, `<FINANCIAL_INTELLIGENCE>`, `<FINANCIAL_CONTEXT>`, `<GOALS_PROGRESS>`, and `<SMART_ACTIONS>`.
- **Anti-Prompt Injection Guardrails**: 36 mandatory operational rules prevent prompt leaking, data hallucination, or unauthorized access.

---

## 🏛️ System Architecture

```
+-----------------------------------------------------------------------------------------------------------------------+
|                                    FASTAPI UNIFIED FINANCIAL INTELLIGENCE ARCHITECTURE                                |
+-----------------------------------------------------------------------------------------------------------------------+
|                                                                                                                       |
|  [ Frontend Dashboard UI: SVG Health Ring / 7 Breakdown Bars / What-If Simulator / Explanation Modal / AI Drawer ]    |
|         │                                                                                                             |
|         ▼ (JWT Authenticated: Strict Identity Scoped to Authenticated User)                                            |
|  [ Protected FastAPI Endpoints: /api/auth, /api/transactions, /api/budgets, /api/goals, /api/ai/* ]                   |
|         │                                                                                                             |
|         ├───────────────────────────────┬───────────────────────────────┬───────────────────────────────┐             |
|         ▼                               ▼                               ▼                               ▼             |
|  [ HealthScoreEngine ]        [ ExplanationEngine ]           [ SimulationEngine ]       [ SmartActionEngine ]        |
|  • 7 Weighted Dimensions      • 6 Explanation Types           • 8 In-Memory Scenarios    • 8 Action Types             |
|  • Deterministic Scoring      • Verified Citations            • Zero DB Mutations        • Two-Stage Confirmation     |
|  • Status Classifications     • Calculation Rationale         • Delta Projections        • SHA-256 Tamper Defense     |
|                                                                                          • Immutable Audit Trail      |
|         └───────────────────────────────┴───────────────────────────────┴───────────────────────────────┘             |
|                                                         │                                                             |
|                                                         ▼                                                             |
|                                  [ Unified AI Intelligence Engine & Tool Dispatcher ]                                 |
|                                  • 41 Registered Scoped Financial Tools                                               |
|                                  • Google Gemini 2.5 Flash / Offline Mock Provider                                    |
|                                  • 36 Mandatory System Guardrails & Prompt Defense                                    |
|                                                         │                                                             |
|                                                         ▼                                                             |
|                                       [ SQLite Database Grounding Layer ]                                             |
|                                       • Tables: User, Transaction, Budget, Goal, SmartAction, Audit                   |
|                                       • Strict User Isolation: WHERE user_id == token.user_id                         |
|                                                                                                                       |
+-----------------------------------------------------------------------------------------------------------------------+
```

---

## 📁 Directory Structure

```text
smart-personal-finance/
├── frontend/                     # Vanilla HTML5 + CSS3 + ES6 JavaScript
│   ├── index.html                # Main financial intelligence dashboard
│   ├── login.html                # User authentication portal
│   ├── register.html             # Account registration page
│   ├── css/
│   │   ├── style.css             # Glassmorphic tokens, theme variables, reset
│   │   ├── dashboard.css         # Health ring, stat cards, simulation & action UI
│   │   └── responsive.css        # Mobile, tablet & desktop media breakpoints
│   └── js/
│       ├── api.js                # Centralized FastAPI client & JWT token handling
│       ├── app.js                # AppState store & lifecycle controller
│       ├── auth.js               # Sign in, registration, strength validation
│       ├── dashboard.js          # Health score, simulations, explanations, AI drawer
│       ├── transactions.js       # Transaction CRUD, multi-filter, search, pagination
│       ├── budgets.js            # Category envelopes & live utilization tracking
│       └── charts.js             # Theme-aware Chart.js visualizers
├── backend/                      # Python 3 + FastAPI + SQLAlchemy 2.x
│   ├── app/
│   │   ├── main.py               # FastAPI entrypoint, middleware, router mount
│   │   ├── core/
│   │   │   ├── config.py         # Pydantic Settings v2 (.env management)
│   │   │   ├── database.py       # SQLAlchemy engine & session factory
│   │   │   └── security.py       # bcrypt hashing & JWT token verification
│   │   ├── models/               # SQLAlchemy 2.x mapped models
│   │   │   ├── user.py
│   │   │   ├── transaction.py
│   │   │   ├── budget.py
│   │   │   ├── goal.py
│   │   │   └── smart_action.py
│   │   ├── schemas/              # Pydantic v2 validation models
│   │   │   ├── user.py, transaction.py, budget.py, dashboard.py
│   │   │   ├── ai_goals.py, ai_planning.py, ai_forecasting.py
│   │   │   ├── ai_actions.py, ai_intelligence.py, ai.py
│   │   ├── routers/              # Protected API endpoints (/auth, /transactions, /budgets, /goals, /ai/*)
│   │   └── services/
│   │       ├── auth_service.py, transaction_service.py, budget_service.py, finance_service.py
│   │       └── ai/               # AI Subsystems & Coordinators
│   │           ├── ai_service.py, prompt_builder.py, system_instructions.py
│   │           ├── intelligence/ # HealthScoreEngine & UnifiedIntelligenceEngine
│   │           ├── explainability/ # ExplanationEngine
│   │           ├── simulation/   # SimulationEngine
│   │           ├── automation/   # SmartActionEngine & ActionExecutor
│   │           ├── forecasting/  # ForecastingEngine
│   │           ├── risk/         # RiskEngine
│   │           ├── goals/        # GoalService & GoalCalculator
│   │           ├── planning/     # PlanningEngine & ScenarioEngine
│   │           ├── insights/     # InsightEngine
│   │           └── tools/        # 41 Tool Definitions & Execution Handlers
│   ├── .env.example
│   ├── requirements.txt
│   └── README.md
└── scratch/                      # Multi-phase automated test suites
```

---

## 📡 API Endpoints Reference

### 🔐 Authentication & Profile (`/api/auth`)
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/auth/register` | Register a new user account |
| `POST` | `/api/auth/login` | Authenticate and obtain JWT access token |
| `GET` | `/api/auth/me` | Retrieve authenticated user profile |

### 💳 Transactions & Budgets (`/api/transactions`, `/api/budgets`)
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/transactions` | List user transactions (filterable by type, category, date) |
| `POST` | `/api/transactions` | Create a new income/expense transaction |
| `PUT` | `/api/transactions/{id}` | Update transaction details |
| `DELETE` | `/api/transactions/{id}` | Remove a transaction |
| `GET` | `/api/budgets` | Retrieve active monthly budget envelopes |
| `POST` | `/api/budgets` | Set or adjust category budget envelope |
| `DELETE` | `/api/budgets/{id}` | Remove budget envelope |

### 🎯 Financial Goals (`/api/goals`)
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/goals` | List financial goals with calculated progress & pace |
| `POST` | `/api/goals` | Create a financial goal |
| `PUT` | `/api/goals/{id}` | Update goal amount or target date |
| `DELETE` | `/api/goals/{id}` | Delete a goal |

### 🤖 AI Financial Intelligence & Explanations (`/api/ai/*`)
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/ai/intelligence` | Unified master intelligence aggregate payload |
| `GET` | `/api/ai/health-score` | 7-factor financial health score (0–100) & dimensions |
| `GET` | `/api/ai/explanations` | List active domain explanations |
| `GET` | `/api/ai/explanations/{type}` | Detailed explanation drill-down |
| `POST` | `/api/ai/simulate` | Execute what-if financial decision simulation |
| `GET` | `/api/ai/simulation/examples` | Retrieve preset simulation templates |
| `GET` | `/api/ai/actions` | Retrieve active Smart Action proposals |
| `POST` | `/api/ai/actions/{id}/confirm` | User confirmation for proposed action |
| `POST` | `/api/ai/actions/{id}/execute` | Execute confirmed action server-side |
| `POST` | `/api/ai/actions/{id}/reject` | Reject action proposal |
| `GET` | `/api/ai/actions/history` | Immutable audit history of actions |
| `POST` | `/api/ai/chat` | Context-grounded conversational AI assistant |
| `GET` | `/api/ai/status` | AI provider connectivity and status |

---

## 🔒 Security & Anti-Hallucination Design

1. **Strict User Isolation**: All database operations are filtered by the authenticated user's ID (`WHERE user_id == token.user_id`). Client-supplied user IDs are never trusted.
2. **Zero Secrets in AI Responses**: Passwords, hashes, JWT keys, and API tokens are completely barred from AI prompts and API outputs.
3. **Database Grounding**: The AI model has no direct database access. Facts are pre-calculated deterministically and injected via typed XML contexts.
4. **Prompt Injection Defense**: All user-provided strings (transaction titles, descriptions, notes) are sanitized and isolated to prevent prompt hijacking.
5. **No Autonomous Writes**: Write operations require explicit two-stage user confirmation (`PROPOSED` $\rightarrow$ `CONFIRMED` $\rightarrow$ `EXECUTED`).

---

## 🚀 Quick Start Guide

### Prerequisites
- **Python**: Version 3.11 or higher
- **Modern Web Browser**: Chrome, Edge, Firefox, or Safari

### Backend Setup

1. **Navigate to the backend directory:**
   ```bash
   cd backend
   ```

2. **Create and activate a virtual environment:**
   ```bash
   # Windows (PowerShell)
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1

   # macOS / Linux
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   ```bash
   cp .env.example .env
   ```
   *(Optional)*: To use Google Gemini, set `AI_PROVIDER="gemini"` and add your `AI_API_KEY="your-key"` in `.env`. By default, `AI_PROVIDER="mock"` runs fully offline with deterministic intelligence.

5. **Start the FastAPI server:**
   ```bash
   uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```
   The backend API will be available at `http://127.0.0.1:8000`. Interactive OpenAPI documentation is accessible at `http://127.0.0.1:8000/docs`.

### Frontend Setup

Simply open `frontend/index.html` in your browser, or serve it using any lightweight static server:
```bash
# Using Python's built-in HTTP server:
cd frontend
python -m http.server 3000
```
Open `http://localhost:3000` in your web browser.

---

## 🧪 Test Suite & Verification

The project includes an automated regression test suite covering all architecture phases:

```bash
# Execute the full multi-phase regression suite:
python scratch/phase_2_2_test.py
python scratch/phase_2_3_test.py
python scratch/phase_2_4_test.py
python scratch/phase_2_5_test.py
python scratch/phase_3_1_test.py
python scratch/phase_3_2_test.py
python scratch/phase_3_3_test.py
python scratch/phase_3_4_intelligence_test.py
python scratch/phase_3_5_proactive_insights_test.py
python scratch/phase_3_6_goal_planning_test.py
python scratch/phase_3_7_forecasting_risk_test.py
python scratch/phase_3_8_automation_test.py
python scratch/phase_3_9_intelligence_final_test.py
```

### Verified Multi-Phase Test Results: **355/355 Passed (100%)**
- ✅ Phase 2.2: Authentication & JWT Security (**8/8**)
- ✅ Phase 2.3: Transaction Management & Analytics (**6/6**)
- ✅ Phase 2.4: Budget Envelopes & Overrun Prediction (**4/4**)
- ✅ Phase 2.5: Financial Analytics & Health Score (**3/3**)
- ✅ Phase 3.1: Production Security & Validation (**4/4**)
- ✅ Phase 3.2: Financial Intelligence Services (**6/6**)
- ✅ Phase 3.3: AI Assistant Architecture & Tool Calling (**4/4**)
- ✅ Phase 3.4: AI Financial Intelligence & Reasoning (**23/23**)
- ✅ Phase 3.5: Proactive AI Insights & Recommendations (**30/30**)
- ✅ Phase 3.6: AI Goals, Planning & Personalized Coaching (**47/47**)
- ✅ Phase 3.7: AI Financial Forecasting & Risk Detection (**48/48**)
- ✅ Phase 3.8: AI Financial Automation & Smart Actions (**77/77**)
- ✅ Phase 3.9: AI Intelligence Finalization, Explainability & Simulation (**95/95**)

---

## 📄 License
This project is open-source and licensed under the [MIT License](LICENSE).
