const express = require('express');
const { getTransactions, getTransactionSummary, getMonthlyTrends } = require('../controllers/transactionController');
const { protect } = require('../middleware/auth');

const router = express.Router();

// Protect all routes
router.use(protect);

router.route('/')
  .get(getTransactions);

router.route('/summary')
  .get(getTransactionSummary);

router.route('/trends')
  .get(getMonthlyTrends);

module.exports = router;
