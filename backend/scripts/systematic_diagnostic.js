const http = require('http');

const API_BASE = 'http://127.0.0.1:5000/api';

const request = (endpoint, options = {}) => {
  return new Promise((resolve, reject) => {
    const url = `${API_BASE}${endpoint}`;
    const parsed = new URL(url);
    const postData = options.body || '';

    const reqOptions = {
      hostname: parsed.hostname,
      port: parsed.port,
      path: parsed.pathname + parsed.search,
      method: options.method || 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...(options.headers || {})
      }
    };

    if (postData) {
      reqOptions.headers['Content-Length'] = Buffer.byteLength(postData);
    }

    const req = http.request(reqOptions, (res) => {
      let data = '';
      res.on('data', (chunk) => { data += chunk; });
      res.on('end', () => {
        let json = {};
        try {
          json = JSON.parse(data);
        } catch (e) {
          json = { raw: data };
        }
        resolve({
          status: res.statusCode,
          headers: res.headers,
          data: json
        });
      });
    });

    req.on('error', (err) => reject(err));
    req.setTimeout(60000, () => {
      req.destroy(new Error('Request timed out after 60000ms'));
    });

    if (postData) {
      req.write(postData);
    }
    req.end();
  });
};

async function runDiagnostic() {
  console.log('================================================================');
  console.log('🔍 SYSTEMATIC DIAGNOSTIC SUITE');
  console.log('================================================================');

  const ts = Date.now();
  const testEmail = `diag.user.${ts}@test.com`;
  const testPassword = 'Password123!';

  // 1. Register & Login Test User
  console.log('\n--- 1. Testing Registration & Authentication ---');
  const regRes = await request('/auth/register', {
    method: 'POST',
    body: JSON.stringify({
      name: 'Diagnostic User',
      email: testEmail,
      password: testPassword
    })
  });

  if (regRes.status !== 201 || !regRes.data.success) {
    console.error('❌ Auth Registration Failed:', regRes.data);
    process.exit(1);
  }
  console.log('✅ User registered successfully. Status:', regRes.status);

  const token = regRes.data.data?.token || regRes.data.token;
  const authHeader = { Authorization: `Bearer ${token}` };

  // 2. Verify JWT via /auth/me
  const meRes = await request('/auth/me', { headers: authHeader });
  if (meRes.status !== 200 || !meRes.data.success) {
    console.error('❌ /auth/me verification failed:', meRes.data);
    process.exit(1);
  }
  const userId = meRes.data.data?._id || meRes.data.user?._id;
  console.log('✅ JWT verified successfully. User ID:', userId);

  // Add initial data for read tool testing
  await request('/incomes', {
    method: 'POST',
    headers: authHeader,
    body: JSON.stringify({ amount: 50000, source: 'Salary', date: '2026-08-01' })
  });
  await request('/expenses', {
    method: 'POST',
    headers: authHeader,
    body: JSON.stringify({ amount: 10000, category: 'Rent', date: '2026-08-05' })
  });

  // 3 & 4. Send ONE simple AI query that requires NO tool call
  console.log('\n--- 2. Testing Simple AI Query (No Tools) ---');
  await new Promise(r => setTimeout(r, 1500));
  const simpleQueryRes = await request('/ai/chat', {
    method: 'POST',
    headers: authHeader,
    body: JSON.stringify({
      message: 'Hello, reply with exactly: AI_OK',
      history: []
    })
  });

  console.log('Simple Query HTTP Status:', simpleQueryRes.status);
  console.log('Simple Query Response:', JSON.stringify(simpleQueryRes.data, null, 2));

  if (simpleQueryRes.status !== 200 || !simpleQueryRes.data.success) {
    console.error('❌ Simple AI Query Failed');
    process.exit(1);
  }
  console.log('✅ Simple AI Query PASSED');

  // 5, 6 & 7. Send ONE READ-only tool query & verify data belongs only to authenticated user
  console.log('\n--- 3. Testing READ Tool Query & Data Isolation ---');
  await new Promise(r => setTimeout(r, 1500));
  const readToolQueryRes = await request('/ai/chat', {
    method: 'POST',
    headers: authHeader,
    body: JSON.stringify({
      message: 'Meri total income kitni hai?',
      history: []
    })
  });

  console.log('Read Tool Query HTTP Status:', readToolQueryRes.status);
  console.log('Read Tool Query Response:', JSON.stringify(readToolQueryRes.data, null, 2));

  if (readToolQueryRes.status !== 200 || !readToolQueryRes.data.success) {
    console.error('❌ Read Tool Query Failed');
    process.exit(1);
  }
  const incomeText = readToolQueryRes.data.message || '';
  if (!incomeText.includes('50,000') && !incomeText.includes('50000')) {
    console.error('❌ Read Tool Data Mismatch (Expected 50000 in response):', incomeText);
    process.exit(1);
  }
  console.log('✅ Read Tool & User Isolation Query PASSED');

  // 8. Test ONE Budget Proposal flow
  console.log('\n--- 4. Testing Budget Proposal Flow ---');
  await new Promise(r => setTimeout(r, 1500));
  const budgetProposalRes = await request('/ai/chat', {
    method: 'POST',
    headers: authHeader,
    body: JSON.stringify({
      message: 'Mere liye ₹30,000 ka monthly budget bana do',
      history: []
    })
  });

  console.log('Budget Proposal HTTP Status:', budgetProposalRes.status);
  console.log('Budget Proposal Response:', JSON.stringify(budgetProposalRes.data, null, 2));

  if (budgetProposalRes.status !== 200 || budgetProposalRes.data.type !== 'confirmation') {
    console.error('❌ Budget Proposal Flow Failed');
    process.exit(1);
  }

  const conf = budgetProposalRes.data.confirmation || {};
  const actionId = conf.actionId;
  const args = conf.arguments || conf.payload || {};
  const monthlyBudget = args.monthlyBudget;
  const categories = args.categories || [];
  const catSum = categories.reduce((sum, c) => sum + (c.amount || 0), 0);

  console.log(`Proposal: monthlyBudget=${monthlyBudget}, categorySum=${catSum}`);

  if (monthlyBudget !== 30000 || catSum !== 30000) {
    console.error('❌ Budget Proposal Invariant Violated! monthlyBudget or catSum !== 30000');
    process.exit(1);
  }
  console.log('✅ Budget Proposal Exact Invariant PASSED: sum(categories) === 30000');

  // Test Approval of Proposal
  console.log('\n--- 5. Testing Budget Approval Flow ---');
  const approveRes = await request('/ai/confirm', {
    method: 'POST',
    headers: authHeader,
    body: JSON.stringify({ actionId })
  });

  console.log('Approve HTTP Status:', approveRes.status);
  console.log('Approve Response:', JSON.stringify(approveRes.data, null, 2));

  if (approveRes.status !== 200 || !approveRes.data.success) {
    console.error('❌ Budget Approval Failed');
    process.exit(1);
  }
  console.log('✅ Budget Approval PASSED');

  console.log('\n================================================================');
  console.log('🎉 ALL SYSTEMATIC DIAGNOSTIC PHASES PASSED WITH 100% SUCCESS!');
  console.log('================================================================');
}

runDiagnostic().catch(err => {
  console.error('💥 Diagnostic Fatal Error:', err);
  process.exit(1);
});
