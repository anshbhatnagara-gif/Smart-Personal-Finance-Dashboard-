import React, { useState, useEffect } from 'react';
import { budgetAPI, getErrorMessage } from '../services/api';
import BudgetCard from '../components/BudgetCard';
import Loading from '../components/Loading';
import { AlertCircle, Target, Sparkles, PieChart } from 'lucide-react';

const Budgets = () => {
  const getCurrentMonthString = () => {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    return `${year}-${month}`;
  };

  const [selectedMonth, setSelectedMonth] = useState(() => getCurrentMonthString());
  const [budgetProgress, setBudgetProgress] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Form State
  const [limitInput, setLimitInput] = useState('');
  const [submitLoading, setSubmitLoading] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');

  const fetchBudgetData = async () => {
    setLoading(true);
    setError('');
    setSuccessMsg('');
    try {
      const res = await budgetAPI.getBudgetProgress(selectedMonth);
      if (res.data.success) {
        setBudgetProgress(res.data.data);
        setLimitInput(res.data.data.monthlyBudget || '');
      }
    } catch (err) {
      console.error('Error fetching budget:', err);
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBudgetData();
  }, [selectedMonth]);

  useEffect(() => {
    window.addEventListener('financial-update', fetchBudgetData);
    return () => window.removeEventListener('financial-update', fetchBudgetData);
  }, [selectedMonth]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccessMsg('');

    const parsedLimit = parseFloat(limitInput);
    if (isNaN(parsedLimit) || parsedLimit < 0) {
      setError('Budget limit cannot be negative or invalid');
      return;
    }

    setSubmitLoading(true);

    try {
      const payload = {
        monthlyBudget: parsedLimit,
        month: selectedMonth
      };
      
      const res = await budgetAPI.setBudget(payload);
      if (res.data.success) {
        setSuccessMsg('Budget limit updated successfully!');
        fetchBudgetData();
      }
    } catch (err) {
      console.error('Update budget limit failed:', err);
      setError(getErrorMessage(err));
    } finally {
      setSubmitLoading(false);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0
    }).format(amount || 0);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* Month Selection Panel */}
      <div className="panel animate-fade" style={{ display: 'flex', flexWrap: 'wrap', gap: '16px', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Target size={18} style={{ color: 'var(--accent)' }} />
          <span style={{ fontWeight: 600, fontSize: '0.95rem', color: 'var(--text-primary)' }}>Select Active Budget Period</span>
        </div>
        <input 
          type="month" 
          className="form-control" 
          value={selectedMonth}
          onChange={(e) => setSelectedMonth(e.target.value)}
          style={{ width: '180px' }}
        />
      </div>

      {/* Main Budget Grid */}
      <div className="grid-cols-2">
        {/* Left column: Visual progress details */}
        <div>
          {loading ? (
            <Loading message="Fetching budget records..." />
          ) : (
            <BudgetCard 
              month={selectedMonth}
              monthlyBudget={budgetProgress ? budgetProgress.monthlyBudget : 0}
              totalSpent={budgetProgress ? budgetProgress.totalSpent : 0}
              remaining={budgetProgress ? budgetProgress.remaining : 0}
              savings={budgetProgress ? budgetProgress.savings : 0}
              status={budgetProgress ? budgetProgress.status : 'NO_BUDGET'}
              isExceeded={budgetProgress ? budgetProgress.isExceeded : false}
            />
          )}
        </div>

        {/* Right column: Form to set/update budget limit */}
        <div className="panel" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 600, fontFamily: 'var(--font-display)', color: 'var(--text-primary)' }}>
            Configure Monthly Limit
          </h3>
          <p style={{ fontSize: '0.88rem', color: 'var(--text-secondary)' }}>
            Set a monthly spending limit. Real-time alerts will notify you if expenses approach or exceed this limit.
          </p>

          {/* Form alerts */}
          {error && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '10px 12px',
              borderRadius: 'var(--radius-md)',
              background: 'var(--danger-light)',
              color: 'var(--danger)',
              fontSize: '0.82rem',
              fontWeight: 500
            }}>
              <AlertCircle size={14} />
              <span>{error}</span>
            </div>
          )}

          {successMsg && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '10px 12px',
              borderRadius: 'var(--radius-md)',
              background: 'var(--success-light)',
              color: 'var(--success)',
              fontSize: '0.82rem',
              fontWeight: 500
            }}>
              <Sparkles size={14} />
              <span>{successMsg}</span>
            </div>
          )}

          {/* Budget Setting Form */}
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label">Monthly Limit (₹)</label>
              <input 
                type="number" 
                step="1"
                className="form-control" 
                placeholder="e.g. 5000"
                value={limitInput}
                onChange={(e) => setLimitInput(e.target.value)}
                required
              />
            </div>

            <button 
              type="submit" 
              className="btn btn-primary" 
              style={{ width: '100%', padding: '12px' }}
              disabled={submitLoading}
            >
              {submitLoading ? 'Updating Limit...' : 'Save Budget Limit'}
            </button>
          </form>
        </div>
      </div>

      {/* Category Spending Breakdown Panel */}
      {budgetProgress && budgetProgress.categorySpending && budgetProgress.categorySpending.length > 0 && (
        <div className="panel animate-fade" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <PieChart size={18} style={{ color: 'var(--accent)' }} />
            <h3 style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--text-primary)', fontFamily: 'var(--font-display)' }}>
              Category Spending Breakdown ({selectedMonth})
            </h3>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '12px' }}>
            {budgetProgress.categorySpending.map((cat, idx) => (
              <div 
                key={idx} 
                style={{
                  padding: '12px',
                  borderRadius: 'var(--radius-md)',
                  background: 'rgba(255,255,255,0.02)',
                  border: '1px solid var(--border)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '4px'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                  <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{cat.category}</span>
                  <span style={{ color: 'var(--accent)', fontWeight: 600 }}>{cat.percentage}%</span>
                </div>
                <span style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                  {formatCurrency(cat.amount)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

    </div>
  );
};

export default Budgets;
