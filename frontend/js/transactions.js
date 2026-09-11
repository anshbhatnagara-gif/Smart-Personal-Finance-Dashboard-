/**
 * ==========================================================================
 * SMART PERSONAL FINANCE DASHBOARD - TRANSACTIONS CONTROLLER
 * Real FastAPI Transaction CRUD, search, filter, sort & pagination
 * ==========================================================================
 */

let currentTxFilter = {
  search: "",
  category: "ALL",
  type: "ALL", // 'ALL' | 'income' | 'expense'
  sortBy: "date",
  sortOrder: "desc",
  page: 1,
  pageSize: 10,
  total: 0,
  totalPages: 1
};

let editingTxId = null;
let deletingTxId = null;

/**
 * Initialize Transactions UI & Event Listeners
 */
function initTransactions() {
  setupTransactionFilters();
  setupTransactionModals();
  fetchAndRenderTransactions();
}

/**
 * Setup search, filters, sorting, and pagination controls
 */
function setupTransactionFilters() {
  const searchInput = document.getElementById("tx-search-input");
  if (searchInput) {
    let debounceTimer;
    searchInput.addEventListener("input", (e) => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        currentTxFilter.search = e.target.value.trim();
        currentTxFilter.page = 1;
        fetchAndRenderTransactions();
      }, 300);
    });
  }

  const categorySelect = document.getElementById("tx-category-filter");
  if (categorySelect) {
    categorySelect.addEventListener("change", (e) => {
      currentTxFilter.category = e.target.value;
      currentTxFilter.page = 1;
      fetchAndRenderTransactions();
    });
  }

  const typeTabs = document.querySelectorAll(".tx-type-tab");
  typeTabs.forEach(tab => {
    tab.addEventListener("click", () => {
      typeTabs.forEach(t => t.classList.remove("active"));
      tab.classList.add("active");
      currentTxFilter.type = tab.dataset.type || "ALL";
      currentTxFilter.page = 1;
      fetchAndRenderTransactions();
    });
  });

  const sortSelect = document.getElementById("tx-sort-select");
  if (sortSelect) {
    sortSelect.addEventListener("change", (e) => {
      const val = e.target.value;
      if (val === "date-desc") {
        currentTxFilter.sortBy = "date";
        currentTxFilter.sortOrder = "desc";
      } else if (val === "date-asc") {
        currentTxFilter.sortBy = "date";
        currentTxFilter.sortOrder = "asc";
      } else if (val === "amount-desc") {
        currentTxFilter.sortBy = "amount";
        currentTxFilter.sortOrder = "desc";
      } else if (val === "amount-asc") {
        currentTxFilter.sortBy = "amount";
        currentTxFilter.sortOrder = "asc";
      } else if (val === "category") {
        currentTxFilter.sortBy = "category";
        currentTxFilter.sortOrder = "asc";
      }
      currentTxFilter.page = 1;
      fetchAndRenderTransactions();
    });
  }

  const pageSizeSelect = document.getElementById("tx-page-size-select");
  if (pageSizeSelect) {
    pageSizeSelect.addEventListener("change", (e) => {
      currentTxFilter.pageSize = Number(e.target.value) || 10;
      currentTxFilter.page = 1;
      fetchAndRenderTransactions();
    });
  }

  // Header quick add buttons
  const addTxBtns = document.querySelectorAll("#btn-open-add-tx, #header-quick-add-btn");
  addTxBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      openAddTransactionModal();
    });
  });
}

/**
 * Fetch transactions from FastAPI backend with query filters
 */
async function fetchAndRenderTransactions() {
  const tableBody = document.getElementById("transactions-tbody");
  if (!tableBody) return;

  const params = {
    page: currentTxFilter.page,
    page_size: currentTxFilter.pageSize,
    sort_by: currentTxFilter.sortBy,
    sort_order: currentTxFilter.sortOrder
  };

  if (currentTxFilter.search) {
    params.search = currentTxFilter.search;
  }
  if (currentTxFilter.category && currentTxFilter.category !== "ALL") {
    params.category = currentTxFilter.category;
  }
  if (currentTxFilter.type && currentTxFilter.type !== "ALL") {
    params.type = currentTxFilter.type.toLowerCase();
  }

  try {
    const res = await apiGet("/transactions", params);
    const paginated = res.data || { items: [], total: 0, page: 1, page_size: 10, total_pages: 1 };
    
    currentTxFilter.total = paginated.total;
    currentTxFilter.totalPages = paginated.total_pages;

    renderTransactionsTable(paginated.items);
    renderPaginationControls();
  } catch (err) {
    console.error("Failed to fetch transactions:", err);
    tableBody.innerHTML = `
      <tr>
        <td colspan="6" style="text-align: center; padding: 2rem; color: var(--rose);">
          Failed to load transactions: ${escapeHtml(err.message)}
        </td>
      </tr>
    `;
  }
}

/**
 * Render Transaction Table rows
 */
function renderTransactionsTable(items = []) {
  const tableBody = document.getElementById("transactions-tbody");
  if (!tableBody) return;

  if (items.length === 0) {
    tableBody.innerHTML = `
      <tr>
        <td colspan="6" style="text-align: center; padding: 3.5rem 1rem; color: var(--text-muted);">
          <div style="font-size: 2.25rem; margin-bottom: 0.5rem;">🔍</div>
          <div style="font-weight: 700; color: var(--text-primary); font-size: 1rem;">No transactions found</div>
          <div style="font-size: 0.8125rem; margin-top: 0.25rem;">Try adjusting your filters or click '+ Add Transaction' to record cash flow.</div>
        </td>
      </tr>
    `;
    return;
  }

  tableBody.innerHTML = items.map(tx => {
    const isIncome = (tx.type || "").toLowerCase() === "income";
    const dateStr = tx.transaction_date || tx.date || "";
    const formattedDate = dateStr ? new Date(dateStr).toLocaleDateString("en-IN", {
      year: "numeric", month: "short", day: "numeric"
    }) : "";

    return `
      <tr>
        <td>
          <div style="display: flex; align-items: center; gap: 0.75rem;">
            <div class="table-cat-icon">${getCategoryIcon(tx.category)}</div>
            <div>
              <div style="font-weight: 700; color: var(--text-primary); font-size: 0.875rem;">${escapeHtml(tx.title)}</div>
              <div style="font-size: 0.75rem; color: var(--text-muted);">${escapeHtml(tx.description || tx.category)}</div>
            </div>
          </div>
        </td>
        <td>
          <span class="badge ${isIncome ? 'badge-emerald' : 'badge-rose'}" style="font-size: 0.6875rem;">
            ${(tx.type || '').toUpperCase()}
          </span>
        </td>
        <td style="color: var(--text-secondary); font-size: 0.8125rem;">
          <span class="table-cat-tag">${escapeHtml(tx.category)}</span>
        </td>
        <td style="color: var(--text-secondary); font-size: 0.8125rem;">${formattedDate}</td>
        <td style="text-align: right; font-weight: 800; font-size: 0.9375rem; color: ${isIncome ? 'var(--emerald)' : 'var(--text-primary)'};">
          ${isIncome ? '+' : '-'}${formatCurrency(tx.amount)}
        </td>
        <td style="text-align: right;">
          <div style="display: flex; align-items: center; justify-content: flex-end; gap: 0.375rem;">
            <button class="btn btn-ghost btn-icon-sm" onclick="openEditTxModal(${tx.id})" title="Edit Transaction">
              <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"></path></svg>
            </button>
            <button class="btn btn-ghost btn-icon-sm" style="color: var(--rose);" onclick="openDeleteTxModal(${tx.id})" title="Delete Transaction">
              <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
            </button>
          </div>
        </td>
      </tr>
    `;
  }).join("");
}

/**
 * Render pagination numbers and previous/next buttons
 */
function renderPaginationControls() {
  const infoEl = document.getElementById("tx-pagination-info");
  const controlsEl = document.getElementById("tx-pagination-controls");
  if (!infoEl || !controlsEl) return;

  const total = currentTxFilter.total;
  const page = currentTxFilter.page;
  const pageSize = currentTxFilter.pageSize;
  const totalPages = Math.max(1, currentTxFilter.totalPages);

  const start = total === 0 ? 0 : (page - 1) * pageSize + 1;
  const end = Math.min(page * pageSize, total);

  infoEl.textContent = `Showing ${start} to ${end} of ${total} transactions`;

  let buttonsHtml = `
    <button class="btn btn-secondary btn-sm" ${page <= 1 ? 'disabled' : ''} onclick="goToTxPage(${page - 1})">
      Previous
    </button>
  `;

  for (let p = 1; p <= totalPages; p++) {
    if (p === 1 || p === totalPages || (p >= page - 1 && p <= page + 1)) {
      buttonsHtml += `
        <button class="btn btn-sm ${p === page ? 'btn-primary' : 'btn-ghost'}" onclick="goToTxPage(${p})">
          ${p}
        </button>
      `;
    } else if (p === page - 2 || p === page + 2) {
      buttonsHtml += `<span style="padding: 0 0.25rem; color: var(--text-muted);">...</span>`;
    }
  }

  buttonsHtml += `
    <button class="btn btn-secondary btn-sm" ${page >= totalPages ? 'disabled' : ''} onclick="goToTxPage(${page + 1})">
      Next
    </button>
  `;

  controlsEl.innerHTML = buttonsHtml;
}

function goToTxPage(page) {
  if (page < 1 || page > currentTxFilter.totalPages) return;
  currentTxFilter.page = page;
  fetchAndRenderTransactions();
}

/**
 * Setup Transaction Modals (Add, Edit, Delete)
 */
/**
 * Setup Transaction Modals (Add, Edit, Delete)
 */
function setupTransactionModals() {
  const form = document.getElementById("tx-modal-form");
  if (form && !form.dataset.bound) {
    form.dataset.bound = "true";
    form.addEventListener("submit", handleSaveTransaction);
  }

  const submitBtn = document.getElementById("tx-modal-submit-btn");
  if (submitBtn && !submitBtn.dataset.bound) {
    submitBtn.dataset.bound = "true";
    submitBtn.addEventListener("click", (e) => {
      if (form) {
        if (typeof form.requestSubmit === "function") {
          e.preventDefault();
          form.requestSubmit();
        }
      }
    });
  }

  const deleteConfirmBtn = document.getElementById("tx-delete-confirm-btn");
  if (deleteConfirmBtn && !deleteConfirmBtn.dataset.bound) {
    deleteConfirmBtn.dataset.bound = "true";
    deleteConfirmBtn.addEventListener("click", handleConfirmDeleteTransaction);
  }

  // Support Escape key to close transaction modals
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      const txModal = document.getElementById("tx-modal");
      const delModal = document.getElementById("tx-delete-modal");
      if (txModal && txModal.classList.contains("active")) closeTxModal();
      if (delModal && delModal.classList.contains("active")) closeDeleteTxModal();
    }
  });
}

/**
 * Open Modal to Add New Transaction
 */
function openAddTransactionModal() {
  editingTxId = null;
  const modal = document.getElementById("tx-modal");
  const modalTitle = document.getElementById("tx-modal-title");
  const form = document.getElementById("tx-modal-form");
  const submitBtn = document.getElementById("tx-modal-submit-btn") || document.querySelector("#tx-modal-form button[type='submit']");

  if (!modal || !form) return;

  if (modalTitle) modalTitle.textContent = "Record New Transaction";
  if (submitBtn) {
    submitBtn.textContent = "Save Transaction";
    submitBtn.disabled = false;
  }
  form.reset();

  const typeInput = document.getElementById("tx-modal-type") || document.querySelector("[name='type']");
  if (typeInput) typeInput.value = "expense";

  const dateInput = document.getElementById("tx-modal-date") || document.querySelector("[name='date']") || document.querySelector("[name='transaction_date']");
  if (dateInput) {
    dateInput.value = new Date().toISOString().split("T")[0];
  }

  modal.classList.add("active");
  const titleInput = document.getElementById("tx-modal-title-input") || document.querySelector("#tx-modal-form input[type='text']");
  if (titleInput) {
    setTimeout(() => titleInput.focus(), 150);
  }
}

/**
 * Open Modal to Edit Existing Transaction
 */
async function openEditTxModal(txId) {
  editingTxId = txId;
  const modal = document.getElementById("tx-modal");
  const modalTitle = document.getElementById("tx-modal-title");
  const submitBtn = document.getElementById("tx-modal-submit-btn") || document.querySelector("#tx-modal-form button[type='submit']");

  if (!modal) return;

  if (modalTitle) modalTitle.textContent = "Edit Transaction";
  if (submitBtn) {
    submitBtn.textContent = "Update Transaction";
    submitBtn.disabled = false;
  }

  try {
    const res = await apiGet(`/transactions/${txId}`);
    const tx = res.data;
    if (!tx) throw new Error("Transaction data missing from response");

    const typeEl = document.getElementById("tx-modal-type") || document.querySelector("[name='type']");
    const titleEl = document.getElementById("tx-modal-title-input") || document.querySelector("#tx-modal-form input[type='text']");
    const amountEl = document.getElementById("tx-modal-amount") || document.querySelector("#tx-modal-form input[type='number']");
    const categoryEl = document.getElementById("tx-modal-category") || document.querySelector("#tx-modal-form select:not([id='tx-modal-type'])");
    const dateEl = document.getElementById("tx-modal-date") || document.querySelector("#tx-modal-form input[type='date']");
    const descEl = document.getElementById("tx-modal-desc") || document.getElementById("tx-modal-description");

    if (typeEl) typeEl.value = tx.type;
    if (titleEl && titleEl.tagName === "INPUT") titleEl.value = tx.title || "";
    if (amountEl) amountEl.value = tx.amount;
    if (categoryEl) categoryEl.value = tx.category;
    if (dateEl) dateEl.value = tx.transaction_date || tx.date;
    if (descEl && descEl.tagName === "INPUT") descEl.value = tx.description || "";

    modal.classList.add("active");
  } catch (err) {
    console.error("Failed to load transaction for edit:", err);
    showToast("Error", err.message || "Failed to load transaction", "danger");
  }
}

function closeTxModal() {
  const modal = document.getElementById("tx-modal");
  if (modal) modal.classList.remove("active");
  editingTxId = null;
}

/**
 * Handle Save Transaction (Create or Update via FastAPI)
 */
async function handleSaveTransaction(e) {
  if (e && typeof e.preventDefault === "function") {
    e.preventDefault();
  }

  const typeEl = document.getElementById("tx-modal-type") || document.querySelector("[name='type']") || document.getElementById("tx-type");
  const titleEl = document.getElementById("tx-modal-title-input") || document.querySelector("#tx-modal-form input[type='text']") || document.getElementById("tx-title");
  const amountEl = document.getElementById("tx-modal-amount") || document.querySelector("#tx-modal-form input[type='number']") || document.getElementById("tx-amount");
  const categoryEl = document.getElementById("tx-modal-category") || document.querySelector("#tx-modal-form select:not([id='tx-modal-type'])") || document.getElementById("tx-category");
  const dateEl = document.getElementById("tx-modal-date") || document.querySelector("#tx-modal-form input[type='date']") || document.getElementById("tx-date");
  const descEl = document.getElementById("tx-modal-desc") || document.getElementById("tx-modal-description") || document.getElementById("tx-description");

  const type = (typeEl && typeEl.value) ? typeEl.value : "expense";
  const title = (titleEl && titleEl.value) ? titleEl.value.trim() : "";
  const rawAmount = (amountEl && amountEl.value) ? amountEl.value : "";
  const category = (categoryEl && categoryEl.value) ? categoryEl.value : "Other";
  const transaction_date = (dateEl && dateEl.value) ? dateEl.value : new Date().toISOString().split("T")[0];
  const description = (descEl && descEl.value) ? descEl.value.trim() : "";

  // 1. Validation Checks
  if (!title) {
    showToast("Validation Error", "Please provide a transaction title or payee name.", "warning");
    if (titleEl) titleEl.focus();
    return;
  }

  const numAmount = parseFloat(rawAmount);
  if (isNaN(numAmount) || numAmount <= 0) {
    showToast("Validation Error", "Please enter a valid positive transaction amount.", "warning");
    if (amountEl) amountEl.focus();
    return;
  }

  if (!transaction_date) {
    showToast("Validation Error", "Please select a valid transaction date.", "warning");
    if (dateEl) dateEl.focus();
    return;
  }

  const payload = {
    type,
    title,
    amount: numAmount.toFixed(2),
    category,
    transaction_date,
    description: description || null
  };

  const submitBtn = document.getElementById("tx-modal-submit-btn") || document.querySelector("#tx-modal-form button[type='submit']");
  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.textContent = editingTxId ? "Updating..." : "Saving...";
  }

  try {
    if (editingTxId) {
      await apiPut(`/transactions/${editingTxId}`, payload);
      showToast("Transaction Updated", `Updated ${title} successfully.`, "success");
    } else {
      await apiPost("/transactions", payload);
      showToast("Transaction Recorded", `Recorded ${title} (${formatCurrency(numAmount)}).`, "success");
    }

    closeTxModal();

    // Instant state refresh across all components without manual page refresh
    await Promise.all([
      fetchAndRenderTransactions(),
      loadAppData()
    ]);

    if (typeof loadInsightsView === "function") loadInsightsView();
    if (typeof loadAnalyticsView === "function") loadAnalyticsView();
  } catch (err) {
    console.error("Failed to save transaction:", err);
    showToast("Save Failed", err.message || "Failed to save transaction.", "danger");
  } finally {
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.textContent = editingTxId ? "Update Transaction" : "Save Transaction";
    }
  }
}

/**
 * Open Modal to Confirm Transaction Deletion
 */
function openDeleteTxModal(txId) {
  deletingTxId = txId;
  const modal = document.getElementById("tx-delete-modal");
  if (modal) modal.classList.add("active");
}

function closeDeleteTxModal() {
  const modal = document.getElementById("tx-delete-modal");
  if (modal) modal.classList.remove("active");
  deletingTxId = null;
}

/**
 * Handle Delete Transaction Confirmation via FastAPI
 */
async function handleConfirmDeleteTransaction() {
  if (!deletingTxId) return;

  const confirmBtn = document.getElementById("tx-delete-confirm-btn");
  if (confirmBtn) {
    confirmBtn.disabled = true;
    confirmBtn.textContent = "Deleting...";
  }

  try {
    await apiDelete(`/transactions/${deletingTxId}`);
    showToast("Transaction Deleted", "Transaction permanently removed.", "success");
    closeDeleteTxModal();
    
    await Promise.all([
      fetchAndRenderTransactions(),
      loadAppData()
    ]);

    if (typeof loadInsightsView === "function") loadInsightsView();
    if (typeof loadAnalyticsView === "function") loadAnalyticsView();
  } catch (err) {
    console.error("Failed to delete transaction:", err);
    showToast("Delete Failed", err.message || "Could not delete transaction.", "danger");
  } finally {
    if (confirmBtn) {
      confirmBtn.disabled = false;
      confirmBtn.textContent = "Delete Transaction";
    }
  }
}

// Expose functions globally for inline HTML onclick attributes
window.openAddTxModal = openAddTransactionModal;
window.openAddTransactionModal = openAddTransactionModal;
window.openEditTxModal = openEditTxModal;
window.closeTxModal = closeTxModal;
window.openDeleteTxModal = openDeleteTxModal;
window.closeDeleteTxModal = closeDeleteTxModal;
window.goToTxPage = goToTxPage;
window.initTransactions = initTransactions;


