import React from 'react';
import { AlertTriangle, CheckCircle, Target } from 'lucide-react';

const BudgetCard = ({ month, monthlyBudget, totalSpent, remaining, isExceeded, onSetBudgetClick }) => {
  const percentage = monthlyBudget > 0 ? Math.min(Math.round((totalSpent / monthlyBudget) * 100), 100) : 0;
  const actualPercent = monthlyBudget > 0 ? Math.round((totalSpent / monthlyBudget) * 100) : 0;

  // Format month YYYY-MM to word format (e.g. August 2026)
  const formatMonthName = (monthString) => {
    if (!monthString) return '';
    const [year, monthNum] = monthString.split('-');
    const date = new Date(year, monthNum - 1, 1);
    return date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
  };

  const getProgressColor = () => {
    if (actualPercent > 100) return 'var(--danger)';
    if (actualPercent > 75) return 'var(--warning)';
    return 'var(--success)';
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  return (
    <div className="panel animate-fade" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Title Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Target size={18} style={{ color: 'var(--accent)' }} />
          <span style={{ fontWeight: 600, fontSize: '0.95rem', color: 'var(--text-primary)' }}>
            Budget: {formatMonthName(month)}
          </span>
        </div>
        {onSetBudgetClick && (
          <button 
            onClick={onSetBudgetClick}
            className="btn btn-secondary"
            style={{ padding: '6px 12px', fontSize: '0.82rem', borderRadius: 'var(--radius-sm)' }}
          >
            Adjust Limit
          </button>
        )}
      </div>

      {/* Stats row */}
      {monthlyBudget === 0 ? (
        <div style={{
          padding: '16px',
          textAlign: 'center',
          background: 'rgba(255,255,255,0.01)',
          borderRadius: 'var(--radius-md)',
          border: '1px dashed var(--border)'
        }}>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>No budget set for this month.</span>
        </div>
      ) : (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Monthly Limit</span>
              <span style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--text-primary)', fontFamily: 'var(--font-display)' }}>
                {formatCurrency(monthlyBudget)}
              </span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Remaining</span>
              <span style={{ 
                fontSize: '1.2rem', 
                fontWeight: 700, 
                color: remaining >= 0 ? 'var(--success)' : 'var(--danger)',
                fontFamily: 'var(--font-display)'
              }}>
                {formatCurrency(remaining)}
              </span>
            </div>
          </div>

          {/* Progress Bar Container */}
          <div style={{ width: '100%', marginTop: '4px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', marginBottom: '6px', color: 'var(--text-secondary)' }}>
              <span>Spent: {formatCurrency(totalSpent)}</span>
              <span style={{ fontWeight: 600, color: getProgressColor() }}>{actualPercent}%</span>
            </div>
            <div style={{
              width: '100%',
              height: '8px',
              background: 'var(--bg-primary)',
              borderRadius: 'var(--radius-full)',
              overflow: 'hidden',
              border: '1px solid var(--border)'
            }}>
              <div style={{
                width: `${percentage}%`,
                height: '100%',
                background: getProgressColor(),
                borderRadius: 'var(--radius-full)',
                transition: 'width 0.4s cubic-bezier(0.4, 0, 0.2, 1)'
              }} />
            </div>
          </div>

          {/* Warning / Exceeded status */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '10px 12px',
            borderRadius: 'var(--radius-md)',
            background: isExceeded ? 'var(--danger-light)' : 'var(--success-light)',
            color: isExceeded ? 'var(--danger)' : 'var(--success)',
            fontSize: '0.82rem',
            fontWeight: 500,
            marginTop: '4px'
          }}>
            {isExceeded ? (
              <>
                <AlertTriangle size={14} />
                <span>Limit Exceeded! Try trimming down expenses.</span>
              </>
            ) : (
              <>
                <CheckCircle size={14} />
                <span>Within budget limits. Great financial tracking!</span>
              </>
            )}
          </div>
        </>
      )}
    </div>
  );
};

export default BudgetCard;
