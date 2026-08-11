import React from 'react';
import { X } from 'lucide-react';

const Modal = ({ isOpen, onClose, title, children }) => {
  if (!isOpen) return null;

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      width: '100vw',
      height: '100vh',
      zIndex: 1100,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '16px'
    }}>
      {/* Backdrop */}
      <div 
        onClick={onClose}
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          background: 'rgba(5, 8, 16, 0.75)',
          backdropFilter: 'blur(5px)',
          WebkitBackdropFilter: 'blur(5px)',
        }} 
      />
      
      {/* Modal Card */}
      <div 
        className="panel animate-scale"
        style={{
          position: 'relative',
          width: '100%',
          maxWidth: '500px',
          background: 'var(--bg-secondary)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius-lg)',
          boxShadow: 'var(--shadow-lg)',
          zIndex: 1,
          padding: '24px',
        }}
      >
        {/* Header */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '20px',
          paddingBottom: '12px',
          borderBottom: '1px solid var(--border)'
        }}>
          <h2 style={{
            fontSize: '1.2rem',
            fontWeight: 600,
            fontFamily: 'var(--font-display)',
            color: 'var(--text-primary)'
          }}>{title}</h2>
          <button 
            onClick={onClose}
            className="btn-icon"
            style={{
              width: '30px',
              height: '30px',
              borderRadius: 'var(--radius-sm)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            <X size={16} />
          </button>
        </div>

        {/* Content Body */}
        <div>
          {children}
        </div>
      </div>
    </div>
  );
};

export default Modal;
