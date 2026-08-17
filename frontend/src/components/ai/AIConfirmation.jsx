import React, { useState } from 'react';
import { Check, X, AlertCircle, RefreshCw } from 'lucide-react';
import { aiAPI, getErrorMessage } from '../../services/api';

const AIConfirmation = ({ confirmation, onConfirmSuccess, onCancel }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  if (!confirmation) return null;

  const { action, arguments: args, actionId } = confirmation;

  // Pretty print action labels
  const getActionLabel = () => {
    switch (action) {
      case 'createExpense': return 'Add Expense?';
      case 'createIncome': return 'Add Income?';
      case 'updateExpense': return 'Update Expense?';
      case 'updateIncome': return 'Update Income?';
      case 'createBudget':
      case 'updateBudget': return 'Set Monthly Budget?';
      case 'deleteIncome': return 'Delete Income Entry?';
      case 'deleteExpense': return 'Delete Expense Entry?';
      default: return 'Confirm Transaction Action?';
    }
  };

  const handleApprove = async () => {
    if (loading) return;
    setLoading(true);
    setError('');

    try {
      const res = await aiAPI.confirm(actionId);
      if (res.data.success) {
        // Dispatch financial-update event to trigger re-fetches globally
        window.dispatchEvent(new CustomEvent('financial-update'));
        onConfirmSuccess(res.data);
      }
    } catch (err) {
      console.error('Approve action failed:', err);
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = async () => {
    if (loading) return;
    setLoading(true);
    setError('');

    try {
      const res = await aiAPI.cancel(actionId);
      if (res.data.success) {
        onCancel();
      }
    } catch (err) {
      console.error('Cancel action failed:', err);
      // Even if cancel API fails locally, clear card on client side for safety
      onCancel();
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="ai-confirmation animate-slide-in"
      style={{
        background: 'var(--panel-bg)',
        border: '1px solid var(--accent)',
        borderRadius: 'var(--radius-lg)',
        padding: '16px',
        marginBottom: '16px',
        boxShadow: 'var(--shadow-md)',
        display: 'flex',
        flexDirection: 'column',
        gap: '12px',
        width: '100%'
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', borderBottom: '1px solid var(--border)', paddingBottom: '8px' }}>
        <AlertCircle size={16} style={{ color: 'var(--accent)' }} />
        <span style={{ fontWeight: 600, fontSize: '0.9rem', color: 'var(--text-primary)' }}>
          {getActionLabel()}
        </span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
        {args.amount && (
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span>Amount:</span>
            <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
              ₹{parseFloat(args.amount).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </span>
          </div>
        )}
        {args.category && (
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span>Category:</span>
            <span style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{args.category}</span>
          </div>
        )}
        {args.source && (
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span>Source:</span>
            <span style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{args.source}</span>
          </div>
        )}
        {args.month && (
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span>Target Month:</span>
            <span style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{args.month}</span>
          </div>
        )}
        {args.monthlyBudget && (
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span>Monthly Budget:</span>
            <span style={{ fontWeight: 700, color: 'var(--accent)', fontSize: '0.92rem' }}>
              ₹{parseFloat(args.monthlyBudget).toLocaleString('en-IN', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
            </span>
          </div>
        )}
        {args.isExistingBudget && (
          <div style={{
            padding: '6px 8px',
            borderRadius: 'var(--radius-sm)',
            background: 'var(--warning-light)',
            color: 'var(--warning)',
            fontSize: '0.75rem',
            fontWeight: 500
          }}>
            Existing budget for this month: ₹{parseFloat(args.existingBudgetAmount || 0).toLocaleString('en-IN')}. Approving will update it.
          </div>
        )}
        {Array.isArray(args.categories) && args.categories.length > 0 && (
          <div style={{ marginTop: '8px', borderTop: '1px solid var(--border)', paddingTop: '8px' }}>
            <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Category Breakdown
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', background: 'rgba(0,0,0,0.1)', borderRadius: 'var(--radius-sm)', padding: '8px' }}>
              {args.categories.map((cat, idx) => (
                <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>{cat.category}:</span>
                  <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                    ₹{parseFloat(cat.amount).toLocaleString('en-IN', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
                  </span>
                </div>
              ))}
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', borderTop: '1px dashed var(--border)', paddingTop: '4px', marginTop: '2px', fontWeight: 700 }}>
                <span style={{ color: 'var(--text-primary)' }}>Total:</span>
                <span style={{ color: 'var(--accent)' }}>
                  ₹{parseFloat(args.monthlyBudget || args.total || 0).toLocaleString('en-IN', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
                </span>
              </div>
            </div>
          </div>
        )}
        {(args.description || args.notes) && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '2px', borderTop: '1px dashed var(--border)', paddingTop: '6px', marginTop: '4px' }}>
            <span>Description:</span>
            <span style={{ color: 'var(--text-primary)', fontStyle: 'italic' }}>{args.description || args.notes}</span>
          </div>
        )}
      </div>

      {error && (
        <div style={{ fontSize: '0.78rem', color: 'var(--danger)', display: 'flex', gap: '6px', alignItems: 'center' }}>
          <AlertCircle size={12} />
          <span>{error}</span>
        </div>
      )}

      <div style={{ display: 'flex', gap: '8px', marginTop: '4px' }}>
        <button
          onClick={handleCancel}
          disabled={loading}
          className="btn btn-secondary"
          style={{ flex: 1, padding: '8px', fontSize: '0.82rem', gap: '4px', justifyContent: 'center' }}
        >
          <X size={14} />
          <span>Cancel</span>
        </button>
        <button
          onClick={handleApprove}
          disabled={loading}
          className="btn btn-primary"
          style={{ flex: 1, padding: '8px', fontSize: '0.82rem', gap: '4px', justifyContent: 'center' }}
        >
          {loading ? <RefreshCw size={14} className="animate-spin" /> : <Check size={14} />}
          <span>Approve</span>
        </button>
      </div>
    </div>
  );
};

export default AIConfirmation;
