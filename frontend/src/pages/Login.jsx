import React, { useState, useEffect } from 'react';
import { useNavigate, Link, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Wallet, AlertCircle } from 'lucide-react';
import { getErrorMessage } from '../services/api';

const Login = () => {
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [infoMessage, setInfoMessage] = useState('');

  // Redirect to dashboard if user is already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/');
    }
    // Check if session expired query parameter is set
    if (searchParams.get('expired') === 'true') {
      setInfoMessage('Your session has expired. Please log in again.');
    }
  }, [isAuthenticated, navigate, searchParams]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setInfoMessage('');
    setLoading(true);

    try {
      await login(email, password);
      navigate('/');
    } catch (err) {
      console.error('Login failed:', err);
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '100vh',
      background: 'var(--bg-primary)',
      padding: '20px'
    }}>
      <div 
        className="panel animate-scale"
        style={{
          width: '100%',
          maxWidth: '420px',
          background: 'var(--bg-secondary)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius-lg)',
          boxShadow: 'var(--shadow-lg)',
          padding: '36px 30px'
        }}
      >
        {/* Branding header */}
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '12px',
          marginBottom: '32px',
          textAlign: 'center'
        }}>
          <div style={{
            padding: '12px',
            borderRadius: 'var(--radius-md)',
            background: 'var(--accent-light)',
            color: 'var(--accent)',
            display: 'flex'
          }}>
            <Wallet size={28} />
          </div>
          <h1 className="title-display" style={{ fontSize: '1.6rem', color: 'var(--text-primary)' }}>Welcome Back</h1>
          <p className="subtitle" style={{ fontSize: '0.88rem' }}>Log in to manage your smart finance dashboard</p>
        </div>

        {/* Info alerts (e.g. Session Expired) */}
        {infoMessage && (
          <div style={{
            padding: '12px 14px',
            borderRadius: 'var(--radius-md)',
            background: 'var(--warning-light)',
            color: 'var(--warning)',
            fontSize: '0.85rem',
            fontWeight: 500,
            marginBottom: '20px',
            border: '1px solid rgba(245, 158, 11, 0.2)'
          }}>
            {infoMessage}
          </div>
        )}

        {/* Error Alert */}
        {error && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            padding: '12px 14px',
            borderRadius: 'var(--radius-md)',
            background: 'var(--danger-light)',
            color: 'var(--danger)',
            fontSize: '0.85rem',
            fontWeight: 500,
            marginBottom: '20px',
            border: '1px solid rgba(244, 63, 94, 0.2)'
          }}>
            <AlertCircle size={16} style={{ flexShrink: 0 }} />
            <span>{error}</span>
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Email Address</label>
            <input 
              type="email" 
              className="form-control"
              placeholder="name@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <div className="form-group" style={{ marginBottom: '24px' }}>
            <label className="form-label">Password</label>
            <input 
              type="password" 
              className="form-control"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <button 
            type="submit" 
            className="btn btn-primary"
            style={{ width: '100%', padding: '12px', fontSize: '1rem' }}
            disabled={loading}
          >
            {loading ? 'Logging in...' : 'Sign In'}
          </button>
        </form>

        {/* Footer Link */}
        <div style={{
          marginTop: '28px',
          textAlign: 'center',
          fontSize: '0.88rem',
          color: 'var(--text-secondary)'
        }}>
          Don't have an account?{' '}
          <Link to="/register" style={{ color: 'var(--accent)', fontWeight: 500 }}>
            Sign Up
          </Link>
        </div>
      </div>
    </div>
  );
};

export default Login;
