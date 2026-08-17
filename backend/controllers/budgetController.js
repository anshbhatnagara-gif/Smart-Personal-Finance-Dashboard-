const Budget = require('../models/Budget');
const Expense = require('../models/Expense');
const Income = require('../models/Income');

// Helper to get current month in YYYY-MM format (local time)
const getCurrentMonthString = () => {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  return `${year}-${month}`;
};

/**
 * Helper to compute budget status indicator based on utilization percentage:
 * - UNDER_BUDGET: <= 70%
 * - ON_TRACK: 71% - 85%
 * - NEAR_LIMIT: 86% - 100%
 * - OVER_BUDGET: > 100%
 */
const getBudgetStatus = (usedPercentage, limit) => {
  if (!limit || limit === 0) return 'NO_BUDGET';
  if (usedPercentage > 100) return 'OVER_BUDGET';
  if (usedPercentage > 85) return 'NEAR_LIMIT';
  if (usedPercentage > 70) return 'ON_TRACK';
  return 'UNDER_BUDGET';
};

// @desc    Set or Update Budget for a month
// @route   POST /api/budgets
// @access  Private
const setBudget = async (req, res) => {
  try {
    const { monthlyBudget, month } = req.body;

    if (monthlyBudget === undefined || monthlyBudget === null || !month) {
      return res.status(400).json({ success: false, message: 'Please provide monthlyBudget and month' });
    }

    const numericLimit = parseFloat(monthlyBudget);
    if (isNaN(numericLimit) || numericLimit < 0) {
      return res.status(400).json({ success: false, message: 'Monthly budget limit cannot be negative or invalid' });
    }

    const updateDoc = { monthlyBudget: numericLimit };
    if (Array.isArray(req.body.categories)) {
      const { normalizeBudgetCategories } = require('../services/ai/utils/budgetCalculator');
      const normalized = normalizeBudgetCategories(numericLimit, req.body.categories);
      updateDoc.categories = normalized.map(c => ({ category: c.category, allocatedAmount: c.amount }));
    }

    // Upsert budget for current authenticated user and month
    const budget = await Budget.findOneAndUpdate(
      { user: req.user.id, month },
      updateDoc,
      { new: true, upsert: true, runValidators: true }
    );

    res.status(200).json({ success: true, data: budget });
  } catch (error) {
    console.error('Set Budget Error:', error.message);
    res.status(500).json({ success: false, message: error.message });
  }
};

// @desc    Get Budget for a month
// @route   GET /api/budgets
// @access  Private
const getBudget = async (req, res) => {
  try {
    const month = req.query.month || getCurrentMonthString();

    const budget = await Budget.findOne({ user: req.user.id, month });

    res.status(200).json({ success: true, data: budget || { user: req.user.id, monthlyBudget: 0, month } });
  } catch (error) {
    console.error('Get Budget Error:', error.message);
    res.status(500).json({ success: false, message: error.message });
  }
};

// @desc    Get Detailed Budget Progress & Financial Metrics for a month
// @route   GET /api/budgets/progress
// @access  Private
const getBudgetProgress = async (req, res) => {
  try {
    const month = req.query.month || getCurrentMonthString();

    // Find the user's budget limit for the month
    const budget = await Budget.findOne({ user: req.user.id, month });
    const limit = budget ? budget.monthlyBudget : 0;

    // Calculate start and end boundaries for the target month
    const [year, monthNum] = month.split('-').map(Number);
    const startOfMonth = new Date(year, monthNum - 1, 1, 0, 0, 0, 0);
    const endOfMonth = new Date(year, monthNum, 0, 23, 59, 59, 999);

    // Query income and expenses for this user in the target month
    const [expenses, incomes] = await Promise.all([
      Expense.find({ user: req.user.id, date: { $gte: startOfMonth, $lte: endOfMonth } }),
      Income.find({ user: req.user.id, date: { $gte: startOfMonth, $lte: endOfMonth } })
    ]);

    const totalSpent = expenses.reduce((sum, item) => sum + (item.amount || 0), 0);
    const totalIncome = incomes.reduce((sum, item) => sum + (item.amount || 0), 0);
    const remaining = limit - totalSpent;
    const savings = totalIncome - totalSpent;
    const savingsRate = totalIncome > 0 ? parseFloat(((savings / totalIncome) * 100).toFixed(2)) : 0;
    const usedPercentage = limit > 0 ? parseFloat(((totalSpent / limit) * 100).toFixed(2)) : 0;
    const status = getBudgetStatus(usedPercentage, limit);

    // Category breakdown calculation
    const categoryMap = {};
    expenses.forEach(e => {
      categoryMap[e.category] = (categoryMap[e.category] || 0) + e.amount;
    });

    const categorySpending = Object.entries(categoryMap).map(([category, amount]) => ({
      category,
      amount,
      percentage: totalSpent > 0 ? parseFloat(((amount / totalSpent) * 100).toFixed(2)) : 0
    })).sort((a, b) => b.amount - a.amount);

    const highestCategory = categorySpending.length > 0 ? categorySpending[0] : null;

    res.status(200).json({
      success: true,
      data: {
        month,
        totalIncome,
        monthlyBudget: limit,
        totalSpent,
        remaining,
        savings,
        savingsRate,
        usedPercentage,
        status,
        isExceeded: totalSpent > limit,
        highestCategory,
        categorySpending
      }
    });
  } catch (error) {
    console.error('Get Budget Progress Error:', error.message);
    res.status(500).json({ success: false, message: error.message });
  }
};

module.exports = {
  setBudget,
  getBudget,
  getBudgetProgress,
  getBudgetStatus
};
