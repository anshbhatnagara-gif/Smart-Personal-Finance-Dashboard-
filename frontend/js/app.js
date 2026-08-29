/**
 * ==========================================================================
 * SMART PERSONAL FINANCE DASHBOARD - CORE ENGINE & STATE MANAGEMENT
 * Pure financial calculations, centralized state store, FastAPI data synchronization,
 * theme management, and local intelligence parser.
 * ==========================================================================
 */

// --- Centralized Application State ---
const AppState = {
  user: null,
  dashboard: null,
  transactions: [],
  budgets: [],
  loading: false
};

// --- Global Event Bus & State Subscriptions ---
const StateEvents = {
  listeners: [],
  subscribe(fn) {
    this.listeners.push(fn);
  },
  notify() {
    this.listeners.forEach(fn => {
      try {
        fn();
      } catch (e) {
        console.error("State listener execution error:", e);
      }
    });
  }
};

/**
 * Load complete application data from FastAPI backend
 */
async function loadAppData() {
  AppState.loading = true;
  try {
    const [dashboardRes, txRes, budgetRes] = await Promise.all([
      apiGet("/dashboard").catch(err => {
        console.warn("Failed to load dashboard data:", err);
        return null;
      }),
      apiGet("/transactions", { page: 1, page_size: 50 }).catch(err => {
        console.warn("Failed to load transactions data:", err);
        return null;
      }),
      apiGet("/budgets").catch(err => {
        console.warn("Failed to load budgets data:", err);
        return null;
      })
    ]);

    if (dashboardRes && dashboardRes.data) {
      AppState.dashboard = dashboardRes.data;
    }
    if (txRes && txRes.data) {
      AppState.transactions = txRes.data.items || [];
    }
    if (budgetRes && budgetRes.data) {
      AppState.budgets = budgetRes.data || [];
    }

    StateEvents.notify();
  } catch (err) {
    console.error("Error loading application state:", err);
    showToast("Server Connection Issue", err.message || "Failed to synchronize financial data.", "danger");
  } finally {
    AppState.loading = false;
  }
}

/**
 * Handle User Logout
 */
function handleLogout() {
  clearAuthSession();
  AppState.user = null;
  AppState.dashboard = null;
  AppState.transactions = [];
  AppState.budgets = [];
  showToast("Signed Out", "You have been successfully signed out.", "info");
  setTimeout(() => {
    window.location.href = "login.html";
  }, 400);
}

/**
 * ==========================================================================
 * 1. PURE FINANCIAL CALCULATION FORMULAS (INR ₹)
 * Centralized business logic - Never duplicate in UI components
 * ==========================================================================
 */

/**
 * Format numerical amount to Indian Rupee (INR) representation
 * @param {number|string} amount
 * @param {boolean} includeSign
 * @returns {string} Formatted string (e.g. ₹1,25,000)
 */
function formatCurrency(amount, includeSign = false) {
  const numericAmount = Number(amount) || 0;
  const isNegative = numericAmount < 0;
  const absAmount = Math.abs(numericAmount);

  const formatted = new Intl.NumberFormat("en-IN", {
    maximumFractionDigits: 0,
    minimumFractionDigits: 0
  }).format(absAmount);

  if (includeSign) {
    return isNegative ? `-₹${formatted}` : `+₹${formatted}`;
  }
  return isNegative ? `-₹${formatted}` : `₹${formatted}`;
}

/**
 * Calculate total income for a set of transactions
 */
function calculateTotalIncome(transactions = [], monthKey = null) {
  return transactions
    .filter(tx => {
      const matchType = (tx.type || "").toLowerCase() === "income";
      if (!matchType) return false;
      if (monthKey) {
        const txDate = tx.transaction_date || tx.date || "";
        return txDate.startsWith(monthKey);
      }
      return true;
    })
    .reduce((sum, tx) => sum + (Number(tx.amount) || 0), 0);
}

/**
 * Calculate total expenses for a set of transactions
 */
function calculateTotalExpenses(transactions = [], monthKey = null) {
  return transactions
    .filter(tx => {
      const matchType = (tx.type || "").toLowerCase() === "expense";
      if (!matchType) return false;
      if (monthKey) {
        const txDate = tx.transaction_date || tx.date || "";
        return txDate.startsWith(monthKey);
      }
      return true;
    })
    .reduce((sum, tx) => sum + (Number(tx.amount) || 0), 0);
}

/**
 * Calculate net savings
 */
function calculateSavings(income, expenses) {
  return (Number(income) || 0) - (Number(expenses) || 0);
}

/**
 * Calculate savings rate percentage
 */
function calculateSavingsRate(income, expenses) {
  const inc = Number(income) || 0;
  const exp = Number(expenses) || 0;
  if (inc <= 0) return 0;
  const rate = ((inc - exp) / inc) * 100;
  return Math.max(0, Math.min(100, Math.round(rate * 10) / 10));
}

/**
 * Calculate budget usage percentage and status tag
 */
function calculateBudgetUsage(spent, budget) {
  const sp = Number(spent) || 0;
  const bg = Number(budget) || 1;
  const percentage = Math.round((sp / bg) * 100);
  const remaining = bg - sp;

  let status = "UNDER_BUDGET";
  let statusClass = "badge-emerald";
  let barClass = "under-budget";

  if (percentage > 100) {
    status = "OVER_BUDGET";
    statusClass = "badge-rose";
    barClass = "over-budget";
  } else if (percentage >= 80) {
    status = "NEAR_LIMIT";
    statusClass = "badge-amber";
    barClass = "near-limit";
  } else if (percentage >= 60) {
    status = "ON_TRACK";
    statusClass = "badge-cyan";
    barClass = "on-track";
  }

  return { percentage, remaining, status, statusClass, barClass };
}

/**
 * Compare two months and calculate percentage delta
 */
function compareMonths(current, previous) {
  const cur = Number(current) || 0;
  const prev = Number(previous) || 0;
  const delta = cur - prev;

  if (prev === 0) {
    return {
      delta,
      percentage: cur > 0 ? 100 : 0,
      isIncrease: cur >= 0,
      text: cur > 0 ? "+100%" : "0%"
    };
  }

  const pct = Math.round(((cur - prev) / prev) * 1000) / 10;
  const isIncrease = pct >= 0;
  const text = `${isIncrease ? "+" : ""}${pct}%`;

  return { delta, percentage: Math.abs(pct), isIncrease, text };
}

/**
 * Analyze transactions by category for a period
 */
function analyzeCategories(transactions = [], monthKey = null) {
  const categoryTotals = {};
  let totalExpense = 0;

  transactions
    .filter(tx => {
      if ((tx.type || "").toLowerCase() !== "expense") return false;
      if (monthKey) {
        const txDate = tx.transaction_date || tx.date || "";
        return txDate.startsWith(monthKey);
      }
      return true;
    })
    .forEach(tx => {
      const cat = tx.category || "Other";
      const amt = Number(tx.amount) || 0;
      categoryTotals[cat] = (categoryTotals[cat] || 0) + amt;
      totalExpense += amt;
    });

  const sortedCategories = Object.entries(categoryTotals)
    .map(([category, amount]) => ({
      category,
      amount,
      percentage: totalExpense > 0 ? Math.round((amount / totalExpense) * 100) : 0
    }))
    .sort((a, b) => b.amount - a.amount);

  return {
    totals: categoryTotals,
    sorted: sortedCategories,
    totalExpense,
    topCategory: sortedCategories[0] || null
  };
}

/**
 * ==========================================================================
 * 2. THEME & TOAST NOTIFICATION HELPERS
 * ==========================================================================
 */

function initTheme() {
  const savedTheme = localStorage.getItem("theme") || "dark";
  document.documentElement.setAttribute("data-theme", savedTheme);

  const toggleBtns = document.querySelectorAll(".theme-toggle-btn");
  toggleBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      const current = document.documentElement.getAttribute("data-theme") || "dark";
      const next = current === "dark" ? "light" : "dark";
      document.documentElement.setAttribute("data-theme", next);
      localStorage.setItem("theme", next);
      if (typeof updateAllCharts === "function") {
        updateAllCharts();
      }
    });
  });
}

function showToast(title, message, type = "info") {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;

  const iconSvg = type === "success" 
    ? `<svg class="toast-icon" style="color: var(--emerald);" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>`
    : type === "danger"
    ? `<svg class="toast-icon" style="color: var(--rose);" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>`
    : `<svg class="toast-icon" style="color: var(--indigo);" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>`;

  toast.innerHTML = `
    ${iconSvg}
    <div class="toast-content">
      <div class="toast-title">${escapeHtml(title)}</div>
      <div class="toast-message">${escapeHtml(message)}</div>
    </div>
  `;

  container.appendChild(toast);

  setTimeout(() => {
    toast.classList.add("fade-out");
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function getCategoryIcon(category) {
  const map = {
    Salary: "💼", Freelance: "💻", Investments: "📈", "Side Hustle": "⚡",
    Food: "🍕", Rent: "🏠", Utilities: "⚡", Shopping: "🛍️",
    Entertainment: "🎬", Health: "🩺", Travel: "✈️", Education: "📚", Other: "📦"
  };
  return map[category] || "💳";
}
