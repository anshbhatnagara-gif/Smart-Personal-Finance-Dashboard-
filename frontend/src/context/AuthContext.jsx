import React, { createContext, useState, useEffect, useContext } from 'react';
import { authAPI } from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    const storedUser = localStorage.getItem('user');
    return storedUser ? JSON.parse(storedUser) : null;
  });
  const [token, setToken] = useState(() => localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  // Validate session on load
  useEffect(() => {
    const verifySession = async () => {
      if (token) {
        try {
          const res = await authAPI.getProfile();
          if (res.data && res.data.success) {
            const profileData = res.data.data;
            setUser(profileData);
            localStorage.setItem('user', JSON.stringify(profileData));
          }
        } catch (error) {
          console.error('Session verification failed:', error.message);
          // Token is invalid/expired (Axios response interceptor handles clearing local storage)
          setUser(null);
          setToken(null);
        }
      }
      setLoading(false);
    };

    verifySession();
  }, [token]);

  const login = async (email, password) => {
    try {
      const res = await authAPI.login({ email, password });
      if (res.data && res.data.success) {
        const { token: receivedToken, ...userData } = res.data.data;
        
        localStorage.setItem('token', receivedToken);
        localStorage.setItem('user', JSON.stringify(userData));
        
        setToken(receivedToken);
        setUser(userData);
        return { success: true };
      }
    } catch (error) {
      throw error;
    }
  };

  const register = async (name, email, password) => {
    try {
      const res = await authAPI.register({ name, email, password });
      if (res.data && res.data.success) {
        const { token: receivedToken, ...userData } = res.data.data;

        localStorage.setItem('token', receivedToken);
        localStorage.setItem('user', JSON.stringify(userData));

        setToken(receivedToken);
        setUser(userData);
        return { success: true };
      }
    } catch (error) {
      throw error;
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setToken(null);
    setUser(null);
  };

  const isAuthenticated = !!token;

  return (
    <AuthContext.Provider value={{ user, token, loading, login, register, logout, isAuthenticated }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
