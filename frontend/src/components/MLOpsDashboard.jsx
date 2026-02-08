import { useState, useEffect } from 'react'
import { fetchMLOpsStatus, fetchMLOpsPipeline } from '../api/client'

const STATUS_COLORS = {
  healthy: 'var(--green)',
  degraded: 'var(--yellow)',
  down: 'var(--pink)',
  unknown: 'var(--text-muted)',
}

function StatusDot({ status }) {
  const color = STATUS_COLORS[status] || STATUS_COLORS.unknown
  return (
    <span
      className="inline-block w-2.5 h-2.5 rounded-full mr-2"
      style={{
        background: color,
        boxShadow: `0 0 6px ${color}`,
        animation: status === 'healthy' ? 'pulse-glow 2s infinite' : 'none',
      }}
    />
  )
}

export default function MLOpsDashboard() {
  const [status, setStatus] = useState(null)
  const [pipeline, setPipeline] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const refresh = async () => {
    setLoading(true)
    setError(null)
    try {
      const [s, p] = await Promise.all([fetchMLOpsStatus(), fetchMLOpsPipeline()])
      setStatus(s)
      setPipeline(p?.pipeline)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { refresh() }, [])

  if (loading) {
    return (
      <div className="glass-card p-6 flex flex-col items-center gap-3">
        <div className="cyber-spinner" style={{ width: 28, height: 28, borderWidth: 3 }}></div>
        <span className="font-mono text-xs tracking-wider" style={{ color: 'var(--cyan)' }}>
          LOADING MLOPS STATUS...
        </span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="glass-card neon-border-pink p-4">
        <span style={{ color: 'var(--pink)' }}>MLOps status unavailable: {error}</span>
        <button onClick={refresh} className="cyber-badge cyber-badge-cyan ml-3 cursor-pointer">Retry</button>
      </div>
    )
  }

  const serving = status?.serving_endpoint || {}
  const mlflowRun = status?.latest_mlflow_run || {}
  const servingHealth = serving.status === 'ready' ? 'healthy' : serving.error ? 'down' : 'unknown'

  return (
    <div className="space-y-4 animate-fade-in-up">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="font-mono text-[0.7rem] tracking-[0.15em] uppercase font-bold" style={{ color: 'var(--cyan)' }}>
            MLOps Dashboard
          </span>
          <span className="cyber-badge cyber-badge-purple">Databricks</span>
        </div>
        <button
          onClick={refresh}
          className="cyber-badge cyber-badge-cyan cursor-pointer hover:opacity-80 transition-opacity text-[0.6rem]"
        >
          Refresh
        </button>
      </div>

      {/* Active Backend */}
      <div
        className="glass-card p-4"
        style={{ borderLeft: '3px solid var(--cyan)' }}
      >
        <div className="font-mono text-[0.6rem] tracking-[0.12em] uppercase mb-2" style={{ color: 'var(--text-muted)' }}>
          Vector Search Backend
        </div>
        <div className="flex items-center gap-3">
          <StatusDot status={status?.vector_search_backend === 'databricks' ? 'healthy' : 'degraded'} />
          <span className="font-mono text-sm font-bold" style={{ color: 'var(--text-primary)' }}>
            {status?.vector_search_backend === 'databricks' ? 'Databricks Model Serving' : 'Qdrant Cloud (Direct)'}
          </span>
        </div>
      </div>

      {/* Pipeline architecture */}
      {pipeline && (
        <div className="glass-card p-4 space-y-3">
          <div className="font-mono text-[0.6rem] tracking-[0.12em] uppercase" style={{ color: 'var(--text-muted)' }}>
            Data Pipeline Architecture
          </div>

          {/* Visual pipeline flow */}
          <div className="flex items-center gap-1 flex-wrap">
            {(pipeline.preprocessing?.steps || []).map((step, i, arr) => (
              <span key={step} className="flex items-center gap-1">
                <span className="cyber-badge cyber-badge-green text-[0.55rem]">{step.replace(/_/g, ' ')}</span>
                {i < arr.length - 1 && <span style={{ color: 'var(--text-muted)' }}>→</span>}
              </span>
            ))}
          </div>

          {/* Embedding config */}
          <div className="grid grid-cols-2 gap-3 mt-2">
            <div className="p-2 rounded" style={{ background: 'rgba(131,56,236,0.1)', border: '1px solid rgba(131,56,236,0.2)' }}>
              <div className="font-mono text-[0.55rem] uppercase" style={{ color: 'var(--purple)' }}>Embedding Model</div>
              <div className="font-mono text-xs mt-1" style={{ color: 'var(--text-primary)' }}>{pipeline.embedding?.model}</div>
              <div className="font-mono text-[0.55rem] mt-0.5" style={{ color: 'var(--text-muted)' }}>{pipeline.embedding?.dimension}d &middot; {pipeline.embedding?.normalization}</div>
            </div>
            <div className="p-2 rounded" style={{ background: 'rgba(0,243,255,0.08)', border: '1px solid rgba(0,243,255,0.2)' }}>
              <div className="font-mono text-[0.55rem] uppercase" style={{ color: 'var(--cyan)' }}>Named Vectors</div>
              {(pipeline.embedding?.vectors || []).map(v => (
                <div key={v} className="font-mono text-[0.6rem] mt-0.5" style={{ color: 'var(--text-primary)' }}>&#x25B8; {v}</div>
              ))}
            </div>
          </div>

          {/* Search config */}
          <div className="p-2 rounded" style={{ background: 'rgba(0,255,135,0.08)', border: '1px solid rgba(0,255,135,0.2)' }}>
            <div className="font-mono text-[0.55rem] uppercase" style={{ color: 'var(--green)' }}>Search Method</div>
            <div className="font-mono text-xs mt-1" style={{ color: 'var(--text-primary)' }}>
              Reciprocal Rank Fusion (k={pipeline.search?.rrf_k})
            </div>
            <div className="font-mono text-[0.55rem] mt-0.5" style={{ color: 'var(--text-muted)' }}>
              Multi-vector: {pipeline.search?.multi_vector ? 'Yes' : 'No'} &middot; Metadata filtering: {pipeline.search?.metadata_filtering ? 'Yes' : 'No'}
            </div>
          </div>

          {/* Stats */}
          <div className="flex gap-4 mt-1">
            <div>
              <span className="font-mono text-lg font-bold" style={{ color: 'var(--cyan)' }}>
                {pipeline.preprocessing?.total_facilities?.toLocaleString()}
              </span>
              <span className="font-mono text-[0.55rem] ml-1 uppercase" style={{ color: 'var(--text-muted)' }}>facilities</span>
            </div>
            <div>
              <span className="font-mono text-lg font-bold" style={{ color: 'var(--green)' }}>
                {pipeline.preprocessing?.with_coordinates?.toLocaleString()}
              </span>
              <span className="font-mono text-[0.55rem] ml-1 uppercase" style={{ color: 'var(--text-muted)' }}>geocoded</span>
            </div>
          </div>
        </div>
      )}

      {/* Databricks Serving Endpoint */}
      <div className="glass-card p-4 space-y-2">
        <div className="font-mono text-[0.6rem] tracking-[0.12em] uppercase" style={{ color: 'var(--text-muted)' }}>
          Databricks Model Serving
        </div>
        <div className="flex items-center gap-2">
          <StatusDot status={servingHealth} />
          <span className="font-mono text-xs" style={{ color: 'var(--text-primary)' }}>
            {serving.endpoint || 'Not configured'}
          </span>
          <span className="cyber-badge ml-auto text-[0.5rem]" style={{
            background: servingHealth === 'healthy' ? 'rgba(0,255,135,0.15)' : 'rgba(255,255,255,0.05)',
            color: STATUS_COLORS[servingHealth],
          }}>
            {serving.status || 'N/A'}
          </span>
        </div>
        {serving.error && (
          <div className="font-mono text-[0.6rem]" style={{ color: 'var(--pink)' }}>{serving.error}</div>
        )}
      </div>

      {/* MLflow Latest Run */}
      <div className="glass-card p-4 space-y-2">
        <div className="font-mono text-[0.6rem] tracking-[0.12em] uppercase" style={{ color: 'var(--text-muted)' }}>
          MLflow Experiment Tracking
        </div>
        {mlflowRun.run_id ? (
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <StatusDot status="healthy" />
              <span className="font-mono text-xs" style={{ color: 'var(--text-primary)' }}>
                Run: {mlflowRun.run_id?.substring(0, 12)}...
              </span>
              <span className="cyber-badge cyber-badge-green ml-auto text-[0.5rem]">{mlflowRun.status}</span>
            </div>
            {/* Metrics */}
            {mlflowRun.metrics && Object.keys(mlflowRun.metrics).length > 0 && (
              <div className="grid grid-cols-3 gap-2 mt-2">
                {Object.entries(mlflowRun.metrics).slice(0, 6).map(([k, v]) => (
                  <div key={k} className="p-1.5 rounded text-center" style={{ background: 'rgba(0,243,255,0.06)' }}>
                    <div className="font-mono text-[0.5rem] uppercase" style={{ color: 'var(--text-muted)' }}>{k.replace(/_/g, ' ')}</div>
                    <div className="font-mono text-xs font-bold" style={{ color: 'var(--cyan)' }}>
                      {typeof v === 'number' ? (v % 1 === 0 ? v : v.toFixed(3)) : v}
                    </div>
                  </div>
                ))}
              </div>
            )}
            {/* Params */}
            {mlflowRun.params && Object.keys(mlflowRun.params).length > 0 && (
              <div className="mt-2">
                <div className="font-mono text-[0.5rem] uppercase mb-1" style={{ color: 'var(--text-muted)' }}>Parameters</div>
                <div className="flex flex-wrap gap-1">
                  {Object.entries(mlflowRun.params).slice(0, 8).map(([k, v]) => (
                    <span key={k} className="cyber-badge text-[0.5rem]" style={{ background: 'rgba(131,56,236,0.12)', color: 'var(--purple)' }}>
                      {k}: {v}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="flex items-center gap-2">
            <StatusDot status="unknown" />
            <span className="font-mono text-xs" style={{ color: 'var(--text-muted)' }}>
              {mlflowRun.error || 'No runs recorded yet -- run the Databricks pipeline notebook to populate'}
            </span>
          </div>
        )}
      </div>
    </div>
  )
}
