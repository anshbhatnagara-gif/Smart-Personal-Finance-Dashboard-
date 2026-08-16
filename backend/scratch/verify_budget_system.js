const BASE_URL = 'http://127.0.0.1:5000/api';

const delay = ms => new Promise(r => setTimeout(r, ms));

async function runBudgetAuditSuite() {
  console.log('================================================================');
  console.log('   STARTING BUDGET SYSTEM COMPREHENSIVE AUDIT & TEST SUITE     ');
  console.log('================================================================');

  // 1. Authenticate primary test user
  const loginRes = await fetch(`${BASE_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: 'test@example.com', password: 'password123' })
  });
  const loginData = await loginRes.json();
  if (!loginData.success || !loginData.data?.token) {
    throw new Error('Primary user login failed');
  }
  const token = loginData.data.token;
  const authHeaders = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  };

  // --- PART A: API CALCULATIONS & METRICS VERIFICATION ---
  console.log('\n--- [Part A]: Verifying Budget API Calculations & Metrics ---');
  const month = new Date().toISOString().slice(0, 7);
  const progRes = await fetch(`${BASE_URL}/budgets/progress?month=${month}`, { headers: authHeaders });
  const progData = await progRes.json();

  console.log('Budget Progress API Output:', JSON.stringify(progData.data, null, 2));

  if (progRes.status !== 200 || !progData.success) throw new Error('Budget progress API failed');
  const d = progData.data;

  // Assertions against seeded data (Income: 5850, Expenses: 1990, Budget: 3000)
  if (d.totalIncome !== 5850) throw new Error(`Incorrect totalIncome: expected 5850, got ${d.totalIncome}`);
  if (d.totalSpent !== 1990) throw new Error(`Incorrect totalSpent: expected 1990, got ${d.totalSpent}`);
  if (d.monthlyBudget !== 3000) throw new Error(`Incorrect monthlyBudget: expected 3000, got ${d.monthlyBudget}`);
  if (d.remaining !== 1010) throw new Error(`Incorrect remaining: expected 1010, got ${d.remaining}`);
  if (d.savings !== 3860) throw new Error(`Incorrect savings: expected 3860, got ${d.savings}`);
  if (d.status !== 'UNDER_BUDGET') throw new Error(`Incorrect status: expected UNDER_BUDGET, got ${d.status}`);
  if (!d.highestCategory || d.highestCategory.category !== 'Rent') throw new Error('Incorrect highestCategory');

  console.log('✅ Assertion Passed: Budget API calculations match database figures exactly.');

  // --- PART B: EDGE CASE HANDLING ---
  console.log('\n--- [Part B]: Testing Edge Cases ---');

  // Invalid negative budget
  const negRes = await fetch(`${BASE_URL}/budgets`, {
    method: 'POST',
    headers: authHeaders,
    body: JSON.stringify({ monthlyBudget: -500, month })
  });
  if (negRes.status !== 400) throw new Error(`Negative budget should return 400, got ${negRes.status}`);
  console.log('✅ Assertion Passed: Negative budget limit correctly rejected with 400.');

  // User with no income
  const userNoIncRes = await fetch(`${BASE_URL}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: 'No Income User', email: `noinc_${Date.now()}@example.com`, password: 'password123' })
  });
  const tokenNoInc = (await userNoIncRes.json()).data.token;

  // Add an expense of ₹200 for No Income user
  await fetch(`${BASE_URL}/expenses`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${tokenNoInc}` },
    body: JSON.stringify({ amount: 200, category: 'Food', description: 'Lunch' })
  });

  const progNoIncRes = await fetch(`${BASE_URL}/budgets/progress?month=${month}`, {
    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${tokenNoInc}` }
  });
  const dNoInc = (await progNoIncRes.json()).data;
  if (dNoInc.totalIncome !== 0 || dNoInc.savings !== -200 || dNoInc.savingsRate !== 0) {
    throw new Error('Zero income edge case handling failed');
  }
  console.log('✅ Assertion Passed: ₹0 income edge case handled gracefully without NaN errors.');

  // User Exceeding Budget Status
  await fetch(`${BASE_URL}/budgets`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${tokenNoInc}` },
    body: JSON.stringify({ monthlyBudget: 150, month })
  });
  const progOverRes = await fetch(`${BASE_URL}/budgets/progress?month=${month}`, {
    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${tokenNoInc}` }
  });
  const dOver = (await progOverRes.json()).data;
  if (dOver.status !== 'OVER_BUDGET' || !dOver.isExceeded) {
    throw new Error(`Exceeded budget status failed: expected OVER_BUDGET, got ${dOver.status}`);
  }
  console.log('✅ Assertion Passed: Over-budget user status correctly identified as OVER_BUDGET.');

  // --- PART C: CROSS-USER SECURITY ISOLATION ---
  console.log('\n--- [Part C]: Verifying Cross-User Data Isolation ---');
  if (dNoInc.totalIncome === 5850 || dNoInc.totalSpent === 1990) {
    throw new Error('SECURITY VIOLATION: User B accessed User A financial data!');
  }
  console.log('✅ Assertion Passed: Cross-user data isolation verified (User B cannot see User A data).');

  // --- PART D: EXACT AI BUDGET QUERIES (1 THROUGH 5) ---
  console.log('\n--- [Part D]: Testing Exact AI Budget Queries (Live Groq) ---');

  async function testAIQuery(queryNum, prompt) {
    console.log(`\nQuery ${queryNum}: "${prompt}"`);
    await delay(12000); // 12s pause for rate limit safety
    const res = await fetch(`${BASE_URL}/ai/chat`, {
      method: 'POST',
      headers: authHeaders,
      body: JSON.stringify({ message: prompt, history: [] })
    });
    const data = await res.json();
    console.log(`Status: ${res.status}`);
    console.log('AI Response Output:\n------------------------------------------------');
    console.log(data.message);
    console.log('------------------------------------------------');
    if (data.confirmation) {
      console.log('Interactive Confirmation Card Proposed:', JSON.stringify(data.confirmation));
    }
    if (res.status !== 200 || !data.success) {
      throw new Error(`AI query ${queryNum} failed with status ${res.status}`);
    }
    if (data.message.includes('Completed maximum analysis steps')) {
      throw new Error(`AI query ${queryNum} returned maximum step message`);
    }
  }

  // Query 1: "Mera budget kaisa chal raha hai?"
  await testAIQuery(1, 'Mera budget kaisa chal raha hai?');

  // Query 2: "Mere liye ek realistic monthly budget bana do."
  await testAIQuery(2, 'Mere liye ek realistic monthly budget bana do.');

  // Query 3: "Main kis category mein sabse zyada overspend kar raha hoon?"
  await testAIQuery(3, 'Main kis category mein sabse zyada overspend kar raha hoon?');

  // Query 4: "Agar main har month ₹500 save karna chahta hoon to mera budget kya hona chahiye?"
  await testAIQuery(4, 'Agar main har month ₹500 save karna chahta hoon to mera budget kya hona chahiye?');

  // Query 5: "Mere current expenses ko dekhkar budget optimize karo."
  await testAIQuery(5, 'Mere current expenses ko dekhkar budget optimize karo.');

  console.log('\n================================================================');
  console.log('   ALL BUDGET SYSTEM AUDIT TESTS PASSED SUCCESSFULLY!          ');
  console.log('================================================================');
}

runBudgetAuditSuite().catch(err => {
  console.error('\n❌ BUDGET AUDIT SUITE FAILED:', err.message);
  process.exit(1);
});
