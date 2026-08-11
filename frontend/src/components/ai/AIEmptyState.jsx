import React from 'react';
import { Bot, HelpCircle } from 'lucide-react';

const SUGGESTIONS = [
  'Analyze my spending this month',
  'bhai iss month sabse zyada kharcha kaha hua?',
  'Compare this month with last month',
  'Add ₹500 food expense today',
  'Am I going over my budget?',
  'How much did I save this month?'
];

const AIEmptyState = ({ onSelectPrompt }) => {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '32px 16px',
        textAlign: 'center',
        height: '100%',
        margin: 'auto 0'
      }}
    >
      <div
        style={{
          width: '48px',
          height: '48px',
          borderRadius: '50%',
          background: 'rgba(59, 130, 246, 0.1)',
          color: 'var(--accent)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          marginBottom: '16px',
          boxShadow: 'var(--shadow-sm)',
          border: '1px solid rgba(59, 130, 246, 0.2)'
        }}
      >
        <Bot size={24} />
      </div>

      <h3 style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '8px', fontFamily: 'var(--font-display)' }}>
        Your Personal Finance Assistant
      </h3>
      <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginBottom: '24px', maxWidth: '280px', lineHeight: '1.4' }}>
        Ask me about your spending, income, budget, or transactions. Click any example below to start:
      </p>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', width: '100%', maxWidth: '320px' }}>
        {SUGGESTIONS.map((prompt) => (
          <button
            key={prompt}
            onClick={() => onSelectPrompt(prompt)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              padding: '10px 14px',
              background: 'var(--panel-bg)',
              border: '1px solid var(--border)',
              borderRadius: 'var(--radius-lg)',
              color: 'var(--text-primary)',
              fontSize: '0.82rem',
              textAlign: 'left',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
              width: '100%',
              outline: 'none',
              fontWeight: 500
            }}
            className="ai-suggestion-btn"
          >
            <HelpCircle size={14} style={{ color: 'var(--accent)', flexShrink: 0 }} />
            <span>{prompt}</span>
          </button>
        ))}
      </div>
    </div>
  );
};

export default AIEmptyState;
