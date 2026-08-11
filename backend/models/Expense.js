const mongoose = require('mongoose');

const expenseCategories = [
  'Food',
  'Shopping',
  'Travel',
  'Fuel',
  'Education',
  'Healthcare',
  'Entertainment',
  'Bills',
  'Rent',
  'Others',
];

const expenseSchema = new mongoose.Schema(
  {
    user: {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'User',
      required: true,
    },
    amount: {
      type: Number,
      required: [true, 'Please add an expense amount'],
      min: [0.01, 'Amount must be greater than 0'],
    },
    category: {
      type: String,
      required: [true, 'Please specify a category'],
      enum: {
        values: expenseCategories,
        message: 'Please select a valid category: ' + expenseCategories.join(', '),
      },
    },
    date: {
      type: Date,
      required: [true, 'Please specify the date'],
      default: Date.now,
    },
    description: {
      type: String,
      trim: true,
    },
  },
  {
    timestamps: true,
  }
);

module.exports = mongoose.model('Expense', expenseSchema);
