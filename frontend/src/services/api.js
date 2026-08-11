import axios from 'axios';

// Axios instance using Vite proxy '/api' pointing to 'http://localhost:5000/api'
const API = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request Interceptor: Attach token if it exists in localStorage
API.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor: Handle global errors (specifically 401 Unauthorized)
API.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Clear token and user session on authorization failures
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      
      // Force page reload to trigger login redirect if we are not on auth pages
      if (!window.location.pathname.includes('/login') && !window.location.pathname.includes('/register')) {
        window.location.href = '/login?expired=true';
      }
    }
    return Promise.reject(error);
  }
);

// Helper to format Axios error messages consistently
export const getErrorMessage = (error) => {
  if (error.response && error.response.data && error.response.data.message) {
    return error.response.data.message;
  }
  return error.message || 'An unexpected error occurred';
};

// --- API Endpoint Functions ---

export const authAPI = {
  register: (userData) => API.post('/auth/register', userData),
  login: (credentials) => API.post('/auth/login', credentials),
  getProfile: () => API.get('/auth/profile'),
};

export const incomeAPI = {
  getIncomes: (params) => API.get('/income', { params }),
  createIncome: (data) => API.post('/income', data),
  updateIncome: (id, data) => API.put(`/income/${id}`, data),
  deleteIncome: (id) => API.delete(`/income/${id}`),
};

export const expenseAPI = {
  getExpenses: (params) => API.get('/expenses', { params }),
  createExpense: (data) => API.post('/expenses', data),
  updateExpense: (id, data) => API.put(`/expenses/${id}`, data),
  deleteExpense: (id) => API.delete(`/expenses/${id}`),
};

export const budgetAPI = {
  getBudget: (month) => API.get('/budgets', { params: { month } }),
  setBudget: (data) => API.post('/budgets', data),
  getBudgetProgress: (month) => API.get('/budgets/progress', { params: { month } }),
};

export const transactionAPI = {
  getTransactions: (params) => API.get('/transactions', { params }),
  getSummary: (params) => API.get('/transactions/summary', { params }),
  getTrends: (params) => API.get('/transactions/trends', { params }),
};

export const aiAPI = {
  chat: (message, history) => API.post('/ai/chat', { message, history }),
  getInsights: () => API.get('/ai/insights'),
  confirm: (actionId) => API.post('/ai/confirm', { actionId }),
  cancel: (actionId) => API.post('/ai/cancel', { actionId }),
};

export default API;
