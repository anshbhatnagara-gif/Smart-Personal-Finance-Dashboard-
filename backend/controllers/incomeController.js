const Income = require('../models/Income');
const Transaction = require('../models/Transaction');

// @desc    Add Income
// @route   POST /api/income
// @access  Private
const addIncome = async (req, res) => {
  try {
    const { amount, source, date, notes } = req.body;

    if (!amount || !source) {
      return res.status(400).json({ success: false, message: 'Please provide amount and source' });
    }

    const incomeDate = date ? new Date(date) : new Date();

    const income = await Income.create({
      user: req.user.id,
      amount: parseFloat(amount),
      source,
      date: incomeDate,
      notes,
    });

    // Sync to Transaction collection
    await Transaction.create({
      user: req.user.id,
      type: 'income',
      amount: parseFloat(amount),
      categoryOrSource: source,
      date: incomeDate,
      description: notes || 'Income entry',
      referenceId: income._id,
    });

    res.status(201).json({ success: true, data: income });
  } catch (error) {
    console.error('Add Income Error:', error.message);
    res.status(500).json({ success: false, message: error.message });
  }
};

// @desc    Get Income History (with search and date filters)
// @route   GET /api/income
// @access  Private
const getIncome = async (req, res) => {
  try {
    const { search, startDate, endDate } = req.query;
    let query = { user: req.user.id };

    // Search query on source or notes
    if (search) {
      query.$or = [
        { source: { $regex: search, $options: 'i' } },
        { notes: { $regex: search, $options: 'i' } },
      ];
    }

    // Date filters
    if (startDate || endDate) {
      query.date = {};
      if (startDate) {
        query.date.$gte = new Date(startDate);
      }
      if (endDate) {
        // Extend to end of the day
        const end = new Date(endDate);
        end.setHours(23, 59, 59, 999);
        query.date.$lte = end;
      }
    }

    const incomes = await Income.find(query).sort({ date: -1 });
    res.status(200).json({ success: true, count: incomes.length, data: incomes });
  } catch (error) {
    console.error('Get Income Error:', error.message);
    res.status(500).json({ success: false, message: error.message });
  }
};

// @desc    Update Income
// @route   PUT /api/income/:id
// @access  Private
const updateIncome = async (req, res) => {
  try {
    const { amount, source, date, notes } = req.body;
    const { id } = req.params;

    let income = await Income.findOne({ _id: id, user: req.user.id });

    if (!income) {
      return res.status(404).json({ success: false, message: 'Income record not found' });
    }

    const updatedData = {};
    if (amount !== undefined) updatedData.amount = parseFloat(amount);
    if (source !== undefined) updatedData.source = source;
    if (date !== undefined) updatedData.date = new Date(date);
    if (notes !== undefined) updatedData.notes = notes;

    income = await Income.findByIdAndUpdate(id, updatedData, { new: true, runValidators: true });

    // Sync to Transaction collection
    const transactionData = {};
    if (amount !== undefined) transactionData.amount = parseFloat(amount);
    if (source !== undefined) transactionData.categoryOrSource = source;
    if (date !== undefined) transactionData.date = new Date(date);
    if (notes !== undefined) transactionData.description = notes;

    await Transaction.findOneAndUpdate(
      { referenceId: id, user: req.user.id },
      transactionData
    );

    res.status(200).json({ success: true, data: income });
  } catch (error) {
    console.error('Update Income Error:', error.message);
    res.status(500).json({ success: false, message: error.message });
  }
};

// @desc    Delete Income
// @route   DELETE /api/income/:id
// @access  Private
const deleteIncome = async (req, res) => {
  try {
    const { id } = req.params;

    const income = await Income.findOne({ _id: id, user: req.user.id });

    if (!income) {
      return res.status(404).json({ success: false, message: 'Income record not found' });
    }

    await Income.findByIdAndDelete(id);

    // Delete matching transaction
    await Transaction.findOneAndDelete({ referenceId: id, user: req.user.id });

    res.status(200).json({ success: true, message: 'Income record removed' });
  } catch (error) {
    console.error('Delete Income Error:', error.message);
    res.status(500).json({ success: false, message: error.message });
  }
};

module.exports = {
  addIncome,
  getIncome,
  updateIncome,
  deleteIncome,
};
