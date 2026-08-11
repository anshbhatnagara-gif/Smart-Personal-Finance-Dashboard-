import React from 'react';
import { ArrowDownLeft, ArrowUpRight, Edit, Trash2 } from 'lucide-react';

const TransactionTable = ({ transactions, onEdit, onDelete, showActions = false }) => {
  
  const formatCurrency = (amount, type) => {
    const formatted = new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
    return type === 'income' ? `+ ${formatted}` : `- ${formatted}`;
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  return (
    <div className="table-container">
      <table className="table">
        <thead>
          <tr>
            <th>Type</th>
            <th>Category / Source</th>
            <th>Description</th>
            <th>Date</th>
            <th>Amount</th>
            {showActions && <th style={{ textAlign: 'right' }}>Actions</th>}
          </tr>
        </thead>
        <tbody>
          {transactions.map((tx) => (
            <tr key={tx._id} className="animate-fade">
              {/* Type Badge */}
              <td>
                <span className={`badge ${tx.type === 'income' ? 'badge-success' : 'badge-danger'}`} style={{ gap: '4px' }}>
                  {tx.type === 'income' ? (
                    <ArrowDownLeft size={12} style={{ strokeWidth: 3 }} />
                  ) : (
                    <ArrowUpRight size={12} style={{ strokeWidth: 3 }} />
                  )}
                  {tx.type}
                </span>
              </td>

              {/* Category or Source */}
              <td style={{ fontWeight: 500, color: 'var(--text-primary)' }}>
                {tx.categoryOrSource}
              </td>

              {/* Description */}
              <td style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                {tx.description || <span style={{ fontStyle: 'italic', color: 'var(--text-muted)' }}>No description</span>}
              </td>

              {/* Date */}
              <td style={{ color: 'var(--text-secondary)' }}>
                {formatDate(tx.date)}
              </td>

              {/* Amount (Styled by type) */}
              <td style={{ 
                fontWeight: 600, 
                color: tx.type === 'income' ? 'var(--success)' : 'var(--danger)',
                fontFamily: 'var(--font-display)'
              }}>
                {formatCurrency(tx.amount, tx.type)}
              </td>

              {/* Row Action Buttons */}
              {showActions && (
                <td style={{ textAlign: 'right' }}>
                  <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                    {onEdit && (
                      <button 
                        onClick={() => onEdit(tx)}
                        className="btn-icon"
                        title="Edit entry"
                        style={{ width: '32px', height: '32px' }}
                      >
                        <Edit size={14} />
                      </button>
                    )}
                    {onDelete && (
                      <button 
                        onClick={() => onDelete(tx)}
                        className="btn-icon"
                        title="Delete entry"
                        style={{ width: '32px', height: '32px', color: 'var(--danger)' }}
                      >
                        <Trash2 size={14} />
                      </button>
                    )}
                  </div>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default TransactionTable;
