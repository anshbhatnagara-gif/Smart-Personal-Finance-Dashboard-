const BaseProvider = require('../BaseProvider');
const { GoogleGenAI } = require('@google/genai');
const { EXPENSE_CATEGORIES } = require('../tools/definitions');
const { AIError } = require('../errors');

class GeminiProvider extends BaseProvider {
  constructor(apiKey = null) {
    super();
    this.apiKey = apiKey || process.env.AI_API_KEY;
    this.modelName = process.env.AI_MODEL || 'gemini-2.5-flash';

    if (!this.apiKey) {
      throw new Error('Gemini API key is missing. Please set AI_API_KEY in environment variables.');
    }

    if (this.apiKey === 'mock-testing-key') {
      // Stub SDK client for E2E tests to run deterministic verification checks
      this.ai = {
        models: {
          generateContent: async ({ model, contents, config }) => {
            // Check if structured response is requested
            if (config && config.responseMimeType === 'application/json') {
              return {
                text: JSON.stringify({
                  insights: [
                    {
                      type: 'budget',
                      severity: 'warning',
                      title: 'Budget Alert Simulated',
                      message: 'You have spent 90% of your food budget.',
                      data: { spent: 450, limit: 500 }
                    }
                  ],
                  summary: 'Simulated high-level summary of your financial status.'
                })
              };
            }

            // Check if tool/function response was returned in the second turn
            const toolTurn = contents.find(turn => turn.role === 'tool' || (turn.parts && turn.parts[0] && turn.parts[0].functionResponse));
            if (toolTurn) {
              let toolResult = null;
              if (toolTurn.parts && toolTurn.parts[0] && toolTurn.parts[0].functionResponse) {
                toolResult = toolTurn.parts[0].functionResponse.response.result;
              } else {
                toolResult = toolTurn.content;
              }
              return {
                text: `Mock final response: ${JSON.stringify(toolResult)}`
              };
            }

            // Inspect the current user turn prompt
            const userTurn = contents[contents.length - 1];
            const userMessage = userTurn.parts[0].text;

            if (userMessage.includes('error-trigger')) {
              throw new Error('Simulated network timeout error');
            }

            if (userMessage.startsWith('mock-tool:')) {
              const parts = userMessage.split(':');
              const toolName = parts[1];
              const argsStr = parts.slice(2).join(':');
              let args = {};
              try {
                if (argsStr) {
                  args = JSON.parse(argsStr);
                }
              } catch (e) {}

              return {
                functionCalls: [{
                  name: toolName,
                  args: args
                }]
              };
            }

            return {
              text: `Simulated response to: "${userMessage}"`
            };
          }
        }
      };
    } else {
      // Initialize the official Google Gen AI client
      this.ai = new GoogleGenAI({ apiKey: this.apiKey });
    }
  }

  /**
   * Helper method to execute model call with retry logic for transient rate-limit (429) errors.
   */
  async generateContentWithRetry(payload, maxAttempts = 3) {
    let attempt = 0;
    while (attempt < maxAttempts) {
      attempt++;
      try {
        return await this.ai.models.generateContent(payload);
      } catch (error) {
        const errorMsg = error.message || '';
        const isRateLimit = errorMsg.includes('429') || errorMsg.includes('RESOURCE_EXHAUSTED') || errorMsg.includes('quota');
        const isTransient5xx = errorMsg.includes('503') || errorMsg.includes('502') || errorMsg.includes('UNAVAILABLE');

        if ((isRateLimit || isTransient5xx) && attempt < maxAttempts) {
          const delayMs = attempt * 2000;
          console.warn(`[GeminiProvider Retry Attempt ${attempt}/${maxAttempts}]: Transient error (${errorMsg.slice(0, 100)}). Retrying in ${delayMs}ms...`);
          await new Promise((res) => setTimeout(res, delayMs));
          continue;
        }

        throw error;
      }
    }
  }

  /**
   * Generates a raw text response from a prompt.
   */
  async generateResponse(prompt, systemInstruction = '') {
    try {
      const response = await this.ai.models.generateContent({
        model: this.modelName,
        contents: prompt,
        config: {
          systemInstruction: systemInstruction || undefined
        }
      });

      if (!response || !response.text) {
        throw new Error('Received empty or malformed response from Gemini.');
      }

      return response.text;
    } catch (error) {
      this.handleError(error);
    }
  }

  /**
   * Generates a validated structured JSON object matching a given schema.
   */
  async generateStructuredResponse(prompt, schema, systemInstruction = '') {
    try {
      const response = await this.ai.models.generateContent({
        model: this.modelName,
        contents: prompt,
        config: {
          systemInstruction: systemInstruction || undefined,
          responseMimeType: 'application/json',
          responseSchema: schema
        }
      });

      if (!response || !response.text) {
        throw new Error('Received empty response from Gemini for structured call.');
      }

      return JSON.parse(response.text);
    } catch (error) {
      this.handleError(error);
    }
  }

  /**
   * Safe validator and sanitizer for Gemini tool arguments.
   * Prevents injection of MongoDB query operators, invalid formats, or oversized parameters.
   */
  validateAndSanitizeArgs(toolName, rawArgs) {
    const clean = {};
    if (!rawArgs || typeof rawArgs !== 'object') {
      return clean;
    }

    const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
    const monthRegex = /^\d{4}-\d{2}$/;

    // Guard helper to detect potential query operator injections ($where, operators, objects)
    const hasOperator = (val) => {
      if (typeof val === 'string' && (val.includes('$') || val.includes('{') || val.includes('}'))) {
        return true;
      }
      return false;
    };

    if (toolName === 'getTransactions') {
      if (rawArgs.type && ['income', 'expense'].includes(rawArgs.type)) {
        clean.type = rawArgs.type;
      }
      if (rawArgs.search && typeof rawArgs.search === 'string' && rawArgs.search.length <= 100 && !hasOperator(rawArgs.search)) {
        clean.search = rawArgs.search;
      }
      if (rawArgs.startDate && dateRegex.test(rawArgs.startDate)) {
        clean.startDate = rawArgs.startDate;
      }
      if (rawArgs.endDate && dateRegex.test(rawArgs.endDate)) {
        clean.endDate = rawArgs.endDate;
      }
      if (rawArgs.page !== undefined) {
        const p = parseInt(rawArgs.page);
        if (!isNaN(p) && p >= 1 && p <= 1000) {
          clean.page = p;
        }
      }
      if (rawArgs.limit !== undefined) {
        const l = parseInt(rawArgs.limit);
        if (!isNaN(l) && l >= 1 && l <= 50) {
          clean.limit = l;
        }
      } else {
        clean.limit = 20; // Default limit for safe responses
      }
    }

    if (toolName === 'getTransactionSummary') {
      if (rawArgs.month && monthRegex.test(rawArgs.month)) {
        clean.month = rawArgs.month;
      }
      if (rawArgs.allTime !== undefined) {
        clean.allTime = !!rawArgs.allTime;
      }
    }

    if (toolName === 'getBudgetProgress' || toolName === 'analyzeBudget' || toolName === 'generateFinancialAlerts') {
      if (rawArgs.month && monthRegex.test(rawArgs.month)) {
        clean.month = rawArgs.month;
      }
    }

    if (toolName === 'getIncome' || toolName === 'getExpenses') {
      if (rawArgs.search && typeof rawArgs.search === 'string' && rawArgs.search.length <= 100 && !hasOperator(rawArgs.search)) {
        clean.search = rawArgs.search;
      }
      if (rawArgs.startDate && dateRegex.test(rawArgs.startDate)) {
        clean.startDate = rawArgs.startDate;
      }
      if (rawArgs.endDate && dateRegex.test(rawArgs.endDate)) {
        clean.endDate = rawArgs.endDate;
      }
    }

    if (['analyzeSpending', 'analyzeIncome', 'analyzeCategories', 'analyzeSavings'].includes(toolName)) {
      if (rawArgs.month && monthRegex.test(rawArgs.month)) {
        clean.month = rawArgs.month;
      }
      if (rawArgs.allTime !== undefined) {
        clean.allTime = !!rawArgs.allTime;
      }
    }

    if (toolName === 'compareMonths') {
      if (rawArgs.month1 && monthRegex.test(rawArgs.month1)) {
        clean.month1 = rawArgs.month1;
      }
      if (rawArgs.month2 && monthRegex.test(rawArgs.month2)) {
        clean.month2 = rawArgs.month2;
      }
    }

    if (['createIncome', 'updateIncome'].includes(toolName)) {
      if (toolName === 'updateIncome') {
        if (rawArgs.id && typeof rawArgs.id === 'string' && !hasOperator(rawArgs.id)) {
          clean.id = rawArgs.id;
        }
      }
      if (rawArgs.amount !== undefined) {
        const amt = parseFloat(rawArgs.amount);
        if (!isNaN(amt) && amt > 0 && amt <= 10000000) {
          clean.amount = amt;
        }
      }
      if (rawArgs.source && typeof rawArgs.source === 'string' && rawArgs.source.length <= 100 && !hasOperator(rawArgs.source)) {
        clean.source = rawArgs.source;
      }
      if (rawArgs.date && dateRegex.test(rawArgs.date)) {
        clean.date = rawArgs.date;
      }
      if (rawArgs.notes && typeof rawArgs.notes === 'string' && rawArgs.notes.length <= 200 && !hasOperator(rawArgs.notes)) {
        clean.notes = rawArgs.notes;
      }
    }

    if (['createExpense', 'updateExpense'].includes(toolName)) {
      if (toolName === 'updateExpense') {
        if (rawArgs.id && typeof rawArgs.id === 'string' && !hasOperator(rawArgs.id)) {
          clean.id = rawArgs.id;
        }
      }
      if (rawArgs.amount !== undefined) {
        const amt = parseFloat(rawArgs.amount);
        if (!isNaN(amt) && amt > 0 && amt <= 10000000) {
          clean.amount = amt;
        }
      }
      if (rawArgs.category && typeof rawArgs.category === 'string' && EXPENSE_CATEGORIES.includes(rawArgs.category)) {
        clean.category = rawArgs.category;
      }
      if (rawArgs.date && dateRegex.test(rawArgs.date)) {
        clean.date = rawArgs.date;
      }
      if (rawArgs.description && typeof rawArgs.description === 'string' && rawArgs.description.length <= 200 && !hasOperator(rawArgs.description)) {
        clean.description = rawArgs.description;
      }
    }

    if (['createBudget', 'updateBudget'].includes(toolName)) {
      if (rawArgs.monthlyBudget !== undefined) {
        const bgt = parseFloat(rawArgs.monthlyBudget);
        if (!isNaN(bgt) && bgt > 0 && bgt <= 10000000) {
          clean.monthlyBudget = bgt;
        }
      }
      if (rawArgs.month && monthRegex.test(rawArgs.month)) {
        clean.month = rawArgs.month;
      }
    }

    if (['deleteIncome', 'deleteExpense'].includes(toolName)) {
      if (rawArgs.id && typeof rawArgs.id === 'string' && !hasOperator(rawArgs.id)) {
        clean.id = rawArgs.id;
      }
    }

    return clean;
  }

  /**
   * Executes a conversation cycle with support for multi-tool reasoning loops.
   */
  async executeWithTools(userMessage, chatHistory = [], tools = [], userId, systemInstruction = '') {
    try {
      // 1. Translate chat history roles from 'assistant' -> 'model'
      const contents = chatHistory.map((item) => ({
        role: item.role === 'assistant' ? 'model' : 'user',
        parts: [{ text: item.content }]
      }));

      // Append current message
      contents.push({
        role: 'user',
        parts: [{ text: userMessage }]
      });

      // 2. Prepare function declarations
      const functionDeclarations = tools.map((t) => ({
        name: t.name,
        description: t.description,
        parameters: t.parameters
      }));

      const MAX_TURNS = 4;
      let turnCount = 0;
      let executedToolCalls = [];

      const READ_ONLY_TOOLS = new Set([
        'getTransactions',
        'getTransactionSummary',
        'getBudgetProgress',
        'getIncome',
        'getExpenses',
        'analyzeSpending',
        'analyzeIncome',
        'analyzeBudget',
        'analyzeCategories',
        'compareMonths',
        'analyzeSavings',
        'generateFinancialAlerts',
        'getFinancialSummary',
        'searchTransactions',
        'getCategoryBreakdown',
        'getMonthlyTrend'
      ]);

      while (turnCount < MAX_TURNS) {
        turnCount++;

        // Request model completion turn with retry support
        let response = await this.generateContentWithRetry({
          model: this.modelName,
          contents,
          config: {
            systemInstruction: systemInstruction || undefined,
            tools: [{ functionDeclarations }]
          }
        });

        if (!response) {
          throw new Error('Malformed AI provider response.');
        }

        // Check for tool/function calls
        if (response.functionCalls && response.functionCalls.length > 0) {
          const call = response.functionCalls[0];
          executedToolCalls.push({ name: call.name, args: call.args });

          // Find tool definition to check classification
          const matchedTool = tools.find((t) => t.name === call.name);
          const classification = matchedTool ? matchedTool.classification : 'read';

          // WRITE TOOLS: Lock and return confirmation card immediately
          if (classification === 'write') {
            const { createPendingAction } = require('../pendingActions');
            const sanitizedArgs = this.validateAndSanitizeArgs(call.name, call.args);
            const pending = createPendingAction(userId, call.name, sanitizedArgs);

            return {
              message: `I prepared a request to execute "${call.name}". Please approve or cancel below.`,
              type: 'confirmation',
              toolCalls: executedToolCalls,
              confirmation: {
                actionId: pending.actionId,
                action: call.name,
                arguments: sanitizedArgs,
                requiresConfirmation: true
              }
            };
          }

          // READ TOOLS: Validate allowed tools
          if (!READ_ONLY_TOOLS.has(call.name)) {
            return {
              message: `The tool "${call.name}" is not permitted or enabled.`,
              type: 'text',
              toolCalls: executedToolCalls,
              confirmation: null
            };
          }

          // Sanitize arguments and execute reader handler
          const sanitizedArgs = this.validateAndSanitizeArgs(call.name, call.args);
          const { executeTool } = require('../tools/handlers');
          let toolResult = await executeTool(userId, call.name, sanitizedArgs);

          // Limit array returns to 50 items
          if (Array.isArray(toolResult)) {
            toolResult = toolResult.slice(0, 50);
          } else if (toolResult && Array.isArray(toolResult.transactions)) {
            toolResult.transactions = toolResult.transactions.slice(0, 50);
          }

          // Append function call turn and tool response turn to contents
          contents.push({
            role: 'model',
            parts: [{ functionCalls: [call] }]
          });

          contents.push({
            role: 'tool',
            parts: [{
              functionResponse: {
                name: call.name,
                response: { result: toolResult }
              }
            }]
          });

          // Continue loop to allow Gemini to analyze toolResult or invoke another tool
          continue;
        }

        // If response is text, return final response
        return {
          message: response.text || 'No response generated.',
          type: 'text',
          toolCalls: executedToolCalls,
          confirmation: null
        };
      }

      // If loop limit reached, attempt to return response text
      return {
        message: 'Completed maximum analysis steps.',
        type: 'text',
        toolCalls: executedToolCalls,
        confirmation: null
      };

    } catch (error) {
      this.handleError(error);
    }
  }

  /**
   * Safe operational error mapper converting internal exceptions into structured AIError instances.
   */
  handleError(error) {
    if (error instanceof AIError) {
      throw error;
    }

    const errorMsg = error.message || '';
    console.error('[GeminiProvider Exception]:', error.stack || errorMsg);

    if (errorMsg.includes('API key') || errorMsg.includes('API_KEY')) {
      throw new AIError('AI Assistant is not connected yet. Invalid API credentials.', 401, 'AI_AUTH_ERROR', false);
    }
    if (errorMsg.includes('RESOURCE_EXHAUSTED') || errorMsg.includes('429') || errorMsg.includes('quota')) {
      throw new AIError('Gemini API free-tier rate limit reached. Please retry in a few moments or upgrade quota.', 429, 'AI_QUOTA_EXCEEDED', true);
    }
    if (errorMsg.includes('NOT_FOUND') || errorMsg.includes('404') || errorMsg.includes('no longer available')) {
      throw new AIError(`Gemini model "${this.modelName}" was not found or is unavailable.`, 404, 'AI_MODEL_NOT_FOUND', false);
    }
    if (errorMsg.includes('timeout') || errorMsg.includes('ETIMEDOUT')) {
      throw new AIError('AI Assistant request timed out. Please try again.', 504, 'AI_TIMEOUT', true);
    }

    throw new AIError('Unable to reach the AI assistant right now. Please try again.', 500, 'AI_PROVIDER_ERROR', true);
  }
}

module.exports = GeminiProvider;
