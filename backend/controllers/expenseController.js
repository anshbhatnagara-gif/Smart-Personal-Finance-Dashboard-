const Expense = require('../models/Expense');
const Transaction = require('../models/Transaction');

// @desc    Add Expense
// @route   POST /api/expenses
// @access  Private
const addExpense = async (req, res) => {
  try {
    const { amount, category, date, description } = req.body;

    if (amount === undefined || !category) {
      return res.status(400).json({ success: false, message: 'Please provide amount and category' });
    }

    const expenseDate = date ? new Date(date) : new Date();

    const expense = await Expense.create({
      user: req.user.id,
      amount: parseFloat(amount),
      category,
      date: expenseDate,
      description,
    });

    // Sync to Transaction collection
    await Transaction.create({
      user: req.user.id,
      type: 'expense',
      amount: parseFloat(amount),
      categoryOrSource: category,
      date: expenseDate,
      description: description || 'Expense entry',
      referenceId: expense._id,
    });

    res.status(201).json({ success: true, data: expense });
  } catch (error) {
    console.error('Add Expense Error:', error.message);
    res.status(500).json({ success: false, message: error.message });
  }
};

// @desc    Get Expense History (with search and date filters)
// @route   GET /api/expenses
// @access  Private
const getExpenses = async (req, res) => {
  try {
    const { search, startDate, endDate } = req.query;
    let query = { user: req.user.id };

    // Search query on category or description
    if (search) {
      query.$or = [
        { category: { $regex: search, $options: 'i' } },
        { description: { $regex: search, $options: 'i' } },
      ];
    }

    // Date filters
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

    const expenses = await Expense.find(query).sort({ date: -1 });
    res.status(200).json({ success: true, count: expenses.length, data: expenses });
  } catch (error) {
    console.error('Get Expenses Error:', error.message);
    res.status(500).json({ success: false, message: error.message });
  }
};

// @desc    Update Expense
// @route   PUT /api/expenses/:id
// @access  Private
const updateExpense = async (req, res) => {
  try {
    const { amount, category, date, description } = req.body;
    const { id } = req.params;

    let expense = await Expense.findOne({ _id: id, user: req.user.id });

    if (!expense) {
      return res.status(404).json({ success: false, message: 'Expense record not found' });
    }

    const updatedData = {};
    if (amount !== undefined) updatedData.amount = parseFloat(amount);
    if (category !== undefined) updatedData.category = category;
    if (date !== undefined) updatedData.date = new Date(date);
    if (description !== undefined) updatedData.description = description;

    expense = await Expense.findByIdAndUpdate(id, updatedData, { new: true, runValidators: true });

    // Sync to Transaction collection
    const transactionData = {};
    if (amount !== undefined) transactionData.amount = parseFloat(amount);
    if (category !== undefined) transactionData.categoryOrSource = category;
    if (date !== undefined) transactionData.date = new Date(date);
    if (description !== undefined) transactionData.description = description;

    await Transaction.findOneAndUpdate(
      { referenceId: id, user: req.user.id },
      transactionData
    );

    res.status(200).json({ success: true, data: expense });
  } catch (error) {
    console.error('Update Expense Error:', error.message);
    res.status(500).json({ success: false, message: error.message });
  }
};

// @desc    Delete Expense
// @route   DELETE /api/expenses/:id
// @access  Private
const deleteExpense = async (req, res) => {
  try {
    const { id } = req.params;

    const expense = await Expense.findOne({ _id: id, user: req.user.id });

    if (!expense) {
      return res.status(404).json({ success: false, message: 'Expense record not found' });
    }

    await Expense.findByIdAndDelete(id);

    // Delete matching transaction
    await Transaction.findOneAndDelete({ referenceId: id, user: req.user.id });

    res.status(200).json({ success: true, message: 'Expense record removed' });
  } catch (error) {
    console.error('Delete Expense Error:', error.message);
    res.status(500).json({ success: false, message: error.message });
  }
};

module.exports = {
  addExpense,
  getExpenses,
  updateExpense,
  deleteExpense,
};
