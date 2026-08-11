const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '../.env') });
const { GoogleGenAI } = require('@google/genai');

const apiKey = process.env.AI_API_KEY;
const ai = new GoogleGenAI({ apiKey });

async function runDiagnostic() {
  console.log('Waiting 22 seconds for 429 rate limit window to clear...');
  await new Promise(res => setTimeout(res, 22000));

  const candidateModels = [
    'gemini-3.5-flash',
    'gemini-2.5-flash-lite',
    'gemini-1.5-flash-8b',
    'gemini-flash'
  ];

  console.log('\n--- Testing Text Generation ---');
  for (const modelName of candidateModels) {
    try {
      process.stdout.write(`Testing [${modelName}]... `);
      const res = await ai.models.generateContent({
        model: modelName,
        contents: 'Say Hello'
      });
      console.log(`SUCCESS! "${res.text?.trim()}"`);
    } catch (err) {
      console.log(`FAILED: ${err.message?.slice(0, 150)}`);
    }
  }

  console.log('\n--- Testing Function Calling on gemini-3.5-flash ---');
  try {
    const res = await ai.models.generateContent({
      model: 'gemini-3.5-flash',
      contents: 'bhai iss month sabse zyada kharcha kaha hua?',
      config: {
        tools: [{
          functionDeclarations: [{
            name: 'analyzeCategories',
            description: 'Analyzes spending categories for a given month',
            parameters: {
              type: 'OBJECT',
              properties: { month: { type: 'STRING' } }
            }
          }]
        }]
      }
    });
    console.log('Function call result:', res.functionCalls || res.text);
  } catch (err) {
    console.log('Function call error:', err.message);
  }
}

runDiagnostic().catch(console.error);
