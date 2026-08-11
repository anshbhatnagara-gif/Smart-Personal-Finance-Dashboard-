import React, { useState, useEffect } from 'react';
import { incomeAPI, getErrorMessage } from '../services/api';
import TransactionTable from '../components/TransactionTable';
import Modal from '../components/Modal';
import Loading from '../components/Loading';
import EmptyState from '../components/EmptyState';
import { PlusCircle, Search, Calendar, AlertCircle } from 'lucide-react';

const Income = () => {
  const [incomes, setIncomes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  
  // Date Filters
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  // Modal states
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalTitle, setModalTitle] = useState('Add Income');
  const [editingIncome, setEditingIncome] = useState(null);

  // Form Fields
  const [amount, setAmount] = useState('');
  const [source, setSource] = useState('');
  const [date, setDate] = useState(() => new Date().toISOString().split('T')[0]);
  const [notes, setNotes] = useState('');
  const [formError, setFormError] = useState('');
  const [formLoading, setFormLoading] = useState(false);

  const fetchIncomes = async () => {
    setLoading(true);
    setError('');
    try {
      const params = {};
      if (search) params.search = search;
      if (startDate) params.startDate = startDate;
      if (endDate) params.endDate = endDate;

      const res = await incomeAPI.getIncomes(params);
      if (res.data.success) {
        setIncomes(res.data.data);
      }
    } catch (err) {
      console.error('Error fetching incomes:', err);
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Debounce search slightly
    const delayDebounceFn = setTimeout(() => {
      fetchIncomes();
    }, 300);

    return () => clearTimeout(delayDebounceFn);
  }, [search, startDate, endDate]);

  useEffect(() => {
    window.addEventListener('financial-update', fetchIncomes);
    return () => window.removeEventListener('financial-update', fetchIncomes);
  }, [search, startDate, endDate]);

  const handleOpenAddModal = () => {
    setEditingIncome(null);
    setAmount('');
    setSource('');
    setDate(new Date().toISOString().split('T')[0]);
    setNotes('');
    setFormError('');
    setModalTitle('Add Income');
    setIsModalOpen(true);
  };

  const handleOpenEditModal = (tx) => {
    // Find matching income object in the local array
    const rawIncome = incomes.find(item => item._id === tx._id);
    if (!rawIncome) return;

    setEditingIncome(rawIncome);
    setAmount(rawIncome.amount);
    setSource(rawIncome.source);
    setDate(new Date(rawIncome.date).toISOString().split('T')[0]);
    setNotes(rawIncome.notes || '');
    setFormError('');
    setModalTitle('Edit Income');
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
      source,
      date,
      notes,
    };

    try {
      if (editingIncome) {
        await incomeAPI.updateIncome(editingIncome._id, payload);
      } else {
        await incomeAPI.createIncome(payload);
      }
      setIsModalOpen(false);
      fetchIncomes();
    } catch (err) {
      console.error('Save income failed:', err);
      setFormError(getErrorMessage(err));
    } finally {
      setFormLoading(false);
    }
  };

  const handleDeleteClick = async (tx) => {
    if (window.confirm(`Are you sure you want to delete this income entry for "${tx.categoryOrSource}"?`)) {
      try {
        await incomeAPI.deleteIncome(tx._id);
        fetchIncomes();
      } catch (err) {
        console.error('Delete income failed:', err);
        alert(getErrorMessage(err));
      }
    }
  };

  // Map incomes to TransactionTable format
  const mappedIncomes = incomes.map(inc => ({
    _id: inc._id,
    type: 'income',
    categoryOrSource: inc.source,
    description: inc.notes,
    date: inc.date,
    amount: inc.amount
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
              placeholder="Search source or notes..." 
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
          <span>Add Income</span>
        </button>
      </div>

      {/* Main Income Panel */}
      <div className="panel">
        {loading ? (
          <Loading message="Loading income ledger..." />
        ) : error ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--danger)' }}>
            <AlertCircle size={18} />
            <span>{error}</span>
          </div>
        ) : mappedIncomes.length > 0 ? (
          <TransactionTable 
            transactions={mappedIncomes}
            onEdit={handleOpenEditModal}
            onDelete={handleDeleteClick}
            showActions={true}
          />
        ) : (
          <EmptyState 
            title="No Income Registered" 
            description="It looks like you have not logged any income for the active filter range."
            actionText="Add Income Entry"
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
            <label className="form-label">Income Source</label>
            <input 
              type="text" 
              className="form-control" 
              placeholder="e.g. Salary, Freelance, Dividend"
              value={source}
              onChange={(e) => setSource(e.target.value)}
              required
            />
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
            <label className="form-label">Notes (Optional)</label>
            <textarea 
              className="form-control" 
              placeholder="Add additional remarks..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              style={{ minHeight: '80px', resize: 'vertical' }}
            />
          </div>

          <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
            <button type="button" className="btn btn-secondary" onClick={() => setIsModalOpen(false)}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={formLoading}>
              {formLoading ? 'Saving...' : 'Save Income'}
            </button>
          </div>
        </form>
      </Modal>

    </div>
  );
};

export default Income;
