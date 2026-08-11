import React, { useState, useEffect } from 'react';
import { expenseAPI, getErrorMessage } from '../services/api';
import TransactionTable from '../components/TransactionTable';
import Modal from '../components/Modal';
import Loading from '../components/Loading';
import EmptyState from '../components/EmptyState';
import { PlusCircle, Search, Calendar, AlertCircle } from 'lucide-react';

const EXPENSE_CATEGORIES = [
  'Food',
  'Shopping',
  'Travel',
  'Fuel',
  'Education',
  'Healthcare',
  'Entertainment',
  'Bills',
  'Rent',
  'Others',
];

const Expenses = () => {
  const [expenses, setExpenses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  
  // Date Filters
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  // Modal states
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalTitle, setModalTitle] = useState('Add Expense');
  const [editingExpense, setEditingExpense] = useState(null);

  // Form Fields
  const [amount, setAmount] = useState('');
  const [category, setCategory] = useState('Food');
  const [date, setDate] = useState(() => new Date().toISOString().split('T')[0]);
  const [description, setDescription] = useState('');
  const [formError, setFormError] = useState('');
  const [formLoading, setFormLoading] = useState(false);

  const fetchExpenses = async () => {
    setLoading(true);
    setError('');
    try {
      const params = {};
      if (search) params.search = search;
      if (startDate) params.startDate = startDate;
      if (endDate) params.endDate = endDate;

      const res = await expenseAPI.getExpenses(params);
      if (res.data.success) {
        setExpenses(res.data.data);
      }
    } catch (err) {
      console.error('Error fetching expenses:', err);
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Debounce search slightly
    const delayDebounceFn = setTimeout(() => {
      fetchExpenses();
    }, 300);

    return () => clearTimeout(delayDebounceFn);
  }, [search, startDate, endDate]);

  useEffect(() => {
    window.addEventListener('financial-update', fetchExpenses);
    return () => window.removeEventListener('financial-update', fetchExpenses);
  }, [search, startDate, endDate]);

  const handleOpenAddModal = () => {
    setEditingExpense(null);
    setAmount('');
    setCategory('Food');
    setDate(new Date().toISOString().split('T')[0]);
    setDescription('');
    setFormError('');
    setModalTitle('Add Expense');
    setIsModalOpen(true);
  };

  const handleOpenEditModal = (tx) => {
    const rawExpense = expenses.find(item => item._id === tx._id);
    if (!rawExpense) return;

    setEditingExpense(rawExpense);
    setAmount(rawExpense.amount);
    setCategory(rawExpense.category);
    setDate(new Date(rawExpense.date).toISOString().split('T')[0]);
    setDescription(rawExpense.description || '');
    setFormError('');
    setModalTitle('Edit Expense');
    setIsModalOpen(true);
  };

  const handleFormSubmit = async (e) => {
    e.preventDefault();
    setFormError('');
    
    if (parseFloat(amount) <= 0) {
      setFormError('Amount must be greater than 0');
      return;
    }

    setFormLoading(true);

    const payload = {
      amount: parseFloat(amount),
      category,
      date,
      description,
    };

    try {
      if (editingExpense) {
        await expenseAPI.updateExpense(editingExpense._id, payload);
      } else {
        await expenseAPI.createExpense(payload);
      }
      setIsModalOpen(false);
      fetchExpenses();
    } catch (err) {
      console.error('Save expense failed:', err);
      setFormError(getErrorMessage(err));
    } finally {
      setFormLoading(false);
    }
  };

  const handleDeleteClick = async (tx) => {
    if (window.confirm(`Are you sure you want to delete this expense entry for "${tx.categoryOrSource}"?`)) {
      try {
        await expenseAPI.deleteExpense(tx._id);
        fetchExpenses();
      } catch (err) {
        console.error('Delete expense failed:', err);
        alert(getErrorMessage(err));
      }
    }
  };

  // Map expenses to TransactionTable format
  const mappedExpenses = expenses.map(exp => ({
    _id: exp._id,
    type: 'expense',
    categoryOrSource: exp.category,
    description: exp.description,
    date: exp.date,
    amount: exp.amount
  }));

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* Filters and Header Bar */}
      <div className="panel animate-fade" style={{ display: 'flex', flexWrap: 'wrap', gap: '16px', alignItems: 'center', justifyContent: 'space-between' }}>
        
        {/* Filters inputs */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px', flex: 1 }}>
          
          {/* Search Box */}
          <div style={{ position: 'relative', minWidth: '220px', flex: 1 }}>
            <Search size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
            <input 
              type="text" 
              className="form-control" 
              placeholder="Search category or description..." 
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{ paddingLeft: '38px' }}
            />
          </div>

          {/* Date Range Start */}
          <div style={{ position: 'relative', minWidth: '150px' }}>
            <Calendar size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)', zIndex: 1 }} />
            <input 
              type="date" 
              className="form-control" 
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              style={{ paddingLeft: '38px' }}
              title="Start Date"
            />
          </div>

          {/* Date Range End */}
          <div style={{ position: 'relative', minWidth: '150px' }}>
            <Calendar size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)', zIndex: 1 }} />
            <input 
              type="date" 
              className="form-control" 
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              style={{ paddingLeft: '38px' }}
              title="End Date"
            />
          </div>
        </div>

        {/* Action Button */}
        <button className="btn btn-primary" onClick={handleOpenAddModal}>
          <PlusCircle size={18} />
          <span>Add Expense</span>
        </button>
      </div>

      {/* Main Expenses Panel */}
      <div className="panel">
        {loading ? (
          <Loading message="Loading expense ledger..." />
        ) : error ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--danger)' }}>
            <AlertCircle size={18} />
            <span>{error}</span>
          </div>
        ) : mappedExpenses.length > 0 ? (
          <TransactionTable 
            transactions={mappedExpenses}
            onEdit={handleOpenEditModal}
            onDelete={handleDeleteClick}
            showActions={true}
          />
        ) : (
          <EmptyState 
            title="No Expenses Logged" 
            description="It looks like you have not logged any expenses for the active filter range."
            actionText="Add Expense Entry"
            onAction={handleOpenAddModal}
          />
        )}
      </div>

      {/* Add / Edit Modal Form */}
      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title={modalTitle}>
        {formError && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '10px 12px',
            borderRadius: 'var(--radius-md)',
            background: 'var(--danger-light)',
            color: 'var(--danger)',
            fontSize: '0.85rem',
            marginBottom: '16px',
            fontWeight: 500
          }}>
            <AlertCircle size={14} />
            <span>{formError}</span>
          </div>
        )}
        <form onSubmit={handleFormSubmit}>
          <div className="form-group">
            <label className="form-label">Category</label>
            <select 
              className="form-control"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              required
            >
              {EXPENSE_CATEGORIES.map((cat) => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Amount (USD)</label>
            <input 
              type="number" 
              step="0.01"
              className="form-control" 
              placeholder="0.00"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label">Date</label>
            <input 
              type="date" 
              className="form-control" 
              value={date}
              onChange={(e) => setDate(e.target.value)}
              required
            />
          </div>

          <div className="form-group" style={{ marginBottom: '24px' }}>
            <label className="form-label">Description (Optional)</label>
            <textarea 
              className="form-control" 
              placeholder="Add additional details..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              style={{ minHeight: '80px', resize: 'vertical' }}
            />
          </div>

          <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
            <button type="button" className="btn btn-secondary" onClick={() => setIsModalOpen(false)}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={formLoading}>
              {formLoading ? 'Saving...' : 'Save Expense'}
            </button>
          </div>
        </form>
      </Modal>

    </div>
  );
};

export default Expenses;
