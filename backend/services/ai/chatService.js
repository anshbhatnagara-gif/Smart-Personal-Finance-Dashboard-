const ProviderFactory = require('./ProviderFactory');
const { systemInstructions } = require('./prompts/systemInstructions');
const { toolDefinitions } = require('./tools/definitions');
const FinanceContextBuilder = require('./FinanceContextBuilder');
const { AIError } = require('./errors');

/**
 * Validates and sanitizes input message and conversation history.
 * @param {*} message - Raw input message from req.body
 * @param {*} history - Raw conversation history array from req.body
 * @returns {string} Trimmed message if valid
 * @throws {AIError} Throw 400 errors for validation breaches
 */
const validateChatPayload = (message, history) => {
  // Validate message
  if (message === undefined || message === null) {
    throw new AIError('Message is required.', 400, 'INVALID_PAYLOAD', false);
  }
  if (typeof message !== 'string') {
    throw new AIError('Message must be a string.', 400, 'INVALID_PAYLOAD', false);
  }
  const trimmed = message.trim();
  if (trimmed.length === 0) {
    throw new AIError('Message cannot be empty or only whitespace.', 400, 'EMPTY_MESSAGE', false);
  }
  if (trimmed.length > 2000) {
    throw new AIError('Message payload too large. Maximum size is 2000 characters.', 400, 'PAYLOAD_TOO_LARGE', false);
  }

  // Validate history
  if (history !== undefined && history !== null) {
    if (!Array.isArray(history)) {
      throw new AIError('History must be a valid array.', 400, 'INVALID_HISTORY', false);
    }
    if (history.length > 20) {
      throw new AIError('History queue too large. Maximum size is 20 dialogue turns.', 400, 'HISTORY_TOO_LARGE', false);
    }

    const validRoles = ['user', 'assistant'];
    history.forEach((item, index) => {
      if (!item || typeof item !== 'object') {
        throw new AIError(`Invalid history format at index ${index}. Must be an object.`, 400, 'INVALID_HISTORY', false);
      }
      
      const { role, content } = item;
      if (!validRoles.includes(role)) {
        throw new AIError(`Forbidden role "${role}" in history index ${index}. Only "user" and "assistant" are permitted.`, 400, 'FORBIDDEN_ROLE', false);
      }
      if (typeof content !== 'string') {
        throw new AIError(`Content must be a string in history index ${index}.`, 400, 'INVALID_HISTORY', false);
      }
      if (content.length > 4000) {
        throw new AIError(`Dialogue content size exceeded in history index ${index}. Max 4000 chars.`, 400, 'HISTORY_ITEM_TOO_LARGE', false);
      }
    });
  }

  return trimmed;
};

/**
 * Process chat interaction through the AI provider pipeline.
 * @param {string} rawMessage - Message text
 * @param {Array<object>} rawHistory - Previous chat turns
 * @param {string} userId - Authenticated user ID (strictly injected from Express)
 * @param {object} [req] - Optional Express request for test mocks propagation
 * @returns {Promise<object>} Normalized AI response contract
 */
const processChat = async (rawMessage, rawHistory, userId, req = null) => {
  // 1. Perform strict request validation
  const message = validateChatPayload(rawMessage, rawHistory);

  // 2. Sanitize and isolate chat history structure
  const history = (rawHistory || []).map(item => ({
    role: item.role,
    content: item.content.trim()
  }));

  // 3. Resolve AI provider instance
  const provider = ProviderFactory.getProvider(req);
  if (!provider) {
    throw new AIError('AI provider is not configured. Please set the environment variables.', 503, 'AI_NOT_CONFIGURED', false);
  }

  // 4. Optionally assemble light financial context summary for high-level prompts
  let dynamicInstructions = systemInstructions;

  try {
    const result = await provider.executeWithTools(
      message, 
      history, 
      toolDefinitions, 
      userId,
      dynamicInstructions
    );
    
    // Normalize return contract:
    return {
      success: true,
      message: result.message || '',
      type: result.type || 'text',
      toolCalls: result.toolCalls || [],
      confirmation: result.confirmation || null
    };
  } catch (error) {
    if (error instanceof AIError) {
      throw error;
    }
    const isQuotaOrTimeout = error.message.includes('quota') || error.message.includes('timeout');
    throw new AIError(`AI Provider error: ${error.message}`, 500, 'AI_PROVIDER_ERROR', isQuotaOrTimeout);
  }
};

module.exports = {
  processChat,
  AIError
};
