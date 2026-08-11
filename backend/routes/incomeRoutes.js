const express = require('express');
const { addIncome, getIncome, updateIncome, deleteIncome } = require('../controllers/incomeController');
const { protect } = require('../middleware/auth');

const router = express.Router();

// Protect all routes
router.use(protect);

router.route('/')
  .post(addIncome)
  .get(getIncome);

router.route('/:id')
  .put(updateIncome)
  .delete(deleteIncome);

module.exports = router;
