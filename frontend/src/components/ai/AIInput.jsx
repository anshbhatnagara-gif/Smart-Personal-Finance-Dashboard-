import React, { useState, useRef, useEffect } from 'react';
import { Send } from 'lucide-react';

const AIInput = ({ onSend, disabled }) => {
  const [text, setText] = useState('');
  const textareaRef = useRef(null);

  const handleSubmit = (e) => {
    if (e) e.preventDefault();
    if (disabled || !text.trim()) return;

    if (text.length > 2000) {
      alert('Message exceeds the maximum limit of 2000 characters.');
      return;
    }

    onSend(text.trim());
    setText('');
  };

  const handleKeyDown = (e) => {
    // Submit on Enter without shift
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  // Autoresize textarea height
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [text]);

  const charCount = text.length;
  const isNearLimit = charCount > 1800;

  return (
    <form onSubmit={handleSubmit} className="ai-input" style={{ width: '100%' }}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'flex-end', position: 'relative' }}>
          <textarea
            ref={textareaRef}
            rows={1}
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask AI Assistant..."
            disabled={disabled}
            maxLength={2000}
            aria-label="Ask AI Assistant input"
            style={{
              flex: 1,
              background: 'var(--bg-primary)',
              color: 'var(--text-primary)',
              border: '1px solid var(--border)',
              borderRadius: 'var(--radius-lg)',
              padding: '10px 14px',
              fontSize: '0.9rem',
              resize: 'none',
              minHeight: '40px',
              maxHeight: '120px',
              outline: 'none',
              transition: 'border 0.2s ease',
              fontFamily: 'inherit'
            }}
          />
          <button
            type="submit"
            disabled={disabled || !text.trim()}
            className="btn btn-primary"
            aria-label="Send message"
            style={{
              padding: '10px',
              borderRadius: 'var(--radius-lg)',
              height: '40px',
              width: '40px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer'
            }}
          >
            <Send size={16} />
          </button>
        </div>

        {/* Character count feedback near limit */}
        {isNearLimit && (
          <span style={{
            fontSize: '0.72rem',
            color: charCount >= 2000 ? 'var(--danger)' : 'var(--text-secondary)',
            alignSelf: 'flex-end',
            fontWeight: 500
          }}>
            {charCount}/2000
          </span>
        )}
      </div>
    </form>
  );
};

export default AIInput;
