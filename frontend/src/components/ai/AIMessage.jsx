import React from 'react';

const AIMessage = ({ role, content }) => {
  const isUser = role === 'user';

  // Helper to format bold markdown syntax safely
  const renderFormattedContent = (text) => {
    if (!text || typeof text !== 'string') return text;

    // Split text by ** bold tags
    const parts = text.split(/(\*\*.*?\*\*)/g);
    return parts.map((part, idx) => {
      if (part.startsWith('**') && part.endsWith('**') && part.length > 4) {
        return <strong key={idx} style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{part.slice(2, -2)}</strong>;
      }
      return part;
    });
  };

  return (
    <div
      style={{
        display: 'flex',
        justifyContent: isUser ? 'flex-end' : 'flex-start',
        marginBottom: '16px',
        width: '100%'
      }}
    >
      <div
        className={`ai-message ${isUser ? 'ai-message-user' : 'ai-message-assistant'}`}
        style={{
          maxWidth: '85%',
          padding: '12px 16px',
          borderRadius: 'var(--radius-lg)',
          fontSize: '0.9rem',
          lineHeight: '1.45',
          wordBreak: 'break-word',
          whiteSpace: 'pre-wrap',
          color: 'var(--text-primary)',
          boxShadow: 'var(--shadow-sm)',
          border: '1px solid var(--border)',
          background: isUser ? 'rgba(59, 130, 246, 0.15)' : 'var(--panel-bg)',
          alignSelf: isUser ? 'flex-end' : 'flex-start',
          borderBottomRightRadius: isUser ? '4px' : 'var(--radius-lg)',
          borderBottomLeftRadius: isUser ? 'var(--radius-lg)' : '4px'
        }}
      >
        {renderFormattedContent(content)}
      </div>
    </div>
  );
};

export default AIMessage;
