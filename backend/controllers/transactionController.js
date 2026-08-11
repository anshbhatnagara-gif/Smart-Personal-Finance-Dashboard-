const mongoose = require('mongoose');
const Transaction = require('../models/Transaction');

// Helper to get current month in YYYY-MM format (local time)
const getCurrentMonthString = () => {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  return `${year}-${month}`;
};

// @desc    Get all transactions (unified income & expenses)
// @route   GET /api/transactions
// @access  Private
const getTransactions = async (req, res) => {
  try {
    const { type, categoryOrSource, startDate, endDate, search, page = 1, limit = 50 } = req.query;
    const query = { user: req.user.id };

    // Filter by type ('income' or 'expense')
    if (type) {
      query.type = type;
    }

    // Filter by category or source
    if (categoryOrSource) {
      query.categoryOrSource = categoryOrSource;
    }

    // Date range filters
    if (startDate || endDate) {
      query.date = {};
      if (startDate) {
        query.date.$gte = new Date(startDate);
      }
      if (endDate) {
        const end = new Date(endDate);
        end.setHours(23, 59, 59, 999);
        query.date.$lte = end;
      }
    }

    // Text search on categoryOrSource or description
    if (search) {
      query.$or = [
        { categoryOrSource: { $regex: search, $options: 'i' } },
        { description: { $regex: search, $options: 'i' } },
      ];
    }

    // Pagination
    const skip = (parseInt(page) - 1) * parseInt(limit);

    const total = await Transaction.countDocuments(query);
    const transactions = await Transaction.find(query)
      .sort({ date: -1 })
      .skip(skip)
      .limit(parseInt(limit));

    res.status(200).json({
      success: true,
      count: transactions.length,
      pagination: {
        total,
        page: parseInt(page),
        limit: parseInt(limit),
        pages: Math.ceil(total / parseInt(limit)),
      },
      data: transactions,
    });
  } catch (error) {
    console.error('Get Transactions Error:', error.message);
    res.status(500).json({ success: false, message: error.message });
  }
};

// @desc    Get dashboard summary statistics (total income, total expense, savings, recent items, category breakdown)
// @route   GET /api/transactions/summary
// @access  Private
const getTransactionSummary = async (req, res) => {
  try {
    const { month, allTime } = req.query;
    const isAllTime = allTime === 'true';

    let dateFilter = {};
    if (!isAllTime) {
      const targetMonth = month || getCurrentMonthString();
      const [year, monthNum] = targetMonth.split('-').map(Number);
      const startOfMonth = new Date(year, monthNum - 1, 1, 0, 0, 0, 0);
      const endOfMonth = new Date(year, monthNum, 0, 23, 59, 59, 999);
      dateFilter = { date: { $gte: startOfMonth, $lte: endOfMonth } };
    }

    // 1. Aggregate total income and expenses in a single query
    const stats = await Transaction.aggregate([
      {
        $match: {
          user: new mongoose.Types.ObjectId(req.user.id),
          ...dateFilter,
        },
      },
      {
        $group: {
          _id: '$type',
          total: { $sum: '$amount' },
        },
      },
    ]);

    let totalIncome = 0;
    let totalExpense = 0;

    stats.forEach((stat) => {
      if (stat._id === 'income') totalIncome = stat.total;
      if (stat._id === 'expense') totalExpense = stat.total;
    });

    const netSavings = totalIncome - totalExpense;

    // 2. Aggregate expense category breakdown
    const categoryBreakdown = await Transaction.aggregate([
      {
        $match: {
          user: new mongoose.Types.ObjectId(req.user.id),
          type: 'expense',
          ...dateFilter,
        },
      },
      {
        $group: {
          _id: '$categoryOrSource',
          amount: { $sum: '$amount' },
        },
      },
      {
        $sort: { amount: -1 },
      },
      {
        $project: {
          _id: 0,
          category: '$_id',
          amount: 1,
        },
      },
    ]);

    const breakdownWithPercentage = categoryBreakdown.map((item) => ({
      category: item.category,
      amount: item.amount,
      percentage: totalExpense > 0 ? parseFloat(((item.amount / totalExpense) * 100).toFixed(2)) : 0,
    }));

    // 3. Get recent 5 transactions
    const recentTransactions = await Transaction.find({ user: req.user.id })
      .sort({ date: -1 })
      .limit(5);

    res.status(200).json({
      success: true,
      data: {
        timePeriod: isAllTime ? 'All Time' : (month || getCurrentMonthString()),
        totalIncome,
        totalExpense,
        netSavings,
        categoryBreakdown: breakdownWithPercentage,
        recentTransactions,
      },
    });
  } catch (error) {
    console.error('Get Transaction Summary Error:', error.message);
    res.status(500).json({ success: false, message: error.message });
  }
};

// @desc    Get monthly income vs expense trends for charting (last 6 months by default)
// @route   GET /api/transactions/trends
// @access  Private
const getMonthlyTrends = async (req, res) => {
  try {
    const monthsLimit = parseInt(req.query.limit) || 6;
    const sixMonthsAgo = new Date();
    // Go to first day of the start month
    sixMonthsAgo.setMonth(sixMonthsAgo.getMonth() - monthsLimit + 1);
    sixMonthsAgo.setDate(1);
    sixMonthsAgo.setHours(0, 0, 0, 0);

    const trends = await Transaction.aggregate([
      {
        $match: {
          user: new mongoose.Types.ObjectId(req.user.id),
          date: { $gte: sixMonthsAgo },
        },
      },
      {
        $group: {
          _id: {
            month: { $dateToString: { format: '%Y-%m', date: '$date' } },
            type: '$type',
          },
          totalAmount: { $sum: '$amount' },
        },
      },
      {
        $group: {
          _id: '$_id.month',
          income: {
            $sum: {
              $cond: [{ $eq: ['$_id.type', 'income'] }, '$totalAmount', 0],
            },
          },
          expense: {
            $sum: {
              $cond: [{ $eq: ['$_id.type', 'expense'] }, '$totalAmount', 0],
            },
          },
        },
      },
      {
        $sort: { _id: 1 },
      },
      {
        $project: {
          _id: 0,
          month: '$_id',
          income: 1,
          expense: 1,
          savings: { $subtract: ['$income', '$expense'] },
        },
      },
    ]);

    res.status(200).json({ success: true, data: trends });
  } catch (error) {
    console.error('Get Monthly Trends Error:', error.message);
    res.status(500).json({ success: false, message: error.message });
  }
};

module.exports = {
  getTransactions,
  getTransactionSummary,
  getMonthlyTrends,
};
