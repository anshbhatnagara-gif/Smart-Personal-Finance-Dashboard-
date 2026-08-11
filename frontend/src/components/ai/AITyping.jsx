import React from 'react';

const AITyping = () => {
  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'flex-start',
        marginBottom: '16px',
        width: '100%'
      }}
    >
      <div
        className="ai-typing"
        style={{
          background: 'var(--panel-bg)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius-lg)',
          borderBottomLeftRadius: '4px',
          padding: '12px 16px',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          boxShadow: 'var(--shadow-sm)'
        }}
      >
        <span style={{ fontSize: '0.88rem', color: 'var(--text-secondary)' }}>AI is thinking</span>
        <div style={{ display: 'flex', gap: '3px' }}>
          <div className="typing-dot" style={{ width: '4px', height: '4px', borderRadius: '50%', background: 'var(--text-secondary)' }} />
          <div className="typing-dot" style={{ width: '4px', height: '4px', borderRadius: '50%', background: 'var(--text-secondary)', animationDelay: '0.2s' }} />
          <div className="typing-dot" style={{ width: '4px', height: '4px', borderRadius: '50%', background: 'var(--text-secondary)', animationDelay: '0.4s' }} />
        </div>
      </div>
    </div>
  );
};

export default AITyping;
