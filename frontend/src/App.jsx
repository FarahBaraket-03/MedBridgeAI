import { useState, useEffect } from 'react'
import Header from './components/Header'
import StatsBar from './components/StatsBar'
import QueryInput from './components/QueryInput'
import ReasoningTrace from './components/ReasoningTrace'
import ResultsPanel from './components/ResultsPanel'
import MapView from './components/MapView'
import PlanningPanel from './components/PlanningPanel'
import RoutingMap from './components/RoutingMap'
import ExplainPanel from './components/ExplainPanel'
import { queryApi, fetchStats, fetchFacilities } from './api/client'

const EXAMPLE_QUERIES = [
  "Where are the medical deserts in Ghana?",
  "Which regions lack emergency care?",
  "Find suspicious facility capability claims",
  "How many hospitals offer cardiology services?",
  "Where should we deploy mobile eye care units?",
  "Compare healthcare access: Accra vs Northern Region",
  "Which facilities can handle trauma patients near Kumasi?",
  "Find coverage gaps for maternal health services",
]

export default function App() {
  const [stats, setStats] = useState(null)
  const [facilities, setFacilities] = useState([])
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('results')
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [viewMode, setViewMode] = useState('dashboard') // 'dashboard' | 'routing-map'

  useEffect(() => {
    fetchStats().then(setStats).catch(console.error)
    fetchFacilities()
      .then(data => setFacilities(data.facilities || []))
      .catch(console.error)
  }, [])

  const handleQuery = async (q) => {
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const res = await queryApi(q)
      setResult(res)
      // Auto-switch to map tab for geospatial/planning intents, results for others
      const geoIntents = ['distance_query', 'coverage_gap', 'medical_desert', 'planning']
      if (geoIntents.includes(res.intent) || res.agents_used?.includes('geospatial') || res.agents_used?.includes('planning')) {
        setActiveTab('map')
      } else {
        setActiveTab('results')
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const mapFacilities = extractMapFacilities(result, facilities)
  const routeData = extractRouteData(result)
  const { deserts: medicalDeserts, coldSpots } = extractDesertData(result)

  // ── Full-screen Routing Map mode ─────────────────────────────────────
  if (viewMode === 'routing-map') {
    return (
      <div className="flex flex-col" style={{ height: '100vh', background: 'var(--bg-deep)' }}>
        <div className="grid-background"></div>
        {/* Minimal top bar with back button */}
        <div className="flex items-center gap-3 px-4 py-2" style={{
          background: 'var(--bg-main)', borderBottom: '1px solid var(--border-dim)', zIndex: 10,
        }}>
          <button onClick={() => setViewMode('dashboard')}
            className="font-mono" style={{
              background: 'rgba(0,243,255,0.08)', border: '1px solid var(--border-med)',
              color: 'var(--cyan)', padding: '6px 14px', borderRadius: 6,
              cursor: 'pointer', fontWeight: 600, fontSize: '0.75rem',
              letterSpacing: '0.08em',
            }}>◂ Dashboard</button>
          <div className="flex items-center gap-2">
            <span className="font-mono text-sm font-bold" style={{ color: 'var(--cyan)' }}>⚕ VIRTUE AI</span>
            <span className="font-mono text-xs" style={{ color: 'var(--text-muted)' }}>— Routing & Reasoning Map</span>
          </div>
        </div>
        <div style={{ flex: 1, position: 'relative' }}>
          <RoutingMap />
        </div>
      </div>
    )
  }

  // ── Dashboard mode ───────────────────────────────────────────────────
  return (
    <div className="min-h-screen flex flex-col" style={{ background: 'var(--bg-deep)' }}>
      <div className="grid-background"></div>
      <Header onOpenRoutingMap={() => setViewMode('routing-map')} />

      <main className="flex-1 flex overflow-hidden">
        {/* ── Left Sidebar: Planning Scenarios ───────────────── */}
        <aside
          className="shrink-0 overflow-y-auto transition-all duration-300"
          style={{
            width: sidebarOpen ? '280px' : '0px',
            minWidth: sidebarOpen ? '280px' : '0px',
            background: 'var(--bg-main)',
            borderRight: '1px solid var(--border-dim)',
            padding: sidebarOpen ? '16px' : '0px',
            opacity: sidebarOpen ? 1 : 0,
          }}
        >
          <PlanningPanel onRunScenario={handleQuery} loading={loading} />
        </aside>

        {/* ── Sidebar toggle ─────────────────────────────────── */}
        <button
          className="shrink-0 w-5 flex items-center justify-center cursor-pointer transition-colors"
          style={{
            background: 'var(--bg-card)',
            borderRight: '1px solid var(--border-dim)',
            color: 'var(--text-muted)',
          }}
          onClick={() => setSidebarOpen(!sidebarOpen)}
          title={sidebarOpen ? 'Collapse sidebar' : 'Expand sidebar'}
        >
          <span className="font-mono text-[0.6rem]">{sidebarOpen ? '◂' : '▸'}</span>
        </button>

        {/* ── Main Content ───────────────────────────────────── */}
        <div className="flex-1 flex flex-col overflow-y-auto" style={{ background: 'var(--bg-deep)' }}>
          <div className="p-4 space-y-4 max-w-6xl mx-auto w-full">
            {/* Stats */}
            <StatsBar stats={stats} />

            {/* Query */}
            <QueryInput
              onSubmit={handleQuery}
              loading={loading}
              examples={EXAMPLE_QUERIES}
            />

            {/* Error */}
            {error && (
              <div
                className="glass-card neon-border-pink p-4 flex items-center gap-3"
              >
                <span style={{ color: 'var(--pink)' }}>⚠</span>
                <span className="text-sm" style={{ color: 'var(--text-primary)' }}>{error}</span>
              </div>
            )}

            {/* Loading indicator */}
            {loading && (
              <div className="glass-card p-6 flex flex-col items-center gap-3">
                <div className="cyber-spinner" style={{ width: 32, height: 32, borderWidth: 3 }}></div>
                <span className="font-mono text-xs tracking-wider" style={{ color: 'var(--cyan)' }}>
                  ANALYZING...
                </span>
              </div>
            )}

            {/* Results area */}
            {result && !loading && (
              <div className="space-y-4 animate-fade-in-up">
                {/* Agent badges + timing */}
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-mono text-[0.6rem] tracking-[0.12em] uppercase" style={{ color: 'var(--text-muted)' }}>
                    Agents:
                  </span>
                  {result.agents_used?.map(a => (
                    <span key={a} className={`cyber-badge ${agentBadge(a)}`}>{a}</span>
                  ))}
                  <span className="font-mono text-[0.6rem] ml-auto" style={{ color: 'var(--text-muted)' }}>
                    {result.total_duration_ms?.toFixed(0)}ms
                  </span>
                </div>

                {/* Tabs */}
                <div className="flex gap-0 rounded-lg overflow-hidden" style={{ border: '1px solid var(--border-dim)' }}>
                  {['results', 'explain', 'trace', 'map'].map(tab => (
                    <button
                      key={tab}
                      className={`cyber-tab flex-1 ${activeTab === tab ? 'active' : ''}`}
                      onClick={() => setActiveTab(tab)}
                    >
                      {tab === 'results' ? '◈ Results' : tab === 'explain' ? '📋 Explain' : tab === 'trace' ? '⟐ Trace' : '◎ Map'}
                    </button>
                  ))}
                </div>

                {/* AI Summary — plain language for NGO planners */}
                {result.summary && (
                  <div
                    className="glass-card p-5 space-y-2"
                    style={{
                      borderLeft: '3px solid var(--cyan)',
                      background: 'linear-gradient(135deg, rgba(0,243,255,0.06), rgba(131,56,236,0.04))',
                    }}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <span style={{ fontSize: '1rem' }}>💡</span>
                      <span
                        className="font-mono text-[0.65rem] tracking-[0.15em] uppercase font-bold"
                        style={{ color: 'var(--cyan)' }}
                      >
                        AI Summary
                      </span>
                      <span className="cyber-badge cyber-badge-cyan ml-auto" style={{ fontSize: '0.55rem' }}>
                        Groq LLM
                      </span>
                    </div>
                    <p
                      className="text-sm leading-relaxed"
                      style={{ color: 'var(--text-primary)', whiteSpace: 'pre-wrap' }}
                    >
                      {result.summary}
                    </p>
                  </div>
                )}

                {activeTab === 'results' && <ResultsPanel result={result} />}
                {activeTab === 'explain' && <ExplainPanel result={result} />}
                {activeTab === 'trace' && <ReasoningTrace trace={result.trace} />}
                {activeTab === 'map' && (
                  <div className="h-[500px] rounded-xl overflow-hidden neon-border">
                    <MapView facilities={mapFacilities} routeData={routeData} medicalDeserts={medicalDeserts} coldSpots={coldSpots} />
                  </div>
                )}
              </div>
            )}

            {/* Default Map when no result */}
            {!result && !loading && facilities.length > 0 && (
              <div className="glass-card p-4">
                <div className="flex items-center gap-2 mb-3">
                  <span className="font-mono text-[0.6rem] tracking-[0.15em] uppercase font-semibold" style={{ color: 'var(--text-muted)' }}>
                    ▸ All Facilities
                  </span>
                  <span className="cyber-badge cyber-badge-cyan">{facilities.length} mapped</span>
                </div>
                <div className="h-[450px] rounded-xl overflow-hidden neon-border">
                  <MapView facilities={facilities} />
                </div>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer
        className="py-3 px-6 text-center"
        style={{ background: 'var(--bg-main)', borderTop: '1px solid var(--border-dim)' }}
      >
        <p className="font-mono text-[0.6rem] tracking-[0.1em] uppercase" style={{ color: 'var(--text-muted)' }}>
          VIRTUE AI v2.0 — Virtue Foundation × Databricks × AI Tinkerers Hackathon
        </p>
      </footer>
    </div>
  )
}

function agentBadge(name) {
  const map = {
    genie: 'cyber-badge-green',
    vector_search: 'cyber-badge-purple',
    medical_reasoning: 'cyber-badge-pink',
    geospatial: 'cyber-badge-yellow',
    planning: 'cyber-badge-orange',
    supervisor: 'cyber-badge-cyan',
  }
  return map[name] || 'cyber-badge-cyan'
}

function toArray(val) {
  return Array.isArray(val) ? val : []
}

function extractMapFacilities(result, allFacilities) {
  const resp = result?.response
  if (!resp) return allFacilities

  // 1. Use aggregator's merged _map_facilities if available (best source)
  if (Array.isArray(resp._map_facilities) && resp._map_facilities.length > 0) {
    return resp._map_facilities.filter(f => f && f.latitude != null && f.longitude != null)
  }

  // 2. Dig into multi-agent results
  if (resp.multi_agent_response && resp.results) {
    // Check for _map_facilities inside multi-agent wrapper
    if (Array.isArray(resp.results?._map_facilities) && resp.results._map_facilities.length > 0) {
      return resp.results._map_facilities.filter(f => f && f.latitude != null && f.longitude != null)
    }
    // Collect from all agents
    let collected = []
    for (const agentData of Object.values(resp.results || {})) {
      if (!agentData || typeof agentData !== 'object') continue
      collected.push(...extractFacilitiesFromAgent(agentData))
    }
    const withCoords = collected.filter(f => f && f.latitude != null && f.longitude != null)
    if (withCoords.length > 0) return withCoords
  }

  // 3. Single agent response
  const fromAgent = extractFacilitiesFromAgent(resp)
  const withCoords = fromAgent.filter(f => f && f.latitude != null && f.longitude != null)
  if (withCoords.length > 0) return withCoords

  return allFacilities
}

function extractFacilitiesFromAgent(data) {
  if (!data || typeof data !== 'object') return []
  const all = []

  // All known list keys that may contain map-displayable items
  for (const key of ['facilities', 'results', 'flagged_facilities', 'stops',
    'placements', 'suggestions', 'worst_cold_spots', 'alternatives', 'anomalies', 'regions']) {
    const items = toArray(data[key])
    for (const item of items) {
      if (!item || typeof item !== 'object') continue
      const lat = item.latitude ?? item.lat ?? item.center_lat ?? item.suggested_lat ?? item.grid_lat
      const lng = item.longitude ?? item.lng ?? item.center_lng ?? item.suggested_lng ?? item.grid_lng
      if (lat != null && lng != null) {
        all.push({
          name: item.name || item.facility || item.region || 'Unknown',
          latitude: lat,
          longitude: lng,
          city: item.city || item.address_city,
          region: item.region || item.address_stateOrRegion,
          specialties: item.specialties || [],
          type: item.type || item.facilityTypeId,
          distance_km: item.distance_km || item.distance_from_prev_km,
        })
      }
    }
  }

  // Single-facility fields
  for (const key of ['primary_facility', 'backup_facility']) {
    const pf = data[key]
    if (pf && typeof pf === 'object') {
      const lat = pf.latitude ?? pf.lat
      const lng = pf.longitude ?? pf.lng
      if (lat != null && lng != null) {
        all.push({
          name: pf.facility || pf.name, latitude: lat, longitude: lng,
          city: pf.city, region: pf.region, specialties: pf.specialties || [],
          type: pf.type, distance_km: pf.distance_km,
        })
      }
    }
  }

  return all
}

function extractRouteData(result) {
  const resp = result?.response
  if (!resp) return null

  // Check for route data in multi-agent response
  if (resp.multi_agent_response && resp.results) {
    for (const agentData of Object.values(resp.results)) {
      if (!agentData || typeof agentData !== 'object') continue
      if (agentData.route) return agentData.route
      // Build route from planning stops
      if (agentData.stops && Array.isArray(agentData.stops)) {
        return agentData.stops
          .filter(s => s.latitude != null && s.longitude != null)
          .map(s => ({ lat: s.latitude, lng: s.longitude, name: s.facility || s.name, city: s.city }))
      }
    }
  }

  if (resp.route) return resp.route
  // Build route from planning stops at top level
  if (resp.stops && Array.isArray(resp.stops)) {
    return resp.stops
      .filter(s => s.latitude != null && s.longitude != null)
      .map(s => ({ lat: s.latitude, lng: s.longitude, name: s.facility || s.name, city: s.city }))
  }
  return null
}

function extractDesertData(result) {
  const empty = { deserts: [], coldSpots: [] }
  const resp = result?.response
  if (!resp) return empty

  let deserts = []
  let coldSpots = []

  const scan = (obj) => {
    if (!obj || typeof obj !== 'object') return
    if (Array.isArray(obj.deserts) && obj.deserts.length) deserts = obj.deserts
    if (Array.isArray(obj.worst_cold_spots) && obj.worst_cold_spots.length) coldSpots = obj.worst_cold_spots
    // Also check for coverage gaps from medical reasoning
    if (Array.isArray(obj.gaps) && obj.gaps.length && deserts.length === 0) {
      deserts = obj.gaps.filter(g => g.region).map(g => ({
        region: g.region,
        severity: g.gap_severity || 'medium',
        nearest_distance_km: 0,
        center_lat: null,
        center_lng: null,
      }))
    }
  }

  // Check multi-agent results
  if (resp.multi_agent_response && resp.results) {
    for (const agentData of Object.values(resp.results)) {
      scan(agentData)
    }
  }
  // Check top-level
  scan(resp)

  return { deserts, coldSpots }
}
