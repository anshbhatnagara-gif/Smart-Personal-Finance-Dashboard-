import React from 'react';
import { AlertTriangle, CheckCircle, Target, TrendingUp, ShieldAlert } from 'lucide-react';

const BudgetCard = ({ month, monthlyBudget = 0, totalSpent = 0, remaining = 0, savings = 0, status, isExceeded, onSetBudgetClick }) => {
  const actualPercent = monthlyBudget > 0 ? Math.round((totalSpent / monthlyBudget) * 100) : 0;
  const clampedPercentage = Math.min(actualPercent, 100);

  // Format month YYYY-MM to word format (e.g. August 2026)
  const formatMonthName = (monthString) => {
    if (!monthString) return '';
    const [year, monthNum] = monthString.split('-');
    const date = new Date(year, monthNum - 1, 1);
    return date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
  };

  const getProgressColor = () => {
    if (actualPercent > 100) return 'var(--danger)';
    if (actualPercent > 85) return 'var(--warning)';
    return 'var(--success)';
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0
    }).format(amount || 0);
  };

  const getStatusBadge = () => {
    switch (status) {
      case 'OVER_BUDGET':
        return { text: 'OVER BUDGET', bg: 'var(--danger-light)', color: 'var(--danger)', icon: AlertTriangle };
      case 'NEAR_LIMIT':
        return { text: 'NEAR LIMIT', bg: 'var(--warning-light)', color: 'var(--warning)', icon: ShieldAlert };
      case 'ON_TRACK':
        return { text: 'ON TRACK', bg: 'var(--success-light)', color: 'var(--success)', icon: CheckCircle };
      case 'UNDER_BUDGET':
      default:
        return { text: 'UNDER BUDGET', bg: 'var(--success-light)', color: 'var(--success)', icon: CheckCircle };
    }
  };

  const badge = getStatusBadge();
  const StatusIcon = badge.icon;

  return (
    <div className="panel animate-fade" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Target size={18} style={{ color: 'var(--accent)' }} />
          <span style={{ fontWeight: 600, fontSize: '0.95rem', color: 'var(--text-primary)' }}>
            Budget: {formatMonthName(month)}
          </span>
        </div>
        {monthlyBudget > 0 && (
          <span style={{
            fontSize: '0.72rem',
            fontWeight: 700,
            padding: '4px 8px',
            borderRadius: 'var(--radius-sm)',
            background: badge.bg,
            color: badge.color,
            letterSpacing: '0.5px'
          }}>
            {badge.text}
          </span>
        )}
      </div>

      {/* Stats Grid */}
      {monthlyBudget === 0 ? (
        <div style={{
          padding: '20px',
          textAlign: 'center',
          background: 'rgba(255,255,255,0.01)',
          borderRadius: 'var(--radius-md)',
          border: '1px dashed var(--border)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '8px'
        }}>
          <span style={{ fontSize: '0.88rem', color: 'var(--text-muted)' }}>No monthly budget limit set for this month.</span>
          {onSetBudgetClick && (
            <button onClick={onSetBudgetClick} className="btn btn-primary" style={{ padding: '6px 14px', fontSize: '0.82rem' }}>
              Set Monthly Limit
            </button>
          )}
        </div>
      ) : (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>Monthly Limit</span>
              <span style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--text-primary)', fontFamily: 'var(--font-display)' }}>
                {formatCurrency(monthlyBudget)}
              </span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>Remaining</span>
              <span style={{ 
                fontSize: '1.15rem', 
                fontWeight: 700, 
                color: remaining >= 0 ? 'var(--success)' : 'var(--danger)',
                fontFamily: 'var(--font-display)'
              }}>
                {formatCurrency(remaining)}
              </span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>Spent</span>
              <span style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--text-primary)', fontFamily: 'var(--font-display)' }}>
                {formatCurrency(totalSpent)}
              </span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>Net Savings</span>
              <span style={{ fontSize: '1.05rem', fontWeight: 600, color: savings >= 0 ? 'var(--success)' : 'var(--danger)', fontFamily: 'var(--font-display)' }}>
                {formatCurrency(savings)}
              </span>
            </div>
          </div>

          {/* Progress Bar Container */}
          <div style={{ width: '100%', marginTop: '4px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', marginBottom: '6px', color: 'var(--text-secondary)' }}>
              <span>Used: {formatCurrency(totalSpent)}</span>
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
                width: `${clampedPercentage}%`,
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
            background: badge.bg,
            color: badge.color,
            fontSize: '0.82rem',
            fontWeight: 500,
            marginTop: '4px'
          }}>
            <StatusIcon size={14} />
            <span>
              {isExceeded 
                ? `Limit Exceeded by ${formatCurrency(Math.abs(remaining))}! Review non-essential expenses.` 
                : actualPercent > 85 
                ? `Caution: ${actualPercent}% of budget limit utilized.` 
                : 'Within budget limits. Great financial tracking!'}
            </span>
          </div>
        </>
      )}
    </div>
  );
};

export default BudgetCard;
