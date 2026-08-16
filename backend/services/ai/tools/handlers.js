const mongoose = require('mongoose');
const Transaction = require('../../../models/Transaction');
const Budget = require('../../../models/Budget');
const Expense = require('../../../models/Expense');
const Income = require('../../../models/Income');

// Helper to get current month YYYY-MM in local time
const getCurrentMonthString = () => {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  return `${year}-${month}`;
};

// --- READ HANDLERS (EXECUTE DATABASE QUERY) ---

const getTransactionsHandler = async (userId, args = {}) => {
  const { type, search, startDate, endDate, page = 1, limit = 15 } = args;
  const query = { user: new mongoose.Types.ObjectId(userId) };

  if (type) {
    query.type = type;
  }

  if (search) {
    query.$or = [
      { categoryOrSource: { $regex: search, $options: 'i' } },
      { description: { $regex: search, $options: 'i' } },
    ];
  }

  if (startDate || endDate) {
    query.date = {};
    if (startDate) query.date.$gte = new Date(startDate);
    if (endDate) {
      const end = new Date(endDate);
      end.setHours(23, 59, 59, 999);
      query.date.$lte = end;
    }
  }

  const skip = (parseInt(page) - 1) * parseInt(limit);
  const total = await Transaction.countDocuments(query);
  const transactions = await Transaction.find(query)
    .sort({ date: -1 })
    .skip(skip)
    .limit(parseInt(limit));

  return {
    total,
    page: parseInt(page),
    limit: parseInt(limit),
    totalPages: Math.ceil(total / parseInt(limit)),
    transactions,
  };
};

const getTransactionSummaryHandler = async (userId, args = {}) => {
  const { month, allTime } = args;
  const isAllTime = allTime === true;
  
  let dateFilter = {};
  if (!isAllTime) {
    const targetMonth = month || getCurrentMonthString();
    const [year, monthNum] = targetMonth.split('-').map(Number);
    const startOfMonth = new Date(year, monthNum - 1, 1, 0, 0, 0, 0);
    const endOfMonth = new Date(year, monthNum, 0, 23, 59, 59, 999);
    dateFilter = { date: { $gte: startOfMonth, $lte: endOfMonth } };
  }

  const stats = await Transaction.aggregate([
    {
      $match: {
        user: new mongoose.Types.ObjectId(userId),
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

  const categoryBreakdown = await Transaction.aggregate([
    {
      $match: {
        user: new mongoose.Types.ObjectId(userId),
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

  const recentTransactions = await Transaction.find({ user: new mongoose.Types.ObjectId(userId) })
    .sort({ date: -1 })
    .limit(5);

  return {
    timePeriod: isAllTime ? 'All Time' : (month || getCurrentMonthString()),
    totalIncome,
    totalExpense,
    netSavings,
    categoryBreakdown: breakdownWithPercentage,
    recentTransactions,
  };
};

const getBudgetProgressHandler = async (userId, args = {}) => {
  const month = args.month || getCurrentMonthString();

  const budget = await Budget.findOne({ user: new mongoose.Types.ObjectId(userId), month });
  const limit = budget ? budget.monthlyBudget : 0;

  const [year, monthNum] = month.split('-').map(Number);
  const startOfMonth = new Date(year, monthNum - 1, 1, 0, 0, 0, 0);
  const endOfMonth = new Date(year, monthNum, 0, 23, 59, 59, 999);

  const [expenses, incomes] = await Promise.all([
    Expense.find({ user: new mongoose.Types.ObjectId(userId), date: { $gte: startOfMonth, $lte: endOfMonth } }),
    Income.find({ user: new mongoose.Types.ObjectId(userId), date: { $gte: startOfMonth, $lte: endOfMonth } })
  ]);

  const totalSpent = expenses.reduce((sum, item) => sum + (item.amount || 0), 0);
  const totalIncome = incomes.reduce((sum, item) => sum + (item.amount || 0), 0);
  const remaining = limit - totalSpent;
  const savings = totalIncome - totalSpent;
  const savingsRate = totalIncome > 0 ? parseFloat(((savings / totalIncome) * 100).toFixed(2)) : 0;
  const usedPercentage = limit > 0 ? parseFloat(((totalSpent / limit) * 100).toFixed(2)) : 0;

  let status = 'NO_BUDGET';
  if (limit > 0) {
    if (usedPercentage > 100) status = 'OVER_BUDGET';
    else if (usedPercentage > 85) status = 'NEAR_LIMIT';
    else if (usedPercentage > 70) status = 'ON_TRACK';
    else status = 'UNDER_BUDGET';
  }

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

  return {
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
  };
};

const recommendBudgetHandler = async (userId, args = {}) => {
  const month = args.month || getCurrentMonthString();

  const [year, monthNum] = month.split('-').map(Number);
  const startOfMonth = new Date(year, monthNum - 1, 1, 0, 0, 0, 0);
  const endOfMonth = new Date(year, monthNum, 0, 23, 59, 59, 999);

  const [incomes, expenses, allTimeExpenses, currentBudget] = await Promise.all([
    Income.find({ user: new mongoose.Types.ObjectId(userId), date: { $gte: startOfMonth, $lte: endOfMonth } }),
    Expense.find({ user: new mongoose.Types.ObjectId(userId), date: { $gte: startOfMonth, $lte: endOfMonth } }),
    Expense.find({ user: new mongoose.Types.ObjectId(userId) }),
    Budget.findOne({ user: new mongoose.Types.ObjectId(userId), month })
  ]);

  const actualIncome = incomes.reduce((sum, i) => sum + i.amount, 0);
  const currentSpending = expenses.reduce((sum, e) => sum + e.amount, 0);
  const totalAllTimeSpending = allTimeExpenses.reduce((sum, e) => sum + e.amount, 0);
  const existingBudget = currentBudget ? currentBudget.monthlyBudget : 0;

  const categoryMap = {};
  expenses.forEach(e => {
    categoryMap[e.category] = (categoryMap[e.category] || 0) + e.amount;
  });

  const uniqueMonths = new Set(allTimeExpenses.map(e => e.date ? e.date.toISOString().slice(0, 7) : month));
  const monthCount = Math.max(1, uniqueMonths.size);
  const averageExpenses = parseFloat((totalAllTimeSpending / monthCount).toFixed(2));
  const hasEnoughHistoricalData = monthCount >= 2 || allTimeExpenses.length >= 5;

  const specifiedSavingsTarget = args.savingsTarget !== undefined && args.savingsTarget !== null ? parseFloat(args.savingsTarget) : null;
  const targetSavings = specifiedSavingsTarget !== null && !isNaN(specifiedSavingsTarget) && specifiedSavingsTarget >= 0
    ? specifiedSavingsTarget
    : (actualIncome > 0 ? parseFloat((actualIncome * 0.20).toFixed(2)) : 0);

  let recommendedMonthlyBudget = 0;
  let calculationMethod = '';

  if (actualIncome > 0) {
    recommendedMonthlyBudget = Math.max(0, parseFloat((actualIncome - targetSavings).toFixed(2)));
    calculationMethod = `Income (₹${actualIncome}) minus target savings (₹${targetSavings})`;
  } else if (currentSpending > 0 || averageExpenses > 0) {
    const baseAmount = currentSpending > 0 ? currentSpending : averageExpenses;
    recommendedMonthlyBudget = parseFloat((baseAmount * 1.05).toFixed(2));
    calculationMethod = `Based on current/average expenses (₹${baseAmount}) plus 5% contingency buffer`;
  } else {
    recommendedMonthlyBudget = 0;
    calculationMethod = 'Insufficient financial data logged. Start by adding income and expense entries.';
  }

  const categoryRecommendations = Object.entries(categoryMap).map(([category, spent]) => {
    const share = currentSpending > 0 ? spent / currentSpending : 0;
    const recommendedCategoryLimit = parseFloat((recommendedMonthlyBudget * share).toFixed(2));
    const isOver = spent > recommendedCategoryLimit;
    return {
      category,
      spent,
      recommendedCategoryLimit,
      status: isOver ? 'OVER' : 'OK'
    };
  }).sort((a, b) => b.spent - a.spent);

  const overspendingCategories = categoryRecommendations.filter(c => c.status === 'OVER').map(c => c.category);

  return {
    month,
    actualIncome,
    currentSpending,
    averageExpenses,
    existingBudget,
    recommendedMonthlyBudget,
    targetSavings,
    projectedSavings: Math.max(0, actualIncome - recommendedMonthlyBudget),
    projectedSavingsRate: actualIncome > 0 ? parseFloat((((actualIncome - recommendedMonthlyBudget) / actualIncome) * 100).toFixed(2)) : 0,
    calculationMethod,
    hasEnoughHistoricalData,
    categoryRecommendations,
    overspendingCategories
  };
};

const getIncomeHandler = async (userId, args = {}) => {
  const { search, startDate, endDate } = args;
  const query = { user: new mongoose.Types.ObjectId(userId) };

  if (search) {
    query.$or = [
      { source: { $regex: search, $options: 'i' } },
      { notes: { $regex: search, $options: 'i' } },
    ];
  }

  if (startDate || endDate) {
    query.date = {};
    if (startDate) query.date.$gte = new Date(startDate);
    if (endDate) {
      const end = new Date(endDate);
      end.setHours(23, 59, 59, 999);
      query.date.$lte = end;
    }
  }

  const incomes = await Income.find(query).sort({ date: -1 });
  return incomes;
};

const getExpensesHandler = async (userId, args = {}) => {
  const { search, startDate, endDate } = args;
  const query = { user: new mongoose.Types.ObjectId(userId) };

  if (search) {
    query.$or = [
      { category: { $regex: search, $options: 'i' } },
      { description: { $regex: search, $options: 'i' } },
    ];
  }

  if (startDate || endDate) {
    query.date = {};
    if (startDate) query.date.$gte = new Date(startDate);
    if (endDate) {
      const end = new Date(endDate);
      end.setHours(23, 59, 59, 999);
      query.date.$lte = end;
    }
  }

  const expenses = await Expense.find(query).sort({ date: -1 });
  return expenses;
};

// --- ANALYTICAL READ-ONLY HANDLERS (DATA INTELLIGENCE) ---

const getMonthDateRange = (monthString) => {
  const [year, monthNum] = monthString.split('-').map(Number);
  const start = new Date(year, monthNum - 1, 1, 0, 0, 0, 0);
  const end = new Date(year, monthNum, 0, 23, 59, 59, 999);
  return { start, end };
};

const getPreviousMonthString = (monthString) => {
  const [year, monthNum] = monthString.split('-').map(Number);
  const prevDate = new Date(year, monthNum - 2, 1);
  const prevYear = prevDate.getFullYear();
  const prevMonth = String(prevDate.getMonth() + 1).padStart(2, '0');
  return `${prevYear}-${prevMonth}`;
};

const analyzeSpendingHandler = async (userId, args = {}) => {
  const month = args.month || getCurrentMonthString();
  const isAllTime = args.allTime === true;
  
  let dateFilter = {};
  if (!isAllTime) {
    const { start, end } = getMonthDateRange(month);
    dateFilter = { date: { $gte: start, $lte: end } };
  }

  const query = { user: new mongoose.Types.ObjectId(userId), ...dateFilter };
  const expenses = await Expense.find(query).sort({ date: -1 });

  const totalExpense = expenses.reduce((sum, e) => sum + e.amount, 0);
  const count = expenses.length;
  const averageExpense = count > 0 ? parseFloat((totalExpense / count).toFixed(2)) : 0;
  const highestExpense = count > 0 ? Math.max(...expenses.map(e => e.amount)) : 0;
  const lowestExpense = count > 0 ? Math.min(...expenses.map(e => e.amount)) : 0;

  // MoM Spending Comparison
  let prevMonthTotal = 0;
  let momSpendingChangePercentage = 0;

  if (!isAllTime) {
    const prevMonth = getPreviousMonthString(month);
    const { start: prevStart, end: prevEnd } = getMonthDateRange(prevMonth);
    const prevExpenses = await Expense.find({
      user: new mongoose.Types.ObjectId(userId),
      date: { $gte: prevStart, $lte: prevEnd }
    });
    prevMonthTotal = prevExpenses.reduce((sum, e) => sum + e.amount, 0);
    if (prevMonthTotal > 0) {
      momSpendingChangePercentage = parseFloat((((totalExpense - prevMonthTotal) / prevMonthTotal) * 100).toFixed(2));
    }
  }

  // Category summary
  const categoriesMap = {};
  expenses.forEach(e => {
    categoriesMap[e.category] = (categoriesMap[e.category] || 0) + e.amount;
  });
  const spendingByCategory = Object.entries(categoriesMap).map(([category, amount]) => ({
    category,
    amount,
    percentage: totalExpense > 0 ? parseFloat(((amount / totalExpense) * 100).toFixed(2)) : 0
  })).sort((a, b) => b.amount - a.amount);

  return {
    period: isAllTime ? 'All Time' : month,
    totalSpending: totalExpense,
    transactionCount: count,
    averageExpense,
    highestExpense,
    lowestExpense,
    spendingByCategory,
    previousMonthSpending: isAllTime ? null : prevMonthTotal,
    momSpendingChangePercentage: isAllTime ? null : momSpendingChangePercentage
  };
};

const analyzeIncomeHandler = async (userId, args = {}) => {
  const month = args.month || getCurrentMonthString();
  const isAllTime = args.allTime === true;

  let dateFilter = {};
  if (!isAllTime) {
    const { start, end } = getMonthDateRange(month);
    dateFilter = { date: { $gte: start, $lte: end } };
  }

  const query = { user: new mongoose.Types.ObjectId(userId), ...dateFilter };
  const incomes = await Income.find(query).sort({ date: -1 });

  const totalIncome = incomes.reduce((sum, i) => sum + i.amount, 0);
  const count = incomes.length;
  const averageIncome = count > 0 ? parseFloat((totalIncome / count).toFixed(2)) : 0;
  const largestIncome = count > 0 ? Math.max(...incomes.map(i => i.amount)) : 0;

  // MoM Income Comparison
  let prevMonthTotal = 0;
  let momIncomeChangePercentage = 0;

  if (!isAllTime) {
    const prevMonth = getPreviousMonthString(month);
    const { start: prevStart, end: prevEnd } = getMonthDateRange(prevMonth);
    const prevIncomes = await Income.find({
      user: new mongoose.Types.ObjectId(userId),
      date: { $gte: prevStart, $lte: prevEnd }
    });
    prevMonthTotal = prevIncomes.reduce((sum, i) => sum + i.amount, 0);
    if (prevMonthTotal > 0) {
      momIncomeChangePercentage = parseFloat((((totalIncome - prevMonthTotal) / prevMonthTotal) * 100).toFixed(2));
    }
  }

  // Sources breakdown
  const sourcesMap = {};
  incomes.forEach(i => {
    sourcesMap[i.source] = (sourcesMap[i.source] || 0) + i.amount;
  });
  const incomeBySource = Object.entries(sourcesMap).map(([source, amount]) => ({
    source,
    amount,
    percentage: totalIncome > 0 ? parseFloat(((amount / totalIncome) * 100).toFixed(2)) : 0
  })).sort((a, b) => b.amount - a.amount);

  return {
    period: isAllTime ? 'All Time' : month,
    totalIncome,
    transactionCount: count,
    averageIncome,
    largestIncome,
    incomeBySource,
    previousMonthIncome: isAllTime ? null : prevMonthTotal,
    momIncomeChangePercentage: isAllTime ? null : momIncomeChangePercentage
  };
};

const analyzeBudgetHandler = async (userId, args = {}) => {
  const month = args.month || getCurrentMonthString();
  
  // Reuse getBudgetProgressHandler logic
  const progress = await getBudgetProgressHandler(userId, { month });

  const utilization = progress.monthlyBudget > 0 
    ? parseFloat(((progress.totalSpent / progress.monthlyBudget) * 100).toFixed(2)) 
    : 0;

  // Spending pace projection
  const now = new Date();
  let projection = null;
  const activeMonthString = getCurrentMonthString();

  if (month === activeMonthString) {
    const currentDay = now.getDate();
    // Get total days in current month
    const totalDays = new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate();
    const dailyAverage = progress.totalSpent / currentDay;
    const projectedSpent = parseFloat((dailyAverage * totalDays).toFixed(2));
    projection = {
      projectedSpent,
      projectedRemaining: progress.monthlyBudget - projectedSpent,
      willExceed: projectedSpent > progress.monthlyBudget
    };
  }

  return {
    month,
    budgetLimit: progress.monthlyBudget,
    spentAmount: progress.totalSpent,
    remainingAmount: progress.remaining,
    utilizationPercentage: utilization,
    isExceeded: progress.isExceeded,
    projection
  };
};

const analyzeCategoriesHandler = async (userId, args = {}) => {
  const month = args.month || getCurrentMonthString();
  const isAllTime = args.allTime === true;

  const { start, end } = getMonthDateRange(month);
  const query = { 
    user: new mongoose.Types.ObjectId(userId),
    ...(isAllTime ? {} : { date: { $gte: start, $lte: end } })
  };

  const expenses = await Expense.find(query);
  const totalSpent = expenses.reduce((sum, e) => sum + e.amount, 0);

  const currentCategories = {};
  expenses.forEach(e => {
    currentCategories[e.category] = (currentCategories[e.category] || 0) + e.amount;
  });

  const categoryRanking = Object.entries(currentCategories).map(([category, amount]) => ({
    category,
    amount,
    percentage: totalSpent > 0 ? parseFloat(((amount / totalSpent) * 100).toFixed(2)) : 0
  })).sort((a, b) => b.amount - a.amount);

  // Compare category changes with previous month
  const categoryShifts = [];
  if (!isAllTime) {
    const prevMonth = getPreviousMonthString(month);
    const { start: prevStart, end: prevEnd } = getMonthDateRange(prevMonth);
    const prevExpenses = await Expense.find({
      user: new mongoose.Types.ObjectId(userId),
      date: { $gte: prevStart, $lte: prevEnd }
    });

    const prevCategories = {};
    prevExpenses.forEach(e => {
      prevCategories[e.category] = (prevCategories[e.category] || 0) + e.amount;
    });

    categoryRanking.forEach(item => {
      const prevAmount = prevCategories[item.category] || 0;
      const difference = item.amount - prevAmount;
      const shiftPercentage = prevAmount > 0 ? parseFloat(((difference / prevAmount) * 100).toFixed(2)) : 100;
      categoryShifts.push({
        category: item.category,
        currentAmount: item.amount,
        previousAmount: prevAmount,
        difference,
        shiftPercentage
      });
    });
  }

  return {
    period: isAllTime ? 'All Time' : month,
    categoryRanking,
    categoryShifts: isAllTime ? null : categoryShifts
  };
};

const compareMonthsHandler = async (userId, args = {}) => {
  const { month1, month2 } = args;
  if (!month1 || !month2) {
    throw new Error('month1 and month2 parameters are required.');
  }

  const data1 = await getTransactionSummaryHandler(userId, { month: month1 });
  const data2 = await getTransactionSummaryHandler(userId, { month: month2 });

  const incomeDiff = data1.totalIncome - data2.totalIncome;
  const expenseDiff = data1.totalExpense - data2.totalExpense;
  const savingsDiff = data1.netSavings - data2.netSavings;

  const incomeMoM = data2.totalIncome > 0 ? parseFloat(((incomeDiff / data2.totalIncome) * 100).toFixed(2)) : 0;
  const expenseMoM = data2.totalExpense > 0 ? parseFloat(((expenseDiff / data2.totalExpense) * 100).toFixed(2)) : 0;
  
  const savingsRate1 = data1.totalIncome > 0 ? parseFloat(((data1.netSavings / data1.totalIncome) * 100).toFixed(2)) : 0;
  const savingsRate2 = data2.totalIncome > 0 ? parseFloat(((data2.netSavings / data2.totalIncome) * 100).toFixed(2)) : 0;

  return {
    comparison: {
      period1: month1,
      period2: month2
    },
    month1: {
      totalIncome: data1.totalIncome,
      totalExpense: data1.totalExpense,
      netSavings: data1.netSavings,
      savingsRate: savingsRate1
    },
    month2: {
      totalIncome: data2.totalIncome,
      totalExpense: data2.totalExpense,
      netSavings: data2.netSavings,
      savingsRate: savingsRate2
    },
    deltas: {
      incomeDifference: incomeDiff,
      incomePercentageChange: incomeMoM,
      expenseDifference: expenseDiff,
      expensePercentageChange: expenseMoM,
      savingsDifference: savingsDiff,
      savingsRateDifference: parseFloat((savingsRate1 - savingsRate2).toFixed(2))
    }
  };
};

const analyzeSavingsHandler = async (userId, args = {}) => {
  const month = args.month || getCurrentMonthString();
  const isAllTime = args.allTime === true;

  const summary = await getTransactionSummaryHandler(userId, { month, allTime: isAllTime });

  const savingsRate = summary.totalIncome > 0 
    ? parseFloat(((summary.netSavings / summary.totalIncome) * 100).toFixed(2)) 
    : 0;

  let previousMonthSavings = null;
  let savingsTrendPercentage = null;

  if (!isAllTime) {
    const prevMonth = getPreviousMonthString(month);
    const prevSummary = await getTransactionSummaryHandler(userId, { month: prevMonth });
    previousMonthSavings = prevSummary.netSavings;
    
    if (previousMonthSavings > 0) {
      savingsTrendPercentage = parseFloat((((summary.netSavings - previousMonthSavings) / previousMonthSavings) * 100).toFixed(2));
    }
  }

  return {
    period: isAllTime ? 'All Time' : month,
    totalIncome: summary.totalIncome,
    totalExpenses: summary.totalExpense,
    netSavings: summary.netSavings,
    savingsRatePercentage: savingsRate,
    previousMonthSavings,
    savingsTrendPercentage
  };
};

const generateFinancialAlertsHandler = async (userId, args = {}) => {
  const month = args.month || getCurrentMonthString();

  const alerts = [];

  // 1. Budget Alerts
  const budgetProgress = await analyzeBudgetHandler(userId, { month });
  if (budgetProgress.budgetLimit > 0) {
    if (budgetProgress.isExceeded) {
      alerts.push({
        type: 'budget',
        severity: 'critical',
        title: 'Budget Exceeded',
        message: `You have exceeded your monthly budget of ₹${budgetProgress.budgetLimit} by ₹${Math.abs(budgetProgress.remainingAmount)}.`,
        supportingData: { limit: budgetProgress.budgetLimit, spent: budgetProgress.spentAmount }
      });
    } else if (budgetProgress.utilizationPercentage >= 90) {
      alerts.push({
        type: 'budget',
        severity: 'warning',
        title: 'Budget Warning',
        message: `You have utilized ${budgetProgress.utilizationPercentage}% of your budget limit. Only ₹${budgetProgress.remainingAmount} remaining.`,
        supportingData: { limit: budgetProgress.budgetLimit, spent: budgetProgress.spentAmount }
      });
    }
  }

  // 2. Unusually Large Expense Alerts (Scan for expenses > 50% of the active budget or total income)
  const { start, end } = getMonthDateRange(month);
  const expenses = await Expense.find({
    user: new mongoose.Types.ObjectId(userId),
    date: { $gte: start, $lte: end }
  });

  const incomeSummary = await analyzeIncomeHandler(userId, { month });
  const referenceIncome = incomeSummary.totalIncome;

  expenses.forEach(exp => {
    // Alert if individual purchase > 50% of monthly income OR monthly budget
    const budgetLimit = budgetProgress.budgetLimit;
    const isLargeComparedToBudget = budgetLimit > 0 && exp.amount > (budgetLimit * 0.5);
    const isLargeComparedToIncome = referenceIncome > 0 && exp.amount > (referenceIncome * 0.5);

    if (isLargeComparedToBudget || isLargeComparedToIncome) {
      alerts.push({
        type: 'spending',
        severity: 'warning',
        title: 'Unusually Large Expense',
        message: `An expense of ₹${exp.amount} for "${exp.description || exp.category}" is larger than half of your monthly budget/income.`,
        supportingData: { expenseId: exp._id, amount: exp.amount, description: exp.description || exp.category }
      });
    }
  });

  // 3. Savings Rate Alerts
  const savingsSummary = await analyzeSavingsHandler(userId, { month });
  if (savingsSummary.totalIncome > 0 && savingsSummary.savingsRatePercentage < 10) {
    alerts.push({
      type: 'savings',
      severity: 'warning',
      title: 'Low Savings Rate',
      message: `Your current savings rate is only ${savingsSummary.savingsRatePercentage}%. Try to keep savings above 10% of income.`,
      supportingData: { savingsRate: savingsSummary.savingsRatePercentage, netSavings: savingsSummary.netSavings }
    });
  }

  // 4. Savings Drop Alert
  if (savingsSummary.previousMonthSavings > 0 && savingsSummary.netSavings < savingsSummary.previousMonthSavings) {
    const dropPercent = parseFloat((((savingsSummary.previousMonthSavings - savingsSummary.netSavings) / savingsSummary.previousMonthSavings) * 100).toFixed(2));
    if (dropPercent >= 20) {
      alerts.push({
        type: 'savings',
        severity: 'info',
        title: 'Savings Dropped',
        message: `Your monthly savings rate decreased by ${dropPercent}% compared to the previous month.`,
        supportingData: { currentSavings: savingsSummary.netSavings, previousSavings: savingsSummary.previousMonthSavings }
      });
    }
  }

  return alerts;
};

// --- WRITE HANDLERS (RETURN CONFIRMATION INSTEAD OF EXECUTING) ---

const handleWriteAction = (actionName, args) => {
  // Ensure that no LLM generated userId can overwrite security bounds
  const { userId, ...cleanArgs } = args;
  
  return {
    requiresConfirmation: true,
    action: actionName,
    arguments: cleanArgs
  };
};

// --- ROUTER DISPATCHER FOR ACTIONS ---

const executeTool = async (userId, toolName, args = {}) => {
  // Enforce security check: prevent injection of custom userId in parameters
  if (args.userId || args.user) {
    delete args.userId;
    delete args.user;
  }

  switch (toolName) {
    // Read Actions
    case 'getTransactions':
    case 'searchTransactions':
      return await getTransactionsHandler(userId, args);
    case 'getTransactionSummary':
    case 'getFinancialSummary':
      return await getTransactionSummaryHandler(userId, args);
    case 'getBudgetProgress':
      return await getBudgetProgressHandler(userId, args);
    case 'getIncome':
      return await getIncomeHandler(userId, args);
    case 'getExpenses':
      return await getExpensesHandler(userId, args);

    // Analytical Read Actions
    case 'analyzeSpending':
    case 'getMonthlyTrend':
      return await analyzeSpendingHandler(userId, args);
    case 'analyzeIncome':
      return await analyzeIncomeHandler(userId, args);
    case 'analyzeBudget':
      return await analyzeBudgetHandler(userId, args);
    case 'analyzeCategories':
    case 'getCategoryBreakdown':
      return await analyzeCategoriesHandler(userId, args);
    case 'compareMonths':
      return await compareMonthsHandler(userId, args);
    case 'analyzeSavings':
      return await analyzeSavingsHandler(userId, args);
    case 'generateFinancialAlerts':
      return await generateFinancialAlertsHandler(userId, args);
    case 'recommendBudget':
      return await recommendBudgetHandler(userId, args);

    // Write Actions (Requires Client Side Consent Validation)
    case 'createIncome':
    case 'createExpense':
    case 'updateIncome':
    case 'updateExpense':
    case 'createBudget':
    case 'updateBudget':
    case 'deleteIncome':
    case 'deleteExpense':
    case 'deleteBudget':
      return handleWriteAction(toolName, args);

    default:
      throw new Error(`Tool execution handler not found for name: "${toolName}"`);
  }
};

module.exports = {
  executeTool
};
