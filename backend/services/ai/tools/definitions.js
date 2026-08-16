/**
 * Declarative definitions of AI tools (function calling schemas)
 * Streamlined and optimized for token efficiency.
 */

const EXPENSE_CATEGORIES = [
  'Food',
  'Shopping',
  'Travel',
  'Fuel',
  'Education',
  'Healthcare',
  'Entertainment',
  'Bills',
  'Rent',
  'Others',
];

const toolDefinitions = [
  // --- READ TOOLS ---
  {
    name: 'getTransactionSummary',
    description: 'Fetches monthly financial summary (income, expense, savings, recent transactions, categories).',
    classification: 'read',
    requiresConfirmation: false,
    parameters: {
      type: 'object',
      properties: {
        month: { type: 'string', description: 'Month in YYYY-MM format' },
        allTime: { type: 'boolean', description: 'Fetch all time aggregates' }
      }
    }
  },
  {
    name: 'getBudgetProgress',
    description: 'Gets current budget progress, spent, remaining, savings rate, and status.',
    classification: 'read',
    requiresConfirmation: false,
    parameters: {
      type: 'object',
      properties: {
        month: { type: 'string', description: 'Month in YYYY-MM format' }
      }
    }
  },
  {
    name: 'recommendBudget',
    description: 'Calculates intelligent budget recommendation based on actual income, spending patterns, and savings target.',
    classification: 'read',
    requiresConfirmation: false,
    parameters: {
      type: 'object',
      properties: {
        month: { type: 'string', description: 'Target month in YYYY-MM format' },
        savingsTarget: { type: 'number', description: 'Target savings amount in INR' }
      }
    }
  },
  {
    name: 'analyzeSpending',
    description: 'Calculates detailed spending analytics, rankings, and trends.',
    classification: 'read',
    requiresConfirmation: false,
    parameters: {
      type: 'object',
      properties: {
        month: { type: 'string', description: 'Month in YYYY-MM format' },
        allTime: { type: 'boolean', description: 'Evaluate all history' }
      }
    }
  },
  {
    name: 'analyzeCategories',
    description: 'Calculates category spending shares and rankings.',
    classification: 'read',
    requiresConfirmation: false,
    parameters: {
      type: 'object',
      properties: {
        month: { type: 'string', description: 'Month in YYYY-MM format' }
      }
    }
  },
  {
    name: 'analyzeSavings',
    description: 'Calculates net savings, savings rate %, and savings trend.',
    classification: 'read',
    requiresConfirmation: false,
    parameters: {
      type: 'object',
      properties: {
        month: { type: 'string', description: 'Month in YYYY-MM format' }
      }
    }
  },
  {
    name: 'compareMonths',
    description: 'Compares income, expense, and savings between two months.',
    classification: 'read',
    requiresConfirmation: false,
    parameters: {
      type: 'object',
      properties: {
        month1: { type: 'string', description: 'First month YYYY-MM' },
        month2: { type: 'string', description: 'Second month YYYY-MM' }
      },
      required: ['month1', 'month2']
    }
  },
  {
    name: 'getTransactions',
    description: 'Lists transactions with optional filters and pagination.',
    classification: 'read',
    requiresConfirmation: false,
    parameters: {
      type: 'object',
      properties: {
        type: { type: 'string', enum: ['income', 'expense'], description: 'Transaction type' },
        search: { type: 'string', description: 'Search term' },
        page: { type: 'number', description: 'Page number' }
      }
    }
  },
  {
    name: 'getIncome',
    description: 'Lists income entries matching search keywords or date range.',
    classification: 'read',
    requiresConfirmation: false,
    parameters: {
      type: 'object',
      properties: {
        search: { type: 'string', description: 'Keyword search' }
      }
    }
  },
  {
    name: 'getExpenses',
    description: 'Lists expense entries matching search keywords or date range.',
    classification: 'read',
    requiresConfirmation: false,
    parameters: {
      type: 'object',
      properties: {
        search: { type: 'string', description: 'Keyword search' }
      }
    }
  },

  // --- WRITE TOOLS (REQUIRE CONFIRMATION) ---
  {
    name: 'createIncome',
    description: 'Logs a new income entry. Requires user approval.',
    classification: 'write',
    requiresConfirmation: true,
    parameters: {
      type: 'object',
      properties: {
        amount: { type: 'number', description: 'Income amount (positive)' },
        source: { type: 'string', description: 'Income source (e.g. Salary)' },
        date: { type: 'string', description: 'Date (YYYY-MM-DD)' },
        notes: { type: 'string', description: 'Optional notes' }
      },
      required: ['amount', 'source']
    }
  },
  {
    name: 'createExpense',
    description: 'Logs a new expense entry under a category. Requires user approval.',
    classification: 'write',
    requiresConfirmation: true,
    parameters: {
      type: 'object',
      properties: {
        amount: { type: 'number', description: 'Expense amount (positive)' },
        category: { type: 'string', enum: EXPENSE_CATEGORIES, description: 'Category' },
        date: { type: 'string', description: 'Date (YYYY-MM-DD)' },
        description: { type: 'string', description: 'Description details' }
      },
      required: ['amount', 'category']
    }
  },
  {
    name: 'createBudget',
    description: 'Configures a monthly budget limit. Requires user approval.',
    classification: 'write',
    requiresConfirmation: true,
    parameters: {
      type: 'object',
      properties: {
        monthlyBudget: { type: 'number', description: 'Monthly budget limit amount' },
        month: { type: 'string', description: 'Month in YYYY-MM format' }
      },
      required: ['monthlyBudget', 'month']
    }
  },
  {
    name: 'updateBudget',
    description: 'Updates an existing monthly budget limit. Requires user approval.',
    classification: 'write',
    requiresConfirmation: true,
    parameters: {
      type: 'object',
      properties: {
        monthlyBudget: { type: 'number', description: 'New monthly budget limit' },
        month: { type: 'string', description: 'Month in YYYY-MM format' }
      },
      required: ['monthlyBudget', 'month']
    }
  },
  {
    name: 'updateIncome',
    description: 'Updates an income record. Requires user approval.',
    classification: 'write',
    requiresConfirmation: true,
    parameters: {
      type: 'object',
      properties: {
        id: { type: 'string', description: 'Income record ID' },
        amount: { type: 'number', description: 'Updated amount' },
        source: { type: 'string', description: 'Updated source' }
      },
      required: ['id']
    }
  },
  {
    name: 'updateExpense',
    description: 'Updates an expense record. Requires user approval.',
    classification: 'write',
    requiresConfirmation: true,
    parameters: {
      type: 'object',
      properties: {
        id: { type: 'string', description: 'Expense record ID' },
        amount: { type: 'number', description: 'Updated amount' },
        category: { type: 'string', enum: EXPENSE_CATEGORIES, description: 'Updated category' },
        description: { type: 'string', description: 'Updated description' }
      },
      required: ['id']
    }
  },
  {
    name: 'deleteIncome',
    description: 'Deletes an income entry. Requires user approval.',
    classification: 'write',
    requiresConfirmation: true,
    parameters: {
      type: 'object',
      properties: {
        id: { type: 'string', description: 'Income record ID' }
      },
      required: ['id']
    }
  },
  {
    name: 'deleteExpense',
    description: 'Deletes an expense entry. Requires user approval.',
    classification: 'write',
    requiresConfirmation: true,
    parameters: {
      type: 'object',
      properties: {
        id: { type: 'string', description: 'Expense record ID' }
      },
      required: ['id']
    }
  },
  {
    name: 'deleteBudget',
    description: 'Deletes a monthly budget limit. Requires user approval.',
    classification: 'write',
    requiresConfirmation: true,
    parameters: {
      type: 'object',
      properties: {
        month: { type: 'string', description: 'Month in YYYY-MM format' }
      },
      required: ['month']
    }
  }
];

module.exports = {
  EXPENSE_CATEGORIES,
  toolDefinitions
};
