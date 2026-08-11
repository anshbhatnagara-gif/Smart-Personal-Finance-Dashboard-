const Budget = require('../models/Budget');
const Expense = require('../models/Expense');

// Helper to get current month in YYYY-MM format (local time)
const getCurrentMonthString = () => {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  return `${year}-${month}`;
};

// @desc    Set or Update Budget for a month
// @route   POST /api/budgets
// @access  Private
const setBudget = async (req, res) => {
  try {
    const { monthlyBudget, month } = req.body;

    if (monthlyBudget === undefined || !month) {
      return res.status(400).json({ success: false, message: 'Please provide monthlyBudget and month' });
    }

    // Upsert budget
    const budget = await Budget.findOneAndUpdate(
      { user: req.user.id, month },
      { monthlyBudget: parseFloat(monthlyBudget) },
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

// @desc    Get Budget Progress for a month (spent vs budget)
// @route   GET /api/budgets/progress
// @access  Private
const getBudgetProgress = async (req, res) => {
  try {
    const month = req.query.month || getCurrentMonthString();

    // Find the budget limit
    const budget = await Budget.findOne({ user: req.user.id, month });
    const limit = budget ? budget.monthlyBudget : 0;

    // Calculate start and end of the month
    const [year, monthNum] = month.split('-').map(Number);
    const startOfMonth = new Date(year, monthNum - 1, 1, 0, 0, 0, 0);
    const endOfMonth = new Date(year, monthNum, 0, 23, 59, 59, 999);

    // Sum all expenses for the user in this month
    const expenses = await Expense.find({
      user: req.user.id,
      date: { $gte: startOfMonth, $lte: endOfMonth }
    });

    const totalSpent = expenses.reduce((sum, item) => sum + item.amount, 0);

    res.status(200).json({
      success: true,
      data: {
        month,
        monthlyBudget: limit,
        totalSpent,
        remaining: limit - totalSpent,
        isExceeded: totalSpent > limit
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
};
