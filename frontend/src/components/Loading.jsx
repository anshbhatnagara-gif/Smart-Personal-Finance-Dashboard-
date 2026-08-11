import React from 'react';

const Loading = ({ message = 'Loading financial data...' }) => {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '60px 20px',
      color: 'var(--text-secondary)',
      width: '100%'
    }}>
      <div style={{
        width: '42px',
        height: '42px',
        border: '3.5px solid var(--border)',
        borderTop: '3.5px solid var(--accent)',
        borderRadius: '50%',
        animation: 'spin 0.8s linear infinite',
        marginBottom: '16px'
      }} />
      <p style={{ fontStyle: 'italic', fontSize: '0.92rem', fontFamily: 'var(--font-sans)' }}>{message}</p>
    </div>
  );
};

export default Loading;
