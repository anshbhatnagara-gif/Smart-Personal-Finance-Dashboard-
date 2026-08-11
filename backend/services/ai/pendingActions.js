const crypto = require('crypto');

const pendingActions = new Map();

// Default expiration: 5 minutes (300,000 milliseconds)
const EXPIRATION_MS = 5 * 60 * 1000;

/**
 * Creates a unique pending action on the server.
 * @param {string} userId - Authenticated user identity
 * @param {string} action - Action name (e.g. 'createExpense')
 * @param {object} args - Sanitized arguments for mutation
 * @returns {object} The created pending action record
 */
const createPendingAction = (userId, action, args) => {
  const actionId = crypto.randomUUID();
  const now = Date.now();
  const entry = {
    actionId,
    userId: userId.toString(),
    action,
    arguments: args,
    createdAt: now,
    expiresAt: now + EXPIRATION_MS,
    status: 'pending'
  };

  pendingActions.set(actionId, entry);

  // Set timeout cleanup for memory safety
  setTimeout(() => {
    const active = pendingActions.get(actionId);
    if (active && active.status === 'pending') {
      pendingActions.delete(actionId);
    }
  }, EXPIRATION_MS);

  return entry;
};

/**
 * Resolves a pending action. Validates expiration and deletes expired entries.
 * @param {string} actionId - Unique action ID
 * @returns {object|null} The action entry or null if not found/expired
 */
const getPendingAction = (actionId) => {
  const entry = pendingActions.get(actionId);
  if (!entry) return null;

  // Verify expiration
  if (Date.now() > entry.expiresAt) {
    entry.status = 'expired';
    pendingActions.delete(actionId);
    return null;
  }

  return entry;
};

/**
 * Updates status and handles subsequent cleanup delay.
 * Keeps action stored briefly (1 minute) to support replay prevention messages.
 * @param {string} actionId
 * @param {string} status - 'approved' | 'cancelled'
 */
const updateActionStatus = (actionId, status) => {
  const entry = pendingActions.get(actionId);
  if (entry) {
    entry.status = status;
    setTimeout(() => {
      pendingActions.delete(actionId);
    }, 60 * 1000);
  }
};

module.exports = {
  createPendingAction,
  getPendingAction,
  updateActionStatus
};
