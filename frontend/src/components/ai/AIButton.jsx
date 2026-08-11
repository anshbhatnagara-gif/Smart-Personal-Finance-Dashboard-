import React from 'react';
import { Bot } from 'lucide-react';

const AIButton = ({ isOpen, onToggle }) => {
  return (
    <button
      onClick={onToggle}
      className="btn btn-secondary btn-icon"
      aria-expanded={isOpen}
      aria-label="Toggle Personal Finance AI Assistant"
      title="AI Finance Assistant"
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        padding: '8px 16px',
        borderRadius: 'var(--radius-lg)',
        border: '1px solid var(--border)',
        background: 'var(--panel-bg)',
        color: 'var(--text-primary)',
        cursor: 'pointer',
        transition: 'all 0.2s ease',
        boxShadow: 'var(--shadow-sm)',
        fontWeight: 500
      }}
    >
      <Bot size={18} style={{ color: 'var(--accent)' }} />
      <span className="desktop-only" style={{ fontSize: '0.88rem' }}>AI Assistant</span>
    </button>
  );
};

export default AIButton;
