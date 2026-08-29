/**
 * ==========================================================================
 * SMART PERSONAL FINANCE DASHBOARD - CHART.JS VISUALIZATION CONTROLLER
 * Real FastAPI-driven financial charts with smooth theme adaptivity
 * ==========================================================================
 */

let incomeExpenseChartInstance = null;
let savingsTrendChartInstance = null;
let categoryDoughnutChartInstance = null;
let budgetUtilizationChartInstance = null;

/**
 * Get color tokens based on current active theme
 */
function getChartThemeColors() {
  const isDark = (document.documentElement.getAttribute("data-theme") || "dark") === "dark";
  return {
    isDark,
    textColor: isDark ? "#9CA3AF" : "#4B5563",
    gridColor: isDark ? "rgba(255, 255, 255, 0.06)" : "rgba(0, 0, 0, 0.06)",
    tooltipBg: isDark ? "rgba(17, 24, 39, 0.95)" : "rgba(255, 255, 255, 0.95)",
    tooltipText: isDark ? "#F9FAFB" : "#111827",
    tooltipBorder: isDark ? "rgba(255, 255, 255, 0.1)" : "rgba(0, 0, 0, 0.1)",
    emerald: "#10B981",
    emeraldBg: "rgba(16, 185, 129, 0.2)",
    rose: "#F43F5E",
    roseBg: "rgba(244, 63, 94, 0.2)",
    indigo: "#6366F1",
    indigoBg: "rgba(99, 102, 241, 0.2)",
    cyan: "#06B6D4",
    amber: "#F59E0B",
    purple: "#8B5CF6",
    palette: ["#6366F1", "#10B981", "#F59E0B", "#F43F5E", "#06B6D4", "#8B5CF6", "#EC4899", "#64748B"]
  };
}

/**
 * Initialize all Chart.js instances
 */
function initCharts() {
  renderIncomeExpenseChart();
  renderSavingsTrendChart();
  renderCategoryDoughnutChart();
  renderBudgetUtilizationChart();
}

/**
 * Re-render or update all charts with fresh data
 */
function updateAllCharts() {
  renderIncomeExpenseChart();
  renderSavingsTrendChart();
  renderCategoryDoughnutChart();
  renderBudgetUtilizationChart();
}

/**
 * 1. Income vs Expenses 6-Month Chart
 */
function renderIncomeExpenseChart() {
  const ctx = document.getElementById("incomeExpenseChart");
  if (!ctx) return;

  const colors = getChartThemeColors();
  const d = AppState.dashboard;
  const trends = d?.trends || [
    { month_label: "Mar", income: 0, expenses: 0 },
    { month_label: "Apr", income: 0, expenses: 0 },
    { month_label: "May", income: 0, expenses: 0 },
    { month_label: "Jun", income: 0, expenses: 0 },
    { month_label: "Jul", income: 0, expenses: 0 },
    { month_label: "Aug", income: 0, expenses: 0 }
  ];

  const monthLabels = trends.map(t => t.month_label);
  const incomeData = trends.map(t => Number(t.income) || 0);
  const expenseData = trends.map(t => Number(t.expenses) || 0);

  if (incomeExpenseChartInstance) {
    incomeExpenseChartInstance.destroy();
  }

  incomeExpenseChartInstance = new Chart(ctx, {
    type: "bar",
    data: {
      labels: monthLabels,
      datasets: [
        {
          label: "Income",
          data: incomeData,
          backgroundColor: colors.emerald,
          borderRadius: 6,
          barPercentage: 0.6,
          categoryPercentage: 0.7
        },
        {
          label: "Expenses",
          data: expenseData,
          backgroundColor: colors.rose,
          borderRadius: 6,
          barPercentage: 0.6,
          categoryPercentage: 0.7
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: {
          position: "top",
          align: "end",
          labels: { color: colors.textColor, font: { family: "'Plus Jakarta Sans', sans-serif", weight: 600, size: 12 }, boxWidth: 12, usePointStyle: true }
        },
        tooltip: {
          backgroundColor: colors.tooltipBg,
          titleColor: colors.tooltipText,
          bodyColor: colors.tooltipText,
          borderColor: colors.tooltipBorder,
          borderWidth: 1,
          padding: 10,
          callbacks: {
            label: (item) => `${item.dataset.label}: ${formatCurrency(item.raw)}`
          }
        }
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { color: colors.textColor, font: { family: "'Plus Jakarta Sans', sans-serif" } }
        },
        y: {
          grid: { color: colors.gridColor },
          ticks: {
            color: colors.textColor,
            font: { family: "'Plus Jakarta Sans', sans-serif" },
            callback: (value) => `₹${value >= 1000 ? value / 1000 + 'k' : value}`
          }
        }
      }
    }
  });
}

/**
 * 2. Monthly Savings Trend Chart (Smooth Line/Area)
 */
function renderSavingsTrendChart() {
  const ctx = document.getElementById("savingsTrendChart");
  if (!ctx) return;

  const colors = getChartThemeColors();
  const d = AppState.dashboard;
  const trends = d?.trends || [
    { month_label: "Mar", net_savings: 0 },
    { month_label: "Apr", net_savings: 0 },
    { month_label: "May", net_savings: 0 },
    { month_label: "Jun", net_savings: 0 },
    { month_label: "Jul", net_savings: 0 },
    { month_label: "Aug", net_savings: 0 }
  ];

  const monthLabels = trends.map(t => t.month_label);
  const savingsData = trends.map(t => Number(t.net_savings) || 0);

  if (savingsTrendChartInstance) {
    savingsTrendChartInstance.destroy();
  }

  const gradient = ctx.getContext("2d").createLinearGradient(0, 0, 0, 300);
  gradient.addColorStop(0, "rgba(99, 102, 241, 0.35)");
  gradient.addColorStop(1, "rgba(99, 102, 241, 0.0)");

  savingsTrendChartInstance = new Chart(ctx, {
    type: "line",
    data: {
      labels: monthLabels,
      datasets: [{
        label: "Net Savings",
        data: savingsData,
        borderColor: colors.indigo,
        backgroundColor: gradient,
        borderWidth: 3,
        fill: true,
        tension: 0.4,
        pointBackgroundColor: colors.indigo,
        pointBorderColor: "#FFFFFF",
        pointBorderWidth: 2,
        pointRadius: 4,
        pointHoverRadius: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: colors.tooltipBg,
          titleColor: colors.tooltipText,
          bodyColor: colors.tooltipText,
          borderColor: colors.tooltipBorder,
          borderWidth: 1,
          padding: 10,
          callbacks: {
            label: (item) => `Net Savings: ${formatCurrency(item.raw)}`
          }
        }
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { color: colors.textColor, font: { family: "'Plus Jakarta Sans', sans-serif" } }
        },
        y: {
          grid: { color: colors.gridColor },
          ticks: {
            color: colors.textColor,
            font: { family: "'Plus Jakarta Sans', sans-serif" },
            callback: (value) => `₹${value >= 1000 ? value / 1000 + 'k' : value}`
          }
        }
      }
    }
  });
}

/**
 * 3. Category Expenses Doughnut Chart
 */
function renderCategoryDoughnutChart() {
  const ctx = document.getElementById("categoryDoughnutChart");
  if (!ctx) return;

  const colors = getChartThemeColors();
  const d = AppState.dashboard;
  const categories = d?.category_breakdown || [];

  if (categoryDoughnutChartInstance) {
    categoryDoughnutChartInstance.destroy();
  }

  if (categories.length === 0) {
    categoryDoughnutChartInstance = new Chart(ctx, {
      type: "doughnut",
      data: {
        labels: ["No Expenses Yet"],
        datasets: [{
          data: [1],
          backgroundColor: [colors.gridColor],
          borderWidth: 0
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: { enabled: false }
        },
        cutout: "75%"
      }
    });
    return;
  }

  const labels = categories.map(c => c.category);
  const data = categories.map(c => Number(c.amount) || 0);

  categoryDoughnutChartInstance = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: labels,
      datasets: [{
        data: data,
        backgroundColor: colors.palette.slice(0, labels.length),
        borderColor: colors.isDark ? "#111827" : "#FFFFFF",
        borderWidth: 2,
        hoverOffset: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "bottom",
          labels: {
            color: colors.textColor,
            font: { family: "'Plus Jakarta Sans', sans-serif", size: 11, weight: 600 },
            boxWidth: 10,
            usePointStyle: true,
            padding: 12
          }
        },
        tooltip: {
          backgroundColor: colors.tooltipBg,
          titleColor: colors.tooltipText,
          bodyColor: colors.tooltipText,
          borderColor: colors.tooltipBorder,
          borderWidth: 1,
          padding: 10,
          callbacks: {
            label: (item) => `${item.label}: ${formatCurrency(item.raw)} (${categories[item.dataIndex]?.percentage || 0}%)`
          }
        }
      },
      cutout: "70%"
    }
  });
}

/**
 * 4. Category Budget Utilization Bar Chart
 */
function renderBudgetUtilizationChart() {
  const ctx = document.getElementById("budgetUtilizationChart");
  if (!ctx) return;

  const colors = getChartThemeColors();
  const budgets = AppState.budgets || [];

  if (budgetUtilizationChartInstance) {
    budgetUtilizationChartInstance.destroy();
  }

  if (budgets.length === 0) {
    return;
  }

  const labels = budgets.map(b => b.category);
  const percentages = budgets.map(b => Number(b.percentage) || 0);
  const bgColors = percentages.map(p => {
    if (p > 100) return colors.rose;
    if (p >= 80) return colors.amber;
    if (p >= 60) return colors.cyan;
    return colors.emerald;
  });

  budgetUtilizationChartInstance = new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [{
        label: "Budget Used %",
        data: percentages,
        backgroundColor: bgColors,
        borderRadius: 6,
        barPercentage: 0.5
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: colors.tooltipBg,
          titleColor: colors.tooltipText,
          bodyColor: colors.tooltipText,
          borderColor: colors.tooltipBorder,
          borderWidth: 1,
          padding: 10,
          callbacks: {
            label: (item) => `Utilized: ${item.raw}%`
          }
        }
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { color: colors.textColor, font: { family: "'Plus Jakarta Sans', sans-serif" } }
        },
        y: {
          grid: { color: colors.gridColor },
          ticks: {
            color: colors.textColor,
            font: { family: "'Plus Jakarta Sans', sans-serif" },
            callback: (v) => `${v}%`
          }
        }
      }
    }
  });
}
