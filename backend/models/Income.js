const mongoose = require('mongoose');

const incomeSchema = new mongoose.Schema(
  {
    user: {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'User',
      required: true,
    },
    amount: {
      type: Number,
      required: [true, 'Please add an income amount'],
      min: [0.01, 'Amount must be greater than 0'],
    },
    source: {
      type: String,
      required: [true, 'Please specify the source of income'],
      trim: true,
    },
    date: {
      type: Date,
      required: [true, 'Please specify the date'],
      default: Date.now,
    },
    notes: {
      type: String,
      trim: true,
    },
  },
  {
    timestamps: true,
  }
);

module.exports = mongoose.model('Income', incomeSchema);
