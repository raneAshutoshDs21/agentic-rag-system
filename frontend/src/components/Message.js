import React, { useState } from 'react';
import { User, Bot, ChevronDown, ChevronUp, Clock, Zap } from 'lucide-react';
import { getRouteConfig, getScoreColor, formatTime } from '../utils/api';

const RouteBadge = ({ route }) => {
  const config = getRouteConfig(route);
  return (
    <div style={{
      display: 'inline-flex', alignItems: 'center', gap: '5px',
      padding: '3px 8px', borderRadius: '20px', fontSize: '10px',
      fontWeight: '600', letterSpacing: '0.5px',
      background: `${config.color}18`,
      border: `1px solid ${config.color}40`,
      color: config.color,
      fontFamily: 'var(--font-mono)',
    }}>
      <span>{config.icon}</span>
      {config.label}
    </div>
  );
};

const ScoreBadge = ({ score }) => {
  const color = getScoreColor(score);
  const pct = (score / 10) * 100;
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
      <div style={{ fontSize: '10px', color: 'var(--text-tertiary)' }}>Score</div>
      <div style={{
        width: '60px', height: '4px',
        background: 'rgba(255,255,255,0.08)', borderRadius: '2px',
        overflow: 'hidden',
      }}>
        <div style={{
          height: '100%', width: `${pct}%`,
          background: `linear-gradient(90deg, ${color}88, ${color})`,
          borderRadius: '2px', transition: 'width 0.8s ease',
        }} />
      </div>
      <div style={{ fontSize: '11px', color, fontFamily: 'var(--font-mono)', fontWeight: '600' }}>
        {score?.toFixed(1)}
      </div>
    </div>
  );
};

const SourcesPanel = ({ sources }) => {
  const [open, setOpen] = useState(false);
  if (!sources || sources.length === 0) return null;
  const unique = [...new Set(sources)];

  return (
    <div style={{ marginTop: '10px' }}>
      <button
        onClick={() => setOpen(!open)}
        style={{
          background: 'rgba(99,102,241,0.08)', border: '1px solid rgba(99,102,241,0.2)',
          borderRadius: 'var(--radius-sm)', padding: '5px 10px',
          color: '#6366f1', cursor: 'pointer', fontSize: '11px',
          fontFamily: 'var(--font-body)', display: 'flex', alignItems: 'center', gap: '5px',
          transition: 'all 0.2s',
        }}
        onMouseEnter={e => e.currentTarget.style.background = 'rgba(99,102,241,0.15)'}
        onMouseLeave={e => e.currentTarget.style.background = 'rgba(99,102,241,0.08)'}
      >
        📚 {unique.length} source{unique.length > 1 ? 's' : ''}
        {open ? <ChevronUp size={11} /> : <ChevronDown size={11} />}
      </button>

      {open && (
        <div style={{
          marginTop: '6px', padding: '10px',
          background: 'rgba(99,102,241,0.05)',
          border: '1px solid rgba(99,102,241,0.15)',
          borderRadius: 'var(--radius-sm)',
          animation: 'fadeInUp 0.2s ease',
        }}>
          {unique.map((src, i) => (
            <div key={i} style={{
              display: 'flex', alignItems: 'center', gap: '8px',
              padding: '4px 0',
              borderBottom: i < unique.length - 1 ? '1px solid rgba(255,255,255,0.05)' : 'none',
            }}>
              <div style={{
                width: '6px', height: '6px', borderRadius: '50%',
                background: '#6366f1', flexShrink: 0,
              }} />
              <span style={{ fontSize: '11px', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>
                {src}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const Message = ({ message, index }) => {
  const isUser = message.role === 'user';
  const delay = index * 0.05;

  return (
    <div style={{
      display: 'flex', gap: '14px', padding: '20px 24px',
      animation: `fadeInUp 0.4s ease ${delay}s both`,
      borderBottom: '1px solid rgba(255,255,255,0.03)',
      background: isUser ? 'transparent' : 'rgba(255,255,255,0.01)',
    }}>
      {/* Avatar */}
      <div style={{
        width: '34px', height: '34px', borderRadius: '10px',
        flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center',
        background: isUser
          ? 'linear-gradient(135deg, rgba(99,102,241,0.3), rgba(139,92,246,0.3))'
          : 'linear-gradient(135deg, rgba(6,182,212,0.3), rgba(99,102,241,0.3))',
        border: isUser
          ? '1px solid rgba(99,102,241,0.3)'
          : '1px solid rgba(6,182,212,0.3)',
        boxShadow: isUser
          ? '0 0 15px rgba(99,102,241,0.15)'
          : '0 0 15px rgba(6,182,212,0.15)',
      }}>
        {isUser
          ? <User size={16} style={{ color: '#6366f1' }} />
          : <Bot size={16} style={{ color: '#06b6d4' }} />
        }
      </div>

      {/* Content */}
      <div style={{ flex: 1, minWidth: 0 }}>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px', flexWrap: 'wrap' }}>
          <span style={{
            fontSize: '12px', fontWeight: '600',
            color: isUser ? '#6366f1' : '#06b6d4',
            fontFamily: 'var(--font-display)',
          }}>
            {isUser ? 'You' : 'Agentic RAG'}
          </span>

          {!isUser && message.route && <RouteBadge route={message.route} />}

          {!isUser && message.fromCache && (
            <div style={{
              display: 'inline-flex', alignItems: 'center', gap: '4px',
              padding: '2px 7px', borderRadius: '20px', fontSize: '10px',
              background: 'rgba(139,92,246,0.1)', border: '1px solid rgba(139,92,246,0.25)',
              color: '#8b5cf6',
            }}>
              <Zap size={9} /> Cached
            </div>
          )}

          {!isUser && message.totalTimeMs !== undefined && (
            <div style={{
              display: 'inline-flex', alignItems: 'center', gap: '4px',
              fontSize: '10px', color: 'var(--text-tertiary)',
              fontFamily: 'var(--font-mono)',
            }}>
              <Clock size={9} />
              {message.fromCache ? '0ms' : `${Math.round(message.totalTimeMs)}ms`}
            </div>
          )}

          <span style={{ fontSize: '10px', color: 'var(--text-tertiary)', marginLeft: 'auto' }}>
            {formatTime(message.timestamp)}
          </span>
        </div>

        {/* Message text */}
        <div style={{
          fontSize: '14px', lineHeight: '1.7',
          color: 'var(--text-primary)',
          whiteSpace: 'pre-wrap', wordBreak: 'break-word',
        }}>
          {message.content}
        </div>

        {/* Score */}
        {!isUser && message.score > 0 && (
          <div style={{ marginTop: '10px' }}>
            <ScoreBadge score={message.score} />
          </div>
        )}

        {/* Sources */}
        {!isUser && <SourcesPanel sources={message.sources} />}

        {/* Feedback */}
        {!isUser && message.feedback && message.feedback !== 'N/A' && (
          <div style={{
            marginTop: '10px', padding: '8px 12px',
            background: 'rgba(245,158,11,0.06)',
            border: '1px solid rgba(245,158,11,0.15)',
            borderRadius: 'var(--radius-sm)',
            fontSize: '11px', color: 'var(--text-secondary)',
            fontStyle: 'italic',
          }}>
            💡 {message.feedback}
          </div>
        )}
      </div>
    </div>
  );
};

export default Message;