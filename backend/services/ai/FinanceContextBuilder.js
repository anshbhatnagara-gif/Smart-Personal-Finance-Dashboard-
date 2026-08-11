const { executeTool } = require('./tools/handlers');

/**
 * Helper to retrieve current month YYYY-MM string in local time
 */
const getCurrentMonthString = () => {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  return `${year}-${month}`;
};

/**
 * FinanceContextBuilder
 * Builds clean, targeted user-specific financial context objects
 * without dumping unindexed or excessive records into LLM prompts.
 */
class FinanceContextBuilder {
  /**
   * Fetches targeted user metrics for a specific month or current month.
   * @param {string} userId - Authenticated User ID
   * @param {object} [options] - Options like month
   * @returns {Promise<object>} Compact financial context snapshot
   */
  static async buildUserContext(userId, options = {}) {
    const month = options.month || getCurrentMonthString();

    try {
      const [summary, budgetProgress, alerts, savings] = await Promise.all([
        executeTool(userId, 'getTransactionSummary', { month }),
        executeTool(userId, 'analyzeBudget', { month }),
        executeTool(userId, 'generateFinancialAlerts', { month }),
        executeTool(userId, 'analyzeSavings', { month }),
      ]);

      return {
        month,
        totalIncome: summary.totalIncome || 0,
        totalExpense: summary.totalExpense || 0,
        netSavings: summary.netSavings || 0,
        savingsRate: savings.savingsRatePercentage || 0,
        budgetLimit: budgetProgress.budgetLimit || 0,
        budgetSpent: budgetProgress.spentAmount || 0,
        remainingBudget: budgetProgress.remainingAmount || 0,
        isBudgetExceeded: budgetProgress.isExceeded || false,
        topCategories: (summary.categoryBreakdown || []).slice(0, 5),
        recentTransactions: (summary.recentTransactions || []).slice(0, 5),
        activeAlerts: alerts || []
      };
    } catch (error) {
      console.error('[FinanceContextBuilder Error]:', error.message);
      return {
        month,
        error: 'Unable to compile full financial context'
      };
    }
  }

  /**
   * Formats a financial context object into a clean text prompt snippet.
   * @param {object} context 
   * @returns {string} Formatted prompt text
   */
  static formatContextText(context) {
    if (!context || context.error) {
      return 'User Financial Context: Data unavailable.';
    }

    return `
USER FINANCIAL SNAPSHOT (${context.month}):
- Total Income: ₹${context.totalIncome}
- Total Expenses: ₹${context.totalExpense}
- Net Savings: ₹${context.netSavings} (Savings Rate: ${context.savingsRate}%)
- Monthly Budget Limit: ₹${context.budgetLimit} (Spent: ₹${context.budgetSpent}, Remaining: ₹${context.remainingBudget})
- Budget Status: ${context.isBudgetExceeded ? 'EXCEEDED' : 'WITHIN LIMIT'}
- Top Categories: ${JSON.stringify(context.topCategories)}
- Active Alerts: ${JSON.stringify(context.activeAlerts)}
`.trim();
  }
}

module.exports = FinanceContextBuilder;
