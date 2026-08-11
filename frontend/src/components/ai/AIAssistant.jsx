import React, { useState, useEffect, useRef } from 'react';
import { aiAPI } from '../../services/api';
import AIMessage from './AIMessage';
import AIInput from './AIInput';
import AITyping from './AITyping';
import AIEmptyState from './AIEmptyState';
import AIConfirmation from './AIConfirmation';
import { Bot, X, RefreshCw, AlertCircle, Sparkles, MessageSquare } from 'lucide-react';

const AIAssistant = ({ isOpen, onClose }) => {
  const [activeTab, setActiveTab] = useState('chat'); // 'chat' or 'insights'
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [isUnconfigured, setIsUnconfigured] = useState(false);
  const [pendingConfirmation, setPendingConfirmation] = useState(null);

  // Insights local state
  const [insights, setInsights] = useState([]);
  const [insightsSummary, setInsightsSummary] = useState('');
  const [insightsLoading, setInsightsLoading] = useState(false);
  const [insightsError, setInsightsError] = useState('');

  const messagesEndRef = useRef(null);
  const drawerRef = useRef(null);

  // Focus input or scroll on open
  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
      document.addEventListener('keydown', handleKeyDown);
    } else {
      document.removeEventListener('keydown', handleKeyDown);
    }

    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen]);

  // Fetch insights automatically when switching to insights tab
  useEffect(() => {
    if (isOpen && activeTab === 'insights' && insights.length === 0 && !insightsLoading) {
      fetchInsights();
    }
  }, [activeTab, isOpen]);

  // Scroll message list to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading, pendingConfirmation]);

  const handleKeyDown = (e) => {
    if (e.key === 'Escape') {
      onClose();
    }
  };

  const fetchInsights = async () => {
    setInsightsLoading(true);
    setInsightsError('');
    try {
      const res = await aiAPI.getInsights();
      if (res.data.success) {
        setInsights(res.data.insights || []);
        setInsightsSummary(res.data.summary || '');
      }
    } catch (err) {
      console.error('Failed to fetch insights:', err);
      const status = err.response?.status;
      if (status === 503) {
        setInsightsError('AI Insights provider is not configured. Please set the environment variables.');
      } else {
        setInsightsError('Unable to load financial insights right now. Please try again.');
      }
    } finally {
      setInsightsLoading(false);
    }
  };

  const handleSendMessage = async (text) => {
    if (!text || loading) return;

    setError('');
    setIsUnconfigured(false);
    setPendingConfirmation(null);

    // 1. Add user message
    const userMessage = { role: 'user', content: text };
    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);

    try {
      // 2. Format history for backend
      const sanitizedHistory = messages.map((m) => ({
        role: m.role,
        content: m.content,
      }));

      // 3. Request completion
      const res = await aiAPI.chat(text, sanitizedHistory);

      if (res.data.success) {
        const payload = res.data;

        // Check if confirmation request is returned
        if (payload.type === 'confirmation' && payload.confirmation) {
          setPendingConfirmation(payload.confirmation);
        }

        // Add assistant message
        setMessages((prev) => [
          ...prev,
          { role: 'assistant', content: payload.message || 'Action pending confirmation...' },
        ]);
      }
    } catch (err) {
      console.error('AI chat request failed:', err);
      const status = err.response?.status;
      const serverMsg = err.response?.data?.error?.message || err.response?.data?.message;

      if (status === 503) {
        setIsUnconfigured(true);
      } else if (status === 400) {
        setError(serverMsg || 'Please check your input message and try again.');
      } else {
        setError(serverMsg || 'Unable to reach the AI assistant right now. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSelectPrompt = (prompt) => {
    handleSendMessage(prompt);
  };

  const handleCancelConfirmation = () => {
    setPendingConfirmation(null);
    setMessages((prev) => [
      ...prev,
      { role: 'assistant', content: 'Action cancelled.' },
    ]);
  };

  const handleConfirmSuccess = (result) => {
    setPendingConfirmation(null);
    setMessages((prev) => [
      ...prev,
      { role: 'assistant', content: result.message || 'Action completed successfully.' },
    ]);
    if (typeof fetchInsights === 'function') {
      fetchInsights();
    }
  };

  const handleResetAfterError = () => {
    setError('');
    setIsUnconfigured(false);
  };

  const getSeverityStyle = (severity) => {
    switch (severity) {
      case 'critical':
        return {
          background: 'rgba(239, 68, 68, 0.1)',
          color: 'var(--danger)',
          borderColor: 'rgba(239, 68, 68, 0.2)'
        };
      case 'warning':
        return {
          background: 'rgba(245, 158, 11, 0.1)',
          color: 'var(--warning)',
          borderColor: 'rgba(245, 158, 11, 0.2)'
        };
      case 'info':
      default:
        return {
          background: 'rgba(59, 130, 246, 0.1)',
          color: 'var(--accent)',
          borderColor: 'rgba(59, 130, 246, 0.2)'
        };
    }
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Click-to-close Backdrop */}
      <div 
        className="ai-backdrop"
        onClick={onClose}
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: '100vw',
          height: '100vh',
          background: 'rgba(0, 0, 0, 0.4)',
          backdropFilter: 'blur(3px)',
          zIndex: 999
        }}
      />

      {/* Main Drawer Overlay */}
      <div
        ref={drawerRef}
        className="ai-drawer animate-slide-in"
        role="dialog"
        aria-modal="true"
        aria-label="AI Finance Assistant"
        style={{
          position: 'fixed',
          top: 0,
          right: 0,
          height: '100vh',
          zIndex: 1000,
          background: 'var(--panel-bg)',
          borderLeft: '1px solid var(--border)',
          display: 'flex',
          flexDirection: 'column',
          boxShadow: 'var(--shadow-lg)'
        }}
      >
        {/* Header Section */}
        <div
          style={{
            padding: '16px 20px 8px 20px',
            background: 'var(--bg-primary)',
            borderBottom: '1px solid var(--border)'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div style={{
                width: '32px',
                height: '32px',
                borderRadius: '50%',
                background: 'rgba(59, 130, 246, 0.1)',
                color: 'var(--accent)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <Bot size={18} />
              </div>
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <span style={{ fontWeight: 600, fontSize: '0.92rem', color: 'var(--text-primary)', fontFamily: 'var(--font-display)' }}>
                  AI Assistant
                </span>
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <div style={{
                    width: '6px',
                    height: '6px',
                    borderRadius: '50%',
                    background: isUnconfigured ? 'var(--text-muted)' : 'var(--success)'
                  }} />
                  <span style={{ fontSize: '0.68rem', color: 'var(--text-secondary)' }}>
                    {isUnconfigured ? 'Unconfigured' : 'Active'}
                  </span>
                </div>
              </div>
            </div>
            <button
              onClick={onClose}
              aria-label="Close assistant"
              style={{
                background: 'none',
                border: 'none',
                color: 'var(--text-muted)',
                cursor: 'pointer',
                padding: '6px',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                transition: 'background 0.2s ease'
              }}
              className="btn-icon-hover"
            >
              <X size={18} />
            </button>
          </div>

          {/* Navigation Tabs */}
          <div style={{ display: 'flex', gap: '4px', borderBottom: '1px solid var(--border)', marginTop: '8px' }}>
            <button
              onClick={() => setActiveTab('chat')}
              style={{
                flex: 1,
                padding: '8px 12px',
                background: 'none',
                border: 'none',
                borderBottom: activeTab === 'chat' ? '2px solid var(--accent)' : '2px solid transparent',
                color: activeTab === 'chat' ? 'var(--accent)' : 'var(--text-secondary)',
                fontWeight: activeTab === 'chat' ? '600' : '500',
                fontSize: '0.82rem',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '6px'
              }}
            >
              <MessageSquare size={14} />
              <span>Financial Chat</span>
            </button>
            <button
              onClick={() => setActiveTab('insights')}
              style={{
                flex: 1,
                padding: '8px 12px',
                background: 'none',
                border: 'none',
                borderBottom: activeTab === 'insights' ? '2px solid var(--accent)' : '2px solid transparent',
                color: activeTab === 'insights' ? 'var(--accent)' : 'var(--text-secondary)',
                fontWeight: activeTab === 'insights' ? '600' : '500',
                fontSize: '0.82rem',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '6px'
              }}
            >
              <Sparkles size={14} />
              <span>Smart Insights</span>
            </button>
          </div>
        </div>

        {/* Conversation Body Panel */}
        <div
          style={{
            flex: 1,
            overflowY: 'auto',
            padding: '20px',
            display: 'flex',
            flexDirection: 'column'
          }}
        >
          {activeTab === 'chat' ? (
            /* ==========================================
               CHAT VIEW
               ========================================== */
            isUnconfigured ? (
              /* Graceful 503 State */
              <div style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                textAlign: 'center',
                margin: 'auto 0',
                padding: '16px'
              }}>
                <AlertCircle size={36} style={{ color: 'var(--text-muted)', marginBottom: '16px' }} />
                <h4 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '8px' }}>
                  AI Assistant isn't connected yet
                </h4>
                <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginBottom: '24px', lineHeight: '1.45', maxWidth: '280px' }}>
                  Your finance dashboard is AI-ready, but an AI provider has not been configured in the environment settings yet.
                </p>
                <button onClick={handleResetAfterError} className="btn btn-primary" style={{ gap: '8px' }}>
                  <RefreshCw size={14} />
                  <span>Try Again</span>
                </button>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '16px', fontStyle: 'italic' }}>
                  Your dashboard and financial data are still working normally.
                </span>
              </div>
            ) : error ? (
              /* Custom Error Display */
              <div style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                textAlign: 'center',
                margin: 'auto 0',
                padding: '16px'
              }}>
                <AlertCircle size={36} style={{ color: 'var(--danger)', marginBottom: '16px' }} />
                <h4 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '8px' }}>
                  Operational Issue Detected
                </h4>
                <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginBottom: '24px', lineHeight: '1.45' }}>
                  {error}
                </p>
                <button onClick={handleResetAfterError} className="btn btn-secondary">
                  Clear Error
                </button>
              </div>
            ) : messages.length === 0 ? (
              /* Suggestions list empty state */
              <AIEmptyState onSelectPrompt={handleSelectPrompt} />
            ) : (
              /* Dialogue List */
              <>
                {messages.map((msg, index) => (
                  <AIMessage key={index} role={msg.role} content={msg.content} />
                ))}
                
                {loading && <AITyping />}

                {pendingConfirmation && (
                  <AIConfirmation
                    confirmation={pendingConfirmation}
                    onConfirmSuccess={handleConfirmSuccess}
                    onCancel={handleCancelConfirmation}
                  />
                )}
                
                <div ref={messagesEndRef} />
              </>
            )
          ) : (
            /* ==========================================
               INSIGHTS VIEW
               ========================================== */
            insightsLoading ? (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', margin: 'auto 0', gap: '12px' }}>
                <RefreshCw size={24} className="animate-spin" style={{ color: 'var(--accent)' }} />
                <span style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>Compiling financial reports...</span>
              </div>
            ) : insightsError ? (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center', margin: 'auto 0', padding: '16px' }}>
                <AlertCircle size={36} style={{ color: 'var(--danger)', marginBottom: '16px' }} />
                <h4 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '8px' }}>
                  Could Not Load Insights
                </h4>
                <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginBottom: '24px', lineHeight: '1.45' }}>
                  {insightsError}
                </p>
                <button onClick={fetchInsights} className="btn btn-primary" style={{ gap: '6px' }}>
                  <RefreshCw size={14} />
                  <span>Retry Scan</span>
                </button>
              </div>
            ) : insights.length === 0 && !insightsSummary ? (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center', margin: 'auto 0', padding: '16px' }}>
                <Sparkles size={36} style={{ color: 'var(--text-muted)', marginBottom: '16px' }} />
                <h4 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '8px' }}>
                  No Insights Available
                </h4>
                <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginBottom: '24px', lineHeight: '1.45', maxWidth: '280px' }}>
                  Add incomes and expenses to see AI-generated recommendations and budget progress.
                </p>
                <button onClick={fetchInsights} className="btn btn-primary" style={{ gap: '6px' }}>
                  <RefreshCw size={14} />
                  <span>Generate Report</span>
                </button>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                {/* Header Summary Box */}
                {insightsSummary && (
                  <div style={{
                    padding: '16px',
                    borderRadius: 'var(--radius-md)',
                    background: 'var(--bg-primary)',
                    borderLeft: '4px solid var(--accent)',
                    fontSize: '0.84rem',
                    lineHeight: '1.5',
                    color: 'var(--text-primary)',
                    fontStyle: 'italic'
                  }}>
                    "{insightsSummary}"
                  </div>
                )}

                {/* Refresh Header */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '4px' }}>
                  <span style={{ fontSize: '0.75rem', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)' }}>
                    Personalized Recommendations
                  </span>
                  <button 
                    onClick={fetchInsights} 
                    style={{
                      background: 'none',
                      border: 'none',
                      color: 'var(--accent)',
                      fontSize: '0.75rem',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px',
                      padding: '4px 8px',
                      borderRadius: 'var(--radius-sm)'
                    }}
                    className="btn-icon-hover"
                  >
                    <RefreshCw size={12} />
                    <span>Refresh</span>
                  </button>
                </div>

                {/* Recommendations List */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  {insights.map((item, index) => {
                    const badgeStyle = getSeverityStyle(item.severity);
                    return (
                      <div 
                        key={index}
                        style={{
                          padding: '14px',
                          borderRadius: 'var(--radius-md)',
                          background: 'var(--bg-primary)',
                          border: '1px solid var(--border)',
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '6px',
                          transition: 'var(--transition)'
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                          <span style={{
                            fontSize: '0.62rem',
                            fontWeight: '700',
                            textTransform: 'uppercase',
                            padding: '2px 6px',
                            borderRadius: '4px',
                            border: '1px solid',
                            ...badgeStyle
                          }}>
                            {item.severity}
                          </span>
                          <span style={{
                            fontSize: '0.7rem',
                            fontWeight: '600',
                            textTransform: 'uppercase',
                            color: 'var(--text-muted)'
                          }}>
                            {item.type}
                          </span>
                        </div>
                        <h5 style={{ fontSize: '0.85rem', fontWeight: '600', color: 'var(--text-primary)', margin: '2px 0 0 0' }}>
                          {item.title}
                        </h5>
                        <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', lineHeight: '1.4', margin: 0 }}>
                          {item.message}
                        </p>
                      </div>
                    );
                  })}
                </div>
              </div>
            )
          )}
        </div>

        {/* Chat Input Footer (Only rendered in Chat Tab) */}
        {activeTab === 'chat' && (
          <div
            style={{
              padding: '16px 20px',
              borderTop: '1px solid var(--border)',
              background: 'var(--bg-primary)'
            }}
          >
            <AIInput onSend={handleSendMessage} disabled={loading || isUnconfigured} />
          </div>
        )}
      </div>
    </>
  );
};

export default AIAssistant;
