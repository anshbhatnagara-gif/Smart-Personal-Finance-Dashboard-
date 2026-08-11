const mongoose = require('mongoose');

const transactionSchema = new mongoose.Schema(
  {
    user: {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'User',
      required: true,
    },
    type: {
      type: String,
      required: [true, 'Please specify transaction type'],
      enum: ['income', 'expense'],
    },
    amount: {
      type: Number,
      required: [true, 'Please specify transaction amount'],
      min: [0.01, 'Amount must be greater than 0'],
    },
    categoryOrSource: {
      type: String,
      required: [true, 'Please specify category or source'],
      trim: true,
    },
    date: {
      type: Date,
      required: [true, 'Please specify date'],
      default: Date.now,
    },
    description: {
      type: String,
      trim: true,
    },
    referenceId: {
      type: mongoose.Schema.Types.ObjectId,
      required: true,
    },
  },
  {
    timestamps: true,
  }
);

// Indexes for fast querying, filtering, and sorting
transactionSchema.index({ user: 1, date: -1 });
transactionSchema.index({ user: 1, type: 1 });

module.exports = mongoose.model('Transaction', transactionSchema);
