import React, { useState } from 'react';
import { MessageSquare, Plus, Trash2, Clock, Zap, Activity } from 'lucide-react';

const Sidebar = ({ sessions, currentSession, onNewSession, onSelectSession, onDeleteSession, metrics }) => {
  const [hoveredSession, setHoveredSession] = useState(null);

  return (
    <div style={{
      width: '280px',
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
      background: 'rgba(255,255,255,0.02)',
      borderRight: '1px solid rgba(255,255,255,0.06)',
      flexShrink: 0,
    }}>
      {/* Logo */}
      <div style={{
        padding: '24px 20px 20px',
        borderBottom: '1px solid rgba(255,255,255,0.06)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
          <div style={{
            width: '32px', height: '32px', borderRadius: '10px',
            background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '16px', boxShadow: '0 0 20px rgba(99,102,241,0.4)',
          }}>🤖</div>
          <div>
            <div style={{ fontFamily: 'var(--font-display)', fontWeight: '700', fontSize: '15px', letterSpacing: '-0.3px' }}>
              Agentic RAG
            </div>
            <div style={{ fontSize: '10px', color: 'var(--text-tertiary)', letterSpacing: '0.5px' }}>
              POWERED BY LLAMA 3.3 70B
            </div>
          </div>
        </div>
      </div>

      {/* New Chat Button */}
      <div style={{ padding: '16px 16px 8px' }}>
        <button onClick={onNewSession} style={{
          width: '100%', padding: '10px 16px',
          background: 'linear-gradient(135deg, rgba(99,102,241,0.15), rgba(139,92,246,0.15))',
          border: '1px solid rgba(99,102,241,0.3)',
          borderRadius: 'var(--radius-md)', color: 'var(--text-primary)',
          cursor: 'pointer', display: 'flex', alignItems: 'center',
          gap: '8px', fontSize: '13px', fontFamily: 'var(--font-body)',
          fontWeight: '500', transition: 'all 0.2s',
        }}
          onMouseEnter={e => e.currentTarget.style.background = 'linear-gradient(135deg, rgba(99,102,241,0.25), rgba(139,92,246,0.25))'}
          onMouseLeave={e => e.currentTarget.style.background = 'linear-gradient(135deg, rgba(99,102,241,0.15), rgba(139,92,246,0.15))'}
        >
          <Plus size={14} />
          New Conversation
        </button>
      </div>

      {/* Sessions List */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '4px 8px' }}>
        <div style={{ fontSize: '10px', color: 'var(--text-tertiary)', padding: '8px 8px 6px', letterSpacing: '1px', fontWeight: '600' }}>
          CONVERSATIONS
        </div>
        {sessions.length === 0 ? (
          <div style={{ padding: '20px 8px', textAlign: 'center', color: 'var(--text-tertiary)', fontSize: '12px' }}>
            No conversations yet
          </div>
        ) : (
          sessions.map(session => (
            <div
              key={session.id}
              onClick={() => onSelectSession(session.id)}
              onMouseEnter={() => setHoveredSession(session.id)}
              onMouseLeave={() => setHoveredSession(null)}
              style={{
                padding: '10px 10px',
                borderRadius: 'var(--radius-sm)',
                cursor: 'pointer',
                marginBottom: '2px',
                background: currentSession === session.id
                  ? 'rgba(99,102,241,0.12)'
                  : hoveredSession === session.id ? 'rgba(255,255,255,0.04)' : 'transparent',
                border: currentSession === session.id
                  ? '1px solid rgba(99,102,241,0.25)'
                  : '1px solid transparent',
                transition: 'all 0.15s',
                display: 'flex', alignItems: 'center', gap: '8px',
                position: 'relative',
              }}
            >
              <MessageSquare size={13} style={{ color: currentSession === session.id ? '#6366f1' : 'var(--text-tertiary)', flexShrink: 0 }} />
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{
                  fontSize: '12px', fontWeight: '500',
                  whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
                  color: currentSession === session.id ? 'var(--text-primary)' : 'var(--text-secondary)',
                }}>
                  {session.title || 'New Conversation'}
                </div>
                <div style={{ fontSize: '10px', color: 'var(--text-tertiary)', marginTop: '1px' }}>
                  {session.messageCount} messages
                </div>
              </div>
              {hoveredSession === session.id && (
                <button
                  onClick={e => { e.stopPropagation(); onDeleteSession(session.id); }}
                  style={{
                    background: 'none', border: 'none', cursor: 'pointer',
                    color: 'var(--text-tertiary)', padding: '2px',
                    display: 'flex', alignItems: 'center',
                  }}
                  onMouseEnter={e => e.currentTarget.style.color = '#ef4444'}
                  onMouseLeave={e => e.currentTarget.style.color = 'var(--text-tertiary)'}
                >
                  <Trash2 size={12} />
                </button>
              )}
            </div>
          ))
        )}
      </div>

      {/* System Stats */}
      <div style={{
        padding: '12px 16px',
        borderTop: '1px solid rgba(255,255,255,0.06)',
        background: 'rgba(255,255,255,0.01)',
      }}>
        <div style={{ fontSize: '10px', color: 'var(--text-tertiary)', letterSpacing: '1px', marginBottom: '10px', fontWeight: '600' }}>
          SYSTEM
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          {[
            { icon: <Zap size={11} />, label: 'Model', value: 'LLaMA 3.3 70B', color: '#6366f1' },
            { icon: <Activity size={11} />, label: 'Status', value: 'Online', color: '#10b981' },
            { icon: <Clock size={11} />, label: 'Avg Score', value: metrics?.avg_score ? `${metrics.avg_score}/10` : '—', color: '#f59e0b' },
          ].map(stat => (
            <div key={stat.label} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ color: stat.color }}>{stat.icon}</span>
              <span style={{ fontSize: '11px', color: 'var(--text-tertiary)', flex: 1 }}>{stat.label}</span>
              <span style={{ fontSize: '11px', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>{stat.value}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Sidebar;