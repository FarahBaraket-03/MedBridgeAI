import { useState, useEffect } from 'react'
import Header from './components/Header'
import StatsBar from './components/StatsBar'
import QueryInput from './components/QueryInput'
import ReasoningTrace from './components/ReasoningTrace'
import ResultsPanel from './components/ResultsPanel'
import MapView from './components/MapView'
import PlanningPanel from './components/PlanningPanel'
import ExplainPanel from './components/ExplainPanel'
import MLOpsDashboard from './components/MLOpsDashboard'
import { queryApi, fetchStats, fetchFacilities } from './api/client'
import renderMarkdown from './utils/renderMarkdown'

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
  const placementSuggestions = extractPlacementSuggestions(result)

  return (
    <div className="min-h-screen flex flex-col" style={{ background: 'var(--bg-deep)' }}>
      <div className="grid-background"></div>
      <Header />

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
                <span className="text-sm flex-1" style={{ color: 'var(--text-primary)' }}>{error}</span>
                <button
                  onClick={() => { setError(null); if (result?.query) handleQuery(result.query) }}
                  className="cyber-badge cyber-badge-cyan cursor-pointer hover:opacity-80 transition-opacity"
                >
                  ↻ Retry
                </button>
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
                  <button
                    onClick={() => exportResultsCSV(result)}
                    className="cyber-badge cyber-badge-green cursor-pointer hover:opacity-80 transition-opacity"
                    title="Export results as CSV"
                  >
                    ⬇ CSV
                  </button>
                </div>

                {/* Tabs */}
                <div className="flex gap-0 rounded-lg overflow-hidden" style={{ border: '1px solid var(--border-dim)' }}>
                  {['results', 'explain', 'trace', 'map', 'mlops'].map(tab => (
                    <button
                      key={tab}
                      className={`cyber-tab flex-1 ${activeTab === tab ? 'active' : ''}`}
                      onClick={() => setActiveTab(tab)}
                    >
                      {tab === 'results' ? '◈ Results' : tab === 'explain' ? '📋 Explain' : tab === 'trace' ? '⟐ Trace' : tab === 'map' ? '◎ Map' : '⚙ MLOps'}
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
                    <div
                      className="text-sm leading-relaxed"
                      style={{ color: 'var(--text-primary)' }}
                    >
                      {renderMarkdown(result.summary, { textColor: 'var(--text-secondary)', boldColor: 'var(--text-primary)' })}
                    </div>
                  </div>
                )}

                {activeTab === 'results' && <ResultsPanel result={result} />}
                {activeTab === 'explain' && <ExplainPanel result={result} />}
                {activeTab === 'trace' && <ReasoningTrace trace={result.trace} />}
                {activeTab === 'map' && (
                  <div style={{ height: '550px' }} className="rounded-xl overflow-hidden neon-border">
                    <MapView facilities={mapFacilities} routeData={routeData} medicalDeserts={medicalDeserts} coldSpots={coldSpots} placementSuggestions={placementSuggestions} />
                  </div>
                )}
                {activeTab === 'mlops' && <MLOpsDashboard />}
              </div>
            )}

            {/* Default Map when no result */}
            {!result && !loading && facilities.length > 0 && activeTab !== 'mlops' && (
              <div className="glass-card p-4">
                <div className="flex items-center gap-2 mb-3">
                  <span className="font-mono text-[0.6rem] tracking-[0.15em] uppercase font-semibold" style={{ color: 'var(--text-muted)' }}>
                    ▸ All Facilities
                  </span>
                  <span className="cyber-badge cyber-badge-cyan">{facilities.length} mapped</span>
                </div>
                <div style={{ height: '500px' }} className="rounded-xl overflow-hidden neon-border">
                  <MapView facilities={facilities} />
                </div>
              </div>
            )}

            {/* MLOps dashboard accessible even without a query */}
            {!result && !loading && activeTab === 'mlops' && <MLOpsDashboard />}

            {/* Quick-access MLOps tab button when idle */}
            {!result && !loading && activeTab !== 'mlops' && (
              <div className="flex justify-center">
                <button
                  onClick={() => setActiveTab('mlops')}
                  className="cyber-badge cyber-badge-purple cursor-pointer hover:opacity-80 transition-opacity"
                >
                  ⚙ Open MLOps Dashboard
                </button>
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
        <p className="font-mono text-[0.6rem] tracking-widest uppercase" style={{ color: 'var(--text-muted)' }}>
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

function extractPlacementSuggestions(result) {
  const resp = result?.response
  if (!resp) return []

  const extract = (data) => {
    if (!data || typeof data !== 'object') return []
    if ((data.action === 'new_facility_placement' || data.scenario === 'new_facility_placement') && Array.isArray(data.suggestions)) {
      return data.suggestions.filter(s => (s.suggested_lat ?? s.latitude) != null && (s.suggested_lng ?? s.longitude) != null)
    }
    return []
  }

  // Multi-agent
  if (resp.multi_agent_response && resp.results) {
    for (const agentData of Object.values(resp.results)) {
      const found = extract(agentData)
      if (found.length > 0) return found
    }
  }

  return extract(resp)
}

function exportResultsCSV(result) {
  if (!result?.response) return

  const resp = result.response
  let rows = []
  let headers = []

  // Collect facility-like data from the response
  const collectRows = (data) => {
    if (!data || typeof data !== 'object') return

    // Try known list keys
    for (const key of ['facilities', 'results', 'flagged_facilities', 'stops',
      'placements', 'suggestions', 'worst_cold_spots', 'anomalies', 'regions', 'deserts']) {
      const items = Array.isArray(data[key]) ? data[key] : []
      if (items.length > 0 && typeof items[0] === 'object') {
        rows = items
        return
      }
    }
  }

  if (resp.multi_agent_response && resp.results) {
    for (const agentData of Object.values(resp.results)) {
      collectRows(agentData)
      if (rows.length > 0) break
    }
  } else {
    collectRows(resp)
  }

  if (rows.length === 0) {
    // Fallback: export the summary as a single-row CSV
    rows = [{ query: result.query, intent: result.intent, summary: result.summary }]
  }

  // Build headers from all keys across all rows
  const keySet = new Set()
  rows.forEach(r => Object.keys(r).forEach(k => {
    if (typeof r[k] !== 'object' || r[k] === null) keySet.add(k)
    else if (Array.isArray(r[k])) keySet.add(k)
  }))
  headers = [...keySet]

  const escape = (val) => {
    if (val == null) return ''
    const str = Array.isArray(val) ? val.join('; ') : String(val)
    return str.includes(',') || str.includes('"') || str.includes('\n')
      ? `"${str.replace(/"/g, '""')}"` : str
  }

  const csv = [
    headers.join(','),
    ...rows.map(r => headers.map(h => escape(r[h])).join(','))
  ].join('\n')

  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `medbridge_${result.intent || 'results'}_${Date.now()}.csv`
  a.click()
  URL.revokeObjectURL(url)
}
