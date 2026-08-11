import React from 'react';
import { TrendingUp, TrendingDown, DollarSign } from 'lucide-react';

const StatCard = ({ title, value, type = 'balance', trendText, isTrendPositive }) => {
  const getColors = () => {
    switch (type) {
      case 'income':
        return {
          bg: 'var(--success-light)',
          color: 'var(--success)',
          border: 'rgba(16, 185, 129, 0.2)'
        };
      case 'expense':
        return {
          bg: 'var(--danger-light)',
          color: 'var(--danger)',
          border: 'rgba(244, 63, 94, 0.2)'
        };
      case 'budget':
        return {
          bg: 'var(--warning-light)',
          color: 'var(--warning)',
          border: 'rgba(245, 158, 11, 0.2)'
        };
      case 'balance':
      default:
        return {
          bg: 'var(--accent-light)',
          color: 'var(--accent)',
          border: 'rgba(99, 102, 241, 0.2)'
        };
    }
  };

  const colors = getColors();

  // Helper to format currency numbers
  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  return (
    <div 
      className="panel animate-fade"
      style={{
        display: 'flex',
        flexDirection: 'column',
        position: 'relative',
        overflow: 'hidden'
      }}
    >
      {/* Header Row */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        width: '100%'
      }}>
        <span style={{
          fontSize: '0.88rem',
          color: 'var(--text-secondary)',
          fontWeight: 500
        }}>{title}</span>
        
        <div style={{
          padding: '8px',
          borderRadius: 'var(--radius-sm)',
          background: colors.bg,
          color: colors.color,
          border: `1px solid ${colors.border}`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          <DollarSign size={16} />
        </div>
      </div>

      {/* Main Metric Value */}
      <h3 className="metric-value">
        {formatCurrency(value)}
      </h3>

      {/* Footer Trend Line */}
      {trendText && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          marginTop: '4px'
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            color: isTrendPositive ? 'var(--success)' : 'var(--danger)',
            fontSize: '0.85rem',
            fontWeight: 500
          }}>
            {isTrendPositive ? <TrendingUp size={14} style={{ marginRight: '2px' }} /> : <TrendingDown size={14} style={{ marginRight: '2px' }} />}
          </div>
          <span style={{
            fontSize: '0.8rem',
            color: 'var(--text-muted)'
          }}>{trendText}</span>
        </div>
      )}
    </div>
  );
};

export default StatCard;
