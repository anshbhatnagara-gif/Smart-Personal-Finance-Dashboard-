const express = require('express');
const { handleChat, handleInsights, handleConfirm, handleCancel } = require('../controllers/aiController');
const { protect } = require('../middleware/auth');

const router = express.Router();

// Enforce JWT authentication on all AI services
router.use(protect);

router.post('/chat', handleChat);
router.get('/insights', handleInsights);
router.post('/confirm', handleConfirm);
router.post('/cancel', handleCancel);

module.exports = router;
