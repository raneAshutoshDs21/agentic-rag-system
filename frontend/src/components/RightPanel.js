import React, { useState } from 'react';
import { Brain, BarChart2, Upload, X, CheckCircle, AlertCircle } from 'lucide-react';
import { getScoreColor } from '../utils/api';

const Tab = ({ label, active, onClick, icon }) => (
  <button
    onClick={onClick}
    style={{
      flex: 1, padding: '8px 4px',
      background: active ? 'rgba(99,102,241,0.12)' : 'transparent',
      border: 'none',
      borderBottom: active ? '2px solid #6366f1' : '2px solid transparent',
      color: active ? '#6366f1' : 'var(--text-tertiary)',
      cursor: 'pointer', fontSize: '11px', fontFamily: 'var(--font-body)',
      fontWeight: active ? '600' : '400',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      gap: '5px', transition: 'all 0.2s', letterSpacing: '0.3px',
    }}
  >
    {icon}{label}
  </button>
);

const MetricCard = ({ label, value, color, suffix = '' }) => (
  <div style={{
    padding: '12px', borderRadius: 'var(--radius-md)',
    background: 'rgba(255,255,255,0.03)',
    border: '1px solid rgba(255,255,255,0.06)',
  }}>
    <div style={{ fontSize: '10px', color: 'var(--text-tertiary)', marginBottom: '6px', letterSpacing: '0.5px' }}>
      {label}
    </div>
    <div style={{
      fontSize: '22px', fontWeight: '700',
      fontFamily: 'var(--font-display)',
      color: color || 'var(--text-primary)',
    }}>
      {value}<span style={{ fontSize: '12px', fontWeight: '400', color: 'var(--text-tertiary)' }}>{suffix}</span>
    </div>
  </div>
);

const RightPanel = ({ currentMessages, sessionMetrics, onIngest }) => {
  const [activeTab, setActiveTab] = useState('metrics');
  const [uploadText, setUploadText] = useState('');
  const [uploadStatus, setUploadStatus] = useState(null);
  const [isUploading, setIsUploading] = useState(false);

  // Calculate session metrics from messages
  const assistantMessages = currentMessages.filter(m => m.role === 'assistant');
  const avgScore = assistantMessages.length > 0
    ? assistantMessages.reduce((acc, m) => acc + (m.score || 0), 0) / assistantMessages.length
    : 0;
  const cacheHits = assistantMessages.filter(m => m.fromCache).length;
  const avgLatency = assistantMessages.length > 0
    ? assistantMessages.filter(m => !m.fromCache).reduce((acc, m) => acc + (m.totalTimeMs || 0), 0) /
      Math.max(assistantMessages.filter(m => !m.fromCache).length, 1)
    : 0;

  // Route distribution
  const routeCounts = assistantMessages.reduce((acc, m) => {
    const route = m.fromCache ? 'CACHE' : (m.route || 'UNKNOWN');
    acc[route] = (acc[route] || 0) + 1;
    return acc;
  }, {});

  const routeColors = {
    RAG_AGENT: '#6366f1', WEB_SEARCH: '#06b6d4', PYTHON_AGENT: '#10b981',
    REASONING_AGENT: '#f59e0b', DIRECT_ANSWER: '#ec4899', CACHE: '#8b5cf6',
  };

  // Memory items from messages
  const memoryItems = assistantMessages
    .filter(m => m.score >= 7)
    .slice(-5)
    .map(m => ({
      query: currentMessages.find(cm => cm.role === 'user' &&
        currentMessages.indexOf(cm) < currentMessages.indexOf(m))?.content || '',
      score: m.score,
      route: m.route,
    }));

  const handleUpload = async () => {
    if (!uploadText.trim()) return;
    setIsUploading(true);
    setUploadStatus(null);
    try {
      const result = await onIngest(uploadText.trim());
      setUploadStatus({ success: true, message: `✅ Ingested ${result.chunks_created} chunks` });
      setUploadText('');
    } catch (e) {
      setUploadStatus({ success: false, message: `❌ Failed: ${e.message}` });
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div style={{
      width: '320px', height: '100%', flexShrink: 0,
      display: 'flex', flexDirection: 'column',
      background: 'rgba(255,255,255,0.015)',
      borderLeft: '1px solid rgba(255,255,255,0.06)',
    }}>
      {/* Tabs */}
      <div style={{
        display: 'flex',
        borderBottom: '1px solid rgba(255,255,255,0.06)',
        padding: '0 8px',
      }}>
        <Tab label="Metrics" active={activeTab === 'metrics'} onClick={() => setActiveTab('metrics')} icon={<BarChart2 size={11} />} />
        <Tab label="Memory" active={activeTab === 'memory'} onClick={() => setActiveTab('memory')} icon={<Brain size={11} />} />
        <Tab label="Ingest" active={activeTab === 'ingest'} onClick={() => setActiveTab('ingest')} icon={<Upload size={11} />} />
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: '16px' }}>

        {/* METRICS TAB */}
        {activeTab === 'metrics' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', letterSpacing: '1px', fontWeight: '600' }}>
              SESSION METRICS
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
              <MetricCard
                label="AVG SCORE"
                value={avgScore > 0 ? avgScore.toFixed(1) : '—'}
                color={avgScore > 0 ? getScoreColor(avgScore) : 'var(--text-tertiary)'}
                suffix="/10"
              />
              <MetricCard
                label="MESSAGES"
                value={assistantMessages.length}
                color="#6366f1"
              />
              <MetricCard
                label="CACHE HITS"
                value={cacheHits}
                color="#8b5cf6"
              />
              <MetricCard
                label="AVG LATENCY"
                value={avgLatency > 0 ? Math.round(avgLatency) : '—'}
                color="#06b6d4"
                suffix="ms"
              />
            </div>

            {/* Route distribution */}
            {Object.keys(routeCounts).length > 0 && (
              <div style={{
                padding: '12px',
                background: 'rgba(255,255,255,0.03)',
                border: '1px solid rgba(255,255,255,0.06)',
                borderRadius: 'var(--radius-md)',
              }}>
                <div style={{ fontSize: '10px', color: 'var(--text-tertiary)', marginBottom: '10px', letterSpacing: '0.5px' }}>
                  ROUTE DISTRIBUTION
                </div>
                {Object.entries(routeCounts).map(([route, count]) => {
                  const pct = Math.round((count / assistantMessages.length) * 100);
                  const color = routeColors[route] || '#6366f1';
                  return (
                    <div key={route} style={{ marginBottom: '8px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '3px' }}>
                        <span style={{ fontSize: '10px', color: 'var(--text-secondary)' }}>
                          {route.replace('_', ' ')}
                        </span>
                        <span style={{ fontSize: '10px', color, fontFamily: 'var(--font-mono)' }}>
                          {count} ({pct}%)
                        </span>
                      </div>
                      <div style={{ height: '3px', background: 'rgba(255,255,255,0.06)', borderRadius: '2px' }}>
                        <div style={{
                          height: '100%', width: `${pct}%`,
                          background: color, borderRadius: '2px',
                          transition: 'width 0.6s ease',
                        }} />
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            {/* Score history */}
            {assistantMessages.length > 0 && (
              <div style={{
                padding: '12px',
                background: 'rgba(255,255,255,0.03)',
                border: '1px solid rgba(255,255,255,0.06)',
                borderRadius: 'var(--radius-md)',
              }}>
                <div style={{ fontSize: '10px', color: 'var(--text-tertiary)', marginBottom: '10px', letterSpacing: '0.5px' }}>
                  SCORE HISTORY
                </div>
                <div style={{ display: 'flex', alignItems: 'flex-end', gap: '4px', height: '50px' }}>
                  {assistantMessages.slice(-10).map((m, i) => {
                    const h = ((m.score || 0) / 10) * 50;
                    const color = getScoreColor(m.score || 0);
                    return (
                      <div key={i} title={`${m.score?.toFixed(1)}/10`} style={{
                        flex: 1, height: `${h}px`,
                        background: `${color}60`,
                        border: `1px solid ${color}`,
                        borderRadius: '2px',
                        transition: 'height 0.4s ease',
                        minHeight: '3px',
                      }} />
                    );
                  })}
                </div>
              </div>
            )}

            {assistantMessages.length === 0 && (
              <div style={{
                textAlign: 'center', padding: '40px 20px',
                color: 'var(--text-tertiary)', fontSize: '12px',
              }}>
                <BarChart2 size={32} style={{ opacity: 0.2, marginBottom: '8px' }} />
                <div>Start chatting to see metrics</div>
              </div>
            )}
          </div>
        )}

        {/* MEMORY TAB */}
        {activeTab === 'memory' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', letterSpacing: '1px', fontWeight: '600' }}>
              LONG TERM MEMORY
            </div>
            <div style={{
              padding: '10px 12px',
              background: 'rgba(16,185,129,0.06)',
              border: '1px solid rgba(16,185,129,0.15)',
              borderRadius: 'var(--radius-md)',
              fontSize: '11px', color: '#10b981',
            }}>
              💾 High-quality responses (score ≥ 7) are automatically saved to long-term memory
            </div>

            {memoryItems.length === 0 ? (
              <div style={{
                textAlign: 'center', padding: '40px 20px',
                color: 'var(--text-tertiary)', fontSize: '12px',
              }}>
                <Brain size={32} style={{ opacity: 0.2, marginBottom: '8px' }} />
                <div>No memories yet</div>
                <div style={{ marginTop: '4px', fontSize: '11px' }}>
                  Responses scoring ≥ 7/10 will appear here
                </div>
              </div>
            ) : (
              <>
                <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', letterSpacing: '1px', fontWeight: '600', marginTop: '8px' }}>
                  SAVED MEMORIES ({memoryItems.length})
                </div>
                {memoryItems.map((item, i) => (
                  <div key={i} style={{
                    padding: '10px 12px',
                    background: 'rgba(255,255,255,0.03)',
                    border: '1px solid rgba(255,255,255,0.06)',
                    borderRadius: 'var(--radius-md)',
                    animation: 'fadeInUp 0.3s ease',
                  }}>
                    <div style={{
                      fontSize: '12px', color: 'var(--text-secondary)',
                      marginBottom: '6px', lineHeight: '1.4',
                    }}>
                      {item.query?.slice(0, 80)}{item.query?.length > 80 ? '...' : ''}
                    </div>
                    <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                      <div style={{
                        fontSize: '10px', fontFamily: 'var(--font-mono)',
                        color: getScoreColor(item.score),
                      }}>
                        ★ {item.score?.toFixed(1)}
                      </div>
                      {item.route && (
                        <div style={{
                          fontSize: '10px', padding: '1px 6px', borderRadius: '10px',
                          background: 'rgba(99,102,241,0.1)',
                          border: '1px solid rgba(99,102,241,0.2)',
                          color: '#6366f1',
                        }}>
                          {item.route?.replace('_AGENT', '').replace('_', ' ')}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </>
            )}
          </div>
        )}

        {/* INGEST TAB */}
        {activeTab === 'ingest' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', letterSpacing: '1px', fontWeight: '600' }}>
              INGEST DOCUMENTS
            </div>
            <div style={{
              padding: '10px 12px',
              background: 'rgba(99,102,241,0.06)',
              border: '1px solid rgba(99,102,241,0.15)',
              borderRadius: 'var(--radius-md)',
              fontSize: '11px', color: '#6366f1', lineHeight: '1.5',
            }}>
              📚 Add text to the RAG knowledge base. It will be chunked, embedded, and indexed in FAISS.
            </div>

            <textarea
              value={uploadText}
              onChange={e => setUploadText(e.target.value)}
              placeholder="Paste your document text here...&#10;&#10;It will be automatically chunked into 300-character pieces, embedded with BGE, and indexed in FAISS for retrieval."
              style={{
                width: '100%', minHeight: '180px', padding: '12px',
                background: 'rgba(255,255,255,0.03)',
                border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: 'var(--radius-md)',
                color: 'var(--text-primary)', fontSize: '12px',
                fontFamily: 'var(--font-body)', resize: 'vertical',
                outline: 'none', lineHeight: '1.6',
              }}
              onFocus={e => e.target.style.borderColor = 'rgba(99,102,241,0.4)'}
              onBlur={e => e.target.style.borderColor = 'rgba(255,255,255,0.1)'}
            />

            <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)' }}>
              {uploadText.length} characters
              {uploadText.length > 0 && ` • ~${Math.ceil(uploadText.length / 300)} chunks`}
            </div>

            <button
              onClick={handleUpload}
              disabled={!uploadText.trim() || isUploading}
              style={{
                padding: '10px 16px',
                background: uploadText.trim() && !isUploading
                  ? 'linear-gradient(135deg, #6366f1, #8b5cf6)'
                  : 'rgba(255,255,255,0.05)',
                border: 'none', borderRadius: 'var(--radius-md)',
                color: 'white', cursor: uploadText.trim() && !isUploading ? 'pointer' : 'not-allowed',
                fontSize: '13px', fontFamily: 'var(--font-body)', fontWeight: '500',
                opacity: uploadText.trim() && !isUploading ? 1 : 0.5,
                boxShadow: uploadText.trim() && !isUploading ? '0 0 20px rgba(99,102,241,0.3)' : 'none',
                transition: 'all 0.2s', display: 'flex', alignItems: 'center',
                justifyContent: 'center', gap: '8px',
              }}
            >
              <Upload size={14} />
              {isUploading ? 'Ingesting...' : 'Ingest Document'}
            </button>

            {uploadStatus && (
              <div style={{
                padding: '10px 12px', borderRadius: 'var(--radius-md)',
                background: uploadStatus.success ? 'rgba(16,185,129,0.08)' : 'rgba(239,68,68,0.08)',
                border: `1px solid ${uploadStatus.success ? 'rgba(16,185,129,0.2)' : 'rgba(239,68,68,0.2)'}`,
                fontSize: '12px',
                color: uploadStatus.success ? '#10b981' : '#ef4444',
                display: 'flex', alignItems: 'center', gap: '8px',
                animation: 'fadeInUp 0.3s ease',
              }}>
                {uploadStatus.success ? <CheckCircle size={14} /> : <AlertCircle size={14} />}
                {uploadStatus.message}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default RightPanel;