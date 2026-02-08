import { useState } from 'react'

export default function QueryInput({ onSubmit, loading, examples }) {
  const [query, setQuery] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (query.trim()) onSubmit(query.trim())
  }

  return (
    <div className="glass-card p-4 space-y-3">
      <div className="flex items-center gap-2 mb-1">
        <span style={{ color: 'var(--purple)', fontSize: '1rem' }}>🔍</span>
        <span
          className="font-mono text-sm tracking-widest"
          style={{ color: 'var(--cyan)' }}
        >
          Ask About Healthcare in Ghana
        </span>
      </div>

      <form onSubmit={handleSubmit} className="flex gap-3">
        <input
          type="text"
          className="cyber-input flex-1"
          placeholder="Ask me anything about healthcare facilities, specialties, equipment, or regional gaps..."
          value={query}
          onChange={e => setQuery(e.target.value)}
          disabled={loading}
        />
        <button
          type="submit"
          className="btn-neon flex items-center gap-2"
          disabled={loading || !query.trim()}
        >
          {loading ? (
            <span className="cyber-spinner"></span>
          ) : (
            <>
              <span>⟐</span>
              ANALYZE
            </>
          )}
        </button>
      </form>

      {/* Example queries as neon pills */}
      <div className="flex flex-wrap gap-2">
        {examples?.map((ex, i) => (
          <button
            key={i}
            className="text-[0.7rem] px-3 py-1 rounded-full cursor-pointer transition-all duration-200 font-mono"
            style={{
              background: 'rgba(0, 243, 255, 0.05)',
              border: '1px solid rgba(0, 243, 255, 0.15)',
              color: 'var(--text-secondary)',
            }}
            onMouseEnter={e => {
              e.currentTarget.style.borderColor = 'var(--cyan)'
              e.currentTarget.style.color = 'var(--cyan)'
              e.currentTarget.style.background = 'rgba(0, 243, 255, 0.1)'
            }}
            onMouseLeave={e => {
              e.currentTarget.style.borderColor = 'rgba(0, 243, 255, 0.15)'
              e.currentTarget.style.color = 'var(--text-secondary)'
              e.currentTarget.style.background = 'rgba(0, 243, 255, 0.05)'
            }}
            onClick={() => { setQuery(ex); onSubmit(ex) }}
            disabled={loading}
          >
            {ex}
          </button>
        ))}
      </div>
    </div>
  )
}
