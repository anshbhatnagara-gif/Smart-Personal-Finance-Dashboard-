/**
 * ==========================================================================
 * SMART PERSONAL FINANCE DASHBOARD - MAIN DASHBOARD CONTROLLER
 * Real FastAPI metrics rendering, health score ring, dynamic insights,
 * AI drawer controller, and navigation views
 * ==========================================================================
 */

document.addEventListener("DOMContentLoaded", () => {
  initApp();
});

/**
 * Main application orchestrator
 */
async function initApp() {
  // 1. Verify authentication & session validity
  const isAuthenticated = await checkAuthProtection();
  if (!isAuthenticated) return;

  // 2. Initialize Design System & Theme
  initTheme();

  // 3. Initialize dynamic header greetings
  updateGreetingAndDate();

  // 4. Initialize Navigation View Switcher & Logout
  initNavigation();
  setupLogoutButtons();

  // 5. Initialize Sub-modules
  if (typeof initTransactions === "function") initTransactions();
  if (typeof initBudgets === "function") initBudgets();
  if (typeof initCharts === "function") initCharts();
  if (typeof initAiAssistant === "function") initAiAssistant();

  // 6. Subscribe to global State Events
  StateEvents.subscribe(() => {
    renderDashboardOverview();
    if (typeof updateAllCharts === "function") {
      updateAllCharts();
    }
  });

  // 7. Load real backend data from FastAPI
  await loadAppData();

  // 8. Mobile Sidebar handling
  setupMobileSidebar();
}

/**
 * Route protection: Verify JWT token with FastAPI /api/auth/me
 * @returns {Promise<boolean>} Whether user is valid and authenticated
 */
async function checkAuthProtection() {
  const isAuthPage = window.location.pathname.includes("login.html") || window.location.pathname.includes("register.html");
  if (isAuthPage) return true;

  const token = getAuthToken();
  if (!token) {
    window.location.href = "login.html";
    return false;
  }

  try {
    const res = await apiGet("/auth/me");
    if (res && res.data) {
      AppState.user = res.data;
      updateUserProfileUI(res.data);
      return true;
    }
    throw new Error("Could not load user profile");
  } catch (err) {
    console.warn("Session expired or invalid:", err);
    clearAuthSession();
    window.location.href = "login.html";
    return false;
  }
}

/**
 * Update user avatar, name, and email in sidebar and headers
 */
function updateUserProfileUI(user) {
  if (!user) return;
  const nameEls = document.querySelectorAll(".user-profile-name");
  const emailEls = document.querySelectorAll(".user-profile-email");
  const avatarEls = document.querySelectorAll(".user-avatar-initials");

  nameEls.forEach(el => el.textContent = user.name || "User");
  emailEls.forEach(el => el.textContent = user.email || "");
  avatarEls.forEach(el => el.textContent = (user.name || "U").charAt(0).toUpperCase());
}

/**
 * Update dynamic greeting based on hour of day
 */
function updateGreetingAndDate() {
  const greetingEl = document.getElementById("header-greeting-title");
  const dateEl = document.getElementById("header-current-date");
  const user = AppState.user || JSON.parse(localStorage.getItem("currentUser") || "{}");
  const userName = user.name || "there";

  const hour = new Date().getHours();
  let greeting = "Good Morning";
  if (hour >= 12 && hour < 17) greeting = "Good Afternoon";
  else if (hour >= 17 && hour < 21) greeting = "Good Evening";
  else if (hour >= 21 || hour < 5) greeting = "Good Night";

  if (greetingEl) {
    greetingEl.textContent = `${greeting}, ${userName} 👋`;
  }

  if (dateEl) {
    const options = { weekday: "short", day: "numeric", month: "short", year: "numeric" };
    dateEl.textContent = new Date().toLocaleDateString("en-IN", options);
  }
}

/**
 * View navigation switcher
 */
function initNavigation() {
  const navItems = document.querySelectorAll(".nav-item[data-view]");
  const viewSections = document.querySelectorAll(".view-section");

  navItems.forEach(item => {
    item.addEventListener("click", (e) => {
      e.preventDefault();
      const targetView = item.getAttribute("data-view");

      navItems.forEach(n => n.classList.remove("active"));
      item.classList.add("active");

      viewSections.forEach(section => {
        if (section.id === `view-${targetView}`) {
          section.classList.add("active");
        } else {
          section.classList.remove("active");
        }
      });

      closeMobileSidebar();
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  });
}

/**
 * Wire logout buttons across the interface
 */
function setupLogoutButtons() {
  const logoutBtns = document.querySelectorAll(".btn-logout, #btn-logout-sidebar, #btn-logout-profile");
  logoutBtns.forEach(btn => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      handleLogout();
    });
  });
}

/**
 * Render Financial Summary Cards, Health Score, and Smart Insights
 */
function renderDashboardOverview() {
  const d = AppState.dashboard;
  if (!d) return;

  // 1. Update Financial Summary Stat Cards
  const incomeValEl = document.getElementById("stat-income-val");
  const incomeTrendEl = document.getElementById("stat-income-trend");
  if (incomeValEl) incomeValEl.textContent = formatCurrency(d.total_income);
  if (incomeTrendEl && d.income_comparison) {
    incomeTrendEl.innerHTML = `
      <span class="${d.income_comparison.is_increase ? 'trend-up' : 'trend-down'}">${d.income_comparison.text}</span>
      <span style="color: var(--text-muted);">vs last month</span>
    `;
  }

  const expenseValEl = document.getElementById("stat-expense-val");
  const expenseTrendEl = document.getElementById("stat-expense-trend");
  if (expenseValEl) expenseValEl.textContent = formatCurrency(d.total_expenses);
  if (expenseTrendEl && d.expense_comparison) {
    expenseTrendEl.innerHTML = `
      <span class="${d.expense_comparison.is_increase ? 'trend-down' : 'trend-up'}">${d.expense_comparison.text}</span>
      <span style="color: var(--text-muted);">vs last month</span>
    `;
  }

  const savingsValEl = document.getElementById("stat-savings-val");
  const savingsTrendEl = document.getElementById("stat-savings-trend");
  if (savingsValEl) savingsValEl.textContent = formatCurrency(d.net_savings);
  if (savingsTrendEl && d.savings_comparison) {
    savingsTrendEl.innerHTML = `
      <span class="${d.savings_comparison.is_increase ? 'trend-up' : 'trend-down'}">${d.savings_comparison.text}</span>
      <span style="color: var(--text-muted);">vs last month</span>
    `;
  }

  const rateValEl = document.getElementById("stat-rate-val");
  const rateBarEl = document.getElementById("stat-rate-bar");
  if (rateValEl) rateValEl.textContent = `${d.savings_rate}%`;
  if (rateBarEl) rateBarEl.style.width = `${Math.min(100, Math.max(0, d.savings_rate))}%`;

  // 2. Animated Financial Health Score Meter
  const scoreValEl = document.getElementById("health-score-value");
  const scoreStatusEl = document.getElementById("health-score-status");
  const scoreCircle = document.getElementById("health-score-circle");

  if (d.health_score) {
    const hs = d.health_score;
    if (scoreValEl) scoreValEl.textContent = hs.score;
    if (scoreStatusEl) {
      scoreStatusEl.textContent = hs.status;
      scoreStatusEl.className = `badge ${hs.status_class || 'badge-emerald'}`;
    }

    if (scoreCircle) {
      const radius = 54;
      const circumference = 2 * Math.PI * radius;
      const offset = circumference - (hs.score / 100) * circumference;
      scoreCircle.style.strokeDasharray = `${circumference} ${circumference}`;
      scoreCircle.style.strokeDashoffset = offset;

      if (hs.score >= 90) scoreCircle.style.stroke = "var(--emerald)";
      else if (hs.score >= 75) scoreCircle.style.stroke = "var(--indigo)";
      else if (hs.score >= 60) scoreCircle.style.stroke = "var(--cyan)";
      else if (hs.score >= 40) scoreCircle.style.stroke = "var(--amber)";
      else scoreCircle.style.stroke = "var(--rose)";
    }

    // Health Score Breakdown Factors
    const factorListEl = document.getElementById("health-score-factors-list");
    if (factorListEl && hs.factors) {
      factorListEl.innerHTML = hs.factors.map(f => `
        <div class="health-factor-item">
          <div style="display: flex; justify-content: space-between; font-size: 0.8125rem; margin-bottom: 0.25rem;">
            <span style="color: var(--text-secondary);">${escapeHtml(f.name)} <span style="font-size: 0.6875rem; color: var(--text-muted);">(${f.weight})</span></span>
            <strong style="color: var(--text-primary);">${f.score}/100</strong>
          </div>
          <div class="progress-bar-container" style="height: 6px;">
            <div class="progress-bar-fill" style="width: ${f.score}%; background: ${f.score >= 80 ? 'var(--emerald)' : f.score >= 60 ? 'var(--indigo)' : 'var(--amber)'};"></div>
          </div>
        </div>
      `).join("");
    }
  }

  // 3. Dynamic Smart Insights Cards
  const insightsListEl = document.getElementById("smart-insights-list");
  if (insightsListEl && d.insights) {
    if (d.insights.length === 0) {
      insightsListEl.innerHTML = `
        <div class="empty-state" style="padding: 1.5rem; text-align: center; color: var(--text-muted);">
          <div>✨ No active spending alerts. Your finances are in great shape!</div>
        </div>
      `;
    } else {
      insightsListEl.innerHTML = d.insights.map(item => `
        <div class="insight-card insight-${item.type || 'info'}">
          <div class="insight-icon">${item.icon || '💡'}</div>
          <div class="insight-content">
            <div class="insight-tag">${escapeHtml(item.tag || 'Smart Tip')}</div>
            <div class="insight-text">${item.text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')}</div>
          </div>
        </div>
      `).join("");
    }
  }

  // 4. Quick Highlights: Top Expense & Active Budgets
  const topExpenseCard = document.getElementById("highlight-top-expense");
  if (topExpenseCard && d.category_breakdown && d.category_breakdown.length > 0) {
    const topCat = d.category_breakdown[0];
    topExpenseCard.innerHTML = `
      <div style="font-size: 0.8125rem; color: var(--text-muted);">Highest Outflow Category</div>
      <div style="display: flex; align-items: center; justify-content: space-between; margin-top: 0.5rem;">
        <div style="font-size: 1.25rem; font-weight: 800; color: var(--text-primary);">${getCategoryIcon(topCat.category)} ${escapeHtml(topCat.category)}</div>
        <div style="font-size: 1.25rem; font-weight: 800; color: var(--rose);">${formatCurrency(topCat.amount)}</div>
      </div>
      <div style="font-size: 0.75rem; color: var(--text-secondary); margin-top: 0.25rem;">
        Represents <strong>${topCat.percentage}%</strong> of total monthly expenses
      </div>
    `;
  }

  // 5. Recent Transactions Table (Top 5)
  const recentTbody = document.getElementById("recent-transactions-tbody");
  if (recentTbody && d.recent_transactions) {
    if (d.recent_transactions.length === 0) {
      recentTbody.innerHTML = `
        <tr>
          <td colspan="4" style="text-align: center; padding: 2rem; color: var(--text-muted);">
            No transactions recorded yet. Click '+ Add Transaction' to get started.
          </td>
        </tr>
      `;
    } else {
      recentTbody.innerHTML = d.recent_transactions.slice(0, 5).map(tx => {
        const isIncome = (tx.type || "").toLowerCase() === "income";
        const dateStr = tx.transaction_date || tx.date || "";
        const formattedDate = dateStr ? new Date(dateStr).toLocaleDateString("en-IN", { month: "short", day: "numeric" }) : "";
        return `
          <tr>
            <td>
              <div style="display: flex; align-items: center; gap: 0.625rem;">
                <span style="font-size: 1.125rem;">${getCategoryIcon(tx.category)}</span>
                <div>
                  <div style="font-weight: 700; color: var(--text-primary); font-size: 0.875rem;">${escapeHtml(tx.title)}</div>
                  <div style="font-size: 0.75rem; color: var(--text-muted);">${escapeHtml(tx.category)}</div>
                </div>
              </div>
            </td>
            <td>
              <span class="badge ${isIncome ? 'badge-emerald' : 'badge-rose'}" style="font-size: 0.6875rem;">
                ${(tx.type || '').toUpperCase()}
              </span>
            </td>
            <td style="color: var(--text-secondary); font-size: 0.8125rem;">${formattedDate}</td>
            <td style="text-align: right; font-weight: 800; color: ${isIncome ? 'var(--emerald)' : 'var(--text-primary)'};">
              ${isIncome ? '+' : '-'}${formatCurrency(tx.amount)}
            </td>
          </tr>
        `;
      }).join("");
    }
  }

  // 6. Proactive AI Financial Insights UI
  loadProactiveInsightsUI();

  // 7. Phase 3.6 Financial Goals UI
  loadGoalsUI();

  // 8. Phase 3.7 AI Financial Forecast & Predictions UI
  loadForecastingUI();
  loadPredictiveInsightsUI();

  // 9. Phase 3.8 AI Smart Financial Actions UI
  loadSmartActionsUI();

  // 10. Phase 3.9 AI Financial Health Score & What-If Simulator UI
  loadHealthScoreUI();
  loadSimulationPresetsUI();
}

/**
 * Setup mobile drawer controls
 */
function setupMobileSidebar() {
  const menuBtn = document.getElementById("mobile-menu-toggle-btn");
  const sidebar = document.getElementById("app-sidebar");
  const backdrop = document.getElementById("sidebar-backdrop");

  if (menuBtn && sidebar) {
    menuBtn.addEventListener("click", () => {
      sidebar.classList.toggle("open");
      if (backdrop) backdrop.classList.toggle("active");
    });
  }

  if (backdrop) {
    backdrop.addEventListener("click", closeMobileSidebar);
  }
}

function closeMobileSidebar() {
  const sidebar = document.getElementById("app-sidebar");
  const backdrop = document.getElementById("sidebar-backdrop");
  if (sidebar) sidebar.classList.remove("open");
  if (backdrop) backdrop.classList.remove("active");
}

/**
 * ==========================================================================
 * 8. REAL AI ASSISTANT FRONTEND INTEGRATION (PHASE 3.3 PRODUCTION POLISH)
 * Multi-turn chat drawer, streaming/typing animations, markdown parser,
 * currency badges, retry behavior, accessible triggers, and status sync.
 * ==========================================================================
 */
let aiConversationHistory = [];

function initAiAssistant() {
  const triggerBtns = document.querySelectorAll(
    "#floating-ai-trigger-btn, #header-ai-trigger-btn, #ai-assistant-trigger-btn, #quick-insights-ai-btn"
  );
  const backdrop = document.getElementById("ai-drawer-backdrop");
  const drawer = document.querySelector(".ai-drawer");
  const closeBtn = document.getElementById("ai-drawer-close-btn");
  const clearBtn = document.getElementById("ai-clear-chat-btn");
  const form = document.getElementById("ai-chat-form");
  const input = document.getElementById("ai-user-input");
  const sendBtn = document.getElementById("ai-send-btn");
  const messagesContainer = document.getElementById("ai-chat-messages");

  // Open Drawer triggers
  triggerBtns.forEach(btn => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      window.openAiAssistant();
    });
  });

  window.openAiAssistant = function() {
    if (backdrop) {
      backdrop.classList.add("active");
      if (input) {
        setTimeout(() => input.focus(), 150);
      }
    }
  };

  window.closeAiAssistant = function() {
    if (backdrop) {
      backdrop.classList.remove("active");
    }
  };

  // Close Drawer
  if (closeBtn && backdrop) {
    closeBtn.addEventListener("click", () => {
      backdrop.classList.remove("active");
    });
  }

  // Close on backdrop click (outside drawer)
  if (backdrop) {
    backdrop.addEventListener("click", (e) => {
      if (e.target === backdrop) {
        backdrop.classList.remove("active");
      }
    });
  }

  // Close on Escape key
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && backdrop && backdrop.classList.contains("active")) {
      backdrop.classList.remove("active");
    }
  });

  // Clear Conversation
  if (clearBtn) {
    clearBtn.addEventListener("click", () => {
      resetAiConversation();
    });
  }

  // Suggestion Chips
  const chips = document.querySelectorAll(".quick-prompt-chip");
  chips.forEach(chip => {
    chip.addEventListener("click", () => {
      if (input && form) {
        input.value = chip.textContent.trim();
        form.dispatchEvent(new Event("submit", { cancelable: true }));
      }
    });
  });

  // Auto-resize textarea and submit on Enter (without Shift)
  if (input) {
    input.addEventListener("input", () => {
      input.style.height = "auto";
      input.style.height = Math.min(input.scrollHeight, 120) + "px";
    });

    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        if (form) form.dispatchEvent(new Event("submit", { cancelable: true }));
      }
    });
  }

  // Chat Form Submission
  if (form && input && messagesContainer) {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const query = input.value.trim();
      if (!query) return;

      if (query.length > 1000) {
        showToast("Message Too Long", "Please keep your query under 1000 characters.", "warning");
        return;
      }

      // Reset textarea height and clear input
      input.value = "";
      input.style.height = "44px";
      input.disabled = true;
      if (sendBtn) sendBtn.disabled = true;

      // Append User message bubble
      appendAiMessage("user", query);

      // Add to conversation history buffer
      aiConversationHistory.push({ role: "user", content: query });
      if (aiConversationHistory.length > 10) {
        aiConversationHistory = aiConversationHistory.slice(-10);
      }

      // Show typing indicator
      const typingId = "ai-typing-indicator-" + Date.now();
      appendAiTypingIndicator(typingId);

      try {
        const res = await financeAPI.aiChat(query, aiConversationHistory);
        removeAiTypingIndicator(typingId);

        const data = res?.data || {};
        const reply = data.message || "I processed your financial query.";

        appendAiMessage("assistant", reply);
        aiConversationHistory.push({ role: "assistant", content: reply });
      } catch (err) {
        removeAiTypingIndicator(typingId);
        console.warn("AI Assistant request failed:", err);

        // Render error bubble with retry option
        const errorMsg = err.message || "Unable to reach the financial intelligence engine. Please try again.";
        appendAiMessage("error", errorMsg, { retryQuery: query });
      } finally {
        if (input) {
          input.disabled = false;
          input.focus();
        }
        if (sendBtn) {
          sendBtn.disabled = false;
        }
      }
    });
  }

  // Initial AI Status query
  refreshAiStatus();
}

/**
 * Format AI responses with markdown, lists, code, and INR highlights
 */
function formatAiMarkdown(rawText) {
  if (!rawText) return "";

  // 1. HTML entity encoding to prevent XSS
  let escaped = rawText
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");

  // 2. Bold text **text** -> <strong>text</strong>
  escaped = escaped.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");

  // 3. Inline code `code` -> <code>code</code>
  escaped = escaped.replace(/`([^`]+)`/g, "<code>$1</code>");

  // 4. Highlight Currency INR (e.g. ₹1,50,000, ₹45,000)
  escaped = escaped.replace(/(₹\s?[\d,]+(?:\.\d{1,2})?)/g, '<span class="ai-currency">$1</span>');

  // 5. Line-by-line list and paragraph parsing with Facts vs Recommendations distinction
  const lines = escaped.split("\n");
  let inUl = false;
  let inOl = false;
  const result = [];

  for (let i = 0; i < lines.length; i++) {
    let line = lines[i].trim();
    if (!line) {
      if (inUl) { result.push("</ul>"); inUl = false; }
      if (inOl) { result.push("</ol>"); inOl = false; }
      result.push("<br>");
      continue;
    }

    const isRecHeader = /actionable ways|ways to optimize|recommendation|potential saving|suggested reduction/i.test(line);
    const bulletMatch = line.match(/^[•\-\*]\s+(.+)$/);
    const numMatch = line.match(/^(\d+)\.\s+(.+)$/);

    if (bulletMatch) {
      if (inOl) { result.push("</ol>"); inOl = false; }
      if (!inUl) { result.push("<ul>"); inUl = true; }
      const content = bulletMatch[1];
      if (/reduce by|save approx|potential saving/i.test(content)) {
        result.push(`<li><span class="ai-recommendation-badge">SUGGESTION</span>${content}</li>`);
      } else {
        result.push(`<li>${content}</li>`);
      }
    } else if (numMatch) {
      if (inUl) { result.push("</ul>"); inUl = false; }
      if (!inOl) { result.push("<ol>"); inOl = true; }
      result.push(`<li>${numMatch[2]}</li>`);
    } else {
      if (inUl) { result.push("</ul>"); inUl = false; }
      if (inOl) { result.push("</ol>"); inOl = false; }

      if (isRecHeader) {
        result.push(`<div class="ai-recommendation-card"><span class="ai-recommendation-badge">RECOMMENDATION</span><strong>${line}</strong></div>`);
      } else {
        result.push(`<div>${line}</div>`);
      }
    }
  }

  if (inUl) result.push("</ul>");
  if (inOl) result.push("</ol>");

  return result.join("");
}

/**
 * Append chat message bubble to drawer
 */
function appendAiMessage(sender, text, options = {}) {
  const container = document.getElementById("ai-chat-messages");
  if (!container) return;

  const msgDiv = document.createElement("div");

  if (sender === "user") {
    msgDiv.className = "chat-bubble user";
    msgDiv.textContent = text;
  } else if (sender === "error") {
    msgDiv.className = "chat-bubble error";
    const formatted = formatAiMarkdown(text);
    const retryBtn = options.retryQuery
      ? `<button class="ai-retry-btn" type="button" onclick="retryAiQuery('${encodeURIComponent(options.retryQuery)}')"><svg width="12" height="12" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg> Retry</button>`
      : "";
    msgDiv.innerHTML = `<div>${formatted}</div>${retryBtn}`;
  } else {
    msgDiv.className = "chat-bubble assistant";
    msgDiv.innerHTML = formatAiMarkdown(text);
  }

  container.appendChild(msgDiv);
  container.scrollTop = container.scrollHeight;
}

/**
 * Retry failed AI query
 */
window.retryAiQuery = function(encodedQuery) {
  const query = decodeURIComponent(encodedQuery);
  const input = document.getElementById("ai-user-input");
  const form = document.getElementById("ai-chat-form");
  if (input && form) {
    input.value = query;
    form.dispatchEvent(new Event("submit", { cancelable: true }));
  }
};

/**
 * Append typing indicator
 */
function appendAiTypingIndicator(id) {
  const container = document.getElementById("ai-chat-messages");
  if (!container) return;

  const indicator = document.createElement("div");
  indicator.className = "typing-indicator";
  indicator.id = id;
  indicator.innerHTML = `
    <span class="typing-dot"></span>
    <span class="typing-dot"></span>
    <span class="typing-dot"></span>
    <span style="font-size: 0.75rem; color: var(--text-muted); margin-left: 0.35rem;">Analyzing finances...</span>
  `;
  container.appendChild(indicator);
  container.scrollTop = container.scrollHeight;
}

/**
 * Remove typing indicator
 */
function removeAiTypingIndicator(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
}

/**
 * Reset conversation history and restore greeting
 */
function resetAiConversation() {
  aiConversationHistory = [];
  const container = document.getElementById("ai-chat-messages");
  if (container) {
    const userName = AppState.user?.name || "there";
    container.innerHTML = `
      <div class="chat-bubble assistant" id="ai-welcome-bubble">
        Hello ${userName}! 👋 I'm your intelligent finance assistant. I have real-time access to your verified transactions, budgets, savings rate, and financial health score. What would you like to explore today?
      </div>
    `;
  }
}

/**
 * Refresh backend AI status badge
 */
async function refreshAiStatus() {
  const indicator = document.getElementById("ai-status-indicator");
  const statusText = document.getElementById("ai-status-text");
  if (!statusText) return;

  try {
    const res = await financeAPI.getAIStatus();
    const data = res?.data || {};
    const provider = data.provider || "mock";

    if (indicator) {
      indicator.className = "status-indicator emerald";
    }
    if (provider === "groq") {
      statusText.textContent = "Groq AI Engine • Ultra Fast";
    } else if (provider === "gemini") {
      statusText.textContent = "Gemini 2.5 Flash • Ready";
    } else {
      statusText.textContent = "FastAPI Engine • Ready";
    }


  } catch (e) {
    if (indicator) indicator.className = "status-indicator amber";
    statusText.textContent = "Offline Fallback • Active";
  }
}

/**
 * Fetch and render Proactive AI Financial Insights & Alerts
 */
async function loadProactiveInsightsUI() {
  const container = document.getElementById("proactive-insights-container");
  if (!container) return;

  try {
    const res = await financeAPI.getProactiveInsights();
    const insights = (res?.data?.insights) || [];

    if (insights.length === 0) {
      container.innerHTML = `
        <div style="grid-column: 1 / -1; text-align: center; padding: 1.5rem; color: var(--text-muted); font-size: 0.875rem;">
          <span style="font-size: 1.25rem;">✨</span> No active financial alerts or warnings. Your financial metrics look healthy and on track!
        </div>
      `;
      return;
    }

    container.innerHTML = insights.map(item => {
      const sev = (item.severity || "info").toLowerCase();
      const title = escapeHtml(item.title || "");
      const msg = escapeHtml(item.message || "");
      const rec = escapeHtml(item.recommendation || "");
      const queryPrompt = encodeURIComponent(`Explain alert: ${item.title}`);

      return `
        <div class="proactive-insight-card">
          <div>
            <div class="proactive-insight-header">
              <span class="severity-badge ${sev}">${sev.toUpperCase()}</span>
              <span style="font-size: 0.6875rem; color: var(--text-muted); font-weight: 600;">VERIFIED FACT</span>
            </div>
            <div class="proactive-insight-title">${title}</div>
            <div class="proactive-fact-line">${msg}</div>
            ${rec ? `<div class="proactive-recommendation-line">💡 <strong>AI Suggestion:</strong> ${rec}</div>` : ""}
          </div>
          <button class="proactive-action-btn" type="button" onclick="askAiAboutInsight('${queryPrompt}')">
            <span>💬 Ask AI About This</span>
          </button>
        </div>
      `;
    }).join("");

    // Populate AI Drawer quick chips dynamically
    updateAiDrawerChips(insights);
  } catch (err) {
    console.warn("Failed to load proactive AI insights:", err);
    container.innerHTML = `
      <div style="grid-column: 1 / -1; padding: 1rem; color: var(--text-muted); font-size: 0.8125rem;">
        Proactive insights offline. Standard rules active.
      </div>
    `;
  }
}

/**
 * Open AI drawer and submit contextual question from insight card
 */
window.askAiAboutInsight = function(encodedPrompt) {
  const query = decodeURIComponent(encodedPrompt);
  const backdrop = document.getElementById("ai-drawer-backdrop");
  const input = document.getElementById("ai-user-input");
  const form = document.getElementById("ai-chat-form");

  if (backdrop) backdrop.classList.add("active");
  if (input && form) {
    input.value = query;
    setTimeout(() => {
      form.dispatchEvent(new Event("submit", { cancelable: true }));
    }, 200);
  }
};

/**
 * Update AI drawer prompt chips based on active insights
 */
function updateAiDrawerChips(insights) {
  const chipsContainer = document.getElementById("ai-quick-prompts");
  if (!chipsContainer) return;

  const defaultChips = [
    "How much did I spend this month?",
    "How much did I save this month?",
    "Which category is costing me the most?",
    "How is my budget progress?",
    "How is my financial health?",
    "Give me 3 ways to reduce my expenses"
  ];

  let dynamicChips = [];
  if (insights && insights.length > 0) {
    dynamicChips = insights.slice(0, 3).map(i => `Why is my ${i.category || i.title} flagged?`);
  }

  const allChips = [...dynamicChips, ...defaultChips].slice(0, 6);

  chipsContainer.innerHTML = allChips.map(c => `
    <button class="quick-prompt-chip" type="button">${escapeHtml(c)}</button>
  `).join("");

  // Re-attach click handlers to prompt chips
  const chips = chipsContainer.querySelectorAll(".quick-prompt-chip");
  const input = document.getElementById("ai-user-input");
  const form = document.getElementById("ai-chat-form");

  chips.forEach(chip => {
    chip.addEventListener("click", () => {
      if (input && form) {
        input.value = chip.textContent.trim();
        form.dispatchEvent(new Event("submit", { cancelable: true }));
      }
    });
  });
}

/**
 * ==========================================================================
 * PHASE 3.6 FINANCIAL GOALS & PLANNING CONTROLLER
 * Real-time goal tracking, modal handling, progress calculation, and deletion.
 * ==========================================================================
 */
let pendingDeleteGoalId = null;

async function loadGoalsUI() {
  const container = document.getElementById("financial-goals-container");
  if (!container) return;

  try {
    const res = await financeAPI.getGoals();
    const goals = res?.data?.goals || [];

    if (goals.length === 0) {
      container.innerHTML = `
        <div style="grid-column: 1 / -1; text-align: center; padding: 2rem; color: var(--text-muted); font-size: 0.875rem;">
          <div style="font-size: 2rem; margin-bottom: 0.5rem;">🎯</div>
          <div>No financial goals set yet. Click <strong>+ Add Goal</strong> to start planning your savings targets!</div>
        </div>
      `;
      return;
    }

    container.innerHTML = goals.map(g => {
      const pct = Math.min(100, Math.max(0, g.progress_percentage || 0));
      const statusClass = g.status === "COMPLETED" ? "badge-emerald" : (g.status === "AHEAD" ? "badge-cyan" : (g.status === "BEHIND" ? "badge-amber" : "badge-indigo"));
      const isCompleted = g.status === "COMPLETED";

      return `
        <div class="goal-card">
          <div class="goal-card-header">
            <div>
              <span class="badge ${statusClass}" style="font-size: 0.6875rem;">${g.status}</span>
              <span class="badge badge-secondary" style="font-size: 0.6875rem; margin-left: 0.35rem;">${g.priority.toUpperCase()}</span>
            </div>
            <div style="display: flex; gap: 0.25rem;">
              <button class="btn btn-ghost btn-icon-sm" type="button" title="Ask AI About Goal" onclick="askAiAboutGoal('${encodeURIComponent(g.name)}')">
                <span>🤖</span>
              </button>
              <button class="btn btn-ghost btn-icon-sm" type="button" title="Delete Goal" onclick="confirmDeleteGoal(${g.goal_id})">
                <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
              </button>
            </div>
          </div>

          <div class="goal-title">${escapeHtml(g.name)}</div>
          <div class="goal-category-label">${getCategoryIcon(g.category)} ${escapeHtml(g.category)}</div>

          <div class="goal-amounts-row">
            <div>
              <div class="goal-amount-sub">Saved</div>
              <div class="goal-amount-val" style="color: var(--emerald);">${formatCurrency(g.current_amount)}</div>
            </div>
            <div style="text-align: right;">
              <div class="goal-amount-sub">Target</div>
              <div class="goal-amount-val">${formatCurrency(g.target_amount)}</div>
            </div>
          </div>

          <div class="progress-bar-container" style="margin: 0.75rem 0 0.5rem 0; height: 8px;">
            <div class="progress-bar-fill" style="width: ${pct}%; background: ${g.status === 'BEHIND' ? 'var(--amber)' : 'var(--emerald)'};"></div>
          </div>

          <div class="goal-meta-grid">
            <div><strong>${pct}%</strong> complete</div>
            <div style="text-align: right;">Deadline: <strong>${g.target_date}</strong></div>
          </div>

          <div class="goal-plan-summary">
            ${isCompleted
              ? `<span style="color: var(--emerald); font-weight: 700;">🎉 Goal Achieved!</span>`
              : `Required: <strong>${formatCurrency(g.required_monthly_contribution)}/mo</strong> (${g.months_remaining} mos left)`
            }
          </div>
        </div>
      `;
    }).join("");

  } catch (err) {
    console.warn("Failed to load financial goals:", err);
    container.innerHTML = `
      <div style="grid-column: 1 / -1; padding: 1rem; color: var(--text-muted); font-size: 0.8125rem;">
        Goals service unavailable.
      </div>
    `;
  }
}

window.openAddGoalModal = function() {
  const modal = document.getElementById("goal-modal");
  const form = document.getElementById("goal-modal-form");
  const title = document.getElementById("goal-modal-title");
  const idInput = document.getElementById("goal-modal-id");
  const dateInput = document.getElementById("goal-modal-target-date");

  if (form) form.reset();
  if (idInput) idInput.value = "";
  if (title) title.textContent = "Add Financial Goal";

  // Set default target date to 6 months from today
  if (dateInput) {
    const futureDate = new Date();
    futureDate.setMonth(futureDate.getMonth() + 6);
    dateInput.value = futureDate.toISOString().split("T")[0];
  }

  if (modal) modal.classList.add("active");
};

window.closeGoalModal = function() {
  const modal = document.getElementById("goal-modal");
  if (modal) modal.classList.remove("active");
};

window.confirmDeleteGoal = function(goalId) {
  pendingDeleteGoalId = goalId;
  const modal = document.getElementById("goal-delete-modal");
  if (modal) modal.classList.add("active");
};

window.closeDeleteGoalModal = function() {
  pendingDeleteGoalId = null;
  const modal = document.getElementById("goal-delete-modal");
  if (modal) modal.classList.remove("active");
};

window.askAiAboutGoal = function(encodedGoalName) {
  const goalName = decodeURIComponent(encodedGoalName);
  const backdrop = document.getElementById("ai-drawer-backdrop");
  const input = document.getElementById("ai-user-input");
  const form = document.getElementById("ai-chat-form");

  if (backdrop) backdrop.classList.add("active");
  if (input && form) {
    input.value = `How is my "${goalName}" goal progressing and what is my savings plan?`;
    setTimeout(() => {
      form.dispatchEvent(new Event("submit", { cancelable: true }));
    }, 200);
  }
};

// Handle Goal Form Submission
document.addEventListener("DOMContentLoaded", () => {
  const goalForm = document.getElementById("goal-modal-form");
  if (goalForm) {
    goalForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const idInput = document.getElementById("goal-modal-id");
      const name = document.getElementById("goal-modal-name").value.trim();
      const category = document.getElementById("goal-modal-category").value;
      const targetAmount = parseFloat(document.getElementById("goal-modal-target-amount").value);
      const currentAmount = parseFloat(document.getElementById("goal-modal-current-amount").value || "0");
      const targetDate = document.getElementById("goal-modal-target-date").value;
      const priority = document.getElementById("goal-modal-priority").value;

      try {
        const payload = {
          name,
          category,
          target_amount: targetAmount,
          current_amount: currentAmount,
          target_date: targetDate,
          priority
        };

        if (idInput && idInput.value) {
          await financeAPI.updateGoal(parseInt(idInput.value, 10), payload);
          showToast("Goal Updated", `"${name}" updated successfully.`, "success");
        } else {
          await financeAPI.createGoal(payload);
          showToast("Goal Created", `"${name}" added to financial goals.`, "success");
        }

        closeGoalModal();
        await loadGoalsUI();
      } catch (err) {
        showToast("Error", err.message || "Failed to save financial goal.", "error");
      }
    });
  }

  const deleteGoalConfirmBtn = document.getElementById("goal-delete-confirm-btn");
  if (deleteGoalConfirmBtn) {
    deleteGoalConfirmBtn.addEventListener("click", async () => {
      if (!pendingDeleteGoalId) return;
      try {
        await financeAPI.deleteGoal(pendingDeleteGoalId);
        showToast("Goal Deleted", "Financial goal was removed.", "success");
        closeDeleteGoalModal();
        await loadGoalsUI();
      } catch (err) {
        showToast("Error", err.message || "Failed to delete financial goal.", "error");
      }
    });
  }
});

/**
 * Phase 3.7: Load and Render Deterministic AI Financial Forecasts
 */
async function loadForecastingUI() {
  const container = document.getElementById("forecast-metrics-container");
  const confBadge = document.getElementById("forecast-confidence-badge");
  const riskBadge = document.getElementById("forecast-risk-badge");
  if (!container) return;

  try {
    const res = await financeAPI.getFinancialForecast();
    const data = res && res.data;

    if (!data || !data.is_sufficient_data) {
      if (confBadge) confBadge.textContent = "INSUFFICIENT DATA";
      if (riskBadge) riskBadge.textContent = "STRESS: UNKNOWN";
      container.innerHTML = `
        <div class="forecast-empty-state">
          <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">📈</div>
          <div style="font-weight: 700; color: var(--text-primary);">Forecasting Engine Initializing</div>
          <div style="font-size: 0.8125rem; color: var(--text-muted); margin-top: 0.25rem;">
            Record at least one full month of income and expense transactions to unlock deterministic predictive projections.
          </div>
        </div>
      `;
      return;
    }

    const inc = data.income_forecast || {};
    const exp = data.expense_forecast || {};
    const sav = data.savings_forecast || {};

    if (confBadge) confBadge.textContent = `${sav.confidence || 'MEDIUM'} CONFIDENCE`;

    // Fetch risk report for stress badge
    try {
      const riskRes = await financeAPI.getFinancialRisks();
      if (riskRes && riskRes.data && riskRes.data.stress_summary) {
        const lvl = riskRes.data.stress_summary.overall_risk_level;
        if (riskBadge) {
          riskBadge.textContent = `STRESS: ${lvl}`;
          riskBadge.className = `badge ${lvl === 'CRITICAL' ? 'badge-rose' : lvl === 'HIGH' ? 'badge-amber' : lvl === 'MEDIUM' ? 'badge-amber' : 'badge-emerald'}`;
        }
      }
    } catch (_) {}

    container.innerHTML = `
      <!-- Projected Income -->
      <div class="forecast-metric-card">
        <div class="forecast-metric-top">
          <span class="forecast-metric-label">Projected Income</span>
          <span class="badge ${inc.trend_percentage >= 0 ? 'badge-emerald' : 'badge-rose'}">
            ${inc.trend_percentage >= 0 ? '+' : ''}${inc.trend_percentage || 0}% trend
          </span>
        </div>
        <div class="forecast-metric-val">${formatCurrency(inc.projected_value || 0)}</div>
        <div class="forecast-metric-sub">Current: ${formatCurrency(inc.current_value || 0)}</div>
      </div>

      <!-- Projected Expenses -->
      <div class="forecast-metric-card">
        <div class="forecast-metric-top">
          <span class="forecast-metric-label">Projected Expenses</span>
          <span class="badge ${exp.trend_percentage <= 0 ? 'badge-emerald' : 'badge-amber'}">
            ${exp.trend_percentage >= 0 ? '+' : ''}${exp.trend_percentage || 0}% trend
          </span>
        </div>
        <div class="forecast-metric-val">${formatCurrency(exp.projected_value || 0)}</div>
        <div class="forecast-metric-sub">Current: ${formatCurrency(exp.current_value || 0)}</div>
      </div>

      <!-- Projected Net Savings -->
      <div class="forecast-metric-card">
        <div class="forecast-metric-top">
          <span class="forecast-metric-label">Projected Net Savings</span>
          <span class="badge ${sav.projected_value >= 0 ? 'badge-emerald' : 'badge-rose'}">
            ${sav.projected_value >= 0 ? 'SURPLUS' : 'DEFICIT'}
          </span>
        </div>
        <div class="forecast-metric-val" style="color: ${sav.projected_value >= 0 ? 'var(--emerald)' : 'var(--rose)'};">
          ${formatCurrency(sav.projected_value || 0)}
        </div>
        <div class="forecast-metric-sub">Projected Surplus / Month</div>
      </div>

      <!-- Projected Savings Rate -->
      <div class="forecast-metric-card">
        <div class="forecast-metric-top">
          <span class="forecast-metric-label">Projected Savings Rate</span>
          <span class="badge ${sav.projected_savings_rate_percentage >= 20 ? 'badge-emerald' : 'badge-amber'}">
            ${sav.projected_savings_rate_percentage >= 20 ? 'OPTIMAL' : 'BELOW TARGET'}
          </span>
        </div>
        <div class="forecast-metric-val">${sav.projected_savings_rate_percentage || 0}%</div>
        <div class="forecast-metric-sub">Healthy Benchmark: 20%+</div>
      </div>
    `;
  } catch (err) {
    container.innerHTML = `
      <div style="grid-column: 1 / -1; padding: 1rem; color: var(--text-muted); font-size: 0.8125rem;">
        Forecast service unavailable.
      </div>
    `;
  }
}

/**
 * Phase 3.7: Load and Render Top Prioritized Predictive Insights
 */
async function loadPredictiveInsightsUI() {
  const container = document.getElementById("predictions-container");
  if (!container) return;

  try {
    const res = await financeAPI.getPredictiveInsights();
    const list = res && res.data && res.data.insights ? res.data.insights : [];

    if (list.length === 0) {
      container.innerHTML = `
        <div class="prediction-empty-state">
          <div style="font-size: 1.25rem;">✨</div>
          <div style="font-size: 0.875rem; font-weight: 700; color: var(--text-primary);">All Predictive Signals Healthy</div>
          <div style="font-size: 0.75rem; color: var(--text-muted);">
            No budget exhaustions or critical financial risks detected in current trajectories.
          </div>
        </div>
      `;
      return;
    }

    container.innerHTML = list.map(item => {
      const sevClass = (item.severity || "").toLowerCase();
      const badgeColor = sevClass === 'critical' ? 'badge-rose' : (sevClass === 'high' || sevClass === 'warning') ? 'badge-rose' : sevClass === 'medium' ? 'badge-amber' : sevClass === 'positive' ? 'badge-emerald' : 'badge-indigo';
      const encodedTitle = encodeURIComponent(item.title || "Financial Prediction");

      return `
        <div class="prediction-card prediction-${sevClass}">
          <div class="prediction-card-header">
            <div style="display: flex; align-items: center; gap: 0.5rem;">
              <span class="prediction-category-pill">${escapeHtml(item.category)}</span>
              <span class="prediction-title">${escapeHtml(item.title)}</span>
            </div>
            <span class="badge ${badgeColor}">${(item.severity || 'INFO').toUpperCase()}</span>
          </div>

          <div class="prediction-sections">
            <div class="pred-section">
              <span class="pred-tag pred-tag-fact">VERIFIED FACT</span>
              <span class="pred-text">${escapeHtml(item.verified_fact)}</span>
            </div>
            <div class="pred-section">
              <span class="pred-tag pred-tag-forecast">FORECAST</span>
              <span class="pred-text">${escapeHtml(item.forecast)}</span>
            </div>
            <div class="pred-section">
              <span class="pred-tag pred-tag-risk">RISK</span>
              <span class="pred-text">${escapeHtml(item.risk)}</span>
            </div>
            <div class="pred-section">
              <span class="pred-tag pred-tag-suggestion">AI SUGGESTION</span>
              <span class="pred-text">${escapeHtml(item.ai_suggestion)}</span>
            </div>
          </div>

          <div class="prediction-card-footer">
            <button class="btn btn-secondary btn-sm" onclick="askAiAboutPrediction('${encodedTitle}')">
              <span>🤖</span>
              <span>Ask AI About This</span>
            </button>
          </div>
        </div>
      `;
    }).join("");
  } catch (err) {
    container.innerHTML = `
      <div style="padding: 1rem; color: var(--text-muted); font-size: 0.8125rem;">
        Predictive insights unavailable.
      </div>
    `;
  }
}

window.askAiAboutPrediction = function(encodedTitle) {
  const title = decodeURIComponent(encodedTitle);
  const backdrop = document.getElementById("ai-drawer-backdrop");
  const input = document.getElementById("ai-user-input");
  const form = document.getElementById("ai-chat-form");

  if (backdrop) backdrop.classList.add("active");
  if (input && form) {
    input.value = `Can you explain the prediction regarding "${title}" and how I can mitigate any risks?`;
    setTimeout(() => {
      form.dispatchEvent(new Event("submit", { cancelable: true }));
    }, 200);
  }
};

/**
 * =========================================================================
 * PHASE 3.8: AI SMART FINANCIAL ACTIONS & AUTOMATION CONTROLLERS
 * =========================================================================
 */

let activeActionProposalId = null;

async function loadSmartActionsUI(refresh = false) {
  const container = document.getElementById("smart-actions-container");
  if (!container) return;

  container.innerHTML = `
    <div style="padding: 1.5rem; text-align: center; color: var(--text-muted); font-size: 0.875rem;">
      Analyzing verified financial data & generating grounded optimization actions...
    </div>
  `;

  try {
    const res = await financeAPI.getSmartActions(refresh);
    const actions = (res.data && res.data.actions) ? res.data.actions : [];

    if (actions.length === 0) {
      container.innerHTML = `
        <div style="padding: 2rem; text-align: center; color: var(--text-muted); font-size: 0.875rem; border: 1px dashed var(--border-color); border-radius: var(--radius-lg);">
          <div style="font-size: 1.75rem; margin-bottom: 0.5rem;">🎉</div>
          <div style="font-weight: 700; color: var(--text-primary); margin-bottom: 0.25rem;">No Urgent Action Recommendations</div>
          <div>Your spending patterns, budgets, and savings trajectories are currently balanced with your financial targets.</div>
        </div>
      `;
      return;
    }

    container.innerHTML = actions.map(act => {
      const riskClass = act.risk_level === "CRITICAL" ? "badge-rose" : (act.risk_level === "HIGH" ? "badge-amber" : (act.risk_level === "LOW" ? "badge-emerald" : "badge-indigo"));
      const statusClass = act.status === "EXECUTED" ? "badge-emerald" : (act.status === "CONFIRMED" ? "badge-cyan" : (act.status === "REJECTED" ? "badge-rose" : "badge-amber"));
      const isProposed = act.status === "PROPOSED" || act.status === "CONFIRMED";

      return `
        <div class="smart-action-card ${act.status.toLowerCase()}">
          <div class="smart-action-header">
            <div>
              <div class="smart-action-title">${escapeHtml(act.title)}</div>
              <div class="smart-action-type">${escapeHtml(act.action_type.replace(/_/g, " "))}</div>
            </div>
            <div style="display: flex; gap: 0.35rem; align-items: center;">
              <span class="badge ${riskClass}">${escapeHtml(act.risk_level)} PRIORITY</span>
              <span class="badge ${statusClass}">${escapeHtml(act.status)}</span>
            </div>
          </div>

          <div class="smart-action-body">
            <div class="smart-action-evidence">
              <span style="font-weight: 700; color: var(--indigo);">Verified Evidence:</span>
              <span>${escapeHtml(act.verified_evidence)}</span>
            </div>
            <div class="smart-action-desc">${escapeHtml(act.description)}</div>
            <div class="smart-action-impact">
              <span style="font-weight: 700; color: var(--emerald);">Expected Impact:</span>
              <span>${escapeHtml(act.expected_impact)}</span>
            </div>
          </div>

          <div class="smart-action-footer">
            <div class="smart-action-amount">
              ${act.financial_amount > 0 ? formatCurrency(act.financial_amount) : ''}
            </div>
            <div class="smart-action-buttons">
              ${isProposed ? `
                <button class="btn btn-emerald btn-sm" onclick="openActionConfirmModal('${act.action_id}')">
                  <span>Review & Apply</span>
                </button>
              ` : `
                <span style="font-size: 0.75rem; color: var(--text-muted); font-weight: 600;">
                  ${act.status === 'EXECUTED' ? '✓ Applied to Dashboard' : 'Archived'}
                </span>
              `}
            </div>
          </div>
        </div>
      `;
    }).join("");

  } catch (err) {
    container.innerHTML = `
      <div style="padding: 1rem; color: var(--rose); font-size: 0.8125rem;">
        Failed to load smart financial actions: ${escapeHtml(err.message)}
      </div>
    `;
  }
}

window.loadSmartActionsUI = loadSmartActionsUI;

window.openActionConfirmModal = async function(actionId) {
  activeActionProposalId = actionId;
  const modal = document.getElementById("action-confirm-modal");
  if (!modal) return;

  try {
    const res = await financeAPI.getAction(actionId);
    const act = res.data && res.data.action ? res.data.action : null;
    if (!act) return;

    document.getElementById("action-modal-title").textContent = act.title;
    document.getElementById("action-modal-type").textContent = `${act.action_type} • ₹${Number(act.financial_amount).toLocaleString('en-IN')}`;
    document.getElementById("action-modal-evidence").textContent = act.verified_evidence;
    document.getElementById("action-modal-description").textContent = act.description;
    document.getElementById("action-modal-impact").textContent = `Expected Result: ${act.expected_impact}`;

    const noteInput = document.getElementById("action-modal-note");
    if (noteInput) noteInput.value = "";

    const confirmBtn = document.getElementById("action-modal-confirm-btn");
    if (confirmBtn) {
      confirmBtn.onclick = () => confirmAndExecuteAction(actionId);
    }

    const rejectBtn = document.getElementById("action-modal-reject-btn");
    if (rejectBtn) {
      rejectBtn.onclick = () => rejectSmartAction(actionId);
    }

    modal.classList.add("active");
  } catch (err) {
    showToast(err.message || "Failed to retrieve action details", "error");
  }
};

window.closeActionConfirmModal = function() {
  const modal = document.getElementById("action-confirm-modal");
  if (modal) modal.classList.remove("active");
  activeActionProposalId = null;
};

async function confirmAndExecuteAction(actionId) {
  const confirmBtn = document.getElementById("action-modal-confirm-btn");
  const note = (document.getElementById("action-modal-note")?.value || "").trim();

  if (confirmBtn) {
    confirmBtn.disabled = true;
    confirmBtn.textContent = "Executing...";
  }

  try {
    // 1. First stage: Confirm proposal
    await financeAPI.confirmAction(actionId, note);

    // 2. Second stage: Safe server-side execution
    const execRes = await financeAPI.executeAction(actionId, note);

    showToast("Smart financial action executed successfully!", "success");
    closeActionConfirmModal();

    // 3. Refresh dashboard and actions
    await loadSmartActionsUI();
    if (typeof loadDashboard === "function") {
      loadDashboard();
    }
  } catch (err) {
    showToast(err.message || "Action execution failed", "error");
  } finally {
    if (confirmBtn) {
      confirmBtn.disabled = false;
      confirmBtn.textContent = "Confirm & Execute";
    }
  }
}

async function rejectSmartAction(actionId) {
  const note = (document.getElementById("action-modal-note")?.value || "").trim();

  try {
    await financeAPI.rejectAction(actionId, note || "Rejected by user from dashboard");
    showToast("Action proposal rejected.", "info");
    closeActionConfirmModal();
    await loadSmartActionsUI();
  } catch (err) {
    showToast(err.message || "Failed to reject action", "error");
  }
}

window.loadActionHistoryUI = async function() {
  const modal = document.getElementById("action-history-modal");
  const container = document.getElementById("action-history-container");
  if (!modal || !container) return;

  container.innerHTML = `
    <div style="padding: 1.5rem; text-align: center; color: var(--text-muted); font-size: 0.875rem;">
      Loading audit history...
    </div>
  `;
  modal.classList.add("active");

  try {
    const res = await financeAPI.getActionHistory();
    const items = (res.data && res.data.items) ? res.data.items : [];

    if (items.length === 0) {
      container.innerHTML = `
        <div style="padding: 2rem; text-align: center; color: var(--text-muted); font-size: 0.875rem;">
          No audit records found.
        </div>
      `;
      return;
    }

    container.innerHTML = `
      <div style="display: flex; flex-direction: column; gap: 0.75rem;">
        ${items.map(item => {
          const statusColor = item.execution_status === "SUCCESS" ? "badge-emerald" : (item.execution_status === "CONFIRMED" ? "badge-cyan" : (item.execution_status === "REJECTED" ? "badge-rose" : "badge-amber"));
          const dt = new Date(item.timestamp).toLocaleString();

          return `
            <div style="padding: 0.875rem; border-radius: var(--radius-md); background: var(--bg-card); border: 1px solid var(--border-color); display: flex; flex-direction: column; gap: 0.35rem;">
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="font-weight: 700; font-size: 0.875rem; color: var(--text-primary);">${escapeHtml(item.action_type)}</div>
                <div style="display: flex; gap: 0.35rem; align-items: center;">
                  <span class="badge ${statusColor}">${escapeHtml(item.execution_status)}</span>
                  <span style="font-size: 0.75rem; color: var(--text-muted);">${dt}</span>
                </div>
              </div>
              <div style="font-size: 0.8125rem; color: var(--text-secondary);">${escapeHtml(item.reason)}</div>
              ${item.financial_amount > 0 ? `<div style="font-size: 0.8125rem; font-weight: 700; color: var(--text-primary);">Amount: ${formatCurrency(item.financial_amount)}</div>` : ''}
              <div style="font-size: 0.6875rem; color: var(--text-muted); font-family: monospace;">Action ID: ${escapeHtml(item.action_id)} • Validation: ${escapeHtml(item.validation_result)}</div>
            </div>
          `;
        }).join("")}
      </div>
    `;
  } catch (err) {
    container.innerHTML = `
      <div style="padding: 1rem; color: var(--rose); font-size: 0.8125rem;">
        Failed to load audit history: ${escapeHtml(err.message)}
      </div>
    `;
  }
};

window.closeActionHistoryModal = function() {
  const modal = document.getElementById("action-history-modal");
  if (modal) modal.classList.remove("active");
};

// ==========================================================================
// PHASE 3.9: AI FINANCIAL INTELLIGENCE, HEALTH SCORE, EXPLAINABILITY & SIMULATION
// ==========================================================================

window.loadHealthScoreUI = async function() {
  const scoreNumberEl = document.getElementById("health-score-number");
  const ringProgressEl = document.getElementById("health-score-progress-ring");
  const badgeEl = document.getElementById("health-score-status-badge");
  const factorsContainer = document.getElementById("health-factors-container");

  try {
    const res = await financeAPI.getHealthScore();
    const data = res.data || {};
    const score = data.overall_score;
    const status = data.status || "GOOD";
    const components = data.components || {};

    if (scoreNumberEl) {
      scoreNumberEl.textContent = score !== null && score !== undefined ? Math.round(score) : "--";
    }

    if (badgeEl) {
      badgeEl.textContent = status;
      badgeEl.className = `badge ${status === 'EXCELLENT' ? 'badge-emerald' : status === 'GOOD' ? 'badge-cyan' : status === 'FAIR' ? 'badge-amber' : 'badge-rose'}`;
    }

    if (ringProgressEl) {
      const radius = 70;
      const circumference = 2 * Math.PI * radius;
      const effectiveScore = score !== null && score !== undefined ? score : 0;
      const offset = circumference - (effectiveScore / 100) * circumference;
      ringProgressEl.style.strokeDasharray = `${circumference} ${circumference}`;
      ringProgressEl.style.strokeDashoffset = offset;

      if (effectiveScore >= 80) ringProgressEl.style.stroke = "var(--emerald)";
      else if (effectiveScore >= 60) ringProgressEl.style.stroke = "var(--indigo)";
      else if (effectiveScore >= 40) ringProgressEl.style.stroke = "var(--amber)";
      else ringProgressEl.style.stroke = "var(--rose)";
    }

    if (factorsContainer && Object.keys(components).length > 0) {
      factorsContainer.innerHTML = Object.entries(components).map(([k, c]) => {
        const cScore = c.score !== null && c.score !== undefined ? Math.round(c.score) : "--";
        const cWeight = Math.round(c.weight * 100);
        const fillWidth = c.score !== null && c.score !== undefined ? Math.min(100, Math.max(0, c.score)) : 0;
        const barColor = fillWidth >= 80 ? 'var(--emerald)' : fillWidth >= 60 ? 'var(--indigo)' : fillWidth >= 40 ? 'var(--amber)' : 'var(--rose)';

        return `
          <div class="health-factor-item" style="margin-bottom: 0.5rem;">
            <div style="display: flex; justify-content: space-between; font-size: 0.8125rem; margin-bottom: 0.2rem;">
              <span style="color: var(--text-secondary);">${escapeHtml(c.name)} <span style="font-size: 0.6875rem; color: var(--text-muted);">(${cWeight}%)</span></span>
              <strong style="color: var(--text-primary);">${cScore}/100</strong>
            </div>
            <div class="progress-bar-container" style="height: 6px; background: rgba(255, 255, 255, 0.08); border-radius: 3px; overflow: hidden;">
              <div class="progress-bar-fill" style="width: ${fillWidth}%; background: ${barColor}; height: 100%; transition: width 0.6s ease;"></div>
            </div>
          </div>
        `;
      }).join("");
    }
  } catch (err) {
    console.warn("Could not load financial health score:", err.message);
  }
};

window.loadSimulationPresetsUI = async function() {
  const container = document.getElementById("simulation-presets-container");
  if (!container) return;

  try {
    const res = await financeAPI.getSimulationExamples();
    const examples = res.data && res.data.examples ? res.data.examples : [];

    container.innerHTML = examples.map(ex => `
      <button class="btn btn-secondary btn-xs preset-sim-chip" onclick='runPresetSimulation(${JSON.stringify(ex.payload)})' style="font-size: 0.75rem; padding: 0.35rem 0.65rem; border-radius: 9999px;">
        ⚡ ${escapeHtml(ex.title)}
      </button>
    `).join("");
  } catch (err) {
    container.innerHTML = `<span style="font-size: 0.75rem; color: var(--text-muted);">Preset scenarios ready</span>`;
  }
};

window.openSimulationModal = function() {
  const modal = document.getElementById("simulation-modal");
  if (modal) {
    modal.classList.add("active");
    handleSimulationScenarioChange();
  }
};

window.closeSimulationModal = function() {
  const modal = document.getElementById("simulation-modal");
  if (modal) modal.classList.remove("active");
};

window.handleSimulationScenarioChange = function() {
  const select = document.getElementById("sim-scenario-select");
  const label = document.getElementById("sim-value-label");
  const input = document.getElementById("sim-value-input");
  if (!select || !label || !input) return;

  const val = select.value;
  if (val.includes("PERCENTAGE") || val === "REDUCE_EXPENSES" || val === "INCOME_INCREASE" || val === "INCOME_REDUCTION") {
    label.textContent = "Shift Percentage (%)";
    input.placeholder = "e.g. 15";
    input.value = "15";
    input.min = "1";
    input.max = "100";
    input.step = "1";
  } else if (val === "GOAL_DEADLINE_CHANGE") {
    label.textContent = "Timeline Shift in Months (+ Delay / - Accelerate)";
    input.placeholder = "e.g. 3";
    input.value = "3";
    input.min = "-24";
    input.max = "60";
    input.step = "1";
  } else {
    label.textContent = "Amount (₹ INR)";
    input.placeholder = "e.g. 5000";
    input.value = "5000";
    input.min = "100";
    input.max = "10000000";
    input.step = "100";
  }
};

window.submitCustomSimulation = async function(event) {
  event.preventDefault();
  const select = document.getElementById("sim-scenario-select");
  const input = document.getElementById("sim-value-input");
  const btn = document.getElementById("sim-submit-btn");
  const resultDiv = document.getElementById("modal-simulation-result");
  if (!select || !input) return;

  const scenario = select.value;
  const numVal = parseFloat(input.value) || 0;
  const payload = { scenario };

  if (scenario.includes("PERCENTAGE") || scenario === "REDUCE_EXPENSES" || scenario === "INCOME_INCREASE" || scenario === "INCOME_REDUCTION") {
    payload.percentage = numVal;
  } else if (scenario === "GOAL_DEADLINE_CHANGE") {
    payload.months = parseInt(numVal, 10);
  } else {
    payload.amount = numVal;
  }

  if (btn) {
    btn.disabled = true;
    btn.textContent = "Simulating...";
  }

  try {
    const res = await financeAPI.runFinancialSimulation(payload);
    const sim = res.data;
    renderSimulationComparison(sim, "modal-simulation-result");
    renderSimulationComparison(sim, "simulation-results-container");
    showToast("What-If Simulation calculated!", "info");
  } catch (err) {
    if (resultDiv) {
      resultDiv.innerHTML = `<div style="color: var(--rose); font-size: 0.8125rem;">Simulation failed: ${escapeHtml(err.message)}</div>`;
    }
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = "Run Simulation";
    }
  }
};

window.runPresetSimulation = async function(payload) {
  const container = document.getElementById("simulation-results-container");
  if (!container) return;

  container.innerHTML = `<div style="padding: 1rem; text-align: center; color: var(--text-muted);">Running simulation...</div>`;

  try {
    const res = await financeAPI.runFinancialSimulation(payload);
    renderSimulationComparison(res.data, "simulation-results-container");
  } catch (err) {
    container.innerHTML = `<div style="color: var(--rose); font-size: 0.8125rem; padding: 1rem;">Simulation error: ${escapeHtml(err.message)}</div>`;
  }
};

window.renderSimulationComparison = function(sim, containerId) {
  const container = document.getElementById(containerId);
  if (!container || !sim) return;

  const cur = sim.current_state || {};
  const s = sim.simulated_state || {};
  const imp = sim.impact || {};

  const deltaSavingsStr = imp.delta_monthly_savings >= 0 ? `+${formatCurrency(imp.delta_monthly_savings)}` : `-${formatCurrency(Math.abs(imp.delta_monthly_savings))}`;
  const deltaRateStr = imp.delta_savings_rate >= 0 ? `+${imp.delta_savings_rate.toFixed(1)}%` : `${imp.delta_savings_rate.toFixed(1)}%`;
  const deltaHealthStr = imp.delta_health_score >= 0 ? `+${imp.delta_health_score.toFixed(1)} pts` : `${imp.delta_health_score.toFixed(1)} pts`;

  container.innerHTML = `
    <div style="background: var(--bg-card); padding: 1.25rem; border-radius: var(--radius-md); border: 1px solid var(--border-color); margin-top: 0.75rem;">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
        <div>
          <span class="badge badge-cyan" style="font-size: 0.6875rem;">SIMULATION</span>
          <span style="font-weight: 700; font-size: 0.875rem; margin-left: 0.35rem; color: var(--text-primary);">${escapeHtml(sim.scenario)}</span>
        </div>
        <span style="font-size: 0.6875rem; color: var(--text-muted);">Hypothetical In-Memory</span>
      </div>

      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem;">
        <div style="background: var(--surface-secondary); padding: 0.875rem; border-radius: var(--radius-sm);">
          <div style="font-size: 0.6875rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase;">Current Baseline</div>
          <div style="font-size: 1.125rem; font-weight: 800; color: var(--text-primary); margin-top: 0.25rem;">${formatCurrency(cur.monthly_savings)}/mo</div>
          <div style="font-size: 0.75rem; color: var(--text-secondary); margin-top: 0.25rem;">Savings Rate: ${cur.savings_rate_percentage}% • Health: ${cur.health_score}</div>
        </div>

        <div style="background: rgba(16, 185, 129, 0.08); padding: 0.875rem; border-radius: var(--radius-sm); border: 1px solid rgba(16, 185, 129, 0.2);">
          <div style="font-size: 0.6875rem; font-weight: 700; color: var(--emerald); text-transform: uppercase;">Simulated Outcome</div>
          <div style="font-size: 1.125rem; font-weight: 800; color: var(--emerald); margin-top: 0.25rem;">${formatCurrency(s.monthly_savings)}/mo</div>
          <div style="font-size: 0.75rem; color: var(--text-secondary); margin-top: 0.25rem;">Savings Rate: ${s.savings_rate_percentage}% • Health: ${s.health_score} (${s.health_status || 'GOOD'})</div>
        </div>
      </div>

      <div style="font-size: 0.8125rem; color: var(--text-secondary); line-height: 1.4; padding: 0.5rem; background: var(--surface-secondary); border-radius: var(--radius-sm); margin-bottom: 0.5rem;">
        <strong>Impact:</strong> ${escapeHtml(imp.summary || '')} (Savings Delta: <strong style="color: var(--emerald);">${deltaSavingsStr}</strong>, Rate: <strong>${deltaRateStr}</strong>, Health: <strong>${deltaHealthStr}</strong>)
      </div>
      <div style="font-size: 0.6875rem; color: var(--text-muted); font-style: italic;">
        ${escapeHtml(sim.disclaimer)}
      </div>
    </div>
  `;
};

window.openHealthExplanationModal = async function() {
  try {
    const res = await financeAPI.getFinancialExplanation("WHY_THIS_HEALTH_SCORE");
    openExplanationModal(res.data);
  } catch (err) {
    showToast(err.message || "Failed to load explanation", "error");
  }
};

window.openExplanationModal = function(exp) {
  const modal = document.getElementById("explanation-modal");
  if (!modal || !exp) return;

  document.getElementById("explanation-modal-title").textContent = exp.title || "Financial Explanation";
  document.getElementById("explanation-modal-type").textContent = `${exp.explanation_type || 'EXPLANATION'} • ${exp.confidence || 'HIGH'} CONFIDENCE`;
  document.getElementById("explanation-modal-summary").textContent = exp.summary || "";
  document.getElementById("explanation-modal-evidence").textContent = exp.verified_evidence || "Verified from active workspace transactions.";
  document.getElementById("explanation-modal-basis").textContent = exp.calculation_basis || "Evaluated by deterministic backend financial engine.";
  document.getElementById("explanation-modal-limitations").textContent = `Limitations: ${exp.limitations || 'Evaluates currently recorded transactions.'}`;

  modal.classList.add("active");
};

window.closeExplanationModal = function() {
  const modal = document.getElementById("explanation-modal");
  if (modal) modal.classList.remove("active");
};



