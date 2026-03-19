// API service for connecting to FastAPI backend
const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export const api = {
  // Send a query to the pipeline
  query: async (query, sessionId, useCache = true) => {
    const response = await fetch(`${API_BASE}/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query,
        session_id: sessionId,
        use_cache: useCache,
      }),
    });
    if (!response.ok) throw new Error(`API error: ${response.status}`);
    return response.json();
  },

  // Health check
  health: async () => {
    const response = await fetch(`${API_BASE}/health`);
    return response.json();
  },

  // Get query history
  history: async (sessionId, limit = 20) => {
    const params = new URLSearchParams({ limit });
    if (sessionId) params.append('session_id', sessionId);
    const response = await fetch(`${API_BASE}/query/history?${params}`);
    return response.json();
  },

  // Get metrics
  metrics: async () => {
    const response = await fetch(`${API_BASE}/health/metrics`);
    return response.json();
  },

  // Ingest documents
  ingest: async (texts, sourceName = 'ui_upload') => {
    const response = await fetch(`${API_BASE}/query/ingest`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ texts, source_name: sourceName }),
    });
    return response.json();
  },
};

// Route color mapping
export const ROUTE_CONFIG = {
  RAG_AGENT: {
    label: 'RAG',
    color: '#6366f1',
    glow: 'rgba(99,102,241,0.3)',
    desc: 'Knowledge Base',
    icon: '📚',
  },
  WEB_SEARCH: {
    label: 'Web',
    color: '#06b6d4',
    glow: 'rgba(6,182,212,0.3)',
    desc: 'Live Search',
    icon: '🌐',
  },
  PYTHON_AGENT: {
    label: 'Python',
    color: '#10b981',
    glow: 'rgba(16,185,129,0.3)',
    desc: 'Code Execution',
    icon: '🐍',
  },
  REASONING_AGENT: {
    label: 'Reasoning',
    color: '#f59e0b',
    glow: 'rgba(245,158,11,0.3)',
    desc: 'Chain of Thought',
    icon: '🧠',
  },
  DIRECT_ANSWER: {
    label: 'Direct',
    color: '#ec4899',
    glow: 'rgba(236,72,153,0.3)',
    desc: 'Direct Answer',
    icon: '⚡',
  },
  CACHE: {
    label: 'Cache',
    color: '#8b5cf6',
    glow: 'rgba(139,92,246,0.3)',
    desc: 'Cached Response',
    icon: '⚡',
  },
};

export const getRouteConfig = (route) =>
  ROUTE_CONFIG[route] || {
    label: route || 'Unknown',
    color: '#6366f1',
    glow: 'rgba(99,102,241,0.3)',
    desc: 'Processing',
    icon: '🤖',
  };

// Generate session ID
export const generateSessionId = () =>
  `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

// Format timestamp
export const formatTime = (date) => {
  return new Date(date).toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
  });
};

// Score color
export const getScoreColor = (score) => {
  if (score >= 8) return '#10b981';
  if (score >= 6) return '#f59e0b';
  return '#ef4444';
};