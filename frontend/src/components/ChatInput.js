import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader, Globe, Database } from 'lucide-react';

const ChatInput = ({ onSend, isLoading, useCache, onToggleCache }) => {
  const [value, setValue] = useState('');
  const textareaRef = useRef(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 160) + 'px';
    }
  }, [value]);

  const handleSend = () => {
    if (!value.trim() || isLoading) return;
    onSend(value.trim());
    setValue('');
    if (textareaRef.current) textareaRef.current.style.height = 'auto';
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const suggestions = [
    'What is RAG and how does it work?',
    'Calculate the sum of squares from 1 to 10',
    'Compare RAG vs fine-tuning for production AI',
    'How does FAISS enable fast similarity search?',
  ];

  return (
    <div style={{
      padding: '16px 24px 20px',
      borderTop: '1px solid rgba(255,255,255,0.06)',
      background: 'rgba(5,5,8,0.8)',
      backdropFilter: 'blur(20px)',
    }}>
      {/* Suggestions */}
      {!isLoading && value === '' && (
        <div style={{
          display: 'flex', gap: '8px', marginBottom: '12px',
          overflowX: 'auto', paddingBottom: '4px',
        }}>
          {suggestions.map((s, i) => (
            <button
              key={i}
              onClick={() => setValue(s)}
              style={{
                background: 'rgba(255,255,255,0.03)',
                border: '1px solid rgba(255,255,255,0.08)',
                borderRadius: 'var(--radius-md)',
                padding: '6px 12px',
                color: 'var(--text-secondary)',
                cursor: 'pointer',
                fontSize: '11px',
                whiteSpace: 'nowrap',
                fontFamily: 'var(--font-body)',
                transition: 'all 0.15s',
                flexShrink: 0,
              }}
              onMouseEnter={e => {
                e.currentTarget.style.background = 'rgba(99,102,241,0.08)';
                e.currentTarget.style.borderColor = 'rgba(99,102,241,0.25)';
                e.currentTarget.style.color = 'var(--text-primary)';
              }}
              onMouseLeave={e => {
                e.currentTarget.style.background = 'rgba(255,255,255,0.03)';
                e.currentTarget.style.borderColor = 'rgba(255,255,255,0.08)';
                e.currentTarget.style.color = 'var(--text-secondary)';
              }}
            >
              {s}
            </button>
          ))}
        </div>
      )}

      {/* Input area */}
      <div style={{
        background: 'rgba(255,255,255,0.04)',
        border: '1px solid rgba(255,255,255,0.1)',
        borderRadius: 'var(--radius-lg)',
        transition: 'all 0.2s',
        overflow: 'hidden',
      }}
        onFocus={() => {}}
      >
        <textarea
          ref={textareaRef}
          value={value}
          onChange={e => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask anything... (Shift+Enter for new line)"
          disabled={isLoading}
          rows={1}
          style={{
            width: '100%', padding: '14px 16px 10px',
            background: 'transparent', border: 'none', outline: 'none',
            color: 'var(--text-primary)', fontSize: '14px',
            fontFamily: 'var(--font-body)', resize: 'none',
            lineHeight: '1.6', minHeight: '44px', maxHeight: '160px',
          }}
        />

        {/* Bottom bar */}
        <div style={{
          display: 'flex', alignItems: 'center',
          padding: '8px 12px 10px', gap: '8px',
        }}>
          {/* Cache toggle */}
          <button
            onClick={onToggleCache}
            title={useCache ? 'Cache enabled' : 'Cache disabled'}
            style={{
              display: 'flex', alignItems: 'center', gap: '5px',
              padding: '4px 10px', borderRadius: '20px', cursor: 'pointer',
              fontFamily: 'var(--font-body)', fontSize: '11px',
              background: useCache ? 'rgba(139,92,246,0.1)' : 'rgba(255,255,255,0.04)',
              border: useCache ? '1px solid rgba(139,92,246,0.3)' : '1px solid rgba(255,255,255,0.08)',
              color: useCache ? '#8b5cf6' : 'var(--text-tertiary)',
              transition: 'all 0.2s',
            }}
          >
            <Database size={10} />
            {useCache ? 'Cache ON' : 'Cache OFF'}
          </button>

          <div style={{ flex: 1 }} />

          {/* Char count */}
          <span style={{
            fontSize: '10px', color: value.length > 1800 ? '#ef4444' : 'var(--text-tertiary)',
            fontFamily: 'var(--font-mono)',
          }}>
            {value.length}/2000
          </span>

          {/* Send button */}
          <button
            onClick={handleSend}
            disabled={!value.trim() || isLoading}
            style={{
              width: '34px', height: '34px', borderRadius: 'var(--radius-sm)',
              border: 'none', cursor: value.trim() && !isLoading ? 'pointer' : 'not-allowed',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              background: value.trim() && !isLoading
                ? 'linear-gradient(135deg, #6366f1, #8b5cf6)'
                : 'rgba(255,255,255,0.06)',
              boxShadow: value.trim() && !isLoading
                ? '0 0 20px rgba(99,102,241,0.4)'
                : 'none',
              transition: 'all 0.2s',
              opacity: value.trim() && !isLoading ? 1 : 0.4,
            }}
          >
            {isLoading
              ? <Loader size={14} style={{ color: '#6366f1', animation: 'spin 1s linear infinite' }} />
              : <Send size={14} style={{ color: 'white' }} />
            }
          </button>
        </div>
      </div>

      <div style={{
        textAlign: 'center', marginTop: '8px',
        fontSize: '10px', color: 'var(--text-tertiary)',
      }}>
        Agentic RAG may make mistakes. Always verify important information.
      </div>
    </div>
  );
};

export default ChatInput;