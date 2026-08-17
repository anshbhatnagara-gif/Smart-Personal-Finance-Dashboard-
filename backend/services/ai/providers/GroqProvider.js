const BaseProvider = require('../BaseProvider');
const Groq = require('groq-sdk');
const { EXPENSE_CATEGORIES } = require('../tools/definitions');
const { AIError } = require('../errors');

// Allowed read-only analytical tool handlers
const READ_ONLY_TOOLS = new Set([
  'getTransactions',
  'searchTransactions',
  'getTransactionSummary',
  'getFinancialSummary',
  'getBudgetProgress',
  'getIncome',
  'getExpenses',
  'analyzeSpending',
  'getMonthlyTrend',
  'analyzeIncome',
  'analyzeBudget',
  'analyzeCategories',
  'getCategoryBreakdown',
  'compareMonths',
  'analyzeSavings',
  'generateFinancialAlerts',
  'recommendBudget',
]);

class GroqProvider extends BaseProvider {
  constructor(apiKey = null, model = null) {
    super();
    this.apiKey = apiKey || process.env.GROQ_API_KEY;
    this.modelName = model || process.env.GROQ_MODEL || 'llama-3.3-70b-versatile';

    if (!this.apiKey) {
      throw new Error('Groq API key is missing. Please set GROQ_API_KEY in environment variables.');
    }

    if (this.apiKey === 'mock-testing-key') {
      // Deterministic Mock SDK client for automated testing
      this.groq = {
        chat: {
          completions: {
            create: async ({ model, messages, tools, response_format }) => {
              // 1. Structured JSON output request
              if (response_format && response_format.type === 'json_object') {
                return {
                  choices: [{
                    message: {
                      content: JSON.stringify({
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
                    }
                  }]
                };
              }

              // 2. Check if a tool response turn is present in messages
              const toolTurn = messages.find(m => m.role === 'tool');
              if (toolTurn) {
                return {
                  choices: [{
                    message: {
                      content: `Mock final response: ${toolTurn.content}`
                    }
                  }]
                };
              }

              // 3. Inspect current user message
              const lastUserMessage = [...messages].reverse().find(m => m.role === 'user');
              const userText = lastUserMessage ? lastUserMessage.content : '';

              if (userText.includes('error-trigger')) {
                throw new Error('Simulated network timeout error');
              }

              if (userText.startsWith('mock-tool:')) {
                const parts = userText.split(':');
                const toolName = parts[1];
                const argsStr = parts.slice(2).join(':');
                let args = {};
                try {
                  if (argsStr) args = JSON.parse(argsStr);
                } catch (e) {}

                return {
                  choices: [{
                    message: {
                      content: null,
                      tool_calls: [{
                        id: `call_${Date.now()}`,
                        type: 'function',
                        function: {
                          name: toolName,
                          arguments: JSON.stringify(args)
                        }
                      }]
                    }
                  }]
                };
              }

              return {
                choices: [{
                  message: {
                    content: `Simulated response to: "${userText}"`
                  }
                }]
              };
            }
          }
        }
      };
    } else {
      this.groq = new Groq({
        apiKey: this.apiKey,
        timeout: 90000
      });
    }
  }

  /**
   * Helper to execute chat completions with multi-model fallback and bounded exponential backoff.
   */
  async createChatCompletionWithRetry(payload, maxAttempts = 3) {
    const fallbackModels = [this.modelName, 'llama-3.1-8b-instant', 'openai/gpt-oss-120b', 'openai/gpt-oss-20b', 'llama-3.3-70b-versatile'].filter((m, i, arr) => m && arr.indexOf(m) === i);
    
    for (let modelIdx = 0; modelIdx < fallbackModels.length; modelIdx++) {
      const currentModel = fallbackModels[modelIdx];
      const modelPayload = { ...payload, model: currentModel };
      
      let attempt = 0;
      while (attempt < maxAttempts) {
        attempt++;
        try {
          return await this.groq.chat.completions.create(modelPayload);
        } catch (error) {
          const errorMsg = (error.message || '').toLowerCase();
          const status = error.status || (error.response && error.response.status);
          const errBody = error.error || (error.response && error.response.data) || {};
          const isToolCallError = status === 400 && (errorMsg.includes('failed to call a function') || errBody.failed_generation || errBody.code === 'tool_use_failed' || errorMsg.includes('tool_use_failed'));

          // If Groq tool parse error with failed_generation, rethrow immediately for executeWithTools extraction
          if (isToolCallError) {
            throw error;
          }

          const isTpdLimit = errorMsg.includes('tokens per day') || errorMsg.includes('tpd') || errorMsg.includes('daily limit');
          const isRateLimit = status === 429 || status === 413 || errorMsg.includes('rate_limit') || errorMsg.includes('quota') || errorMsg.includes('429') || errorMsg.includes('413') || errorMsg.includes('tpm') || errorMsg.includes('request too large');
          const isTransient5xx = status >= 500 && status <= 504;
          const isNetwork = errorMsg.includes('timeout') || errorMsg.includes('timed out') || errorMsg.includes('econnreset') || errorMsg.includes('etimedout') || errorMsg.includes('connection error') || errorMsg.includes('fetch failed') || errorMsg.includes('enotfound') || errorMsg.includes('socket');

          // If daily quota exceeded on this model, switch immediately to next fallback model
          if (isTpdLimit && modelIdx < fallbackModels.length - 1) {
            console.warn(`[GroqProvider Model Fallback]: Model ${currentModel} daily quota reached. Switching to fallback model: ${fallbackModels[modelIdx + 1]}`);
            break;
          }

          if ((isRateLimit || isTransient5xx || isNetwork) && attempt < maxAttempts) {
            let delayMs = isRateLimit ? attempt * 2000 : attempt * 500;
            if (isRateLimit) {
              const waitMatch = errorMsg.match(/try again in ([\d\.]+)s/i);
              if (waitMatch && waitMatch[1]) {
                const waitSec = parseFloat(waitMatch[1]);
                if (waitSec <= 15) {
                  delayMs = Math.ceil(waitSec * 1000) + 600;
                } else if (modelIdx < fallbackModels.length - 1) {
                  console.warn(`[GroqProvider Model Fallback]: Rate limit wait is long (${waitSec}s). Switching to ${fallbackModels[modelIdx + 1]}...`);
                  break;
                }
              }
            }
            console.warn(`[GroqProvider Retry Attempt ${attempt}/${maxAttempts}]: Transient error (${errorMsg.slice(0, 100)}). Retrying in ${delayMs}ms...`);
            await new Promise((res) => setTimeout(res, delayMs));
            continue;
          }

          // If last attempt on this model and we have more models, try next model
          if (modelIdx < fallbackModels.length - 1) {
            console.warn(`[GroqProvider Model Fallback]: Model ${currentModel} failed (${errorMsg.slice(0, 80)}). Switching to ${fallbackModels[modelIdx + 1]}...`);
            break;
          }

          throw error;
        }
      }
    }
  }

  /**
   * Generates a raw text response from a prompt.
   */
  async generateResponse(prompt, systemInstruction = '') {
    try {
      const messages = [];
      if (systemInstruction) {
        messages.push({ role: 'system', content: systemInstruction });
      }
      messages.push({ role: 'user', content: prompt });

      const response = await this.createChatCompletionWithRetry({
        model: this.modelName,
        messages,
        temperature: 0.2
      });

      const text = response?.choices?.[0]?.message?.content;
      if (!text) {
        throw new Error('Received empty or malformed response from Groq.');
      }

      return text;
    } catch (error) {
      this.handleError(error);
    }
  }

  /**
   * Generates a validated structured JSON object matching a given schema.
   */
  async generateStructuredResponse(prompt, schema, systemInstruction = '') {
    try {
      const messages = [];
      const systemPrompt = `${systemInstruction || ''}\nYou MUST return a single valid JSON object strictly matching the following schema. Do NOT include markdown code blocks (\`\`\`json), comments, or text outside the JSON object.\n\nSchema:\n${JSON.stringify(schema, null, 2)}`;
      
      messages.push({ role: 'system', content: systemPrompt });
      messages.push({ role: 'user', content: prompt });

      const response = await this.createChatCompletionWithRetry({
        model: this.modelName,
        messages,
        temperature: 0.1,
        response_format: { type: 'json_object' }
      });

      const text = response?.choices?.[0]?.message?.content;
      if (!text) {
        throw new Error('Received empty response from Groq for structured call.');
      }

      return JSON.parse(text);
    } catch (error) {
      this.handleError(error);
    }
  }

  /**
   * Safe validator and sanitizer for tool arguments to prevent injection attacks.
   */
  validateAndSanitizeArgs(toolName, rawArgs) {
    const clean = {};
    if (!rawArgs || typeof rawArgs !== 'object') {
      return clean;
    }

    const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
    const monthRegex = /^\d{4}-\d{2}$/;

    const hasOperator = (val) => {
      if (typeof val === 'string' && (val.includes('$') || val.includes('{') || val.includes('}'))) {
        return true;
      }
      return false;
    };

    if (toolName === 'getTransactions') {
      if (rawArgs.type && ['income', 'expense'].includes(rawArgs.type)) clean.type = rawArgs.type;
      if (rawArgs.search && typeof rawArgs.search === 'string' && rawArgs.search.length <= 100 && !hasOperator(rawArgs.search)) clean.search = rawArgs.search;
      if (rawArgs.startDate && dateRegex.test(rawArgs.startDate)) clean.startDate = rawArgs.startDate;
      if (rawArgs.endDate && dateRegex.test(rawArgs.endDate)) clean.endDate = rawArgs.endDate;
      if (rawArgs.page !== undefined) {
        const p = parseInt(rawArgs.page);
        if (!isNaN(p) && p > 0 && p < 1000) clean.page = p;
      }
      if (rawArgs.limit !== undefined) {
        const l = parseInt(rawArgs.limit);
        if (!isNaN(l) && l > 0 && l <= 50) clean.limit = l;
      }
    } else if (['getTransactionSummary', 'getFinancialSummary', 'getBudgetProgress', 'analyzeSpending', 'getMonthlyTrend', 'analyzeIncome', 'analyzeBudget', 'analyzeCategories', 'getCategoryBreakdown', 'analyzeSavings', 'generateFinancialAlerts'].includes(toolName)) {
      if (rawArgs.month && monthRegex.test(rawArgs.month)) clean.month = rawArgs.month;
      if (rawArgs.allTime === true || rawArgs.allTime === 'true') clean.allTime = true;
    } else if (['getIncome', 'getExpenses'].includes(toolName)) {
      if (rawArgs.search && typeof rawArgs.search === 'string' && rawArgs.search.length <= 100 && !hasOperator(rawArgs.search)) clean.search = rawArgs.search;
      if (rawArgs.startDate && dateRegex.test(rawArgs.startDate)) clean.startDate = rawArgs.startDate;
      if (rawArgs.endDate && dateRegex.test(rawArgs.endDate)) clean.endDate = rawArgs.endDate;
    } else if (toolName === 'compareMonths') {
      if (rawArgs.month1 && monthRegex.test(rawArgs.month1)) clean.month1 = rawArgs.month1;
      if (rawArgs.month2 && monthRegex.test(rawArgs.month2)) clean.month2 = rawArgs.month2;
    } else if (toolName === 'createIncome') {
      if (rawArgs.amount !== undefined) {
        const amt = parseFloat(rawArgs.amount);
        if (!isNaN(amt) && amt > 0 && amt < 100000000) clean.amount = amt;
      }
      if (rawArgs.source && typeof rawArgs.source === 'string' && rawArgs.source.length <= 100 && !hasOperator(rawArgs.source)) clean.source = rawArgs.source.trim();
      if (rawArgs.date && dateRegex.test(rawArgs.date)) clean.date = rawArgs.date;
      if (rawArgs.notes && typeof rawArgs.notes === 'string' && rawArgs.notes.length <= 500 && !hasOperator(rawArgs.notes)) clean.notes = rawArgs.notes.trim();
    } else if (toolName === 'createExpense') {
      if (rawArgs.amount !== undefined) {
        const amt = parseFloat(rawArgs.amount);
        if (!isNaN(amt) && amt > 0 && amt < 100000000) clean.amount = amt;
      }
      if (rawArgs.category && EXPENSE_CATEGORIES.includes(rawArgs.category)) clean.category = rawArgs.category;
      if (rawArgs.date && dateRegex.test(rawArgs.date)) clean.date = rawArgs.date;
      if (rawArgs.description && typeof rawArgs.description === 'string' && rawArgs.description.length <= 500 && !hasOperator(rawArgs.description)) clean.description = rawArgs.description.trim();
    } else if (toolName === 'updateIncome') {
      if (rawArgs.id && typeof rawArgs.id === 'string' && /^[0-9a-fA-F]{24}$/.test(rawArgs.id)) clean.id = rawArgs.id;
      if (rawArgs.amount !== undefined) {
        const amt = parseFloat(rawArgs.amount);
        if (!isNaN(amt) && amt > 0 && amt < 100000000) clean.amount = amt;
      }
      if (rawArgs.source && typeof rawArgs.source === 'string' && rawArgs.source.length <= 100 && !hasOperator(rawArgs.source)) clean.source = rawArgs.source.trim();
      if (rawArgs.date && dateRegex.test(rawArgs.date)) clean.date = rawArgs.date;
      if (rawArgs.notes && typeof rawArgs.notes === 'string' && rawArgs.notes.length <= 500 && !hasOperator(rawArgs.notes)) clean.notes = rawArgs.notes.trim();
    } else if (toolName === 'updateExpense') {
      if (rawArgs.id && typeof rawArgs.id === 'string' && /^[0-9a-fA-F]{24}$/.test(rawArgs.id)) clean.id = rawArgs.id;
      if (rawArgs.amount !== undefined) {
        const amt = parseFloat(rawArgs.amount);
        if (!isNaN(amt) && amt > 0 && amt < 100000000) clean.amount = amt;
      }
      if (rawArgs.category && EXPENSE_CATEGORIES.includes(rawArgs.category)) clean.category = rawArgs.category;
      if (rawArgs.date && dateRegex.test(rawArgs.date)) clean.date = rawArgs.date;
      if (rawArgs.description && typeof rawArgs.description === 'string' && rawArgs.description.length <= 500 && !hasOperator(rawArgs.description)) clean.description = rawArgs.description.trim();
    } else if (toolName === 'createBudget' || toolName === 'updateBudget') {
      const { parseIndianNumber } = require('../utils/budgetCalculator');
      if (rawArgs.month && monthRegex.test(rawArgs.month)) clean.month = rawArgs.month;
      if (rawArgs.monthlyBudget !== undefined) {
        const bud = parseIndianNumber(rawArgs.monthlyBudget);
        if (bud !== null && bud >= 0 && bud < 100000000) clean.monthlyBudget = bud;
      }
      if (Array.isArray(rawArgs.categories)) {
        clean.categories = rawArgs.categories
          .filter(c => c && typeof c.category === 'string')
          .map(c => ({
            category: c.category.trim(),
            amount: parseIndianNumber(c.amount) || 0
          }));
      }
    } else if (toolName === 'deleteIncome' || toolName === 'deleteExpense' || toolName === 'deleteBudget') {
      if (rawArgs.id && typeof rawArgs.id === 'string' && /^[0-9a-fA-F]{24}$/.test(rawArgs.id)) clean.id = rawArgs.id;
      if (rawArgs.month && monthRegex.test(rawArgs.month)) clean.month = rawArgs.month;
    } else if (toolName === 'recommendBudget') {
      if (rawArgs.month && monthRegex.test(rawArgs.month)) clean.month = rawArgs.month;
      if (rawArgs.savingsTarget !== undefined && rawArgs.savingsTarget !== null) {
        const st = parseFloat(rawArgs.savingsTarget);
        if (!isNaN(st) && st >= 0 && st < 100000000) clean.savingsTarget = st;
      }
    }

    return clean;
  }

  /**
   * Executes a multi-turn conversation cycle supporting Groq tool / function calling.
   */
  async executeWithTools(userMessage, chatHistory = [], tools = [], userId, systemInstruction = '') {
    try {
      // 1. Transform tools into OpenAI/Groq function calling format
      const formattedTools = tools.map((t) => ({
        type: 'function',
        function: {
          name: t.name,
          description: t.description,
          parameters: t.parameters
        }
      }));

      // 2. Build messages array
      const messages = [];
      if (systemInstruction) {
        messages.push({ role: 'system', content: systemInstruction });
      }

      chatHistory.forEach((item) => {
        messages.push({
          role: item.role === 'assistant' ? 'assistant' : 'user',
          content: item.content
        });
      });

      messages.push({
        role: 'user',
        content: userMessage
      });

      const MAX_TURNS = 5;
      let turnCount = 0;
      const executedToolCalls = [];
      const executedToolSignatures = new Set();

      while (turnCount < MAX_TURNS) {
        turnCount++;

        let response = null;
        let extractedTool = null;

        try {
          response = await this.createChatCompletionWithRetry({
            model: this.modelName,
            messages,
            tools: formattedTools.length > 0 ? formattedTools : undefined,
            temperature: 0.2,
            max_tokens: 1024
          });
        } catch (callErr) {
          const errBody = callErr.error || (callErr.response && callErr.response.data) || {};
          const failedGen = errBody.failed_generation || callErr.message || '';
          if (failedGen && (errBody.code === 'tool_use_failed' || failedGen.includes('<function=') || failedGen.includes('\"name\"'))) {
            let funcMatch = failedGen.match(/<function=([a-zA-Z0-9_-]+)[^\{]*(\{[\s\S]*?\})\s*(?:<\/?function>|>|$)/s) ||
                            failedGen.match(/<function=([a-zA-Z0-9_-]+)[^\{]*(\{[\s\S]*?\})/s);
            if (funcMatch) {
              const name = funcMatch[1];
              let args = {};
              try {
                if (funcMatch[2]) args = JSON.parse(funcMatch[2].trim());
              } catch (e) {
                args = {};
              }
              extractedTool = {
                id: `call_${Date.now()}`,
                type: 'function',
                function: {
                  name,
                  arguments: JSON.stringify(args)
                }
              };
            } else {
              try {
                const parsedGen = typeof failedGen === 'string' ? JSON.parse(failedGen) : failedGen;
                if (parsedGen && parsedGen.name) {
                  extractedTool = {
                    id: `call_${Date.now()}`,
                    type: 'function',
                    function: {
                      name: parsedGen.name,
                      arguments: typeof parsedGen.arguments === 'string' ? parsedGen.arguments : JSON.stringify(parsedGen.arguments || {})
                    }
                  };
                }
              } catch (e) {
                const cleanText = failedGen.replace(/<function=[^>]*>[\s\S]*?<\/?function>/gs, '').replace(/<function=[^>]*>[\s\S]*?<function>/gs, '').trim();
                if (cleanText.length > 0) {
                  return {
                    message: cleanText,
                    type: 'text',
                    toolCalls: executedToolCalls,
                    confirmation: null
                  };
                }
              }
            }
          }

          if (!extractedTool) {
            throw callErr;
          }
        }

        let message = response?.choices?.[0]?.message;
        if (extractedTool) {
          message = {
            role: 'assistant',
            content: null,
            tool_calls: [extractedTool]
          };
        }

        if (!message) {
          throw new Error('Malformed AI provider response from Groq.');
        }

        // Check if tool_calls were returned
        if (message.tool_calls && message.tool_calls.length > 0) {
          const toolCall = message.tool_calls[0];
          const funcName = toolCall.function.name;
          let rawArgs = {};
          try {
            rawArgs = toolCall.function.arguments ? JSON.parse(toolCall.function.arguments) : {};
          } catch (e) {
            rawArgs = {};
          }

          const sanitizedArgs = this.validateAndSanitizeArgs(funcName, rawArgs);
          const toolSig = `${funcName}:${JSON.stringify(sanitizedArgs)}`;

          // DUPLICATE TOOL CALL PREVENTION: Break loop to synthesize final answer if identical call is repeated
          if (executedToolSignatures.has(toolSig)) {
            console.warn(`[GroqProvider] Duplicate tool call detected ("${toolSig}"). Halting tool loop to synthesize final answer.`);
            break;
          }
          executedToolSignatures.add(toolSig);

          // Append assistant message with tool calls to context
          messages.push(message);

          executedToolCalls.push({ name: funcName, args: rawArgs });

          const matchedTool = tools.find((t) => t.name === funcName);
          const classification = matchedTool ? matchedTool.classification : 'read';

          // WRITE TOOLS: Return confirmation proposal immediately
          if (classification === 'write') {
            const { createPendingAction } = require('../pendingActions');

            // Enrich budget creation/update with authoritative normalization and duplicate check
            if (funcName === 'createBudget' || funcName === 'updateBudget') {
              const {
                parseIndianNumber,
                normalizeBudgetCategories
              } = require('../utils/budgetCalculator');
              const Budget = require('../../../models/Budget');
              const Expense = require('../../../models/Expense');
              const mongoose = require('mongoose');

              const now = new Date();
              const currentMonth = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
              const targetMonth = sanitizedArgs.month || currentMonth;
              sanitizedArgs.month = targetMonth;

              // Check existing budget in database
              const existingBudget = await Budget.findOne({
                user: new mongoose.Types.ObjectId(userId),
                month: targetMonth
              });

              if (existingBudget) {
                sanitizedArgs.isExistingBudget = true;
                sanitizedArgs.existingBudgetAmount = existingBudget.monthlyBudget;
              } else {
                sanitizedArgs.isExistingBudget = false;
                sanitizedArgs.existingBudgetAmount = 0;
              }

              // Fetch user's historical category spending
              const historicalExpenses = await Expense.find({
                user: new mongoose.Types.ObjectId(userId)
              }).sort({ date: -1 }).limit(100);

              const historicalMap = {};
              historicalExpenses.forEach(exp => {
                historicalMap[exp.category] = (historicalMap[exp.category] || 0) + exp.amount;
              });

              // Ensure category allocations match requested total exactly
              const totalAmount = parseIndianNumber(sanitizedArgs.monthlyBudget) || 0;
              sanitizedArgs.monthlyBudget = totalAmount;
              sanitizedArgs.categories = normalizeBudgetCategories(
                totalAmount,
                sanitizedArgs.categories,
                historicalMap
              );
              sanitizedArgs.total = totalAmount;
            }

            const pending = createPendingAction(userId, funcName, sanitizedArgs);

            let proposalMsg = `I prepared a request to execute "${funcName}". Please approve or cancel below.`;
            if (funcName === 'createBudget' || funcName === 'updateBudget') {
              const formattedAmt = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(sanitizedArgs.monthlyBudget || 0);
              if (sanitizedArgs.isExistingBudget) {
                proposalMsg = `Found an existing monthly budget of ₹${sanitizedArgs.existingBudgetAmount}. Would you like to update it to ${formattedAmt} for ${sanitizedArgs.month}? Please review the category breakdown and approve or cancel below.`;
              } else {
                proposalMsg = `I have prepared a monthly budget proposal of ${formattedAmt} for ${sanitizedArgs.month}. Please review the category breakdown and approve or cancel below.`;
              }
            }

            return {
              message: proposalMsg,
              type: 'confirmation',
              toolCalls: executedToolCalls,
              confirmation: {
                actionId: pending.actionId,
                action: funcName,
                arguments: sanitizedArgs,
                requiresConfirmation: true
              }
            };
          }

          // READ TOOLS: Verify permitted tool and execute
          if (!READ_ONLY_TOOLS.has(funcName)) {
            return {
              message: `The tool "${funcName}" is not permitted or enabled.`,
              type: 'text',
              toolCalls: executedToolCalls,
              confirmation: null
            };
          }

          const { executeTool } = require('../tools/handlers');
          let toolResult = await executeTool(userId, funcName, sanitizedArgs);

          if (Array.isArray(toolResult)) {
            toolResult = toolResult.slice(0, 50);
          } else if (toolResult && Array.isArray(toolResult.transactions)) {
            toolResult.transactions = toolResult.transactions.slice(0, 50);
          }

          // Append tool result turn
          messages.push({
            role: 'tool',
            tool_call_id: toolCall.id,
            name: funcName,
            content: JSON.stringify(toolResult)
          });

          // Continue loop for Groq to formulate the final answer or make another call
          continue;
        }

        // Return final text message if assistant content is present
        if (message.content && message.content.trim().length > 0) {
          return {
            message: message.content.trim(),
            type: 'text',
            toolCalls: executedToolCalls,
            confirmation: null
          };
        }
      }

      // GRACEFUL SYNTHESIS: If turn limit reached or duplicate tool call detected, force a final synthesis completion turn without tools
      console.log('[GroqProvider] Synthesizing final answer from collected tool results...');
      try {
        const synthesisPrompt = [
          ...messages,
          {
            role: 'user',
            content: 'Synthesize a complete final answer based on all gathered data and tool results above. Do NOT request any tools. Ensure your response includes: 1. Financial situation summary, 2. Important observations, 3. Exactly 5 practical suggestions, using exact numbers from the data.'
          }
        ];

        const synthResponse = await this.createChatCompletionWithRetry({
          model: this.modelName,
          messages: synthesisPrompt,
          temperature: 0.3,
          max_tokens: 1024
        });

        const finalContent = synthResponse?.choices?.[0]?.message?.content;
        if (finalContent && finalContent.trim().length > 0) {
          return {
            message: finalContent.trim(),
            type: 'text',
            toolCalls: executedToolCalls,
            confirmation: null
          };
        }
      } catch (synthErr) {
        console.warn('[GroqProvider] Final synthesis error:', synthErr.message);
      }

      return {
        message: 'Aapki financial situation ka analysis complete ho gaya hai. Kripya apna dashboard summary check karein.',
        type: 'text',
        toolCalls: executedToolCalls,
        confirmation: null
      };

    } catch (error) {
      this.handleError(error);
    }
  }

  /**
   * Safe operational error mapper converting Groq exceptions into structured AIError instances.
   */
  handleError(error) {
    if (error instanceof AIError) {
      throw error;
    }

    const errorMsg = error.message || '';
    const status = error.status || (error.response && error.response.status);
    console.error('[GroqProvider Exception]:', error.stack || errorMsg);

    if (status === 401 || errorMsg.includes('api_key') || errorMsg.includes('API key') || errorMsg.includes('Invalid API Key') || errorMsg.includes('authentication')) {
      throw new AIError('Groq API key is invalid or unauthorized. Please check your credentials.', 401, 'AI_AUTH_ERROR', false);
    }
    if (status === 429 || errorMsg.includes('rate_limit') || errorMsg.includes('429') || errorMsg.includes('quota')) {
      throw new AIError('Groq API rate limit reached. Please retry in a few moments.', 429, 'AI_RATE_LIMITED', true);
    }
    if (status === 404 || errorMsg.includes('model_not_found') || errorMsg.includes('404') || errorMsg.includes('decommissioned')) {
      throw new AIError(`Groq model "${this.modelName}" was not found or is unavailable.`, 404, 'AI_MODEL_NOT_FOUND', false);
    }
    if (status === 504 || errorMsg.includes('timeout') || errorMsg.includes('ETIMEDOUT') || errorMsg.includes('ECONNRESET')) {
      throw new AIError('Groq Assistant request timed out. Please try again.', 504, 'AI_TIMEOUT', true);
    }

    throw new AIError('Unable to reach the AI assistant right now. Please try again.', 500, 'AI_PROVIDER_ERROR', true);
  }
}

module.exports = GroqProvider;
