/**
 * Declarative definitions of the AI tools (function calling schemas)
 * that are exposed to the LLM model.
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
    name: 'getTransactions',
    description: 'Retrieve a list of unified transaction logs (both incomes and expenses) for the active user. Supports filters and page pagination.',
    classification: 'read',
    requiresConfirmation: false,
    parameters: {
      type: 'object',
      properties: {
        type: { type: 'string', enum: ['income', 'expense'], description: 'Filter by transaction type' },
        search: { type: 'string', description: 'Keyword query in description or categoryOrSource' },
        startDate: { type: 'string', description: 'ISO date string (YYYY-MM-DD) for start range (inclusive)' },
        endDate: { type: 'string', description: 'ISO date string (YYYY-MM-DD) for end range (inclusive)' },
        page: { type: 'number', description: 'Page number for pagination (defaults to 1)' },
        limit: { type: 'number', description: 'Limit of records per query page (defaults to 15)' }
      }
    }
  },
  {
    name: 'getTransactionSummary',
    description: 'Fetches aggregated dashboard financial summaries (total income, total expense, savings, recent transactions, and category percentage breakdown) for a specific month or all time.',
    classification: 'read',
    requiresConfirmation: false,
    parameters: {
      type: 'object',
      properties: {
        month: { type: 'string', description: 'Active period month (format: YYYY-MM). Defaults to current month.' },
        allTime: { type: 'boolean', description: 'Fetch all time aggregated stats instead of month boundaries.' }
      }
    }
  },
  {
    name: 'getBudgetProgress',
    description: 'Retrieves budget settings progress (total spending, remaining allowance, isExceeded status) for the active user during a given month.',
    classification: 'read',
    requiresConfirmation: false,
    parameters: {
      type: 'object',
      properties: {
        month: { type: 'string', description: 'Active month target (format: YYYY-MM). Defaults to current month.' }
      }
    }
  },
  {
    name: 'getIncome',
    description: 'Lists all registered income records for the user matching optional search keywords and date ranges.',
    classification: 'read',
    requiresConfirmation: false,
    parameters: {
      type: 'object',
      properties: {
        search: { type: 'string', description: 'Keyword match inside income source or notes' },
        startDate: { type: 'string', description: 'ISO date string (YYYY-MM-DD) for start boundary' },
        endDate: { type: 'string', description: 'ISO date string (YYYY-MM-DD) for end boundary' }
      }
    }
  },
  {
    name: 'getExpenses',
    description: 'Lists all logged expense records for the user matching optional search keywords and date ranges.',
    classification: 'read',
    requiresConfirmation: false,
    parameters: {
      type: 'object',
      properties: {
        search: { type: 'string', description: 'Keyword match inside expense category or description' },
        startDate: { type: 'string', description: 'ISO date string (YYYY-MM-DD) for start boundary' },
        endDate: { type: 'string', description: 'ISO date string (YYYY-MM-DD) for end boundary' }
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
        amount: { type: 'number', description: 'Amount of income received (must be positive)' },
        source: { type: 'string', description: 'Source / sender of the income (e.g. Salary, Freelance)' },
        date: { type: 'string', description: 'ISO date string (YYYY-MM-DD). Defaults to today.' },
        notes: { type: 'string', description: 'Optional comments or notes' }
      },
      required: ['amount', 'source']
    }
  },
  {
    name: 'createExpense',
    description: 'Logs a new expense entry under a specific category. Requires user approval.',
    classification: 'write',
    requiresConfirmation: true,
    parameters: {
      type: 'object',
      properties: {
        amount: { type: 'number', description: 'Amount spent (must be positive)' },
        category: { 
          type: 'string', 
          enum: EXPENSE_CATEGORIES, 
          description: 'Categorical type of the expense' 
        },
        date: { type: 'string', description: 'ISO date string (YYYY-MM-DD). Defaults to today.' },
        description: { type: 'string', description: 'Description details of purchase' }
      },
      required: ['amount', 'category']
    }
  },
  {
    name: 'updateIncome',
    description: 'Updates properties of an existing income record. Requires user approval.',
    classification: 'write',
    requiresConfirmation: true,
    parameters: {
      type: 'object',
      properties: {
        id: { type: 'string', description: 'Database ID of the income record' },
        amount: { type: 'number', description: 'Updated amount value' },
        source: { type: 'string', description: 'Updated source name' },
        date: { type: 'string', description: 'Updated ISO date string' },
        notes: { type: 'string', description: 'Updated comments or notes' }
      },
      required: ['id']
    }
  },
  {
    name: 'updateExpense',
    description: 'Updates properties of an existing expense record. Requires user approval.',
    classification: 'write',
    requiresConfirmation: true,
    parameters: {
      type: 'object',
      properties: {
        id: { type: 'string', description: 'Database ID of the expense record' },
        amount: { type: 'number', description: 'Updated amount spent' },
        category: { 
          type: 'string', 
          enum: EXPENSE_CATEGORIES, 
          description: 'Updated category type' 
        },
        date: { type: 'string', description: 'Updated ISO date string' },
        description: { type: 'string', description: 'Updated purchase description' }
      },
      required: ['id']
    }
  },
  {
    name: 'createBudget',
    description: 'Configures a monthly budget limit for a specific month period. Requires user approval.',
    classification: 'write',
    requiresConfirmation: true,
    parameters: {
      type: 'object',
      properties: {
        monthlyBudget: { type: 'number', description: 'Monthly budget limit (positive number)' },
        month: { type: 'string', description: 'Active month period (format: YYYY-MM)' }
      },
      required: ['monthlyBudget', 'month']
    }
  },
  {
    name: 'updateBudget',
    description: 'Updates an existing monthly budget limit limit. Requires user approval.',
    classification: 'write',
    requiresConfirmation: true,
    parameters: {
      type: 'object',
      properties: {
        monthlyBudget: { type: 'number', description: 'New monthly budget limit' },
        month: { type: 'string', description: 'Active month target (format: YYYY-MM)' }
      },
      required: ['monthlyBudget', 'month']
    }
  },
  {
    name: 'deleteIncome',
    description: 'Deletes an existing income entry. Requires user approval.',
    classification: 'write',
    requiresConfirmation: true,
    parameters: {
      type: 'object',
      properties: {
        id: { type: 'string', description: 'Database ID of the income record' }
      },
      required: ['id']
    }
  },
  {
    name: 'deleteExpense',
    description: 'Deletes an existing expense entry. Requires user approval.',
    classification: 'write',
    requiresConfirmation: true,
    parameters: {
      type: 'object',
      properties: {
        id: { type: 'string', description: 'Database ID of the expense record' }
      },
      required: ['id']
    }
  },
  {
    name: 'deleteBudget',
    description: 'Deletes an existing monthly budget setting. Requires user approval.',
    classification: 'write',
    requiresConfirmation: true,
    parameters: {
      type: 'object',
      properties: {
        month: { type: 'string', description: 'Target month period (format: YYYY-MM)' }
      },
      required: ['month']
    }
  },

  // --- DEDICATED ALIAS TOOLS FOR LLM QUERY RECOGNITION ---
  {
    name: 'getFinancialSummary',
    description: 'Retrieves an overall high-level financial summary including total income, total expense, net savings, budget utilization, and alerts.',
    classification: 'read',
    requiresConfirmation: false,
    parameters: {
      type: 'object',
      properties: {
        month: { type: 'string', description: 'Period month (format: YYYY-MM). Defaults to current month.' }
      }
    }
  },
  {
    name: 'searchTransactions',
    description: 'Searches user transactions by keyword, date range, or transaction type (income/expense).',
    classification: 'read',
    requiresConfirmation: false,
    parameters: {
      type: 'object',
      properties: {
        search: { type: 'string', description: 'Keyword to search in description or source/category' },
        type: { type: 'string', enum: ['income', 'expense'], description: 'Filter by transaction type' },
        startDate: { type: 'string', description: 'Start date (YYYY-MM-DD)' },
        endDate: { type: 'string', description: 'End date (YYYY-MM-DD)' }
      }
    }
  },
  {
    name: 'getCategoryBreakdown',
    description: 'Gets a detailed breakdown of spending per category for a given month or all time.',
    classification: 'read',
    requiresConfirmation: false,
    parameters: {
      type: 'object',
      properties: {
        month: { type: 'string', description: 'Period month (format: YYYY-MM). Defaults to current month.' }
      }
    }
  },
  {
    name: 'getMonthlyTrend',
    description: 'Retrieves month-over-month trend statistics comparing income, expense, and savings.',
    classification: 'read',
    requiresConfirmation: false,
    parameters: {
      type: 'object',
      properties: {
        month: { type: 'string', description: 'Current month to evaluate (format: YYYY-MM)' }
      }
    }
  },
  
  // --- ANALYTICAL READ-ONLY TOOLS ---
  {
    name: 'analyzeSpending',
    description: 'Calculates high-level expense aggregates (total spending, count, average/highest/lowest purchases, category rankings, and month-over-month trend percentages) for a month or all time.',
    classification: 'read',
    requiresConfirmation: false,
    parameters: {
      type: 'object',
      properties: {
        month: { type: 'string', description: 'Period month (format: YYYY-MM). Defaults to current month.' },
        allTime: { type: 'boolean', description: 'Evaluate all historical data instead of a single month.' }
      }
    }
  },
  {
    name: 'analyzeIncome',
    description: 'Calculates total income earned, number of entries, average income, largest source, and MoM trend aggregates for a month or all time.',
    classification: 'read',
    requiresConfirmation: false,
    parameters: {
      type: 'object',
      properties: {
        month: { type: 'string', description: 'Period month (format: YYYY-MM). Defaults to current month.' },
        allTime: { type: 'boolean', description: 'Evaluate all historical income records.' }
      }
    }
  },
  {
    name: 'analyzeBudget',
    description: 'Calculates spending progress utilization, remaining allowance, exceeded status, and daily pace projections for a specific month.',
    classification: 'read',
    requiresConfirmation: false,
    parameters: {
      type: 'object',
      properties: {
        month: { type: 'string', description: 'Target budget month (format: YYYY-MM). Defaults to current month.' }
      }
    }
  },
  {
    name: 'analyzeCategories',
    description: 'Calculates percentage share of spending per category, ranking of top categories, and category shifts compared to the previous month.',
    classification: 'read',
    requiresConfirmation: false,
    parameters: {
      type: 'object',
      properties: {
        month: { type: 'string', description: 'Period month (format: YYYY-MM). Defaults to current month.' },
        allTime: { type: 'boolean', description: 'Retrieve breakdowns for all time records.' }
      }
    }
  },
  {
    name: 'compareMonths',
    description: 'Compares income, expense, savings totals, and category breakdown differences between two specific months.',
    classification: 'read',
    requiresConfirmation: false,
    parameters: {
      type: 'object',
      properties: {
        month1: { type: 'string', description: 'First month period (format: YYYY-MM). Required.' },
        month2: { type: 'string', description: 'Second month period (format: YYYY-MM). Required.' }
      },
      required: ['month1', 'month2']
    }
  },
  {
    name: 'analyzeSavings',
    description: 'Calculates net savings (income minus expenses), savings rate ratio, savings trends, and MoM changes.',
    classification: 'read',
    requiresConfirmation: false,
    parameters: {
      type: 'object',
      properties: {
        month: { type: 'string', description: 'Period month (format: YYYY-MM). Defaults to current month.' },
        allTime: { type: 'boolean', description: 'Evaluate all time aggregates.' }
      }
    }
  },
  {
    name: 'generateFinancialAlerts',
    description: 'Generates rule-based alert messages (budget exceeded, unusually large transactions, drop in savings) based on real financial data.',
    classification: 'read',
    requiresConfirmation: false,
    parameters: {
      type: 'object',
      properties: {
        month: { type: 'string', description: 'Target month for alerts scan (format: YYYY-MM). Defaults to current month.' }
      }
    }
  }
];

module.exports = {
  EXPENSE_CATEGORIES,
  toolDefinitions
};
