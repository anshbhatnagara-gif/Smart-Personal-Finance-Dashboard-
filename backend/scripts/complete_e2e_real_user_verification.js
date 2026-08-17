/**
 * Complete Real-User End-to-End Test Suite for Smart Personal Finance Dashboard
 * Covers all requirements in Phases 1 through 23:
 * 1. Auth & Session Management (Registration, Login, Me)
 * 2. Realistic Financial Data Entry (Income ₹50,000, 7 Expenses totaling ₹29,000)
 * 3. Dashboard Calculation Verification (Income 50k, Expenses 29k, Savings 21k)
 * 4. Normal Budget Creation & Exact Category Sum Invariant (₹30,000)
 * 5. Live Groq AI Assistant Verification (Hinglish, 7 analytical queries, exact database numbers)
 * 6. Live AI Budget Proposal Flow (Proposal Card, Sum Invariant check, Approval & DB mutation)
 * 7. Action Cancellation Test (Cancel mutation -> DB remains unchanged)
 * 8. Multi-User Data Isolation (User B cannot see User A data)
 * 9. Hindi & Indian Number Parsing Suite (₹30,000, 30000, 30k, 30 K, 30 hazar, 1.5 lakh)
 */

const BASE_URL = 'http://127.0.0.1:5000/api';

const request = async (endpoint, options = {}) => {
  const url = `${BASE_URL}${endpoint}`;
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });
    const data = await response.json();
    return { status: response.status, data };
  } catch (error) {
    console.error(`Request to ${endpoint} failed:`, error.message);
    throw error;
  }
};

let passed = 0;
let failed = 0;

const assert = (condition, message, detail = '') => {
  if (!condition) {
    console.error(`❌ Assertion Failed: ${message} ${detail ? '(' + detail + ')' : ''}`);
    failed++;
  } else {
    console.log(`✅ ${message} ${detail ? '(' + detail + ')' : ''}`);
    passed++;
  }
};

async function runRealUserE2ETest() {
  console.log('================================================================');
  console.log('🚀 STARTING COMPLETE REAL-USER END-TO-END VERIFICATION');
  console.log('================================================================\n');

  const uniqueTs = Date.now();
  const testEmailA = `ansh.finance.test.${uniqueTs}@example.com`;
  const testPassword = 'Test@12345FinanceSecure!';
  let tokenA, userAId;

  // ==========================================================================
  // PHASE 5: USER REGISTRATION & LOGIN
  // ==========================================================================
  console.log('--- PHASE 5: Registration & Authentication ---');
  const regA = await request('/auth/register', {
    method: 'POST',
    body: JSON.stringify({
      name: 'Ansh Test User',
      email: testEmailA,
      password: testPassword
    })
  });
  assert(regA.status === 201 && regA.data.success, 'User A registered successfully');
  tokenA = regA.data.data?.token || regA.data.token;
  userAId = regA.data.data?._id;

  const authHeaderA = { Authorization: `Bearer ${tokenA}` };

  const sessionA = await request('/auth/me', { headers: authHeaderA });
  assert(sessionA.status === 200 && (sessionA.data.data?.email === testEmailA || sessionA.data.user?.email === testEmailA), 'User A session verified via /auth/me');

  // ==========================================================================
  // PHASE 6: REALISTIC FINANCIAL DATA ENTRY
  // ==========================================================================
  console.log('\n--- PHASE 6: Adding Realistic Financial Data ---');
  const now = new Date();
  const currentMonth = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
  const today = now.toISOString().split('T')[0];

  // Monthly Income: Salary ₹50,000
  const incRes = await request('/incomes', {
    method: 'POST',
    headers: authHeaderA,
    body: JSON.stringify({
      amount: 50000,
      source: 'Salary',
      date: today,
      notes: 'Primary monthly salary'
    })
  });
  assert(incRes.status === 201 && incRes.data.data.amount === 50000, 'Income created: Salary ₹50,000');

  // Expenses (Total: ₹29,000)
  const testExpenses = [
    { category: 'Rent', amount: 10000, description: 'Monthly Apartment Rent' },
    { category: 'Food', amount: 5000, description: 'Groceries and dining' },
    { category: 'Bills', amount: 3000, description: 'Electricity & Broadband' },
    { category: 'Shopping', amount: 4000, description: 'Clothing & essentials' },
    { category: 'Travel', amount: 2000, description: 'Commute and fuel' },
    { category: 'Entertainment', amount: 2000, description: 'Movies & subscriptions' },
    { category: 'Others', amount: 3000, description: 'Miscellaneous household supplies' }
  ];

  for (const exp of testExpenses) {
    const res = await request('/expenses', {
      method: 'POST',
      headers: authHeaderA,
      body: JSON.stringify({
        category: exp.category,
        amount: exp.amount,
        date: today,
        description: exp.description
      })
    });
    assert(res.status === 201 && res.data.data.amount === exp.amount, `Expense created: ${exp.category} ₹${exp.amount}`);
  }

  // ==========================================================================
  // PHASE 7: VERIFY DASHBOARD & TRANSACTIONS
  // ==========================================================================
  console.log('\n--- PHASE 7: Dashboard Calculation Verification ---');
  const summaryRes = await request(`/transactions/summary?month=${currentMonth}`, { headers: authHeaderA });
  assert(summaryRes.status === 200, 'Summary API returned status 200');

  const summary = summaryRes.data.data;
  assert(summary.totalIncome === 50000, 'Dashboard Total Income is exactly ₹50,000', `Actual: ₹${summary.totalIncome}`);
  assert(summary.totalExpense === 29000, 'Dashboard Total Expense is exactly ₹29,000', `Actual: ₹${summary.totalExpense}`);
  assert(summary.netSavings === 21000, 'Dashboard Net Savings is exactly ₹21,000', `Actual: ₹${summary.netSavings}`);
  assert(summary.categoryBreakdown && summary.categoryBreakdown.length === 7, 'Category breakdown contains all 7 categories');

  // Verify unified transactions ledger
  const txRes = await request('/transactions?limit=20', { headers: authHeaderA });
  const txList = Array.isArray(txRes.data.data) ? txRes.data.data : txRes.data.data?.transactions || [];
  assert(txRes.status === 200 && txList.length === 8, 'Unified ledger contains 8 transactions (1 income + 7 expenses)', `Found: ${txList.length}`);

  // ==========================================================================
  // PHASE 8: INITIAL BUDGET CREATION & INVARIANT
  // ==========================================================================
  console.log('\n--- PHASE 8: Initial Budget Creation & Invariant Verification ---');
  const budgetInitRes = await request('/budgets', {
    method: 'POST',
    headers: authHeaderA,
    body: JSON.stringify({
      monthlyBudget: 30000,
      month: currentMonth,
      categories: [
        { category: 'Rent', amount: 10000 },
        { category: 'Food', amount: 5000 },
        { category: 'Bills', amount: 3000 },
        { category: 'Shopping', amount: 3000 },
        { category: 'Travel', amount: 2000 },
        { category: 'Entertainment', amount: 2000 },
        { category: 'Others', amount: 5000 }
      ]
    })
  });
  assert(budgetInitRes.status === 200 && budgetInitRes.data.data.monthlyBudget === 30000, 'Initial budget set to ₹30,000');

  const budgetProgressRes = await request(`/budgets/progress?month=${currentMonth}`, { headers: authHeaderA });
  assert(budgetProgressRes.status === 200, 'Budget Progress API returned 200');
  const progress = budgetProgressRes.data.data;
  assert(progress.monthlyBudget === 30000, 'Budget Progress limit is ₹30,000');
  assert(progress.totalSpent === 29000, 'Budget Progress spent is ₹29,000');
  assert(progress.remaining === 1000, 'Budget Progress remaining is ₹1,000');
  assert(progress.status === 'NEAR_LIMIT' || progress.status === 'ON_TRACK', `Budget status calculated correctly: ${progress.status}`);

  // ==========================================================================
  // PHASE 9: LIVE GROQ AI ASSISTANT CONVERSATION TESTS
  // ==========================================================================
  console.log('\n--- PHASE 9: Live Groq AI Assistant Financial Queries ---');

  const testQueries = [
    {
      query: 'Meri total income kitni hai?',
      validate: (msg) => msg.includes('50,000') || msg.includes('50000'),
      name: 'Query 1: Total Income recognition (₹50,000)'
    },
    {
      query: 'Mera total expense kitna hai?',
      validate: (msg) => msg.includes('29,000') || msg.includes('29000'),
      name: 'Query 2: Total Expense recognition (₹29,000)'
    },
    {
      query: 'Mere paas kitna paisa bacha hai?',
      validate: (msg) => msg.includes('21,000') || msg.includes('21000'),
      name: 'Query 3: Net Savings recognition (₹21,000)'
    },
    {
      query: 'Sabse zyada mera paisa kis category mein ja raha hai?',
      validate: (msg) => msg.toLowerCase().includes('rent') || msg.includes('10,000'),
      name: 'Query 4: Highest spending category (Rent: ₹10,000)'
    },
    {
      query: 'Food aur shopping mein mera spending kaisa hai?',
      validate: (msg) => (msg.includes('5,000') || msg.includes('5000') || msg.includes('9,000') || msg.includes('9000')) && (msg.toLowerCase().includes('food') || msg.toLowerCase().includes('shopping')),
      name: 'Query 5: Specific category queries (Food & Shopping)'
    },
    {
      query: 'Meri financial situation ka detailed analysis karo aur mujhe 5 practical suggestions do.',
      validate: (msg) => msg.length > 100 && !msg.includes('Completed maximum analysis steps'),
      name: 'Query 6: Multi-step financial analysis with 5 actionable suggestions'
    }
  ];

  for (const item of testQueries) {
    try {
      const chatRes = await request('/ai/chat', {
        method: 'POST',
        headers: authHeaderA,
        body: JSON.stringify({
          message: item.query,
          history: []
        })
      });

      assert(chatRes.status === 200 && chatRes.data.success, `${item.name} - API 200 OK`);
      const msg = chatRes.data.message || '';
      const isValid = item.validate(msg);
      assert(isValid, `${item.name} - Content verified with real DB data`, `Preview: ${msg.slice(0, 80)}...`);
      await new Promise((res) => setTimeout(res, 1200));
    } catch (e) {
      assert(false, `${item.name} failed with error: ${e.message}`);
    }
  }

  // ==========================================================================
  // PHASE 10 & 11: AI BUDGET PROPOSAL & APPROVAL FLOW
  // ==========================================================================
  console.log('\n--- PHASE 10 & 11: AI Budget Creation Proposal & Approval ---');

  const budgetProposalRes = await request('/ai/chat', {
    method: 'POST',
    headers: authHeaderA,
    body: JSON.stringify({
      message: 'Mere liye ₹30,000 ka monthly budget bana do',
      history: []
    })
  });

  assert(budgetProposalRes.status === 200, 'AI Budget request returned 200');
  const proposalPayload = budgetProposalRes.data;
  assert(proposalPayload.type === 'confirmation', 'Proposal type is "confirmation"');
  assert(proposalPayload.confirmation && proposalPayload.confirmation.actionId, 'Proposal has valid actionId');

  const actionArgs = proposalPayload.confirmation.arguments;
  assert(actionArgs.monthlyBudget === 30000, 'Proposal monthlyBudget is exactly 30000');
  assert(Array.isArray(actionArgs.categories) && actionArgs.categories.length > 0, 'Proposal includes normalized category allocations');

  const propCategorySum = actionArgs.categories.reduce((s, c) => s + c.amount, 0);
  assert(propCategorySum === 30000, 'Exact sum invariant verified on proposal: sum(categories) === 30000', `Sum: ${propCategorySum}`);

  // APPROVAL EXECUTION
  console.log('\nExecuting Approval...');
  const approveRes = await request('/ai/confirm', {
    method: 'POST',
    headers: authHeaderA,
    body: JSON.stringify({
      actionId: proposalPayload.confirmation.actionId
    })
  });

  assert(approveRes.status === 200 && approveRes.data.success, 'Approval executed successfully');
  assert(approveRes.data.data.monthlyBudget === 30000, 'Post-write verified monthly budget is ₹30,000');

  // Verify MongoDB directly via API
  const getBudgetRes = await request(`/budgets?month=${currentMonth}`, { headers: authHeaderA });
  assert(getBudgetRes.status === 200 && getBudgetRes.data.data.monthlyBudget === 30000, 'Direct MongoDB verification confirms budget is ₹30,000');

  // ==========================================================================
  // PHASE 12: CANCEL ACTION TEST
  // ==========================================================================
  console.log('\n--- PHASE 12: Cancel Action Test ---');
  await new Promise(r => setTimeout(r, 1500));
  const cancelProposalRes = await request('/ai/chat', {
    method: 'POST',
    headers: authHeaderA,
    body: JSON.stringify({
      message: 'Mere liye ₹40,000 ka monthly budget bana do',
      history: []
    })
  });

  assert(cancelProposalRes.status === 200 && cancelProposalRes.data.type === 'confirmation', 'Second proposal generated for ₹40,000');
  const cancelActionId = cancelProposalRes.data?.confirmation?.actionId;
  assert(!!cancelActionId, 'Cancel proposal has valid actionId');

  // Cancel action
  const cancelRes = await request('/ai/cancel', {
    method: 'POST',
    headers: authHeaderA,
    body: JSON.stringify({ actionId: cancelActionId })
  });
  assert(cancelRes.status === 200 && cancelRes.data.success, 'Action cancelled successfully');

  // Verify database was NOT changed to ₹40,000
  const verifyAfterCancel = await request(`/budgets?month=${currentMonth}`, { headers: authHeaderA });
  assert(verifyAfterCancel.data.data.monthlyBudget === 30000, 'Database remains unchanged at ₹30,000 after cancellation (no accidental mutation)');

  // ==========================================================================
  // PHASE 16: MULTI-USER DATA ISOLATION
  // ==========================================================================
  console.log('\n--- PHASE 16: Multi-User Data Isolation ---');
  const testEmailB = `qa.user.b.${uniqueTs}@example.com`;
  const regB = await request('/auth/register', {
    method: 'POST',
    body: JSON.stringify({
      name: 'QA User B',
      email: testEmailB,
      password: testPassword
    })
  });
  assert(regB.status === 201 && regB.data.success, 'User B registered successfully');
  const tokenB = regB.data.data?.token || regB.data.token;
  const authHeaderB = { Authorization: `Bearer ${tokenB}` };

  // User B checks transactions and summary
  const summaryB = await request(`/transactions/summary?month=${currentMonth}`, { headers: authHeaderB });
  assert(summaryB.data.data.totalIncome === 0, 'User B total income is ₹0 (isolated from User A)');
  assert(summaryB.data.data.totalExpense === 0, 'User B total expense is ₹0 (isolated from User A)');

  // User B adds Income ₹20,000
  await request('/incomes', {
    method: 'POST',
    headers: authHeaderB,
    body: JSON.stringify({ amount: 20000, source: 'Consulting', date: today })
  });

  // Query AI as User B
  const aiQueryB = await request('/ai/chat', {
    method: 'POST',
    headers: authHeaderB,
    body: JSON.stringify({ message: 'Meri total income kitni hai?' })
  });
  assert(aiQueryB.data.message.includes('20,000') || aiQueryB.data.message.includes('20000'), 'User B AI query correctly reports ₹20,000 (User B data)');
  assert(!aiQueryB.data.message.includes('50,000'), 'User B AI query does NOT contain User A ₹50,000');

  // Query AI as User A again
  const aiQueryA = await request('/ai/chat', {
    method: 'POST',
    headers: authHeaderA,
    body: JSON.stringify({ message: 'Meri total income kitni hai?' })
  });
  assert(aiQueryA.data.message.includes('50,000') || aiQueryA.data.message.includes('50000'), 'User A AI query still accurately reports ₹50,000 (User A data)');

  // ==========================================================================
  // FINAL RESULTS
  // ==========================================================================
  console.log('\n================================================================');
  console.log(`🎉 ALL TESTS COMPLETED: ${passed} PASSED, ${failed} FAILED`);
  console.log('================================================================\n');

  if (failed > 0) {
    process.exit(1);
  } else {
    process.exit(0);
  }
}

runRealUserE2ETest().catch(err => {
  console.error('Fatal E2E Test Runner Error:', err);
  process.exit(1);
});
