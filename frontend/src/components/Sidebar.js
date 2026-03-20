{/* Clear all button */}
{sessions.length > 0 && (
  <div style={{ padding: '8px 16px' }}>
    <button
      onClick={onClearAll}
      style={{
        width: '100%', padding: '7px',
        background: 'transparent',
        border: '1px solid rgba(239,68,68,0.2)',
        borderRadius: 'var(--radius-sm)',
        color: 'rgba(239,68,68,0.6)',
        cursor: 'pointer', fontSize: '11px',
        fontFamily: 'var(--font-body)',
        transition: 'all 0.2s',
      }}
      onMouseEnter={e => {
        e.currentTarget.style.background = 'rgba(239,68,68,0.08)';
        e.currentTarget.style.color = '#ef4444';
      }}
      onMouseLeave={e => {
        e.currentTarget.style.background = 'transparent';
        e.currentTarget.style.color = 'rgba(239,68,68,0.6)';
      }}
    >
      🗑️ Clear All History
    </button>
  </div>
)}
export default Sidebar;