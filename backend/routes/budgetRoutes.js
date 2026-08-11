const express = require('express');
const { setBudget, getBudget, getBudgetProgress } = require('../controllers/budgetController');
const { protect } = require('../middleware/auth');

const router = express.Router();

// Protect all routes
router.use(protect);

router.route('/')
  .post(setBudget)
  .get(getBudget);

router.route('/progress')
  .get(getBudgetProgress);

module.exports = router;
