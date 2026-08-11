const { processChat, AIError } = require('../services/ai/chatService');
const ProviderFactory = require('../services/ai/ProviderFactory');
const { executeTool } = require('../services/ai/tools/handlers');
const { systemInstructions } = require('../services/ai/prompts/systemInstructions');

// @desc    Chat with the AI financial assistant
// @route   POST /api/ai/chat
// @access  Private
const handleChat = async (req, res) => {
  try {
    const { message, history } = req.body;

    // Security: Prevent any user ID override attempts from payload inputs
    if (req.body.userId || req.body.user) {
      return res.status(400).json({
        success: false,
        message: 'Supplying user parameter fields is strictly forbidden.'
      });
    }

    // Delegate execution to chat service passing express session ID and req context
    const result = await processChat(message, history, req.user.id, req);
    
    return res.status(200).json(result);
  } catch (error) {
    // Catch standard AI validation and 503 exceptions
    if (error instanceof AIError) {
      return res.status(error.statusCode).json({
        success: false,
        message: error.message
      });
    }

    // Log internally, avoid leaking debug/stack trace variables to client
    console.error('AI Chat Error:', error.stack || error.message);
    return res.status(500).json({
      success: false,
      message: 'An unexpected internal server error occurred.'
    });
  }
};

const getCurrentMonthString = () => {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  return `${year}-${month}`;
};

// @desc    Get AI-generated personalized financial insights
// @route   GET /api/ai/insights
// @access  Private
const handleInsights = async (req, res) => {
  try {
    const provider = ProviderFactory.getProvider(req);

    if (!provider) {
      return res.status(503).json({
        success: false,
        message: 'AI provider is not configured. Please set the environment variables.'
      });
    }

    const userId = req.user.id;
    const currentMonth = getCurrentMonthString();

    // 1. Gather compact metrics from read tool handlers
    const summary = await executeTool(userId, 'getTransactionSummary', { month: currentMonth });
    const budgetProgress = await executeTool(userId, 'analyzeBudget', { month: currentMonth });
    const activeAlerts = await executeTool(userId, 'generateFinancialAlerts', { month: currentMonth });
    const savingsSummary = await executeTool(userId, 'analyzeSavings', { month: currentMonth });

    // 2. Build secure, compact prompt
    const prompt = `
Analyze the following financial metrics for the month of ${currentMonth} and provide concise recommendations:
- Total Income: ₹${summary.totalIncome}
- Total Expenses: ₹${summary.totalExpense}
- Net Savings: ₹${summary.netSavings}
- Savings Rate: ${savingsSummary.savingsRatePercentage}%
- Budget Limit: ₹${budgetProgress.budgetLimit}
- Total Budget Spent: ₹${budgetProgress.spentAmount}
- Budget Utilization: ${budgetProgress.utilizationPercentage}%
- Exceeded Status: ${budgetProgress.isExceeded ? 'YES' : 'NO'}
- Category Breakdown: ${JSON.stringify(summary.categoryBreakdown.slice(0, 5))}
- Alerts List: ${JSON.stringify(activeAlerts)}

Generate structured JSON containing:
1. "insights": list of points. Each must have type ("spending", "income", "budget", "savings"), severity ("info", "warning", "critical"), title, message, and a clean data object.
2. "summary": A concise, natural summary paragraph of the overall financial standing.
`.trim();

    // 3. Define schema matching the expected contract
    const schema = {
      type: 'object',
      properties: {
        insights: {
          type: 'array',
          items: {
            type: 'object',
            properties: {
              type: { type: 'string', enum: ['spending', 'income', 'budget', 'savings'] },
              severity: { type: 'string', enum: ['info', 'warning', 'critical'] },
              title: { type: 'string' },
              message: { type: 'string' },
              data: { type: 'object' }
            },
            required: ['type', 'severity', 'title', 'message']
          }
        },
        summary: { type: 'string' }
      },
      required: ['insights', 'summary']
    };

    // 4. Request structured response from Gemini
    const result = await provider.generateStructuredResponse(prompt, schema, systemInstructions);

    return res.status(200).json({
      success: true,
      insights: result.insights || [],
      summary: result.summary || '',
      generatedAt: new Date().toISOString()
    });

  } catch (error) {
    console.error('AI Insights Error:', error.stack || error.message);
    return res.status(500).json({
      success: false,
      message: 'An unexpected internal server error occurred.'
    });
  }
};

// @desc    Confirm and execute a pending AI-proposed write mutation
// @route   POST /api/ai/confirm
// @access  Private
const handleConfirm = async (req, res) => {
  try {
    const { actionId } = req.body;
    const { getPendingAction, updateActionStatus } = require('../services/ai/pendingActions');
    const Expense = require('../models/Expense');
    const Income = require('../models/Income');
    const Budget = require('../models/Budget');
    const Transaction = require('../models/Transaction');
    const mongoose = require('mongoose');

    if (!actionId) {
      return res.status(400).json({ success: false, message: 'Please provide actionId' });
    }

    const pending = getPendingAction(actionId);
    if (!pending) {
      return res.status(400).json({ success: false, message: 'Action has already been processed, expired, or is invalid.' });
    }

    // Verify ownership
    if (pending.userId !== req.user.id.toString()) {
      return res.status(403).json({ success: false, message: 'Unauthorized access to this action.' });
    }

    if (pending.status !== 'pending') {
      return res.status(400).json({ success: false, message: 'Action has already been processed.' });
    }

    const { action, arguments: args } = pending;

    // Execute database operations based on action name
    let result = null;

    switch (action) {
      case 'createIncome': {
        const incomeDate = args.date ? new Date(args.date) : new Date();
        const income = await Income.create({
          user: new mongoose.Types.ObjectId(req.user.id),
          amount: parseFloat(args.amount),
          source: args.source,
          date: incomeDate,
          notes: args.notes
        });
        await Transaction.create({
          user: new mongoose.Types.ObjectId(req.user.id),
          type: 'income',
          amount: parseFloat(args.amount),
          categoryOrSource: args.source,
          date: incomeDate,
          description: args.notes || 'Income entry via AI',
          referenceId: income._id
        });
        result = income;
        break;
      }

      case 'createExpense': {
        const expenseDate = args.date ? new Date(args.date) : new Date();
        const expense = await Expense.create({
          user: new mongoose.Types.ObjectId(req.user.id),
          amount: parseFloat(args.amount),
          category: args.category,
          date: expenseDate,
          description: args.description
        });
        await Transaction.create({
          user: new mongoose.Types.ObjectId(req.user.id),
          type: 'expense',
          amount: parseFloat(args.amount),
          categoryOrSource: args.category,
          date: expenseDate,
          description: args.description || 'Expense entry via AI',
          referenceId: expense._id
        });
        result = expense;
        break;
      }

      case 'updateIncome': {
        const income = await Income.findOne({ _id: args.id, user: new mongoose.Types.ObjectId(req.user.id) });
        if (!income) {
          return res.status(404).json({ success: false, message: 'Income record not found' });
        }
        const updatedData = {};
        if (args.amount !== undefined) updatedData.amount = parseFloat(args.amount);
        if (args.source !== undefined) updatedData.source = args.source;
        if (args.date !== undefined) updatedData.date = new Date(args.date);
        if (args.notes !== undefined) updatedData.notes = args.notes;

        const updatedIncome = await Income.findByIdAndUpdate(args.id, updatedData, { new: true, runValidators: true });
        const transactionData = {};
        if (args.amount !== undefined) transactionData.amount = parseFloat(args.amount);
        if (args.source !== undefined) transactionData.categoryOrSource = args.source;
        if (args.date !== undefined) transactionData.date = new Date(args.date);
        if (args.notes !== undefined) transactionData.description = args.notes;

        await Transaction.findOneAndUpdate(
          { referenceId: args.id, user: new mongoose.Types.ObjectId(req.user.id) },
          transactionData
        );
        result = updatedIncome;
        break;
      }

      case 'updateExpense': {
        const expense = await Expense.findOne({ _id: args.id, user: new mongoose.Types.ObjectId(req.user.id) });
        if (!expense) {
          return res.status(404).json({ success: false, message: 'Expense record not found' });
        }
        const updatedData = {};
        if (args.amount !== undefined) updatedData.amount = parseFloat(args.amount);
        if (args.category !== undefined) updatedData.category = args.category;
        if (args.date !== undefined) updatedData.date = new Date(args.date);
        if (args.description !== undefined) updatedData.description = args.description;

        const updatedExpense = await Expense.findByIdAndUpdate(args.id, updatedData, { new: true, runValidators: true });
        const transactionData = {};
        if (args.amount !== undefined) transactionData.amount = parseFloat(args.amount);
        if (args.category !== undefined) transactionData.categoryOrSource = args.category;
        if (args.date !== undefined) transactionData.date = new Date(args.date);
        if (args.description !== undefined) transactionData.description = args.description;

        await Transaction.findOneAndUpdate(
          { referenceId: args.id, user: new mongoose.Types.ObjectId(req.user.id) },
          transactionData
        );
        result = updatedExpense;
        break;
      }

      case 'createBudget':
      case 'updateBudget': {
        let budget = await Budget.findOne({ user: new mongoose.Types.ObjectId(req.user.id), month: args.month });
        if (budget) {
          budget.monthlyBudget = parseFloat(args.monthlyBudget);
          await budget.save();
        } else {
          budget = await Budget.create({
            user: new mongoose.Types.ObjectId(req.user.id),
            month: args.month,
            monthlyBudget: parseFloat(args.monthlyBudget)
          });
        }
        result = budget;
        break;
      }

      case 'deleteIncome': {
        const income = await Income.findOne({ _id: args.id, user: new mongoose.Types.ObjectId(req.user.id) });
        if (!income) {
          return res.status(404).json({ success: false, message: 'Income record not found' });
        }
        await Income.findByIdAndDelete(args.id);
        await Transaction.findOneAndDelete({ referenceId: args.id, user: new mongoose.Types.ObjectId(req.user.id) });
        result = { message: 'Income record deleted' };
        break;
      }

      case 'deleteExpense': {
        const expense = await Expense.findOne({ _id: args.id, user: new mongoose.Types.ObjectId(req.user.id) });
        if (!expense) {
          return res.status(404).json({ success: false, message: 'Expense record not found' });
        }
        await Expense.findByIdAndDelete(args.id);
        await Transaction.findOneAndDelete({ referenceId: args.id, user: new mongoose.Types.ObjectId(req.user.id) });
        result = { message: 'Expense record deleted' };
        break;
      }

      case 'deleteBudget': {
        const budgetMonth = args.month || getCurrentMonthString();
        const budget = await Budget.findOne({ month: budgetMonth, user: new mongoose.Types.ObjectId(req.user.id) });
        if (!budget) {
          return res.status(404).json({ success: false, message: 'Budget setting not found for specified month' });
        }
        await Budget.findByIdAndDelete(budget._id);
        result = { message: `Budget setting for ${budgetMonth} deleted` };
        break;
      }

      default:
        return res.status(400).json({ success: false, message: 'Unknown action name' });
    }

    // Mark as approved & processed
    updateActionStatus(actionId, 'approved');

    return res.status(200).json({
      success: true,
      message: `${action} completed successfully.`,
      type: 'text',
      data: result
    });

  } catch (error) {
    console.error('Confirm Action Error:', error.stack || error.message);
    return res.status(500).json({ success: false, message: 'An unexpected internal error occurred.' });
  }
};

// @desc    Cancel a pending AI-proposed write mutation
// @route   POST /api/ai/cancel
// @access  Private
const handleCancel = async (req, res) => {
  try {
    const { actionId } = req.body;
    const { getPendingAction, updateActionStatus } = require('../services/ai/pendingActions');
    if (!actionId) {
      return res.status(400).json({ success: false, message: 'Please provide actionId' });
    }

    const pending = getPendingAction(actionId);
    if (!pending) {
      return res.status(400).json({ success: false, message: 'Action has already been processed, expired, or is invalid.' });
    }

    // Verify ownership
    if (pending.userId !== req.user.id.toString()) {
      return res.status(403).json({ success: false, message: 'Unauthorized access to this action.' });
    }

    if (pending.status !== 'pending') {
      return res.status(400).json({ success: false, message: 'Action has already been processed.' });
    }

    // Mark as cancelled
    updateActionStatus(actionId, 'cancelled');

    return res.status(200).json({
      success: true,
      message: 'Action cancelled.'
    });

  } catch (error) {
    console.error('Cancel Action Error:', error.stack || error.message);
    return res.status(500).json({ success: false, message: 'An unexpected internal error occurred.' });
  }
};

module.exports = {
  handleChat,
  handleInsights,
  handleConfirm,
  handleCancel
};
