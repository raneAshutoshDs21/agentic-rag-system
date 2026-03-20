import React, { useState, useEffect, useRef, useCallback } from 'react';
import './index.css';
import Sidebar from './components/Sidebar';
import Message from './components/Message';
import ChatInput from './components/ChatInput';
import RightPanel from './components/RightPanel';
import LoadingMessage from './components/LoadingMessage';
import { api, generateSessionId } from './utils/api';

// Background orbs
const BgOrbs = () => (
  <div style={{ position: 'fixed', inset: 0, pointerEvents: 'none', overflow: 'hidden', zIndex: 0 }}>
    <div style={{
      position: 'absolute', top: '-20%', left: '-10%',
      width: '600px', height: '600px', borderRadius: '50%',
      background: 'radial-gradient(circle, rgba(99,102,241,0.06) 0%, transparent 70%)',
      filter: 'blur(40px)',
    }} />
    <div style={{
      position: 'absolute', bottom: '-20%', right: '-10%',
      width: '500px', height: '500px', borderRadius: '50%',
      background: 'radial-gradient(circle, rgba(6,182,212,0.05) 0%, transparent 70%)',
      filter: 'blur(40px)',
    }} />
    <div style={{
      position: 'absolute', top: '40%', right: '20%',
      width: '300px', height: '300px', borderRadius: '50%',
      background: 'radial-gradient(circle, rgba(139,92,246,0.04) 0%, transparent 70%)',
      filter: 'blur(60px)',
    }} />
  </div>
);

// Welcome screen
const WelcomeScreen = () => (
  <div style={{
    flex: 1, display: 'flex', flexDirection: 'column',
    alignItems: 'center', justifyContent: 'center',
    padding: '40px', textAlign: 'center',
  }}>
    <div style={{
      width: '72px', height: '72px', borderRadius: '20px',
      background: 'linear-gradient(135deg, rgba(99,102,241,0.2), rgba(6,182,212,0.2))',
      border: '1px solid rgba(99,102,241,0.3)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      fontSize: '32px', marginBottom: '24px',
      boxShadow: '0 0 40px rgba(99,102,241,0.2)',
      animation: 'pulse-glow 3s ease infinite',
    }}>
      🤖
    </div>

    <h1 style={{
      fontFamily: 'var(--font-display)', fontSize: '28px',
      fontWeight: '700', marginBottom: '12px', letterSpacing: '-0.5px',
      background: 'linear-gradient(135deg, #6366f1, #06b6d4)',
      WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
    }}>
      Agentic RAG System
    </h1>

    <p style={{
      color: 'var(--text-secondary)', fontSize: '14px',
      lineHeight: '1.7', maxWidth: '420px', marginBottom: '40px',
    }}>
      An intelligent multi-agent system powered by LLaMA 3.3 70B.
      Ask anything — I'll route your query to the best agent automatically.
    </p>

    <div style={{
      display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)',
      gap: '10px', maxWidth: '480px', width: '100%',
    }}>
      {[
        { icon: '📚', label: 'RAG Agent', desc: 'Query knowledge base with FAISS retrieval', color: '#6366f1' },
        { icon: '🌐', label: 'Web Search', desc: 'Fetch live information from the internet', color: '#06b6d4' },
        { icon: '🐍', label: 'Python Agent', desc: 'Execute code for computation tasks', color: '#10b981' },
        { icon: '🧠', label: 'Reasoning', desc: 'Multi-step chain of thought analysis', color: '#f59e0b' },
      ].map(cap => (
        <div key={cap.label} style={{
          padding: '14px', borderRadius: 'var(--radius-md)',
          background: 'rgba(255,255,255,0.03)',
          border: '1px solid rgba(255,255,255,0.06)',
          textAlign: 'left', transition: 'all 0.2s',
          cursor: 'default',
        }}
          onMouseEnter={e => {
            e.currentTarget.style.background = `${cap.color}10`;
            e.currentTarget.style.borderColor = `${cap.color}30`;
          }}
          onMouseLeave={e => {
            e.currentTarget.style.background = 'rgba(255,255,255,0.03)';
            e.currentTarget.style.borderColor = 'rgba(255,255,255,0.06)';
          }}
        >
          <div style={{ fontSize: '20px', marginBottom: '6px' }}>{cap.icon}</div>
          <div style={{ fontSize: '12px', fontWeight: '600', color: cap.color, marginBottom: '4px' }}>
            {cap.label}
          </div>
          <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', lineHeight: '1.4' }}>
            {cap.desc}
          </div>
        </div>
      ))}
    </div>
  </div>
);

// ── Storage helpers ───────────────────────────────────────
const STORAGE_KEYS = {
  SESSIONS   : 'rag_sessions',
  MESSAGES   : 'rag_messages',
  CURRENT    : 'rag_current_session',
};

const loadFromStorage = (key, fallback) => {
  try {
    const val = localStorage.getItem(key);
    return val ? JSON.parse(val) : fallback;
  } catch {
    return fallback;
  }
};

const saveToStorage = (key, value) => {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch (e) {
    console.warn('Storage save failed:', e);
  }
};

const App = () => {
  // ── Load from localStorage on mount ──────────────────────
  const [sessions, setSessions] = useState(() =>
    loadFromStorage(STORAGE_KEYS.SESSIONS, [])
  );
  const [messages, setMessages] = useState(() =>
    loadFromStorage(STORAGE_KEYS.MESSAGES, {})
  );
  const [currentSessionId, setCurrentSessionId] = useState(() =>
    loadFromStorage(STORAGE_KEYS.CURRENT, null)
  );

  const [isLoading, setIsLoading]   = useState(false);
  const [useCache, setUseCache]     = useState(true);
  const [metrics, setMetrics]       = useState(null);
  const messagesEndRef               = useRef(null);

  // ── Persist to localStorage on every change ───────────────
  useEffect(() => {
    saveToStorage(STORAGE_KEYS.SESSIONS, sessions);
  }, [sessions]);

  useEffect(() => {
    saveToStorage(STORAGE_KEYS.MESSAGES, messages);
  }, [messages]);

  useEffect(() => {
    saveToStorage(STORAGE_KEYS.CURRENT, currentSessionId);
  }, [currentSessionId]);

  // ── Auto scroll ───────────────────────────────────────────
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, currentSessionId, isLoading]);

  // ── Load metrics ──────────────────────────────────────────
  useEffect(() => {
    api.metrics().then(setMetrics).catch(() => {});
  }, []);

  const currentMessages = currentSessionId
    ? (messages[currentSessionId] || [])
    : [];

  // ── Create new session ────────────────────────────────────
  const createSession = useCallback(() => {
    const id = generateSessionId();
    const session = {
      id,
      title        : 'New Conversation',
      messageCount : 0,
      createdAt    : new Date().toISOString(),
    };
    setSessions(prev => [session, ...prev]);
    setMessages(prev => ({ ...prev, [id]: [] }));
    setCurrentSessionId(id);
    return id;
  }, []);

  // ── Send message ──────────────────────────────────────────
  const handleSend = useCallback(async (query) => {
    let sessionId = currentSessionId;
    if (!sessionId) sessionId = createSession();

    const userMsg = {
      id        : Date.now(),
      role      : 'user',
      content   : query,
      timestamp : new Date().toISOString(),
    };

    setMessages(prev => ({
      ...prev,
      [sessionId]: [...(prev[sessionId] || []), userMsg],
    }));

    setSessions(prev => prev.map(s => s.id === sessionId
      ? {
          ...s,
          title: s.messageCount === 0
            ? query.slice(0, 40) + (query.length > 40 ? '...' : '')
            : s.title,
          messageCount : s.messageCount + 1,
          updatedAt    : new Date().toISOString(),
        }
      : s
    ));

    setIsLoading(true);

    try {
      const result = await api.query(query, sessionId, useCache);

      const assistantMsg = {
        id          : Date.now() + 1,
        role        : 'assistant',
        content     : result.answer,
        route       : result.route,
        score       : result.score,
        feedback    : result.feedback,
        sources     : result.sources,
        fromCache   : result.from_cache,
        totalTimeMs : result.total_time_ms,
        timestamp   : new Date().toISOString(),
      };

      setMessages(prev => ({
        ...prev,
        [sessionId]: [...(prev[sessionId] || []), assistantMsg],
      }));

      setSessions(prev => prev.map(s =>
        s.id === sessionId
          ? { ...s, messageCount: s.messageCount + 1, updatedAt: new Date().toISOString() }
          : s
      ));

      api.metrics().then(setMetrics).catch(() => {});

    } catch (err) {
      const errorMsg = {
        id        : Date.now() + 1,
        role      : 'assistant',
        content   : `❌ Error: ${err.message}\n\nMake sure the backend is running at http://localhost:8000`,
        route     : null,
        score     : 0,
        timestamp : new Date().toISOString(),
      };
      setMessages(prev => ({
        ...prev,
        [sessionId]: [...(prev[sessionId] || []), errorMsg],
      }));
    } finally {
      setIsLoading(false);
    }
  }, [currentSessionId, createSession, useCache]);

  // ── Delete session ────────────────────────────────────────
  const handleDeleteSession = useCallback((id) => {
    setSessions(prev => prev.filter(s => s.id !== id));
    setMessages(prev => {
      const next = { ...prev };
      delete next[id];
      return next;
    });
    if (currentSessionId === id) {
      setCurrentSessionId(null);
    }
  }, [currentSessionId]);

  // ── Clear all history ─────────────────────────────────────
  const handleClearAll = useCallback(() => {
    if (window.confirm('Clear all conversation history?')) {
      setSessions([]);
      setMessages({});
      setCurrentSessionId(null);
      localStorage.removeItem(STORAGE_KEYS.SESSIONS);
      localStorage.removeItem(STORAGE_KEYS.MESSAGES);
      localStorage.removeItem(STORAGE_KEYS.CURRENT);
    }
  }, []);

  // ── Ingest documents ──────────────────────────────────────
  const handleIngest = useCallback(async (text) => {
    return api.ingest([text], 'ui_upload');
  }, []);

  return (
    <div style={{
      display: 'flex', height: '100vh', width: '100vw',
      overflow: 'hidden', position: 'relative',
      background: 'var(--bg-primary)',
    }}>
      <BgOrbs />

      <div style={{
        display: 'flex', width: '100%', height: '100%',
        position: 'relative', zIndex: 1,
      }}>

        {/* Sidebar */}
        <Sidebar
          sessions={sessions}
          currentSession={currentSessionId}
          onNewSession={createSession}
          onSelectSession={setCurrentSessionId}
          onDeleteSession={handleDeleteSession}
          onClearAll={handleClearAll}
          metrics={metrics}
        />

        {/* Main chat area */}
        <div style={{
          flex: 1, display: 'flex', flexDirection: 'column',
          overflow: 'hidden', minWidth: 0,
        }}>

          {/* Top bar */}
          <div style={{
            padding: '14px 24px',
            borderBottom: '1px solid rgba(255,255,255,0.06)',
            display: 'flex', alignItems: 'center', gap: '12px',
            background: 'rgba(5,5,8,0.6)', backdropFilter: 'blur(20px)',
            flexShrink: 0,
          }}>
            <div style={{
              width: '8px', height: '8px', borderRadius: '50%',
              background: '#10b981', boxShadow: '0 0 8px #10b981',
            }} />
            <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
              {currentSessionId
                ? sessions.find(s => s.id === currentSessionId)?.title || 'Conversation'
                : 'Agentic RAG System'}
            </span>
            <div style={{ marginLeft: 'auto', display: 'flex', gap: '16px' }}>
              {[
                { label: 'FAISS', color: '#6366f1' },
                { label: 'LLaMA 3.3', color: '#06b6d4' },
                { label: 'BGE Embed', color: '#10b981' },
              ].map(tag => (
                <div key={tag.label} style={{
                  fontSize: '10px', color: tag.color,
                  background: `${tag.color}12`,
                  padding: '2px 8px', borderRadius: '20px',
                  border: `1px solid ${tag.color}25`,
                  fontFamily: 'var(--font-mono)',
                }}>
                  {tag.label}
                </div>
              ))}
            </div>
          </div>

          {/* Messages */}
          <div style={{ flex: 1, overflowY: 'auto' }}>
            {currentMessages.length === 0 && !isLoading
              ? <WelcomeScreen />
              : (
                <>
                  {currentMessages.map((msg, i) => (
                    <Message key={msg.id} message={msg} index={i} />
                  ))}
                  {isLoading && <LoadingMessage />}
                  <div ref={messagesEndRef} />
                </>
              )
            }
          </div>

          {/* Input */}
          <ChatInput
            onSend={handleSend}
            isLoading={isLoading}
            useCache={useCache}
            onToggleCache={() => setUseCache(v => !v)}
          />
        </div>

        {/* Right Panel */}
        <RightPanel
          currentMessages={currentMessages}
          sessionMetrics={metrics}
          onIngest={handleIngest}
        />
      </div>

      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to   { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export default App;