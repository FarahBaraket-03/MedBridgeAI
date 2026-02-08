const AGENT_CONFIG = {
  supervisor: { icon: '⬡', color: 'var(--cyan)', label: 'SUPERVISOR' },
  genie: { icon: '◈', color: 'var(--green)', label: 'GENIE' },
  vector_search: { icon: '⟐', color: 'var(--purple)', label: 'VECTOR SEARCH' },
  medical_reasoning: { icon: '✦', color: 'var(--pink)', label: 'MEDICAL REASONING' },
  geospatial: { icon: '◎', color: 'var(--yellow)', label: 'GEOSPATIAL' },
  planning: { icon: '△', color: 'var(--orange)', label: 'PLANNING' },
  aggregator: { icon: '⊕', color: 'var(--cyan)', label: 'AGGREGATOR' },
}

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
          const config = AGENT_CONFIG[step.agent] || { icon: '⚙', color: 'var(--text-secondary)', label: step.agent }
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
                  className="absolute left-[13px] top-full w-[1px] h-2"
                  style={{ background: 'var(--border-dim)' }}
                />
              )}

              <div className="flex items-center gap-3">
                {/* Step number + icon */}
                <div
                  className="w-7 h-7 rounded-md flex items-center justify-center text-xs font-mono font-bold shrink-0"
                  style={{
                    background: `${config.color}15`,
                    color: config.color,
                    border: `1px solid ${config.color}30`,
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
                        background: `${config.color}10`,
                        color: config.color,
                        border: `1px solid ${config.color}25`,
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
                    <p className="text-xs mt-1" style={{ color: 'var(--text-secondary)' }}>
                      {step.summary}
                    </p>
                  )}
                  {step.intent && (
                    <div className="flex items-center gap-1 mt-1 flex-wrap">
                      <span className="font-mono text-[0.6rem]" style={{ color: 'var(--text-muted)' }}>
                        INTENT:
                      </span>
                      <span className="cyber-badge cyber-badge-cyan">{step.intent}</span>
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
