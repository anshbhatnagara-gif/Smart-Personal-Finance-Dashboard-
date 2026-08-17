/**
 * Comprehensive utility for parsing Indian numbering formats (Hinglish/Hindi/English),
 * normalizing category allocations so sum(allocations) === totalBudget exactly,
 * and enforcing strict financial validation invariants.
 */

const STANDARD_CATEGORIES = [
  'Rent',
  'Food',
  'Bills',
  'Shopping',
  'Travel',
  'Entertainment',
  'Healthcare',
  'Education',
  'Others'
];

/**
 * Standard default proportions for categories when user has no expense history.
 */
const DEFAULT_CATEGORY_PROPORTIONS = {
  Rent: 0.35,
  Food: 0.20,
  Bills: 0.15,
  Shopping: 0.10,
  Travel: 0.10,
  Others: 0.10
};

/**
 * Safely parses Indian/Hinglish/English number expressions into standard numeric value.
 * Supports:
 * - 30000, 30,000, ₹30,000
 * - 30k, 30 K, ₹30k
 * - 30 hazar, 30 हजार, 30 hazaar
 * - 1.5 lakh, 1.5 lac, 1.5 लाख
 * - 1 crore, 1 cr
 */
function parseIndianNumber(input) {
  if (input === null || input === undefined) return null;
  if (typeof input === 'number') {
    return !isNaN(input) && isFinite(input) && input >= 0 ? input : null;
  }

  if (typeof input !== 'string') return null;

  let str = input.trim();
  if (!str) return null;

  // Remove currency symbols, commas, and excess whitespace
  str = str.replace(/[₹\u20B9$,]/g, '').trim().toLowerCase();

  // 1. Check Crore (1 cr, 1.5 crore, 1 करोड़)
  const crMatch = str.match(/^([\d.]+)\s*(?:cr|crore|crores|करोड़)$/i);
  if (crMatch) {
    const val = parseFloat(crMatch[1]);
    return !isNaN(val) && val >= 0 ? Math.round(val * 10000000) : null;
  }

  // 2. Check Lakh (1.5 lakh, 1.5 lac, 1.5 लाख)
  const lakhMatch = str.match(/^([\d.]+)\s*(?:lakh|lakhs|lac|lacs|लाख)$/i);
  if (lakhMatch) {
    const val = parseFloat(lakhMatch[1]);
    return !isNaN(val) && val >= 0 ? Math.round(val * 100000) : null;
  }

  // 3. Check Thousand / K / Hazar (30k, 30 K, 30 hazar, 30 hazaar, 30 हजार)
  const kMatch = str.match(/^([\d.]+)\s*(?:k|hazar|hazaar|thousand|हजार)$/i);
  if (kMatch) {
    const val = parseFloat(kMatch[1]);
    return !isNaN(val) && val >= 0 ? Math.round(val * 1000) : null;
  }

  // 4. Standard float/integer string
  const num = parseFloat(str);
  return !isNaN(num) && isFinite(num) && num >= 0 ? Math.round(num) : null;
}

/**
 * Extracts requested budget amount from natural language queries in Hindi/Hinglish/English.
 * E.g., "Mere liye 30000 ka budget bana do", "30k monthly budget set kar do", "30 hazar ka monthly budget"
 */
function extractBudgetAmountFromQuery(text) {
  if (!text || typeof text !== 'string') return null;

  const patterns = [
    /(?:₹|\u20B9|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?\s*(?:cr\b|crore|crores|करोड़))/i,
    /(?:₹|\u20B9|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?\s*(?:lakh|lakhs|lac|lacs|लाख))/i,
    /(?:₹|\u20B9|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?\s*(?:k\b|hazar|hazaar|thousand|हजार))/i,
    /(?:₹|\u20B9|rs\.?|inr)\s*([\d,]+(?:\.\d+)?)/i,
    /budget\s*(?:of|to|limit|is|for)?\s*(?:₹|\u20B9|rs\.?)?\s*([\d,]+(?:\.\d+)?(?:\s*(?:k\b|hazar|lakh|crore))?)/i,
    /([\d,]{4,10})\s*(?:ka|ke|budget|rupees|rupaye|bana|set)/i
  ];

  for (const pattern of patterns) {
    const match = text.match(pattern);
    if (match && match[1]) {
      const parsed = parseIndianNumber(match[1]);
      if (parsed && parsed > 0) return parsed;
    }
  }

  return null;
}

/**
 * Normalizes category allocations so that:
 * 1. Each category amount is a valid non-negative integer.
 * 2. sum(all category allocations) === totalBudget EXACTLY.
 */
function normalizeBudgetCategories(totalBudget, rawCategories = [], userHistoricalSpending = {}) {
  const targetTotal = parseIndianNumber(totalBudget);
  if (!targetTotal || targetTotal <= 0) {
    return [];
  }

  // 1. If valid category array is passed with positive amounts
  const validRaw = Array.isArray(rawCategories)
    ? rawCategories
        .filter(c => c && typeof c.category === 'string' && c.category.trim())
        .map(c => ({
          category: c.category.trim(),
          amount: typeof c.amount === 'number' ? c.amount : (parseFloat(c.amount) || 0)
        }))
        .filter(c => c.amount >= 0)
    : [];

  let proportions = {};

  if (validRaw.length > 0) {
    const rawSum = validRaw.reduce((sum, c) => sum + c.amount, 0);
    if (rawSum > 0) {
      validRaw.forEach(c => {
        proportions[c.category] = c.amount / rawSum;
      });
    }
  }

  // 2. If no valid proportions from raw input, use historical spending
  if (Object.keys(proportions).length === 0 && userHistoricalSpending && typeof userHistoricalSpending === 'object') {
    const historyEntries = Object.entries(userHistoricalSpending).filter(([_, amt]) => amt > 0);
    const historyTotal = historyEntries.reduce((sum, [_, amt]) => sum + amt, 0);
    if (historyTotal > 0) {
      historyEntries.forEach(([cat, amt]) => {
        proportions[cat] = amt / historyTotal;
      });
    }
  }

  // 3. If still no proportions, use DEFAULT_CATEGORY_PROPORTIONS
  if (Object.keys(proportions).length === 0) {
    proportions = { ...DEFAULT_CATEGORY_PROPORTIONS };
  }

  // 4. Calculate initial integer rounded amounts
  const entries = Object.entries(proportions);
  let allocatedSum = 0;
  const result = entries.map(([category, prop]) => {
    const calculatedAmount = Math.round(targetTotal * prop);
    allocatedSum += calculatedAmount;
    return {
      category,
      amount: calculatedAmount
    };
  });

  // 5. Authoritative Rounding Reconciliation:
  // Fix difference (e.g. ±1 or ±2) on the largest category to guarantee exact sum match
  const diff = targetTotal - allocatedSum;
  if (diff !== 0 && result.length > 0) {
    let maxIdx = 0;
    for (let i = 1; i < result.length; i++) {
      if (result[i].amount > result[maxIdx].amount) {
        maxIdx = i;
      }
    }
    result[maxIdx].amount = Math.max(0, result[maxIdx].amount + diff);
  }

  return result;
}

/**
 * Validates budget financial invariants before database write.
 */
function validateBudgetInvariants(totalBudget, categories) {
  const numericTotal = parseIndianNumber(totalBudget);
  if (!numericTotal || numericTotal <= 0) {
    return { valid: false, message: 'Total budget must be a positive number greater than 0.' };
  }

  if (!Array.isArray(categories) || categories.length === 0) {
    return { valid: false, message: 'Budget categories must be a non-empty array.' };
  }

  let catSum = 0;
  for (const item of categories) {
    if (!item.category || typeof item.category !== 'string') {
      return { valid: false, message: 'Every category allocation must have a valid category name.' };
    }
    if (typeof item.amount !== 'number' || isNaN(item.amount) || item.amount < 0) {
      return { valid: false, message: `Category "${item.category}" has an invalid or negative amount.` };
    }
    catSum += item.amount;
  }

  if (Math.round(catSum) !== Math.round(numericTotal)) {
    return {
      valid: false,
      message: `Category allocations sum (₹${catSum}) does not equal total budget (₹${numericTotal}).`
    };
  }

  return { valid: true };
}

module.exports = {
  STANDARD_CATEGORIES,
  DEFAULT_CATEGORY_PROPORTIONS,
  parseIndianNumber,
  extractBudgetAmountFromQuery,
  normalizeBudgetCategories,
  validateBudgetInvariants
};
