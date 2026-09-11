/**
 * ==========================================================================
 * SMART PERSONAL FINANCE DASHBOARD - CENTRALIZED API CLIENT LAYER
 * Production-ready HTTP client handling authentication, JWT tokens,
 * dynamic URL resolution, error parsing, and AI Assistant integration.
 * ==========================================================================
 */

/**
 * Known Production Backend Endpoint on Render
 */
const PRODUCTION_RENDER_BACKEND_URL = "https://smart-personal-finance-dashboard-zed3.onrender.com/api";
const LOCAL_BACKEND_URL = "http://127.0.0.1:8000/api";

/**
 * Detect runtime execution environment:
 * - 'file': Direct filesystem execution (file://)
 * - 'local': Local HTTP server (localhost, 127.0.0.1, 0.0.0.0, 192.168.x.x)
 * - 'production': Hosted web server (e.g. *.vercel.app, *.onrender.com, custom domain)
 */
function getRuntimeEnvironment() {
  if (typeof window === "undefined" || !window.location) {
    return { type: "local", isFile: false, isLocal: true, isProduction: false };
  }

  const protocol = window.location.protocol || "";
  const hostname = (window.location.hostname || "").toLowerCase();

  if (protocol === "file:") {
    return { type: "file", isFile: true, isLocal: false, isProduction: false };
  }

  if (
    hostname === "localhost" ||
    hostname === "127.0.0.1" ||
    hostname === "0.0.0.0" ||
    hostname.startsWith("192.168.") ||
    hostname.startsWith("10.") ||
    hostname.endsWith(".local")
  ) {
    return { type: "local", isFile: false, isLocal: true, isProduction: false };
  }

  return { type: "production", isFile: false, isLocal: false, isProduction: true };
}

/**
 * Normalize and sanitize custom API base URL strings
 */
function sanitizeApiUrl(url) {
  if (!url) return LOCAL_BACKEND_URL;
  let clean = url.trim().replace(/\/+$/, "");
  if (!clean.endsWith("/api")) {
    clean += "/api";
  }
  return clean;
}

/**
 * Resolve API base URL with zero ambiguity:
 * 1. window.__ENV__?.API_BASE_URL (Explicit runtime configuration injection)
 * 2. localStorage.getItem("API_BASE_URL") (Developer manual override)
 * 3. Direct File Protocol (file://):
 *    - NEVER emits "file:///api"
 *    - Defaults to local backend "http://127.0.0.1:8000/api"
 * 4. Local Web Server (e.g. http://127.0.0.1:3000):
 *    - If served directly from backend port 8000: uses same-origin "/api"
 *    - Otherwise uses "http://127.0.0.1:8000/api"
 * 5. Production (Vercel / Render / Custom Domain):
 *    - Vercel proxy rewrite: "/api" (which proxies to Render backend)
 *    - Fallback: PRODUCTION_RENDER_BACKEND_URL
 */
function resolveApiBaseUrl() {
  if (typeof window !== "undefined") {
    // 1. Explicit window.__ENV__
    if (window.__ENV__ && window.__ENV__.API_BASE_URL) {
      return sanitizeApiUrl(window.__ENV__.API_BASE_URL);
    }

    // 2. LocalStorage override
    const localOverride = localStorage.getItem("API_BASE_URL");
    if (localOverride) {
      return sanitizeApiUrl(localOverride);
    }

    const env = getRuntimeEnvironment();

    // 3. Direct File Protocol: NEVER use file:///api
    if (env.isFile) {
      return LOCAL_BACKEND_URL;
    }

    // 4. Local Web Server (e.g. port 3000, 5500, etc.)
    if (env.isLocal) {
      if (window.location.port === "8000") {
        return `${window.location.origin}/api`;
      }
      return LOCAL_BACKEND_URL;
    }

    // 5. Production (Vercel / Render / Custom Domain)
    if (window.location.protocol && window.location.protocol.startsWith("http")) {
      return `${window.location.origin}/api`;
    }

    return PRODUCTION_RENDER_BACKEND_URL;
  }

  return LOCAL_BACKEND_URL;
}

const RUNTIME_ENV = getRuntimeEnvironment();
const API_BASE_URL = resolveApiBaseUrl();
const API_MODE = "real"; // 'real' connects to FastAPI, 'mock' uses localStorage

/**
 * Generate human-friendly network error descriptions based on runtime environment
 */
function formatNetworkErrorMessage(error) {
  const env = getRuntimeEnvironment();
  if (env.isFile) {
    return "Local file mode detected (file://). Please start the local frontend server (e.g. 'python -m http.server 3000') and open http://127.0.0.1:3000/login.html, or access the live deployed dashboard.";
  }
  if (env.isLocal) {
    return `Finance backend server is unavailable at ${API_BASE_URL}. Please ensure the FastAPI backend is running (e.g. 'uv run --with-requirements requirements.txt uvicorn app.main:app --host 127.0.0.1 --port 8000').`;
  }
  return `Finance server is temporarily unreachable at ${API_BASE_URL}. If using the free tier, the backend may be waking from idle sleep. Please wait 15 seconds and try again.`;
}

/**
 * Get authentication Bearer token from localStorage
 * @returns {string|null} JWT token
 */
function getAuthToken() {
  const directToken = localStorage.getItem("authToken");
  if (directToken) return directToken;
  try {
    const user = JSON.parse(localStorage.getItem("currentUser") || "null");
    return user ? user.token || user.access_token : null;
  } catch (e) {
    return null;
  }
}

/**
 * Set active user session
 * @param {string} token - JWT access token
 * @param {Object} user - Safe user profile (no passwords)
 */
function setAuthSession(token, user) {
  if (token) {
    localStorage.setItem("authToken", token);
  }
  if (user) {
    const safeUser = {
      id: user.id,
      name: user.name,
      email: user.email,
      token: token
    };
    localStorage.setItem("currentUser", JSON.stringify(safeUser));
  }
}

/**
 * Clear user authentication session
 */
function clearAuthSession() {
  localStorage.removeItem("authToken");
  localStorage.removeItem("currentUser");
}

/**
 * Common request headers
 * @returns {Object} Request headers
 */
function getHeaders() {
  const headers = {
    "Content-Type": "application/json",
    "Accept": "application/json"
  };
  const token = getAuthToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

/**
 * Parse and format friendly error messages from FastAPI responses
 * @param {Object} errorData - Response error payload
 * @param {number} status - HTTP status code
 * @returns {string} User-friendly message
 */
function formatApiErrorMessage(errorData, status) {
  if (status === 401) {
    return "Your session has expired. Please log in again.";
  }
  if (status === 403) {
    return "Access forbidden. You do not have permission to access this resource.";
  }
  if (status === 404) {
    return (errorData && errorData.detail) || "Requested resource was not found.";
  }
  if (status === 409) {
    return (errorData && errorData.detail) || "Conflict: Record already exists.";
  }
  if (status === 422) {
    if (errorData && Array.isArray(errorData.detail)) {
      return errorData.detail.map(d => d.msg || `${d.loc ? d.loc.slice(1).join('.') : ''}: invalid`).join("; ");
    }
    return (errorData && errorData.detail) || "Validation error in request.";
  }
  if (status >= 500) {
    return "Server encountered an error. Please try again later.";
  }
  return (errorData && (errorData.detail || errorData.message)) || `Request failed with status ${status}`;
}

/**
 * Safely construct absolute API URLs for fetch
 */
function buildApiUrl(endpoint, params = {}) {
  let base = API_BASE_URL;
  if (!base.startsWith("http://") && !base.startsWith("https://")) {
    const origin = (typeof window !== "undefined" && window.location && window.location.origin) ? window.location.origin : "http://127.0.0.1:8000";
    base = `${origin}${base.startsWith("/") ? "" : "/"}${base}`;
  }
  const cleanEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
  const url = new URL(`${base}${cleanEndpoint}`);
  Object.keys(params).forEach(key => {
    if (params[key] !== undefined && params[key] !== null && params[key] !== "") {
      url.searchParams.append(key, params[key]);
    }
  });
  return url.toString();
}

/**
 * Perform a GET request to the API
 * @param {string} endpoint - API route (e.g., '/transactions')
 * @param {Object} [params] - Query parameters
 * @returns {Promise<any>} Response JSON data
 */
async function apiGet(endpoint, params = {}) {
  if (API_MODE === "mock") {
    return handleMockRequest("GET", endpoint, null, params);
  }

  const requestUrl = buildApiUrl(endpoint, params);

  try {
    const response = await fetch(requestUrl, {
      method: "GET",
      headers: getHeaders()
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      if (response.status === 401 && !window.location.pathname.includes("login.html") && !window.location.pathname.includes("register.html")) {
        clearAuthSession();
        window.location.href = "login.html";
      }
      throw new Error(formatApiErrorMessage(errorData, response.status));
    }

    return await response.json();
  } catch (error) {
    if (error.name === "TypeError" && error.message.includes("fetch")) {
      throw new Error(formatNetworkErrorMessage(error));
    }
    throw error;
  }
}

/**
 * Perform a POST request to the API
 * @param {string} endpoint - API route (e.g., '/transactions')
 * @param {Object} data - Payload body
 * @returns {Promise<any>} Response JSON data
 */
async function apiPost(endpoint, data = {}) {
  if (API_MODE === "mock") {
    return handleMockRequest("POST", endpoint, data);
  }

  const requestUrl = buildApiUrl(endpoint);

  try {
    const response = await fetch(requestUrl, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify(data)
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      if (response.status === 401 && !window.location.pathname.includes("login.html") && !window.location.pathname.includes("register.html")) {
        clearAuthSession();
        window.location.href = "login.html";
      }
      throw new Error(formatApiErrorMessage(errorData, response.status));
    }

    return await response.json();
  } catch (error) {
    if (error.name === "TypeError" && error.message.includes("fetch")) {
      throw new Error(formatNetworkErrorMessage(error));
    }
    throw error;
  }
}

/**
 * Perform a PUT request to the API
 * @param {string} endpoint - API route (e.g., '/transactions/1')
 * @param {Object} data - Update body
 * @returns {Promise<any>} Response JSON data
 */
async function apiPut(endpoint, data = {}) {
  if (API_MODE === "mock") {
    return handleMockRequest("PUT", endpoint, data);
  }

  const requestUrl = buildApiUrl(endpoint);

  try {
    const response = await fetch(requestUrl, {
      method: "PUT",
      headers: getHeaders(),
      body: JSON.stringify(data)
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      if (response.status === 401 && !window.location.pathname.includes("login.html") && !window.location.pathname.includes("register.html")) {
        clearAuthSession();
        window.location.href = "login.html";
      }
      throw new Error(formatApiErrorMessage(errorData, response.status));
    }

    return await response.json();
  } catch (error) {
    if (error.name === "TypeError" && error.message.includes("fetch")) {
      throw new Error(formatNetworkErrorMessage(error));
    }
    throw error;
  }
}

/**
 * Perform a DELETE request to the API
 * @param {string} endpoint - API route (e.g., '/transactions/1')
 * @returns {Promise<any>} Response JSON data
 */
async function apiDelete(endpoint) {
  if (API_MODE === "mock") {
    return handleMockRequest("DELETE", endpoint);
  }

  const requestUrl = buildApiUrl(endpoint);

  try {
    const response = await fetch(requestUrl, {
      method: "DELETE",
      headers: getHeaders()
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      if (response.status === 401 && !window.location.pathname.includes("login.html") && !window.location.pathname.includes("register.html")) {
        clearAuthSession();
        window.location.href = "login.html";
      }
      throw new Error(formatApiErrorMessage(errorData, response.status));
    }

    return await response.json();
  } catch (error) {
    if (error.name === "TypeError" && error.message.includes("fetch")) {
      throw new Error(formatNetworkErrorMessage(error));
    }
    throw error;
  }
}

/**
 * Perform a PATCH request to the API
 * @param {string} endpoint - API route (e.g., '/ai/goals/1')
 * @param {Object} data - Update body
 * @returns {Promise<any>} Response JSON data
 */
async function apiPatch(endpoint, data = {}) {
  if (API_MODE === "mock") {
    return handleMockRequest("PATCH", endpoint, data);
  }

  const requestUrl = buildApiUrl(endpoint);

  try {
    const response = await fetch(requestUrl, {
      method: "PATCH",
      headers: getHeaders(),
      body: JSON.stringify(data)
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      if (response.status === 401 && !window.location.pathname.includes("login.html") && !window.location.pathname.includes("register.html")) {
        clearAuthSession();
        window.location.href = "login.html";
      }
      throw new Error(formatApiErrorMessage(errorData, response.status));
    }

    return await response.json();
  } catch (error) {
    if (error.name === "TypeError" && error.message.includes("fetch")) {
      throw new Error(formatNetworkErrorMessage(error));
    }
    throw error;
  }
}

/**
 * Centralized API Client Object
 */
const financeAPI = {
  // Authentication
  register: (data) => apiPost("/auth/register", data),
  login: (data) => apiPost("/auth/login", data),
  getMe: () => apiGet("/auth/me"),
  updateMe: (data) => apiPut("/auth/me", data),
  updateProfile: (data) => apiPut("/auth/me", data),

  // Transactions
  getTransactions: (params = {}) => apiGet("/transactions", params),
  getTransaction: (id) => apiGet(`/transactions/${id}`),
  createTransaction: (data) => apiPost("/transactions", data),
  updateTransaction: (id, data) => apiPut(`/transactions/${id}`, data),
  deleteTransaction: (id) => apiDelete(`/transactions/${id}`),

  // Budgets
  getBudgets: (params = {}) => apiGet("/budgets", params),
  createBudget: (data) => apiPost("/budgets", data),
  updateBudget: (id, data) => apiPut(`/budgets/${id}`, data),
  deleteBudget: (id) => apiDelete(`/budgets/${id}`),

  // Dashboard & Insights
  getDashboard: (params = {}) => apiGet("/dashboard", params),
  getInsights: (params = {}) => apiGet("/insights", params),
  getFinanceAnalysis: (params = {}) => apiGet("/finance/analysis", params),

  // AI Assistant Endpoints
  aiChat: (message, history = []) => apiPost("/ai/chat", { message, history }),
  getAIStatus: () => apiGet("/ai/status"),
  getProactiveInsights: (params = {}) => apiGet("/ai/insights", params),

  // Phase 3.6 Financial Goals & Planning
  getGoals: () => apiGet("/ai/goals"),
  getGoal: (id) => apiGet(`/ai/goals/${id}`),
  createGoal: (data) => apiPost("/ai/goals", data),
  updateGoal: (id, data) => apiPatch(`/ai/goals/${id}`, data),
  deleteGoal: (id) => apiDelete(`/ai/goals/${id}`),
  getGoalProgress: (id) => apiGet(`/ai/goals/${id}/progress`),
  runGoalScenario: (id, data) => apiPost(`/ai/goals/${id}/scenario`, data),

  // Phase 3.7 Financial Forecasting & Risk Intelligence
  getFinancialForecast: () => apiGet("/ai/forecast"),
  getCashflowForecast: () => apiGet("/ai/forecast/cashflow"),
  getExpenseForecast: () => apiGet("/ai/forecast/expenses"),
  getIncomeForecast: () => apiGet("/ai/forecast/income"),
  getSavingsForecast: () => apiGet("/ai/forecast/savings"),
  getFinancialRisks: () => apiGet("/ai/risks"),
  getPredictiveInsights: () => apiGet("/ai/predictions"),

  // Phase 3.8 Smart Actions & Financial Automation
  getSmartActions: (refresh = false) => apiGet("/ai/actions", { refresh }),
  getAction: (id) => apiGet(`/ai/actions/${id}`),
  confirmAction: (id, note = "") => apiPost(`/ai/actions/${id}/confirm`, { note }),
  executeAction: (id, note = "") => apiPost(`/ai/actions/${id}/execute`, { note }),
  rejectAction: (id, reason = "") => apiPost(`/ai/actions/${id}/reject`, { reason }),
  getActionHistory: () => apiGet("/ai/actions/history"),

  // Phase 3.9 Financial Intelligence, Explainability & Decision Simulation
  getFinancialIntelligence: () => apiGet("/ai/intelligence"),
  getHealthScore: () => apiGet("/ai/health-score"),
  getFinancialExplanations: () => apiGet("/ai/explanations"),
  getFinancialExplanation: (type) => apiGet(`/ai/explanations/${type}`),
  runFinancialSimulation: (data) => apiPost("/ai/simulate", data),
  getSimulationExamples: () => apiGet("/ai/simulation/examples")
};

if (typeof window !== "undefined") {
  window.financeAPI = financeAPI;
  window.FinanceAPI = financeAPI;
}

/**
 * Local Storage Mock Request Handler (Preserved for offline resilience)
 */
function handleMockRequest(method, endpoint, body = null, params = {}) {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      try {
        if (endpoint.startsWith("/transactions")) {
          const transactions = JSON.parse(localStorage.getItem("finance_transactions") || "[]");
          if (method === "GET") {
            resolve({ success: true, data: { items: transactions, total: transactions.length, page: 1, page_size: 10, total_pages: 1 } });
          } else if (method === "POST") {
            const newTx = { ...body, id: Date.now(), created_at: new Date().toISOString() };
            transactions.unshift(newTx);
            localStorage.setItem("finance_transactions", JSON.stringify(transactions));
            resolve({ success: true, data: newTx });
          } else if (method === "PUT") {
            const id = parseInt(endpoint.split("/").pop(), 10);
            const index = transactions.findIndex(t => t.id === id);
            if (index !== -1) {
              transactions[index] = { ...transactions[index], ...body };
              localStorage.setItem("finance_transactions", JSON.stringify(transactions));
              resolve({ success: true, data: transactions[index] });
            } else {
              reject(new Error("Transaction not found"));
            }
          } else if (method === "DELETE") {
            const id = parseInt(endpoint.split("/").pop(), 10);
            const filtered = transactions.filter(t => t.id !== id);
            localStorage.setItem("finance_transactions", JSON.stringify(filtered));
            resolve({ success: true, data: { deleted_id: id } });
          }
        } else if (endpoint.startsWith("/budgets")) {
          const budgets = JSON.parse(localStorage.getItem("finance_budgets") || "[]");
          if (method === "GET") {
            resolve({ success: true, data: budgets });
          } else if (method === "POST") {
            const newB = { ...body, id: Date.now(), spent: 0, remaining: body.amount, percentage: 0, status: "UNDER_BUDGET" };
            budgets.push(newB);
            localStorage.setItem("finance_budgets", JSON.stringify(budgets));
            resolve({ success: true, data: newB });
          }
        } else if (endpoint.startsWith("/ai/status")) {
          resolve({
            success: true,
            data: { provider: "mock", configured: true, model: "mock-finance-engine-v1", max_history: 10 }
          });
        } else if (endpoint.startsWith("/ai/chat")) {
          resolve({
            success: true,
            data: { message: "Mock financial analysis generated successfully.", provider: "mock", model: "mock-finance-engine-v1", used_financial_context: true }
          });
        } else {
          resolve({ success: true, message: "OK" });
        }
      } catch (err) {
        reject(err);
      }
    }, 30);
  });
}

// Auto-detect and warn about direct file:// execution
if (typeof window !== "undefined") {
  window.addEventListener("DOMContentLoaded", () => {
    if (window.location && window.location.protocol === "file:") {
      console.warn(
        "[SmartFinance] Local file mode detected (file://). Direct AJAX/Fetch calls may be blocked by browser origin security. Please run 'python -m http.server 3000' in the frontend folder and open http://127.0.0.1:3000/login.html, or access the live deployed dashboard."
      );
      setTimeout(() => {
        if (typeof showToast === "function") {
          showToast(
            "Local File Mode Detected",
            "Please run the frontend with 'python -m http.server 3000' and open http://127.0.0.1:3000/login.html for full functionality.",
            "warning"
          );
        }
      }, 1000);
    }
  });
}
