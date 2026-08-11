import React from 'react';
import { Sparkles } from 'lucide-react';

const EmptyState = ({ title = 'No records found', description = 'Get started by adding some transactions to view details.', actionText, onAction }) => {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '48px 24px',
      textAlign: 'center',
      border: '2px dashed var(--border)',
      borderRadius: 'var(--radius-lg)',
      background: 'rgba(255, 255, 255, 0.01)',
      margin: '16px 0',
      width: '100%'
    }}>
      <div style={{
        padding: '12px',
        borderRadius: 'var(--radius-md)',
        background: 'var(--accent-light)',
        color: 'var(--accent)',
        marginBottom: '16px'
      }}>
        <Sparkles size={28} />
      </div>
      <h3 style={{
        fontSize: '1.15rem',
        fontWeight: 600,
        color: 'var(--text-primary)',
        marginBottom: '8px',
        fontFamily: 'var(--font-display)'
      }}>{title}</h3>
      <p style={{
        fontSize: '0.9rem',
        color: 'var(--text-secondary)',
        maxWidth: '320px',
        marginBottom: '20px',
        lineHeight: 1.5
      }}>{description}</p>
      {actionText && onAction && (
        <button className="btn btn-primary" onClick={onAction}>
          {actionText}
        </button>
      )}
    </div>
  );
};

export default EmptyState;
