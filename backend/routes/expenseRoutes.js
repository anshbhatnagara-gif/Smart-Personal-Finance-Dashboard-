const express = require('express');
const { addExpense, getExpenses, updateExpense, deleteExpense } = require('../controllers/expenseController');
const { protect } = require('../middleware/auth');

const router = express.Router();

// Protect all routes
router.use(protect);

router.route('/')
  .post(addExpense)
  .get(getExpenses);

router.route('/:id')
  .put(updateExpense)
  .delete(deleteExpense);

module.exports = router;
