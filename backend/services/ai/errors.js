/**
 * Custom Error wrapper for AI-specific exceptions with structured error support.
 */
class AIError extends Error {
  constructor(message, statusCode = 500, code = 'AI_PROVIDER_ERROR', retryable = true) {
    super(message);
    this.name = 'AIError';
    this.statusCode = statusCode;
    this.code = code;
    this.retryable = retryable;
  }
}

module.exports = {
  AIError
};
