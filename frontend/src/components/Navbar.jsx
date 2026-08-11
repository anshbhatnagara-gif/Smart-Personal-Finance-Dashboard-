import React, { useState, useEffect } from 'react';
import { Menu, Sun, Moon, LogOut } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useLocation } from 'react-router-dom';
import AIButton from './ai/AIButton';

const Navbar = ({ toggleSidebar, onToggleAI, isAIOpen }) => {
  const { user, logout } = useAuth();
  const location = useLocation();
  
  // Theme state: defaults to dark (premium dashboard)
  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'dark');

  useEffect(() => {
    if (theme === 'light') {
      document.body.classList.add('light-theme');
    } else {
      document.body.classList.remove('light-theme');
    }
    localStorage.setItem('theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => (prev === 'dark' ? 'light' : 'dark'));
  };

  // Map route pathname to clean user-facing title
  const getPageTitle = () => {
    switch (location.pathname) {
      case '/':
        return 'Dashboard';
      case '/income':
        return 'Income Manager';
      case '/expenses':
        return 'Expense Tracker';
      case '/budgets':
        return 'Monthly Budgets';
      case '/transactions':
        return 'Transaction Ledger';
      case '/profile':
        return 'User Profile';
      default:
        return 'Smart Finance';
    }
  };

  return (
    <header 
      style={{
        height: 'var(--navbar-height)',
        background: 'var(--bg-secondary)',
        borderBottom: '1px solid var(--border)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 24px',
        position: 'fixed',
        top: 0,
        right: 0,
        left: 0,
        zIndex: 900,
        marginLeft: 'var(--sidebar-width)',
        transition: 'margin-left 0.3s ease',
      }}
      className="navbar-container"
    >
      {/* Left side: Hamburger (mobile) + Page Title */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <button 
          onClick={toggleSidebar}
          className="btn-icon mobile-menu-btn"
          style={{
            display: 'none',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Menu size={18} />
        </button>

        <h1 
          className="title-display"
          style={{
            fontSize: '1.25rem',
            color: 'var(--text-primary)',
          }}
        >
          {getPageTitle()}
        </h1>
      </div>

      {/* Right side: Quick actions & user info */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        {/* AI Assistant Button */}
        <AIButton isOpen={isAIOpen} onToggle={onToggleAI} />

        {/* Theme Toggle Button */}
        <button 
          onClick={toggleTheme}
          className="btn-icon"
          title={theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            borderRadius: 'var(--radius-md)'
          }}
        >
          {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
        </button>

        {/* User quick badge */}
        {user && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            padding: '4px 12px',
            borderRadius: 'var(--radius-md)',
            background: 'var(--bg-tertiary)',
            border: '1px solid var(--border)'
          }}>
            <div style={{
              width: '28px',
              height: '28px',
              borderRadius: '50%',
              background: 'var(--accent)',
              color: '#ffffff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 600,
              fontSize: '0.85rem'
            }}>
              {user.name.charAt(0).toUpperCase()}
            </div>
            <span 
              className="navbar-username"
              style={{
                fontSize: '0.88rem',
                color: 'var(--text-primary)',
                fontWeight: 500
              }}
            >
              {user.name}
            </span>
          </div>
        )}
      </div>

      <style>{`
        @media (max-width: 992px) {
          .navbar-container {
            left: 0 !important;
            margin-left: 0 !important;
          }
          .mobile-menu-btn {
            display: flex !important;
          }
          .navbar-username {
            display: none !important;
          }
        }
      `}</style>
    </header>
  );
};

export default Navbar;
