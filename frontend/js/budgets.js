/**
 * ==========================================================================
 * SMART PERSONAL FINANCE DASHBOARD - BUDGETS CONTROLLER
 * Real FastAPI Category Envelopes, Live Spending Utilization & Modal Editor
 * ==========================================================================
 */

let editingBudgetId = null;
let editingBudgetCategory = null;

/**
 * Initialize Budgets view
 */
function initBudgets() {
  setupBudgetModals();
  renderBudgetsView();
}

/**
 * Setup Budget Modals
 */
function setupBudgetModals() {
  const form = document.getElementById("budget-modal-form");
  if (form && !form.dataset.bound) {
    form.dataset.bound = "true";
    form.addEventListener("submit", handleSaveBudget);
  }

  const submitBtn = document.getElementById("budget-modal-submit-btn");
  if (submitBtn && !submitBtn.dataset.bound) {
    submitBtn.dataset.bound = "true";
    submitBtn.addEventListener("click", (e) => {
      if (form && typeof form.requestSubmit === "function") {
        e.preventDefault();
        form.requestSubmit();
      }
    });
  }

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      const modal = document.getElementById("budget-modal");
      if (modal && modal.classList.contains("active")) closeBudgetModal();
    }
  });
}

/**
 * Render Budgets Section & Category Cards Grid using real backend data
 */
function renderBudgetsView() {
  const gridContainer = document.getElementById("budgets-grid-container");
  const overallSummary = document.getElementById("budget-overall-progress");
  if (!gridContainer) return;

  const budgets = AppState.budgets || [];

  if (budgets.length === 0) {
    gridContainer.innerHTML = `
      <div style="grid-column: 1 / -1; text-align: center; padding: 3rem 1rem; color: var(--text-muted); background: var(--surface); border-radius: var(--radius-lg); border: 1px dashed var(--border-color);">
        <div style="font-size: 2rem; margin-bottom: 0.5rem;">🎯</div>
        <div style="font-weight: 700; color: var(--text-primary); font-size: 1.1rem;">No Budget Envelopes Set</div>
        <div style="font-size: 0.875rem; margin-top: 0.25rem;">Create category spending limits to gain intelligent insights and discipline.</div>
        <button class="btn btn-primary btn-sm" style="margin-top: 1rem;" onclick="openCreateBudgetModal()">+ Create First Budget</button>
      </div>
    `;
    if (overallSummary) {
      overallSummary.innerHTML = "";
    }
    return;
  }

  let totalBudgetAmount = 0;
  let totalSpentAmount = 0;

  const budgetCardsHtml = budgets.map(b => {
    const amount = Number(b.amount) || 0;
    const spent = Number(b.spent) || 0;
    const remaining = Number(b.remaining) || 0;
    const percentage = Number(b.percentage) || 0;
    const status = b.status || "UNDER_BUDGET";

    totalBudgetAmount += amount;
    totalSpentAmount += spent;

    let statusClass = "badge-emerald";
    let barClass = "under-budget";

    if (status === "OVER_BUDGET") {
      statusClass = "badge-rose";
      barClass = "over-budget";
    } else if (status === "NEAR_LIMIT") {
      statusClass = "badge-amber";
      barClass = "near-limit";
    } else if (status === "ON_TRACK") {
      statusClass = "badge-cyan";
      barClass = "on-track";
    }

    const progressWidth = Math.min(100, percentage);

    return `
      <div class="card budget-card">
        <div class="budget-card-header">
          <div class="budget-category-info">
            <div class="budget-icon">${getCategoryIcon(b.category)}</div>
            <div>
              <div class="budget-category-title">${escapeHtml(b.category)}</div>
              <span class="badge ${statusClass}" style="font-size: 0.6875rem;">
                ${status.replace("_", " ")}
              </span>
            </div>
          </div>
          <div style="display: flex; gap: 0.25rem;">
            <button class="btn btn-secondary btn-icon-sm" onclick="openEditBudgetModal(${b.id}, '${escapeHtml(b.category)}', ${amount})" title="Adjust Budget Limit">
              <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"></path></svg>
            </button>
            <button class="btn btn-ghost btn-icon-sm" style="color: var(--rose);" onclick="handleDeleteBudget(${b.id})" title="Delete Envelope">
              <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
            </button>
          </div>
        </div>

        <div class="budget-numbers-row">
          <div>
            <div style="font-size: 0.75rem; color: var(--text-muted);">Spent</div>
            <div class="budget-spent">${formatCurrency(spent)}</div>
          </div>
          <div style="text-align: right;">
            <div style="font-size: 0.75rem; color: var(--text-muted);">Budget Limit</div>
            <div class="budget-limit">${formatCurrency(amount)}</div>
          </div>
        </div>

        <div class="budget-progress-container">
          <div class="budget-progress-bar ${barClass}" style="width: ${progressWidth}%;"></div>
        </div>

        <div class="budget-footer-info">
          <div>
            <span>Used: </span>
            <strong style="color: var(--text-primary);">${percentage}%</strong>
          </div>
          <div>
            <span>Remaining: </span>
            <strong class="budget-remaining" style="color: ${remaining < 0 ? 'var(--rose)' : 'var(--text-primary)'}">
              ${formatCurrency(remaining)}
            </strong>
          </div>
        </div>
      </div>
    `;
  }).join("");

  gridContainer.innerHTML = budgetCardsHtml;

  // Overall Envelope Progress Card
  if (overallSummary) {
    const overallUsage = calculateBudgetUsage(totalSpentAmount, totalBudgetAmount);
    const overallWidth = Math.min(100, overallUsage.percentage);

    overallSummary.innerHTML = `
      <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.75rem; flex-wrap: wrap; gap: 0.5rem;">
        <div>
          <div style="font-size: 1.125rem; font-weight: 800; color: var(--text-primary);">Monthly Envelope Budget Overview</div>
          <div style="font-size: 0.8125rem; color: var(--text-secondary);">Total budgeted across ${budgets.length} spending categories</div>
        </div>
        <div style="text-align: right;">
          <span class="badge ${overallUsage.statusClass}">${overallUsage.status.replace("_", " ")}</span>
        </div>
      </div>

      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; margin-bottom: 1rem;">
        <div style="background: var(--surface); padding: 0.875rem; border-radius: var(--radius-md); border: 1px solid var(--border-color);">
          <div style="font-size: 0.75rem; color: var(--text-muted);">Total Budget Envelope</div>
          <div style="font-size: 1.35rem; font-weight: 800; color: var(--text-primary); margin-top: 0.25rem;">${formatCurrency(totalBudgetAmount)}</div>
        </div>
        <div style="background: var(--surface); padding: 0.875rem; border-radius: var(--radius-md); border: 1px solid var(--border-color);">
          <div style="font-size: 0.75rem; color: var(--text-muted);">Total Spent (Live)</div>
          <div style="font-size: 1.35rem; font-weight: 800; color: var(--rose); margin-top: 0.25rem;">${formatCurrency(totalSpentAmount)}</div>
        </div>
        <div style="background: var(--surface); padding: 0.875rem; border-radius: var(--radius-md); border: 1px solid var(--border-color);">
          <div style="font-size: 0.75rem; color: var(--text-muted);">Total Safe Buffer</div>
          <div style="font-size: 1.35rem; font-weight: 800; color: ${overallUsage.remaining < 0 ? 'var(--rose)' : 'var(--emerald)'}; margin-top: 0.25rem;">${formatCurrency(overallUsage.remaining)}</div>
        </div>
      </div>

      <div class="budget-progress-container" style="height: 12px;">
        <div class="budget-progress-bar ${overallUsage.barClass}" style="width: ${overallWidth}%;"></div>
      </div>
    `;
  }
}

/**
 * Open Modal to Create New Budget
 */
function openCreateBudgetModal() {
  editingBudgetId = null;
  editingBudgetCategory = null;
  const modal = document.getElementById("budget-modal");
  const modalTitle = document.getElementById("budget-modal-title");
  const categorySelect = document.getElementById("budget-modal-category");
  const amountInput = document.getElementById("budget-modal-amount");
  const submitBtn = document.getElementById("budget-modal-submit-btn") || document.querySelector("#budget-modal-form button[type='submit']");

  if (!modal) return;

  if (modalTitle) modalTitle.textContent = "Create Category Budget Envelope";
  if (submitBtn) {
    submitBtn.textContent = "Save Budget";
    submitBtn.disabled = false;
  }
  if (categorySelect) {
    categorySelect.disabled = false;
    categorySelect.value = "Food";
  }
  if (amountInput) amountInput.value = "10000";

  modal.classList.add("active");
  if (amountInput) {
    setTimeout(() => amountInput.focus(), 150);
  }
}

/**
 * Open Modal to Adjust Existing Budget Limit
 * Robust signature: handles (budgetId, category, currentAmount) OR (category, currentAmount)
 */
function openEditBudgetModal(arg1, arg2, arg3) {
  let budgetId = null;
  let category = "Food";
  let currentAmount = 10000;

  if (arg3 !== undefined) {
    budgetId = arg1;
    category = String(arg2);
    currentAmount = arg3;
  } else if (arg2 !== undefined) {
    if (typeof arg1 === "number") {
      budgetId = arg1;
      currentAmount = arg2;
    } else {
      category = String(arg1);
      currentAmount = arg2;
      // Look up budgetId from AppState
      const match = (AppState.budgets || []).find(b => b.category.toLowerCase() === category.toLowerCase());
      if (match) budgetId = match.id;
    }
  } else if (arg1 !== undefined) {
    category = String(arg1);
    const match = (AppState.budgets || []).find(b => b.category.toLowerCase() === category.toLowerCase());
    if (match) {
      budgetId = match.id;
      currentAmount = match.amount;
    }
  }

  editingBudgetId = budgetId;
  editingBudgetCategory = category;

  const modal = document.getElementById("budget-modal");
  const modalTitle = document.getElementById("budget-modal-title");
  const categorySelect = document.getElementById("budget-modal-category");
  const amountInput = document.getElementById("budget-modal-amount");
  const submitBtn = document.getElementById("budget-modal-submit-btn") || document.querySelector("#budget-modal-form button[type='submit']");

  if (!modal) return;

  if (modalTitle) modalTitle.textContent = `Adjust Budget for ${category}`;
  if (submitBtn) {
    submitBtn.textContent = "Update Budget";
    submitBtn.disabled = false;
  }
  if (categorySelect) {
    categorySelect.value = category;
    categorySelect.disabled = true; // Category locked during envelope limit adjustment
  }
  if (amountInput) amountInput.value = currentAmount;

  modal.classList.add("active");
  if (amountInput) {
    setTimeout(() => amountInput.focus(), 150);
  }
}

function closeBudgetModal() {
  const modal = document.getElementById("budget-modal");
  if (modal) modal.classList.remove("active");
  editingBudgetId = null;
  editingBudgetCategory = null;
}

/**
 * Handle Save Budget (Create or Update via FastAPI)
 */
async function handleSaveBudget(e) {
  if (e && typeof e.preventDefault === "function") {
    e.preventDefault();
  }
  const categorySelect = document.getElementById("budget-modal-category") || document.querySelector("#budget-modal-form select");
  const amountInput = document.getElementById("budget-modal-amount") || document.querySelector("#budget-modal-form input[type='number']");

  const category = (categorySelect && categorySelect.value) ? categorySelect.value : (editingBudgetCategory || "Other");
  const rawAmount = (amountInput && amountInput.value) ? amountInput.value : "";
  const numAmount = parseFloat(rawAmount);
  const now = new Date();
  const month = now.getMonth() + 1;
  const year = now.getFullYear();

  if (!category) {
    showToast("Validation Error", "Please select a budget category.", "warning");
    return;
  }

  if (isNaN(numAmount) || numAmount <= 0) {
    showToast("Validation Error", "Please enter a valid positive budget amount.", "warning");
    if (amountInput) amountInput.focus();
    return;
  }

  const amountStr = numAmount.toFixed(2);
  const submitBtn = document.getElementById("budget-modal-submit-btn") || document.querySelector("#budget-modal-form button[type='submit']");
  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.textContent = "Saving...";
  }

  try {
    if (editingBudgetId) {
      await apiPut(`/budgets/${editingBudgetId}`, {
        amount: amountStr
      });
      showToast("Budget Updated", `Updated ${category} budget to ${formatCurrency(numAmount)}.`, "success");
    } else {
      // Check if existing budget exists for this category
      const existing = (AppState.budgets || []).find(b => b.category.toLowerCase() === category.toLowerCase());
      if (existing) {
        await apiPut(`/budgets/${existing.id}`, {
          amount: amountStr
        });
        showToast("Budget Updated", `Updated ${category} budget to ${formatCurrency(numAmount)}.`, "success");
      } else {
        await apiPost("/budgets", {
          category,
          amount: amountStr,
          month,
          year
        });
        showToast("Budget Set", `Set ${category} envelope to ${formatCurrency(numAmount)}.`, "success");
      }
    }

    closeBudgetModal();
    await loadAppData();
    renderBudgetsView();

    if (typeof loadInsightsView === "function") loadInsightsView();
    if (typeof loadAnalyticsView === "function") loadAnalyticsView();
  } catch (err) {
    console.error("Failed to save budget:", err);
    showToast("Budget Error", err.message || "Failed to save budget limit.", "danger");
  } finally {
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.textContent = editingBudgetId ? "Update Budget" : "Save Budget";
    }
  }
}

/**
 * Delete Budget Envelope via FastAPI
 */
async function handleDeleteBudget(budgetId) {
  if (!confirm("Are you sure you want to remove this budget envelope?")) return;

  try {
    await apiDelete(`/budgets/${budgetId}`);
    showToast("Budget Removed", "Budget envelope deleted successfully.", "success");
    await loadAppData();
    renderBudgetsView();

    if (typeof loadInsightsView === "function") loadInsightsView();
    if (typeof loadAnalyticsView === "function") loadAnalyticsView();
  } catch (err) {
    console.error("Failed to delete budget:", err);
    showToast("Delete Failed", err.message || "Failed to delete budget envelope.", "danger");
  }
}

// Expose budget modal functions globally for inline HTML onclick attributes
window.openCreateBudgetModal = openCreateBudgetModal;
window.openEditBudgetModal = openEditBudgetModal;
window.closeBudgetModal = closeBudgetModal;
window.handleDeleteBudget = handleDeleteBudget;
window.initBudgets = initBudgets;
window.renderBudgetsView = renderBudgetsView;
