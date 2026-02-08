import renderMarkdown from '../utils/renderMarkdown'

const AGENT_CONFIG = {
  supervisor: { icon: '⬡', color: 'var(--cyan)', bg: 'rgba(0,243,255,0.08)', bgDim: 'rgba(0,243,255,0.06)', border: 'rgba(0,243,255,0.18)', borderDim: 'rgba(0,243,255,0.15)', label: 'SUPERVISOR' },
  genie: { icon: '◈', color: 'var(--green)', bg: 'rgba(6,255,165,0.08)', bgDim: 'rgba(6,255,165,0.06)', border: 'rgba(6,255,165,0.18)', borderDim: 'rgba(6,255,165,0.15)', label: 'GENIE' },
  vector_search: { icon: '⟐', color: 'var(--purple)', bg: 'rgba(131,56,236,0.08)', bgDim: 'rgba(131,56,236,0.06)', border: 'rgba(131,56,236,0.18)', borderDim: 'rgba(131,56,236,0.15)', label: 'VECTOR SEARCH' },
  medical_reasoning: { icon: '✦', color: 'var(--pink)', bg: 'rgba(255,0,110,0.08)', bgDim: 'rgba(255,0,110,0.06)', border: 'rgba(255,0,110,0.18)', borderDim: 'rgba(255,0,110,0.15)', label: 'MEDICAL REASONING' },
  geospatial: { icon: '◎', color: 'var(--yellow)', bg: 'rgba(255,214,10,0.08)', bgDim: 'rgba(255,214,10,0.06)', border: 'rgba(255,214,10,0.18)', borderDim: 'rgba(255,214,10,0.15)', label: 'GEOSPATIAL' },
  planning: { icon: '△', color: 'var(--orange)', bg: 'rgba(255,133,0,0.08)', bgDim: 'rgba(255,133,0,0.06)', border: 'rgba(255,133,0,0.18)', borderDim: 'rgba(255,133,0,0.15)', label: 'PLANNING' },
  aggregator: { icon: '⊕', color: 'var(--cyan)', bg: 'rgba(0,243,255,0.08)', bgDim: 'rgba(0,243,255,0.06)', border: 'rgba(0,243,255,0.18)', borderDim: 'rgba(0,243,255,0.15)', label: 'AGGREGATOR' },
}

const DEFAULT_CONFIG = { icon: '⚙', color: 'var(--text-secondary)', bg: 'rgba(128,128,128,0.08)', bgDim: 'rgba(128,128,128,0.06)', border: 'rgba(128,128,128,0.18)', borderDim: 'rgba(128,128,128,0.15)' }

export default function ReasoningTrace({ trace }) {
  if (!trace || trace.length === 0) {
    return (
      <div className="glass-card p-6 text-center">
        <p className="font-mono text-sm" style={{ color: 'var(--text-muted)' }}>
          No trace data available
        </p>
      </div>
    )
  }

  return (
    <div className="glass-card p-4 space-y-1">
      <div className="flex items-center gap-2 mb-3">
        <span className="font-mono text-[0.6rem] tracking-[0.15em] uppercase font-semibold"
              style={{ color: 'var(--text-muted)' }}>
          ▸ Reasoning Trace
        </span>
        <span className="cyber-badge cyber-badge-cyan">{trace.length} steps</span>
      </div>

      <div className="space-y-2">
        {trace.map((step, i) => {
          const config = AGENT_CONFIG[step.agent] || { ...DEFAULT_CONFIG, label: step.agent }
          return (
            <div
              key={i}
              className="animate-slide-in rounded-lg p-3 relative"
              style={{
                animationDelay: `${i * 80}ms`,
                background: 'var(--bg-surface)',
                borderLeft: `3px solid ${config.color}`,
              }}
            >
              {/* Connector line */}
              {i < trace.length - 1 && (
                <div
                  className="absolute top-full w-px h-2"
                  style={{ left: '13px', background: 'var(--border-dim)' }}
                />
              )}

              <div className="flex items-center gap-3">
                {/* Step number + icon */}
                <div
                  className="w-7 h-7 rounded-md flex items-center justify-center text-xs font-mono font-bold shrink-0"
                  style={{
                    background: config.bg,
                    color: config.color,
                    border: `1px solid ${config.border}`,
                  }}
                >
                  {config.icon}
                </div>

                {/* Agent name + action */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span
                      className="font-mono text-xs font-bold tracking-wider"
                      style={{ color: config.color }}
                    >
                      {config.label}
                    </span>
                    {step.action && (
                      <span className="cyber-badge" style={{
                        background: config.bgDim,
                        color: config.color,
                        border: `1px solid ${config.borderDim}`,
                      }}>
                        {step.action}
                      </span>
                    )}
                    {step.duration_ms != null && (
                      <span className="font-mono text-[0.6rem] ml-auto" style={{ color: 'var(--text-muted)' }}>
                        {step.duration_ms.toFixed(0)}ms
                      </span>
                    )}
                  </div>
                  {step.summary && (
                    <div className="text-xs mt-1" style={{ color: 'var(--text-secondary)' }}>
                      {renderMarkdown(step.summary, { textColor: 'var(--text-secondary)', boldColor: 'var(--text-primary)' })}
                    </div>
                  )}
                  {step.intent && (
                    <div className="flex items-center gap-1 mt-1 flex-wrap">
                      <span className="font-mono text-[0.6rem]" style={{ color: 'var(--text-muted)' }}>
                        INTENT:
                      </span>
                      <span className="cyber-badge cyber-badge-cyan">{step.intent}</span>
                      {step.confidence != null && (
                        <span className="cyber-badge" style={{
                          background: step.confidence > 0.7 ? 'rgba(6,255,165,0.1)' : step.confidence > 0.4 ? 'rgba(255,214,10,0.1)' : 'rgba(255,0,110,0.1)',
                          color: step.confidence > 0.7 ? 'var(--green)' : step.confidence > 0.4 ? 'var(--yellow)' : 'var(--pink)',
                          border: `1px solid ${step.confidence > 0.7 ? 'rgba(6,255,165,0.3)' : step.confidence > 0.4 ? 'rgba(255,214,10,0.3)' : 'rgba(255,0,110,0.3)'}`,
                        }}>
                          {(step.confidence * 100).toFixed(0)}% conf
                        </span>
                      )}
                      {step.llm_enhanced && (
                        <span className="cyber-badge cyber-badge-green">LLM Enhanced</span>
                      )}
                      {step.agents?.map(a => (
                        <span key={a} className="cyber-badge cyber-badge-purple">{a}</span>
                      ))}
                    </div>
                  )}
                  {step.llm_used && step.agent === 'aggregator' && (
                    <div className="flex items-center gap-1 mt-1">
                      <span className="cyber-badge cyber-badge-green">Groq LLM</span>
                      <span className="font-mono text-[0.6rem]" style={{ color: 'var(--text-muted)' }}>
                        Natural language synthesis
                      </span>
                    </div>
                  )}
                  {step.vector_used && (
                    <p className="font-mono text-[0.6rem] mt-1" style={{ color: 'var(--text-muted)' }}>
                      VECTOR: {step.vector_used}
                    </p>
                  )}
                  {step.search_method && (
                    <div className="flex items-center gap-1 mt-1 flex-wrap">
                      <span className="font-mono text-[0.6rem]" style={{ color: 'var(--text-muted)' }}>
                        METHOD:
                      </span>
                      <span className="cyber-badge cyber-badge-purple">{step.search_method.replace(/_/g, ' ')}</span>
                      {step.vectors_queried?.length > 0 && (
                        <span className="font-mono text-[0.6rem]" style={{ color: 'var(--text-muted)' }}>
                          ({step.vectors_queried.length} vectors)
                        </span>
                      )}
                    </div>
                  )}
                  {step.vector_weights && typeof step.vector_weights === 'object' && (
                    <div className="flex items-center gap-2 mt-1 flex-wrap">
                      {Object.entries(step.vector_weights).map(([v, w]) => (
                        <span key={v} className="font-mono text-[0.55rem]" style={{ color: 'var(--text-muted)' }}>
                          {v.replace('_', ' ')}: <span style={{ color: 'var(--cyan)' }}>{w.toFixed(1)}</span>
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Step-level citations */}
                  {step.citations && step.citations.length > 0 && (
                    <details className="mt-2">
                      <summary
                        className="cursor-pointer font-mono text-[0.6rem] tracking-wider"
                        style={{ color: 'var(--green)' }}
                      >
                        ▸ {step.citations.length} CITATIONS
                      </summary>
                      <div className="mt-1 space-y-1 pl-2" style={{ borderLeft: '1px solid var(--border-dim)' }}>
                        {step.citations.slice(0, 5).map((c, ci) => (
                          <div key={ci} className="text-[0.65rem]" style={{ color: 'var(--text-secondary)' }}>
                            <span className="font-mono" style={{ color: 'var(--cyan-dim)' }}>
                              [{c.source || c.facility || ci + 1}]
                            </span>{' '}
                            {c.text || c.name || c.evidence || JSON.stringify(c).slice(0, 100)}
                          </div>
                        ))}
                        {step.citations.length > 5 && (
                          <p className="text-[0.6rem]" style={{ color: 'var(--text-muted)' }}>
                            +{step.citations.length - 5} more
                          </p>
                        )}
                      </div>
                    </details>
                  )}
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
