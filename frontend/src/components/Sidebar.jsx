import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { 
  LayoutDashboard, 
  ArrowDownLeft, 
  ArrowUpRight, 
  Target, 
  History, 
  User, 
  LogOut,
  Wallet
} from 'lucide-react';

const Sidebar = ({ isOpen, toggleSidebar }) => {
  const { logout, user } = useAuth();

  const menuItems = [
    { name: 'Dashboard', path: '/', icon: LayoutDashboard },
    { name: 'Income', path: '/income', icon: ArrowDownLeft },
    { name: 'Expenses', path: '/expenses', icon: ArrowUpRight },
    { name: 'Budgets', path: '/budgets', icon: Target },
    { name: 'Transactions', path: '/transactions', icon: History },
    { name: 'Profile', path: '/profile', icon: User },
  ];

  const handleLogoutClick = () => {
    if (window.confirm('Are you sure you want to log out?')) {
      logout();
    }
  };

  return (
    <>
      {/* Mobile Sidebar Overlay */}
      {isOpen && (
        <div 
          onClick={toggleSidebar}
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            width: '100vw',
            height: '100vh',
            background: 'rgba(0, 0, 0, 0.5)',
            backdropFilter: 'blur(3px)',
            zIndex: 998,
          }}
        />
      )}

      {/* Sidebar Navigation */}
      <aside 
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          bottom: 0,
          width: 'var(--sidebar-width)',
          background: 'var(--bg-secondary)',
          borderRight: '1px solid var(--border)',
          display: 'flex',
          flexDirection: 'column',
          zIndex: 999,
          transform: isOpen ? 'translateX(0)' : 'translateX(-100%)',
          transition: 'transform 0.3s ease',
        }}
        className="sidebar-container"
      >
        {/* Brand Logo */}
        <div style={{
          height: 'var(--navbar-height)',
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          padding: '0 24px',
          borderBottom: '1px solid var(--border)'
        }}>
          <div style={{
            padding: '8px',
            borderRadius: 'var(--radius-sm)',
            background: 'var(--accent-light)',
            color: 'var(--accent)',
            display: 'flex'
          }}>
            <Wallet size={22} />
          </div>
          <span style={{
            fontSize: '1.25rem',
            fontWeight: 700,
            fontFamily: 'var(--font-display)',
            letterSpacing: '-0.02em',
            color: 'var(--text-primary)'
          }}>Smart Finance</span>
        </div>

        {/* User Quick Info */}
        {user && (
          <div style={{
            padding: '20px 24px',
            borderBottom: '1px solid var(--border)',
            display: 'flex',
            flexDirection: 'column',
            gap: '4px'
          }}>
            <span style={{ fontSize: '0.88rem', fontWeight: 600, color: 'var(--text-primary)' }}>{user.name}</span>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{user.email}</span>
          </div>
        )}

        {/* Navigation Menu */}
        <nav style={{
          flex: 1,
          padding: '24px 16px',
          display: 'flex',
          flexDirection: 'column',
          gap: '8px',
          overflowY: 'auto'
        }}>
          {menuItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                onClick={() => {
                  if (window.innerWidth <= 992) toggleSidebar();
                }}
                style={({ isActive }) => ({
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  padding: '12px 16px',
                  borderRadius: 'var(--radius-md)',
                  fontSize: '0.95rem',
                  fontWeight: 500,
                  color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
                  background: isActive ? 'var(--accent-light)' : 'transparent',
                  borderLeft: isActive ? '3px solid var(--accent)' : '3px solid transparent',
                  paddingLeft: isActive ? '13px' : '16px',
                  transition: 'var(--transition)'
                })}
              >
                {({ isActive }) => (
                  <>
                    <Icon size={18} style={{ color: isActive ? 'var(--accent)' : 'inherit' }} />
                    <span>{item.name}</span>
                  </>
                )}
              </NavLink>
            );
          })}
        </nav>

        {/* Logout Footer */}
        <div style={{
          padding: '16px',
          borderTop: '1px solid var(--border)'
        }}>
          <button
            onClick={handleLogoutClick}
            className="btn btn-secondary"
            style={{
              width: '100%',
              justifyContent: 'flex-start',
              gap: '12px',
              padding: '12px 16px',
              border: 'none',
              background: 'transparent',
              color: 'var(--danger)'
            }}
          >
            <LogOut size={18} />
            <span>Logout</span>
          </button>
        </div>
      </aside>

      {/* CSS style hook to apply responsive transform overrides */}
      <style>{`
        @media (min-width: 993px) {
          .sidebar-container {
            transform: translateX(0) !important;
          }
        }
      `}</style>
    </>
  );
};

export default Sidebar;
