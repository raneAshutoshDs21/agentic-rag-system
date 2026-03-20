import React, { useState, useEffect } from 'react';
import { Bot } from 'lucide-react';

const steps = [
  { label: 'Checking guardrails', color: '#ef4444' },
  { label: 'Checking cache', color: '#8b5cf6' },
  { label: 'Routing query', color: '#f59e0b' },
  { label: 'Retrieving context', color: '#6366f1' },
  { label: 'Generating answer', color: '#06b6d4' },
  { label: 'Evaluating response', color: '#10b981' },
];

const LoadingMessage = () => {
  const [stepIndex, setStepIndex] = useState(0);
  const [dots, setDots] = useState('');

  useEffect(() => {
    const stepTimer = setInterval(() => {
      setStepIndex(i => Math.min(i + 1, steps.length - 1));
    }, 600);
    const dotTimer = setInterval(() => {
      setDots(d => d.length >= 3 ? '' : d + '.');
    }, 400);
    return () => { clearInterval(stepTimer); clearInterval(dotTimer); };
  }, []);

  const current = steps[stepIndex];

  return (
    <div style={{
      display: 'flex', gap: '14px', padding: '20px 24px',
      borderBottom: '1px solid rgba(255,255,255,0.03)',
      background: 'rgba(255,255,255,0.01)',
      animation: 'fadeInUp 0.3s ease',
    }}>
      {/* Avatar */}
      <div style={{
        width: '34px', height: '34px', borderRadius: '10px', flexShrink: 0,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        background: 'linear-gradient(135deg, rgba(6,182,212,0.3), rgba(99,102,241,0.3))',
        border: '1px solid rgba(6,182,212,0.3)',
        boxShadow: '0 0 15px rgba(6,182,212,0.2)',
        animation: 'pulse-glow 2s ease infinite',
      }}>
        <Bot size={16} style={{ color: '#06b6d4' }} />
      </div>

      <div style={{ flex: 1 }}>
        <div style={{
          fontSize: '12px', fontWeight: '600', color: '#06b6d4',
          fontFamily: 'var(--font-display)', marginBottom: '12px',
        }}>
          Agentic RAG
        </div>

        {/* Steps */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          {steps.slice(0, stepIndex + 1).map((step, i) => (
            <div key={i} style={{
              display: 'flex', alignItems: 'center', gap: '8px',
              animation: 'fadeInUp 0.3s ease',
            }}>
              <div style={{
                width: '6px', height: '6px', borderRadius: '50%',
                background: i === stepIndex ? step.color : 'rgba(255,255,255,0.2)',
                boxShadow: i === stepIndex ? `0 0 8px ${step.color}` : 'none',
                transition: 'all 0.3s',
                flexShrink: 0,
              }} />
              <span style={{
                fontSize: '12px',
                color: i === stepIndex ? 'var(--text-primary)' : 'var(--text-tertiary)',
                fontFamily: i === stepIndex ? 'var(--font-body)' : 'var(--font-body)',
                transition: 'color 0.3s',
              }}>
                {step.label}{i === stepIndex ? dots : ' ✓'}
              </span>
            </div>
          ))}
        </div>

        {/* Shimmer bar */}
        <div style={{
          marginTop: '14px', height: '3px',
          background: 'linear-gradient(90deg, transparent, #6366f1, #8b5cf6, #06b6d4, transparent)',
          backgroundSize: '200% 100%',
          borderRadius: '2px', width: '120px',
          animation: 'shimmer 1.5s linear infinite',
        }} />
      </div>
    </div>
  );
};

export default LoadingMessage;