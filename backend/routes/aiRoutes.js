const express = require('express');
const { handleChat, handleInsights, handleConfirm, handleCancel } = require('../controllers/aiController');
const { protect } = require('../middleware/auth');

const router = express.Router();

// Enforce JWT authentication on all AI services
router.use(protect);

router.post('/chat', handleChat);
router.get('/insights', handleInsights);
router.post('/confirm', handleConfirm);
router.post('/confirm-action', (req, res, next) => {
  if (req.body.decision === 'reject' || req.body.decision === 'cancel') {
    return handleCancel(req, res, next);
  }
  return handleConfirm(req, res, next);
});
router.post('/cancel', handleCancel);
router.post('/cancel-action', handleCancel);

module.exports = router;
