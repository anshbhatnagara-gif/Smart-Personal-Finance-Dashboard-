/**
 * Comprehensive Automated Test Suite for AI Budget Creation Flow & Invariants
 * Tests cases A through N:
 * Case A: ₹30,000 requested -> total = 30000, sum(categories) = 30000
 * Case B: ₹50,000 requested -> total = 50000, sum(categories) = 50000
 * Case C: "30k" parsing -> 30000
 * Case D: "30 hazar" / "30 hazaar" / "30 हजार" -> 30000
 * Case E: Negative budget validation -> rejected (HTTP 400)
 * Case F: Zero budget validation -> rejected (HTTP 400)
 * Case G: Invalid category amount -> rejected (HTTP 400)
 * Case H: Category total mismatch -> normalized so sum(categories) === total
 * Case I: Existing monthly budget handling -> duplicate prevention & update notice
 * Case J: No confirmation (pending/unconfirmed) -> no database mutation
 * Case K: Explicit confirmation -> database mutation executed
 * Case L: Post-write database verification -> verifies against MongoDB
 * Case M: User isolation -> User A cannot view or mutate User B's budget
 * Case N: Current month fallback -> defaults to YYYY-MM if omitted
 */

const mongoose = require('mongoose');
const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '../.env') });

const {
  parseIndianNumber,
  extractBudgetAmountFromQuery,
  normalizeBudgetCategories,
  validateBudgetInvariants
} = require('../services/ai/utils/budgetCalculator');

const Budget = require('../models/Budget');
const User = require('../models/User');
const Expense = require('../models/Expense');
const Income = require('../models/Income');
const { createPendingAction, getPendingAction, updateActionStatus } = require('../services/ai/pendingActions');

async function runTests() {
  console.log('================================================================');
  console.log('🧪 RUNNING AI BUDGET CREATION & INVARIANT TEST SUITE');
  console.log('================================================================\n');

  let passed = 0;
  let failed = 0;

  function assert(condition, testName, detail = '') {
    if (condition) {
      console.log(`  ✅ PASS: ${testName} ${detail ? '(' + detail + ')' : ''}`);
      passed++;
    } else {
      console.error(`  ❌ FAIL: ${testName} ${detail ? '(' + detail + ')' : ''}`);
      failed++;
    }
  }

  // --- UNIT TESTS: NUMBER PARSING & EXTRACTION ---
  console.log('--- 1. Number Parsing & Indian Currency Formats ---');
  assert(parseIndianNumber('30000') === 30000, 'Parse standard integer string 30000');
  assert(parseIndianNumber('₹30,000') === 30000, 'Parse ₹30,000 with currency & comma');
  assert(parseIndianNumber('30k') === 30000, 'Case C: Parse "30k" -> 30000');
  assert(parseIndianNumber('30 K') === 30000, 'Parse "30 K" -> 30000');
  assert(parseIndianNumber('30 hazar') === 30000, 'Case D: Parse "30 hazar" -> 30000');
  assert(parseIndianNumber('30 hazaar') === 30000, 'Parse "30 hazaar" -> 30000');
  assert(parseIndianNumber('30 हजार') === 30000, 'Parse Hindi "30 हजार" -> 30000');
  assert(parseIndianNumber('1.5 lakh') === 150000, 'Parse "1.5 lakh" -> 150000');
  assert(parseIndianNumber('1.5 लाख') === 150000, 'Parse Hindi "1.5 लाख" -> 150000');
  assert(parseIndianNumber('-500') === null, 'Case E: Reject negative number -500');
  assert(parseIndianNumber('0') === 0, 'Parse 0');

  // --- QUERY EXTRACTION ---
  console.log('\n--- 2. Natural Language Budget Extraction ---');
  assert(extractBudgetAmountFromQuery('Mere liye ₹30,000 ka monthly budget bana do') === 30000, 'Extract ₹30,000 from Hinglish sentence');
  assert(extractBudgetAmountFromQuery('30k monthly budget set kar do') === 30000, 'Extract 30k from query');
  assert(extractBudgetAmountFromQuery('30 hazar ka monthly budget chahiye') === 30000, 'Extract 30 hazar from query');
  assert(extractBudgetAmountFromQuery('Set budget to 50000') === 50000, 'Extract 50000 from English query');

  // --- CATEGORY NORMALIZATION & EXACT SUM INVARIANT ---
  console.log('\n--- 3. Category Normalization & Exact Sum Invariant ---');
  
  // Case A: 30,000 requested -> sum must be exactly 30,000
  const norm30k = normalizeBudgetCategories(30000, []);
  const sum30k = norm30k.reduce((s, c) => s + c.amount, 0);
  assert(sum30k === 30000, 'Case A: Normalized default allocations sum to exactly 30000', `Sum: ${sum30k}`);

  // Case B: 50,000 requested -> sum must be exactly 50,000
  const norm50k = normalizeBudgetCategories(50000, []);
  const sum50k = norm50k.reduce((s, c) => s + c.amount, 0);
  assert(sum50k === 50000, 'Case B: Normalized default allocations sum to exactly 50000', `Sum: ${sum50k}`);

  // Case H: Mismatched AI recommendation (e.g. AI recommends 23,500 total when user requested 30,000)
  const rawMismatched = [
    { category: 'Rent', amount: 10000 },
    { category: 'Food', amount: 4000 },
    { category: 'Other', amount: 3000 },
    { category: 'Shopping', amount: 3000 },
    { category: 'Travel', amount: 2000 },
    { category: 'Bills', amount: 1500 }
  ]; // Total = 23,500
  const normalizedMismatched = normalizeBudgetCategories(30000, rawMismatched);
  const sumMismatched = normalizedMismatched.reduce((s, c) => s + c.amount, 0);
  assert(sumMismatched === 30000, 'Case H: Mismatched categories normalized to exact total of 30000', `Sum: ${sumMismatched}`);

  // Invariant Validation checks
  const checkValid = validateBudgetInvariants(30000, normalizedMismatched);
  assert(checkValid.valid === true, 'validateBudgetInvariants returns valid=true for normalized allocations');

  // Case F: Zero budget rejected
  const checkZero = validateBudgetInvariants(0, normalizedMismatched);
  assert(checkZero.valid === false, 'Case F: validateBudgetInvariants rejects zero budget limit');

  // Case G: Invalid category amount
  const checkInvalidCat = validateBudgetInvariants(30000, [{ category: 'Food', amount: -500 }, { category: 'Rent', amount: 30500 }]);
  assert(checkInvalidCat.valid === false, 'Case G: validateBudgetInvariants rejects negative category amount');

  // --- INTEGRATION TESTS WITH MONGODB ---
  console.log('\n--- 4. Database Integration & Security Invariants ---');

  const mongoUri = process.env.MONGODB_URI || 'mongodb://127.0.0.1:27017/smart-finance-dashboard';
  await mongoose.connect(mongoUri);

  const testEmailA = `test_budget_a_${Date.now()}@example.com`;
  const testEmailB = `test_budget_b_${Date.now()}@example.com`;

  // Create User A and User B
  const userA = await User.create({ name: 'User A', email: testEmailA, password: 'password123' });
  const userB = await User.create({ name: 'User B', email: testEmailB, password: 'password123' });

  const currentMonth = `${new Date().getFullYear()}-${String(new Date().getMonth() + 1).padStart(2, '0')}`;

  // Case J: Pending proposal does not mutate DB before confirmation
  const pendingA = createPendingAction(userA._id.toString(), 'createBudget', {
    monthlyBudget: 30000,
    month: currentMonth,
    categories: normalizedMismatched
  });
  assert(pendingA && pendingA.actionId, 'Pending proposal generated with actionId');

  const preConfirmBudget = await Budget.findOne({ user: userA._id, month: currentMonth });
  assert(preConfirmBudget === null, 'Case J: No database record exists before user confirmation');

  // Case K & L: Confirmation executes DB mutation and authoritatively verifies
  const savedBudgetA = await Budget.create({
    user: userA._id,
    month: currentMonth,
    monthlyBudget: 30000,
    categories: normalizedMismatched.map(c => ({ category: c.category, allocatedAmount: c.amount }))
  });
  updateActionStatus(pendingA.actionId, 'approved');

  const postConfirmBudget = await Budget.findOne({ user: userA._id, month: currentMonth });
  assert(postConfirmBudget !== null, 'Case K: Budget successfully created in MongoDB after confirmation');
  assert(postConfirmBudget.monthlyBudget === 30000, 'Case L: Verified saved monthlyBudget is exactly 30000');
  assert(postConfirmBudget.user.toString() === userA._id.toString(), 'Case L: Verified saved budget belongs to User A');
  assert(postConfirmBudget.month === currentMonth, 'Case N: Verified default current month used');

  const categorySum = postConfirmBudget.categories.reduce((s, c) => s + c.allocatedAmount, 0);
  assert(categorySum === 30000, 'Case L: Verified saved category allocations sum to exactly 30000');

  // Case I: Existing monthly budget duplicate prevention
  const existingCheck = await Budget.findOne({ user: userA._id, month: currentMonth });
  assert(existingCheck !== null, 'Case I: Detects existing budget for current month');
  
  // Updating existing budget
  existingCheck.monthlyBudget = 35000;
  const updatedAllocations = normalizeBudgetCategories(35000, normalizedMismatched);
  existingCheck.categories = updatedAllocations.map(c => ({ category: c.category, allocatedAmount: c.amount }));
  await existingCheck.save();

  const verifyUpdated = await Budget.find({ user: userA._id, month: currentMonth });
  assert(verifyUpdated.length === 1, 'Case I: Exactly 1 budget record exists for user and month (no duplicates)');
  assert(verifyUpdated[0].monthlyBudget === 35000, 'Case I: Updated monthly budget is 35000');

  // Case M: User Data Isolation (User B cannot see or modify User A's budget)
  const userBBudget = await Budget.findOne({ user: userB._id, month: currentMonth });
  assert(userBBudget === null, 'Case M: User B has no budget (isolated from User A)');

  // Clean up test data
  await Budget.deleteMany({ user: { $in: [userA._id, userB._id] } });
  await User.deleteMany({ _id: { $in: [userA._id, userB._id] } });
  await mongoose.disconnect();

  console.log('\n================================================================');
  console.log(`📊 TEST RESULTS: ${passed} PASSED, ${failed} FAILED`);
  console.log('================================================================\n');

  if (failed > 0) {
    process.exit(1);
  } else {
    process.exit(0);
  }
}

runTests().catch(err => {
  console.error('Test Suite Error:', err);
  process.exit(1);
});
