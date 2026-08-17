const mongoose = require('mongoose');

const budgetSchema = new mongoose.Schema(
  {
    user: {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'User',
      required: true,
    },
    monthlyBudget: {
      type: Number,
      required: [true, 'Please specify a monthly budget limit'],
      min: [0, 'Budget limit cannot be negative'],
    },
    month: {
      type: String,
      required: [true, 'Please specify the month (YYYY-MM)'],
      match: [/^\d{4}-\d{2}$/, 'Please specify month in YYYY-MM format'],
    },
    categories: [
      {
        category: {
          type: String,
          required: true,
        },
        allocatedAmount: {
          type: Number,
          required: true,
          min: [0, 'Category allocation cannot be negative'],
        }
      }
    ],
  },
  {
    timestamps: true,
  }
);

// Compound index to ensure unique budget limit per user per month
budgetSchema.index({ user: 1, month: 1 }, { unique: true });

module.exports = mongoose.model('Budget', budgetSchema);
