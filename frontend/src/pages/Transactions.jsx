import React, { useState, useEffect } from 'react';
import { transactionAPI, getErrorMessage } from '../services/api';
import TransactionTable from '../components/TransactionTable';
import Loading from '../components/Loading';
import EmptyState from '../components/EmptyState';
import { Search, Calendar, Filter, ChevronLeft, ChevronRight, AlertCircle } from 'lucide-react';

const Transactions = () => {
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Filtering States
  const [search, setSearch] = useState('');
  const [type, setType] = useState(''); // '' (All), 'income', 'expense'
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  // Pagination States
  const [page, setPage] = useState(1);
  const [limit] = useState(15); // Show 15 entries per page
  const [totalPages, setTotalPages] = useState(1);
  const [totalItems, setTotalItems] = useState(0);

  const fetchTransactions = async () => {
    setLoading(true);
    setError('');
    try {
      const params = {
        page,
        limit,
      };
      if (search) params.search = search;
      if (type) params.type = type;
      if (startDate) params.startDate = startDate;
      if (endDate) params.endDate = endDate;

      const res = await transactionAPI.getTransactions(params);
      if (res.data.success) {
        setTransactions(res.data.data);
        if (res.data.pagination) {
          setTotalPages(res.data.pagination.pages || 1);
          setTotalItems(res.data.pagination.total || 0);
        }
      }
    } catch (err) {
      console.error('Error fetching transactions:', err);
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Debounce search/filters, reset page on filter change
    const delayDebounceFn = setTimeout(() => {
      fetchTransactions();
    }, 300);

    return () => clearTimeout(delayDebounceFn);
  }, [search, type, startDate, endDate, page]);

  useEffect(() => {
    window.addEventListener('financial-update', fetchTransactions);
    return () => window.removeEventListener('financial-update', fetchTransactions);
  }, [search, type, startDate, endDate, page]);

  // Reset to page 1 when filters are changed
  const handleFilterChange = (updater, value) => {
    updater(value);
    setPage(1);
  };

  const handlePrevPage = () => {
    if (page > 1) setPage(prev => prev - 1);
  };

  const handleNextPage = () => {
    if (page < totalPages) setPage(prev => prev + 1);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* Filtering Toolbar */}
      <div className="panel animate-fade" style={{ display: 'flex', flexWrap: 'wrap', gap: '16px', alignItems: 'center' }}>
        
        {/* Search */}
        <div style={{ position: 'relative', minWidth: '200px', flex: 1.5 }}>
          <Search size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
          <input 
            type="text" 
            className="form-control" 
            placeholder="Search keyword or description..." 
            value={search}
            onChange={(e) => handleFilterChange(setSearch, e.target.value)}
            style={{ paddingLeft: '38px' }}
          />
        </div>

        {/* Type Select */}
        <div style={{ position: 'relative', minWidth: '130px', flex: 1 }}>
          <Filter size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)', zIndex: 1 }} />
          <select 
            className="form-control" 
            value={type}
            onChange={(e) => handleFilterChange(setType, e.target.value)}
            style={{ paddingLeft: '38px' }}
          >
            <option value="">All Types</option>
            <option value="income">Incomes Only</option>
            <option value="expense">Expenses Only</option>
          </select>
        </div>

        {/* Start Date */}
        <div style={{ position: 'relative', minWidth: '140px', flex: 1 }}>
          <Calendar size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)', zIndex: 1 }} />
          <input 
            type="date" 
            className="form-control" 
            value={startDate}
            onChange={(e) => handleFilterChange(setStartDate, e.target.value)}
            style={{ paddingLeft: '38px' }}
            title="Start Date"
          />
        </div>

        {/* End Date */}
        <div style={{ position: 'relative', minWidth: '140px', flex: 1 }}>
          <Calendar size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)', zIndex: 1 }} />
          <input 
            type="date" 
            className="form-control" 
            value={endDate}
            onChange={(e) => handleFilterChange(setEndDate, e.target.value)}
            style={{ paddingLeft: '38px' }}
            title="End Date"
          />
        </div>
      </div>

      {/* Transactions Table Panel */}
      <div className="panel" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        
        {loading ? (
          <Loading message="Fetching unified transaction log..." />
        ) : error ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--danger)' }}>
            <AlertCircle size={18} />
            <span>{error}</span>
          </div>
        ) : transactions.length > 0 ? (
          <>
            {/* Table */}
            <TransactionTable transactions={transactions} showActions={false} />

            {/* Pagination Controls */}
            {totalPages > 1 && (
              <div style={{ 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'space-between',
                borderTop: '1px solid var(--border)',
                paddingTop: '16px',
                marginTop: '8px'
              }}>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                  Showing {(page - 1) * limit + 1} - {Math.min(page * limit, totalItems)} of {totalItems} logs
                </span>
                
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                  <button 
                    onClick={handlePrevPage} 
                    disabled={page === 1}
                    className="btn btn-secondary btn-icon"
                    style={{ borderRadius: 'var(--radius-md)' }}
                  >
                    <ChevronLeft size={16} />
                  </button>
                  <span style={{ fontSize: '0.88rem', fontWeight: 500, color: 'var(--text-primary)', padding: '0 8px' }}>
                    Page {page} of {totalPages}
                  </span>
                  <button 
                    onClick={handleNextPage} 
                    disabled={page === totalPages}
                    className="btn btn-secondary btn-icon"
                    style={{ borderRadius: 'var(--radius-md)' }}
                  >
                    <ChevronRight size={16} />
                  </button>
                </div>
              </div>
            )}
          </>
        ) : (
          <EmptyState 
            title="No Transactions Match Filters" 
            description="Adjust your search keywords, filter types, or date boundaries to locate the transactions."
          />
        )}
      </div>

    </div>
  );
};

export default Transactions;
