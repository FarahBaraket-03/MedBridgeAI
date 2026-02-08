export default function Header({ onOpenRoutingMap }) {
  return (
    <header
      className="relative px-6 py-3 flex items-center justify-between"
      style={{
        background: 'linear-gradient(180deg, rgba(0,243,255,0.06) 0%, transparent 100%)',
        borderBottom: '1px solid var(--border-dim)',
      }}
    >
      {/* Left: logo + title */}
      <div className="flex items-center gap-3">
        <div
          className="w-9 h-9 rounded-lg flex items-center justify-center text-lg"
          style={{
            background: 'linear-gradient(135deg, var(--cyan), var(--purple))',
            boxShadow: '0 0 15px var(--cyan-glow)',
          }}
        >
          ⚕
        </div>
        <div>
          <h1
            className="font-mono text-lg font-extrabold tracking-widest leading-tight"
            style={{ color: 'var(--cyan)', textShadow: '0 0 10px rgba(0,243,255,0.4)' }}
          >
            VIRTUE AI
          </h1>
          <p
            className="font-mono text-[0.6rem] tracking-[0.15em] uppercase"
            style={{ color: 'var(--text-muted)' }}
          >
            Healthcare Intelligence Layer
          </p>
        </div>
      </div>

      {/* Right: routing map button + status badges */}
      <div className="flex items-center gap-3">
        {onOpenRoutingMap && (
          <button
            onClick={onOpenRoutingMap}
            className="font-mono"
            style={{
              background: 'linear-gradient(135deg, rgba(0,243,255,0.12), rgba(131,56,236,0.12))',
              border: '1px solid var(--border-med)',
              color: 'var(--cyan)',
              padding: '6px 14px',
              borderRadius: 6,
              cursor: 'pointer',
              fontWeight: 600,
              fontSize: '0.7rem',
              letterSpacing: '0.08em',
              transition: 'all 0.2s',
            }}
            onMouseEnter={e => {
              e.currentTarget.style.boxShadow = '0 0 16px rgba(0,243,255,0.3)';
              e.currentTarget.style.borderColor = 'var(--cyan)';
            }}
            onMouseLeave={e => {
              e.currentTarget.style.boxShadow = 'none';
              e.currentTarget.style.borderColor = 'var(--border-med)';
            }}
          >
            🗺️ ROUTING MAP
          </button>
        )}
        <div className="cyber-badge cyber-badge-green">
          <span className="pulse-dot" style={{ width: 6, height: 6 }}></span>
          6 Agents
        </div>
        <div className="cyber-badge cyber-badge-purple">
          LangGraph
        </div>
        <div className="cyber-badge cyber-badge-cyan">
          Qdrant
        </div>
        <div className="cyber-badge cyber-badge-orange">
          Groq LLM
        </div>
      </div>
    </header>
  )
}
