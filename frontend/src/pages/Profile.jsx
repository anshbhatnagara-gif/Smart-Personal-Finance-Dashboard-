import React from 'react';
import { useAuth } from '../context/AuthContext';
import { User, Mail, DollarSign, Settings, ShieldAlert, LogOut } from 'lucide-react';

const Profile = () => {
  const { user, logout } = useAuth();

  const handleLogoutClick = () => {
    if (window.confirm('Are you sure you want to log out?')) {
      logout();
    }
  };

  if (!user) return null;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', maxWidth: '600px', margin: '0 auto' }}>
      
      {/* Profile Card */}
      <div className="panel animate-fade" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
        
        {/* User Large Avatar Header */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px', borderBottom: '1px solid var(--border)', paddingBottom: '20px' }}>
          <div style={{
            width: '64px',
            height: '64px',
            borderRadius: '50%',
            background: 'var(--accent)',
            color: '#ffffff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '1.8rem',
            fontWeight: 700,
            fontFamily: 'var(--font-display)',
            boxShadow: 'var(--shadow-md)'
          }}>
            {user.name.charAt(0).toUpperCase()}
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <h2 className="title-display" style={{ fontSize: '1.35rem', color: 'var(--text-primary)' }}>{user.name}</h2>
            <span style={{ fontSize: '0.88rem', color: 'var(--text-secondary)' }}>Standard Account Member</span>
          </div>
        </div>

        {/* Profile Info Fields */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          
          {/* Email */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div style={{ color: 'var(--text-muted)' }}><Mail size={18} /></div>
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>Email Address</span>
              <span style={{ fontSize: '0.95rem', fontWeight: 500, color: 'var(--text-primary)' }}>{user.email}</span>
            </div>
          </div>

          {/* Currency */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div style={{ color: 'var(--text-muted)' }}><DollarSign size={18} /></div>
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>Default Currency</span>
              <span style={{ fontSize: '0.95rem', fontWeight: 500, color: 'var(--text-primary)' }}>{user.currency || 'USD'}</span>
            </div>
          </div>

          {/* System Role */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div style={{ color: 'var(--text-muted)' }}><ShieldAlert size={18} /></div>
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>Access Authorization Role</span>
              <span style={{ fontSize: '0.95rem', fontWeight: 500, color: 'var(--text-primary)', textTransform: 'capitalize' }}>{user.role || 'user'}</span>
            </div>
          </div>

          {/* Settings / Theme info */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div style={{ color: 'var(--text-muted)' }}><Settings size={18} /></div>
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>Configuration Theme</span>
              <span style={{ fontSize: '0.95rem', fontWeight: 500, color: 'var(--text-primary)', textTransform: 'capitalize' }}>
                {user.theme || 'dark'} mode (adjust via top navigation)
              </span>
            </div>
          </div>
        </div>

        {/* Logout Action Button */}
        <div style={{ borderTop: '1px solid var(--border)', paddingTop: '20px', marginTop: '8px' }}>
          <button 
            onClick={handleLogoutClick}
            className="btn btn-danger"
            style={{ width: '100%', gap: '10px', padding: '12px' }}
          >
            <LogOut size={18} />
            <span>Sign Out of Dashboard</span>
          </button>
        </div>

      </div>

    </div>
  );
};

export default Profile;
