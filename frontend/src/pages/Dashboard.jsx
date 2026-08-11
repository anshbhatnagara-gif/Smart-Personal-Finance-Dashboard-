import React, { useState, useEffect } from 'react';
import { transactionAPI, budgetAPI, getErrorMessage } from '../services/api';
import StatCard from '../components/StatCard';
import BudgetCard from '../components/BudgetCard';
import ChartCard from '../components/ChartCard';
import TransactionTable from '../components/TransactionTable';
import Loading from '../components/Loading';
import { AlertCircle, PlusCircle, ArrowUpRight } from 'lucide-react';
import { Link } from 'react-router-dom';

const Dashboard = () => {
  const [summary, setSummary] = useState(null);
  const [budgetProgress, setBudgetProgress] = useState(null);
  const [trends, setTrends] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Get current YYYY-MM month in local time
  const getCurrentMonth = () => {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    return `${year}-${month}`;
  };

  const fetchDashboardData = async () => {
    setLoading(true);
    setError('');
    const currentMonth = getCurrentMonth();
    
    try {
      // Execute all dashboard queries in parallel
      const [summaryRes, budgetRes, trendsRes] = await Promise.all([
        transactionAPI.getSummary({ month: currentMonth }),
        budgetAPI.getBudgetProgress(currentMonth),
        transactionAPI.getTrends({ limit: 6 })
      ]);

      if (summaryRes.data.success) {
        setSummary(summaryRes.data.data);
      }
      if (budgetRes.data.success) {
        setBudgetProgress(budgetRes.data.data);
      }
      if (trendsRes.data.success) {
        setTrends(trendsRes.data.data);
      }
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
    window.addEventListener('financial-update', fetchDashboardData);
    return () => window.removeEventListener('financial-update', fetchDashboardData);
  }, []);

  if (loading) {
    return <Loading message="Analyzing your financial transactions..." />;
  }

  if (error) {
    return (
      <div className="panel animate-fade" style={{ display: 'flex', alignItems: 'center', gap: '12px', color: 'var(--danger)', background: 'var(--danger-light)' }}>
        <AlertCircle size={20} />
        <span>{error}</span>
      </div>
    );
  }

  const { totalIncome, totalExpense, netSavings, categoryBreakdown, recentTransactions } = summary || {
    totalIncome: 0,
    totalExpense: 0,
    netSavings: 0,
    categoryBreakdown: [],
    recentTransactions: []
  };

  const budgetLimit = budgetProgress ? budgetProgress.monthlyBudget : 0;
  const isBudgetExceeded = budgetProgress ? budgetProgress.isExceeded : false;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* 1. Stat Cards Row */}
      <div className="grid-cols-3">
        <StatCard 
          title="Net Savings" 
          value={netSavings} 
          type="balance" 
          trendText="Total net balance this month"
          isTrendPositive={netSavings >= 0}
        />
        <StatCard 
          title="Total Income" 
          value={totalIncome} 
          type="income" 
          trendText="Income inflows this month"
          isTrendPositive={true}
        />
        <StatCard 
          title="Total Expenses" 
          value={totalExpense} 
          type="expense" 
          trendText="Money spent this month"
          isTrendPositive={false}
        />
      </div>

      {/* 2. Charts and Budget Split Row */}
      <div className="grid-cols-3" style={{ gridTemplateColumns: '2fr 1fr', gap: '24px' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Income vs Expenses Trends */}
          <div style={{ height: '320px' }}>
            <ChartCard 
              title="Income vs Expenses Trends (6 Months)" 
              type="trend" 
              chartData={trends} 
            />
          </div>
        </div>

        {/* Budget Status Widget */}
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          <BudgetCard 
            month={getCurrentMonth()}
            monthlyBudget={budgetLimit}
            totalSpent={totalExpense}
            remaining={budgetLimit - totalExpense}
            isExceeded={isBudgetExceeded}
            onSetBudgetClick={() => window.location.href = '/budgets'}
          />
        </div>
      </div>

      {/* 3. Breakdown & Recent Transactions Row */}
      <div className="grid-cols-2">
        {/* Category Breakdown Chart */}
        <div style={{ height: '360px' }}>
          {categoryBreakdown.length > 0 ? (
            <ChartCard 
              title="Expense Breakdown by Category" 
              type="breakdown" 
              chartData={categoryBreakdown} 
            />
          ) : (
            <div className="panel" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
              <span style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>No expense data available for charts.</span>
            </div>
          )}
        </div>

        {/* Recent Transactions List */}
        <div className="panel" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <h3 style={{ fontSize: '0.95rem', fontWeight: 600, fontFamily: 'var(--font-display)' }}>Recent Activities</h3>
            <Link 
              to="/transactions" 
              style={{ 
                fontSize: '0.82rem', 
                color: 'var(--accent)', 
                display: 'flex', 
                alignItems: 'center', 
                gap: '4px',
                fontWeight: 500
              }}
            >
              See Ledger <ArrowUpRight size={14} />
            </Link>
          </div>

          {recentTransactions.length > 0 ? (
            <div style={{ overflow: 'hidden' }}>
              <TransactionTable 
                transactions={recentTransactions} 
                showActions={false} 
              />
            </div>
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', flex: 1, border: '1px dashed var(--border)', borderRadius: 'var(--radius-md)' }}>
              <span style={{ fontSize: '0.88rem', color: 'var(--text-muted)', padding: '24px 0' }}>No recent activities found.</span>
            </div>
          )}
        </div>
      </div>

      {/* Responsive layout styles overrides */}
      <style>{`
        @media (max-width: 1200px) {
          .grid-cols-3 {
            grid-template-columns: 1fr !important;
          }
        }
      `}</style>
    </div>
  );
};

export default Dashboard;
