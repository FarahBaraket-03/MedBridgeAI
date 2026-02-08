// ────────────────────────────────────────────────────────────────
// ResultsPanel — Cyberpunk-styled results display
// ────────────────────────────────────────────────────────────────

import { useState } from 'react'
import renderMarkdown from '../utils/renderMarkdown'

export default function ResultsPanel({ result }) {
  if (!result) return null

  const response = result.response

  // Multi-agent response
  if (response?.multi_agent_response) {
    const agentColors = {
      genie: { color: 'var(--green)', icon: '◈', label: 'Data Analysis' },
      vector_search: { color: 'var(--purple)', icon: '⟐', label: 'Facility Search' },
      medical_reasoning: { color: 'var(--pink)', icon: '✦', label: 'Medical Analysis' },
      geospatial: { color: 'var(--yellow)', icon: '◉', label: 'Geographic Analysis' },
      planning: { color: 'var(--orange)', icon: '⬡', label: 'Planning & Routing' },
    }
    return (
      <div className="space-y-4">
        {Object.entries(response.results || {}).map(([agent, data]) => {
          const ac = agentColors[agent] || { color: 'var(--cyan)', icon: '▸', label: agent.replace(/_/g, ' ') }
          return (
            <div key={agent} className="glass-card p-4" style={{ borderLeft: `3px solid ${ac.color}` }}>
              <div className="flex items-center gap-2 mb-3">
                <span style={{ fontSize: '0.9rem' }}>{ac.icon}</span>
                <span className="font-mono text-xs font-bold tracking-wider" style={{ color: ac.color }}>
                  {ac.label.toUpperCase()}
                </span>
              </div>
              <AgentResult data={data} />
            </div>
          )
        })}
      </div>
    )
  }

  // Single-agent response
  return (
    <div className="glass-card p-4">
      <AgentResult data={response} />
    </div>
  )
}

function AgentResult({ data }) {
  if (!data) return <p className="font-mono text-xs" style={{ color: 'var(--text-muted)' }}>No data</p>

  const action = data.action || ''

  // Count / simple result
  if (data.count != null && (data.results || data.facilities)) {
    const items = data.results || data.facilities || []
    return (
      <div className="space-y-3">
        <div className="flex items-center gap-4">
          <span className="stat-number neon-text">{data.count}</span>
          <span className="font-mono text-xs uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>
            {action.replace(/_/g, ' ') || 'facilities found'}
          </span>
        </div>
        <FacilityTable facilities={items} />
        <Citations citations={data.citations} />
      </div>
    )
  }

  // Anomaly detection
  if (action === 'anomaly_detection') {
    return (
      <div className="space-y-3">
        <div className="flex gap-6 flex-wrap">
          <StatBlock value={data.anomalies_found} label="SUSPICIOUS FACILITIES" color="var(--yellow)" />
          <StatBlock value={data.total_checked} label="TOTAL CHECKED" color="var(--cyan)" />
        </div>
        {data.anomalies_found > 0 && (
          <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>
            We scanned all facilities and found <strong style={{ color: 'var(--yellow)' }}>{data.anomalies_found}</strong> with suspicious data patterns.
            These may have inflated stats or unusual resource combinations.
          </p>
        )}
        {data.results?.map((r, i) => (
          <div key={i} className="rounded-lg p-3" style={{ background: 'var(--bg-surface)', borderLeft: '3px solid var(--yellow)' }}>
            <div className="flex justify-between items-start">
              <div>
                <h4 className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>{r.facility}</h4>
                <p className="text-xs font-mono" style={{ color: 'var(--text-muted)' }}>{r.city}{r.region ? ` • ${r.region}` : ''}</p>
              </div>
              <div className="flex gap-2 items-center">
                {(() => {
                  // Convert raw anomaly scores to a human-readable risk percentage
                  const rawIF = r.anomaly_score != null ? parseFloat(r.anomaly_score) : null
                  const rawMaha = r.mahalanobis_distance != null ? parseFloat(r.mahalanobis_distance) : null
                  // IF score: more negative = more anomalous. Typical range: -0.5 to 0.3
                  // Mahalanobis: higher = more anomalous. Typical threshold ~16.8 (chi2 p=0.01)
                  let riskPct = 50
                  if (rawIF != null) {
                    riskPct = Math.round(Math.min(100, Math.max(0, (1 - (rawIF + 0.5)) * 80)))
                  }
                  if (rawMaha != null) {
                    riskPct = Math.round(Math.min(100, Math.max(riskPct, (rawMaha / 16.8) * 100)))
                  }
                  const riskColor = riskPct >= 75 ? 'cyber-badge-pink' : riskPct >= 40 ? 'cyber-badge-yellow' : 'cyber-badge-green'
                  const riskLabel = riskPct >= 75 ? 'High Risk' : riskPct >= 40 ? 'Medium Risk' : 'Low Risk'
                  return (
                    <span className={`cyber-badge ${riskColor}`}>
                      ⚠ {riskPct}% — {riskLabel}
                    </span>
                  )
                })()}
              </div>
            </div>
            <ul className="mt-2 space-y-0.5">
              {r.reasons?.map((reason, j) => (
                <li key={j} className="text-xs flex items-start gap-1" style={{ color: 'var(--text-secondary)' }}>
                  <span style={{ color: 'var(--yellow)' }}>▸</span> {reason}
                </li>
              ))}
            </ul>
          </div>
        ))}
        <Citations citations={data.citations} />
      </div>
    )
  }

  // Constraint validation
  if (action === 'constraint_validation') {
    return (
      <div className="space-y-3">
        <div className="flex gap-6">
          <StatBlock value={data.facilities_with_issues} label="ISSUES FOUND" color="var(--pink)" />
          <StatBlock value={data.total_checked} label="TOTAL CHECKED" color="var(--cyan)" />
          {data.summary?.avg_confidence != null && (
            <StatBlock value={`${(data.summary.avg_confidence * 100).toFixed(0)}%`} label="DATA QUALITY" color="var(--green)" />
          )}
        </div>
        {data.facilities_with_issues > 0 && (
          <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>
            These facilities have data or capability issues that may need attention.
          </p>
        )}
        {data.flagged_facilities?.map((f, i) => (
          <div key={i} className="rounded-lg p-3" style={{ background: 'var(--bg-surface)', borderLeft: '3px solid var(--pink)' }}>
            <div className="flex justify-between items-start">
              <h4 className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>{f.facility}</h4>
              <ConfidenceBadge value={f.confidence} />
            </div>
            <div className="mt-2 space-y-1">
              {f.issues?.map((issue, j) => (
                <div key={j} className="text-xs flex items-start gap-2" style={{ color: 'var(--text-secondary)' }}>
                  <span className={`cyber-badge ${issue.severity === 'high' ? 'cyber-badge-pink' : 'cyber-badge-yellow'}`}>
                    {issue.severity}
                  </span>
                  <span>{issue.message}</span>
                </div>
              ))}
            </div>
          </div>
        ))}
        <Citations citations={data.citations} />
      </div>
    )
  }

  // Coverage gaps
  if (action === 'coverage_gap_analysis' && (data.coverage_percentage != null || data.gaps_found != null)) {
    return (
      <div className="space-y-3">
        <div className="flex gap-6 flex-wrap">
          {data.coverage_percentage != null && (
            <StatBlock value={`${data.coverage_percentage}%`} label="AREA COVERED" color="var(--cyan)" />
          )}
          {data.gaps_found != null && (
            <StatBlock value={data.gaps_found} label="UNDERSERVED AREAS" color="var(--pink)" />
          )}
          {data.cold_spots_found != null && (
            <StatBlock value={data.cold_spots_found} label="CRITICAL GAPS" color="var(--pink)" />
          )}
          {data.regions_analyzed != null && (
            <StatBlock value={data.regions_analyzed} label="REGIONS ANALYZED" color="var(--cyan)" />
          )}
        </div>
        {data.gaps_found > 0 && (
          <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>
            These areas have very few healthcare facilities. Residents may lack access to essential services.
          </p>
        )}
        {/* Show gaps from medical reasoning */}
        {data.gaps?.map((g, i) => (
          <div key={i} className="flex justify-between items-center py-2 px-3 rounded" style={{ background: 'var(--bg-surface)', borderLeft: `3px solid ${g.gap_severity === 'high' ? 'var(--pink)' : g.gap_severity === 'critical' ? 'var(--pink)' : 'var(--yellow)'}` }}>
            <div>
              <span className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>
                {g.region}
              </span>
              <span className="text-xs ml-2" style={{ color: 'var(--text-muted)' }}>
                {g.total_facilities} {g.total_facilities === 1 ? 'facility' : 'facilities'} • {g.specialty_count} {g.specialty_count === 1 ? 'specialty' : 'specialties'}
              </span>
            </div>
            <span className={`cyber-badge ${g.gap_severity === 'high' || g.gap_severity === 'critical' ? 'cyber-badge-pink' : 'cyber-badge-yellow'}`}>
              {g.gap_severity === 'high' ? '⚠ High Gap' : g.gap_severity === 'critical' ? '⚠ Critical' : 'Low Coverage'}
            </span>
          </div>
        ))}
        {/* Show cold spots with human description */}
        {data.worst_cold_spots?.map((spot, i) => (
          <div key={i} className="flex justify-between items-center py-2 px-3 rounded" style={{ background: 'var(--bg-surface)' }}>
            <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>
              Nearest to this area: <strong style={{ color: 'var(--text-primary)' }}>{spot.nearest_facility}</strong>
            </span>
            <span className="cyber-badge cyber-badge-pink">{spot.distance_km?.toFixed(0)} km away</span>
          </div>
        ))}
      </div>
    )
  }

  // Medical deserts
  if (action === 'medical_desert_detection') {
    return (
      <div className="space-y-3">
        <div className="flex gap-6 flex-wrap">
          <StatBlock value={data.deserts_found} label="UNDERSERVED AREAS" color="var(--pink)" />
          <StatBlock value={data.regions_analyzed || '—'} label="REGIONS ANALYZED" color="var(--cyan)" />
        </div>
        {data.deserts_found > 0 && (
          <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>
            These regions have <strong style={{ color: 'var(--pink)' }}>no nearby healthcare facilities</strong> within {data.threshold_km || 75} km.
            Residents must travel long distances for medical care.
          </p>
        )}
        {data.deserts?.map((d, i) => (
          <div key={i} className="rounded-lg p-3 flex justify-between items-center" style={{ background: 'var(--bg-surface)', borderLeft: `3px solid ${d.severity === 'critical' ? 'var(--pink)' : d.severity === 'high' ? 'var(--yellow)' : 'var(--green)'}` }}>
            <div>
              <h4 className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>{d.region}</h4>
              <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
                Nearest facility is <strong style={{ color: 'var(--pink)' }}>{d.nearest_distance_km?.toFixed(0) || '?'} km</strong> away
              </p>
            </div>
            <span className={`cyber-badge ${d.severity === 'critical' ? 'cyber-badge-pink' : d.severity === 'high' ? 'cyber-badge-yellow' : 'cyber-badge-green'}`}>
              {d.severity === 'critical' ? '⚠ Critical' : d.severity === 'high' ? '⚠ High' : 'Moderate'}
            </span>
          </div>
        ))}
      </div>
    )
  }

  // Regional equity
  if (action === 'regional_equity_analysis') {
    return (
      <div className="space-y-2">
        <div className="flex items-center gap-2 mb-2">
          <span className="font-mono text-[0.6rem] tracking-[0.15em] uppercase" style={{ color: 'var(--text-muted)' }}>
            ▸ Regional Analysis
          </span>
        </div>
        {data.regions?.map((r, i) => (
          <div key={i} className="flex justify-between items-center py-2 px-3 rounded text-sm"
               style={{ background: i % 2 === 0 ? 'var(--bg-surface)' : 'transparent' }}>
            <span className="font-medium" style={{ color: 'var(--text-primary)' }}>{r.region}</span>
            <div className="flex gap-4 text-xs" style={{ color: 'var(--text-secondary)' }}>
              <span><span style={{ color: 'var(--cyan)' }}>{r.total_facilities}</span> facilities</span>
              <span><span style={{ color: 'var(--green)' }}>{r.total_doctors}</span> doctors</span>
              <span><span style={{ color: 'var(--purple)' }}>{r.total_beds}</span> beds</span>
              <span><span style={{ color: 'var(--yellow)' }}>{r.unique_specialties}</span> specialties</span>
            </div>
          </div>
        ))}
      </div>
    )
  }

  // Red flags
  if (action === 'red_flag_detection') {
    return (
      <div className="space-y-3">
        <StatBlock value={data.facilities_flagged} label="FACILITIES WITH CONCERNS" color="var(--yellow)" />
        {data.facilities_flagged > 0 && (
          <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>
            These facilities have data inconsistencies or concerning patterns that warrant review.
          </p>
        )}
        {data.results?.map((f, i) => (
          <div key={i} className="rounded-lg p-3" style={{ background: 'var(--bg-surface)', borderLeft: '3px solid var(--yellow)' }}>
            <h4 className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>{f.facility}</h4>
            <p className="text-xs" style={{ color: 'var(--text-muted)' }}>{f.city} — {renderMarkdown(f.recommendation, { textColor: 'var(--text-muted)', boldColor: 'var(--text-primary)' })}</p>
            <div className="flex flex-wrap gap-1 mt-1">
              {f.flags?.map((fl, j) => (
                <span key={j} className="cyber-badge cyber-badge-yellow">{fl.category}</span>
              ))}
            </div>
          </div>
        ))}
      </div>
    )
  }

  // Single point of failure
  if (action === 'single_point_of_failure') {
    return (
      <div className="space-y-3">
        <StatBlock value={data.critical_specialties} label="AT-RISK SPECIALTIES" color="var(--pink)" />
        <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>
          These specialties are offered by very few facilities. If one closes, patients may lose access entirely.
        </p>
        {data.results?.map((r, i) => (
          <div key={i} className="rounded-lg p-3" style={{ background: 'var(--bg-surface)', borderLeft: `3px solid ${r.risk_level === 'critical' ? 'var(--pink)' : 'var(--yellow)'}` }}>
            <div className="flex justify-between items-center">
              <h4 className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>{r.specialty}</h4>
              <span className={`cyber-badge ${r.risk_level === 'critical' ? 'cyber-badge-pink' : 'cyber-badge-yellow'}`}>
                Only {r.facility_count} {r.facility_count === 1 ? 'facility' : 'facilities'}
              </span>
            </div>
            <div className="text-xs mt-1" style={{ color: 'var(--text-secondary)' }}>
              Available at: {r.facilities?.map(f => f.name).join(', ')}
            </div>
          </div>
        ))}
      </div>
    )
  }

  // Planning results
  const scenario = data.scenario || ''
  if (action === 'emergency_routing' || action === 'specialist_deployment' || action === 'equipment_distribution' || action === 'new_facility_placement' || action === 'capacity_planning'
    || scenario === 'emergency_routing' || scenario === 'specialist_deployment' || scenario === 'equipment_distribution' || scenario === 'new_facility_placement' || scenario === 'capacity_planning') {
    return <PlanningResult data={data} action={action || scenario} />
  }

  // Semantic search results
  if (data.results && Array.isArray(data.results)) {
    return (
      <div className="space-y-3">
        {data.count != null && (
          <div className="flex items-center gap-4">
            <span className="stat-number neon-text">{data.count}</span>
            <span className="font-mono text-xs uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>
              {action.replace(/_/g, ' ')}
            </span>
          </div>
        )}
        <FacilityTable facilities={data.results} />
        <Citations citations={data.citations} />
      </div>
    )
  }

  // Aggregation results (from genie)
  if (data.aggregation) {
    return (
      <div className="space-y-3">
        {data.top_region && (
          <div className="flex items-center gap-3 mb-2">
            <span className="font-mono text-xs" style={{ color: 'var(--text-muted)' }}>TOP:</span>
            <span className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>{data.top_region}</span>
            <span className="cyber-badge cyber-badge-cyan">{data.top_count}</span>
          </div>
        )}
        {Object.entries(data.aggregation).map(([region, count], i) => (
          <div key={i} className="flex justify-between items-center py-2 px-3 rounded text-sm"
               style={{ background: i % 2 === 0 ? 'var(--bg-surface)' : 'transparent' }}>
            <span style={{ color: 'var(--text-primary)' }}>{region}</span>
            <span className="font-mono" style={{ color: 'var(--cyan)' }}>{count}</span>
          </div>
        ))}
      </div>
    )
  }

  // Distribution results (from genie specialty_distribution)
  if (data.distribution) {
    return (
      <div className="space-y-3">
        <StatBlock value={data.total_unique_specialties} label="UNIQUE SPECIALTIES" color="var(--cyan)" />
        {Object.entries(data.distribution).map(([spec, count], i) => (
          <div key={i} className="flex justify-between items-center py-1 px-3 rounded text-sm"
               style={{ background: i % 2 === 0 ? 'var(--bg-surface)' : 'transparent' }}>
            <span style={{ color: 'var(--text-primary)' }}>{spec}</span>
            <span className="font-mono" style={{ color: 'var(--cyan)' }}>{count}</span>
          </div>
        ))}
      </div>
    )
  }

  // Rare specialties / single point
  if (data.rare_specialties) {
    return (
      <div className="space-y-3">
        <StatBlock value={data.count} label="RARE SPECIALTIES" color="var(--pink)" />
        {Object.entries(data.rare_specialties).map(([spec, count], i) => (
          <div key={i} className="flex justify-between items-center py-1 px-3 rounded text-sm"
               style={{ background: 'var(--bg-surface)', borderLeft: `3px solid ${count === 1 ? 'var(--pink)' : 'var(--yellow)'}` }}>
            <span style={{ color: 'var(--text-primary)' }}>{spec}</span>
            <span className={`cyber-badge ${count === 1 ? 'cyber-badge-pink' : 'cyber-badge-yellow'}`}>{count} facility</span>
          </div>
        ))}
      </div>
    )
  }

  // Facilities list (from genie without count)
  if (data.facilities && Array.isArray(data.facilities) && data.facilities.length > 0) {
    return (
      <div className="space-y-3">
        <FacilityTable facilities={data.facilities} />
      </div>
    )
  }

  // Fallback: JSON dump
  return (
    <div className="rounded-lg p-3 overflow-x-auto" style={{ background: 'var(--bg-surface)' }}>
      <pre className="text-xs font-mono whitespace-pre-wrap" style={{ color: 'var(--text-secondary)' }}>
        {JSON.stringify(data, null, 2)}
      </pre>
    </div>
  )
}

/* ── Planning result sub-component ─────────────────────────── */
function PlanningResult({ data, action }) {
  return (
    <div className="space-y-3">
      {/* Emergency routing — primary & backup facility */}
      {action === 'emergency_routing' && data.primary_facility && (
        <div className="space-y-2">
          {/* Origin / starting point */}
          {data.origin && (
            <div className="rounded-lg p-3 flex items-center gap-3" style={{ background: 'var(--bg-surface)', borderLeft: '3px solid var(--green)' }}>
              <span className="text-lg">📍</span>
              <div>
                <span className="font-mono text-[0.6rem] tracking-wider" style={{ color: 'var(--green)' }}>STARTING POINT</span>
                <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>
                  Patient location ({data.origin.lat?.toFixed(2)}°N, {Math.abs(data.origin.lng)?.toFixed(2)}°W)
                </p>
              </div>
            </div>
          )}
          <div className="rounded-lg p-4 neon-border" style={{ background: 'var(--bg-surface)' }}>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-lg">🚑</span>
              <span className="font-mono text-xs font-bold tracking-wider neon-text">NEAREST RECOMMENDED FACILITY</span>
            </div>
            <h4 className="text-base font-semibold" style={{ color: 'var(--text-primary)' }}>
              {data.primary_facility.facility}
            </h4>
            <div className="text-xs" style={{ color: 'var(--text-muted)' }}>
              {data.primary_facility.city} • {data.primary_facility.region}
            </div>
            <div className="flex gap-4 mt-2 text-xs" style={{ color: 'var(--text-secondary)' }}>
              <span>Distance: <strong className="neon-text">{data.primary_facility.distance_km?.toFixed(1)} km</strong></span>
              <span>Travel: <strong className="neon-text">{data.primary_facility.est_travel_min} min</strong></span>
              <span>Match: <strong className="neon-text-green">{data.primary_facility.capability_match}%</strong></span>
            </div>
          </div>
          {data.backup_facility && (
            <div className="rounded-lg p-3" style={{ background: 'var(--bg-surface)', borderLeft: '3px solid var(--yellow)' }}>
              <span className="font-mono text-[0.6rem] tracking-wider" style={{ color: 'var(--yellow)' }}>BACKUP OPTION</span>
              <div className="text-sm font-medium mt-1" style={{ color: 'var(--text-primary)' }}>{data.backup_facility.facility}</div>
              <div className="text-xs" style={{ color: 'var(--text-muted)' }}>{data.backup_facility.city} — {data.backup_facility.distance_km?.toFixed(1)} km away</div>
            </div>
          )}
          {data.alternatives?.length > 0 && (
            <div className="space-y-1">
              <span className="font-mono text-[0.6rem] tracking-wider" style={{ color: 'var(--text-muted)' }}>MORE OPTIONS NEARBY</span>
              {data.alternatives.map((alt, i) => (
                <div key={i} className="flex justify-between items-center py-1 px-3 rounded text-xs" style={{ background: 'var(--bg-surface)' }}>
                  <span style={{ color: 'var(--text-primary)' }}>{alt.facility}</span>
                  <span className="cyber-badge cyber-badge-cyan">{alt.distance_km?.toFixed(1)} km</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Specialist deployment — stops */}
      {action === 'specialist_deployment' && data.stops && (
        <div className="space-y-2">
          <div className="flex gap-6 flex-wrap items-end">
            <StatBlock value={data.total_stops} label="STOPS" color="var(--cyan)" />
            <StatBlock value={`${data.total_distance_km?.toFixed(0)} km`} label="TOTAL DISTANCE" color="var(--green)" />
            <StatBlock value={`${data.est_total_days} days`} label="DURATION" color="var(--purple)" />
            {data.optimisation && (
              <span className="cyber-badge cyber-badge-purple mb-1" style={{ fontSize: '0.6rem' }}>🔄 {data.optimisation}</span>
            )}
          </div>
          {data.stops.map((stop, i) => (
            <div key={i} className="flex items-center gap-3 py-2 px-3 rounded" style={{ background: 'var(--bg-surface)' }}>
              <span className="font-mono text-xs font-bold w-6 text-center" style={{ color: 'var(--cyan)' }}>{stop.stop}</span>
              <div className="flex-1">
                <span className="text-sm" style={{ color: 'var(--text-primary)' }}>{stop.facility}</span>
                <span className="text-xs ml-2" style={{ color: 'var(--text-muted)' }}>{stop.city}</span>
              </div>
              <span className="cyber-badge cyber-badge-cyan">{stop.distance_from_prev_km?.toFixed(1)} km</span>
            </div>
          ))}
        </div>
      )}

      {/* Equipment distribution — placements */}
      {action === 'equipment_distribution' && data.placements && (
        <div className="space-y-2">
          <div className="flex gap-6">
            <StatBlock value={data.facilities_with} label="HAVE IT" color="var(--green)" />
            <StatBlock value={data.facilities_without} label="NEED IT" color="var(--pink)" />
          </div>
          {data.placements.map((p, i) => (
            <div key={i} className="flex items-center gap-3 py-2 px-3 rounded" style={{ background: 'var(--bg-surface)', borderLeft: `3px solid ${i < 3 ? 'var(--pink)' : 'var(--yellow)'}` }}>
              <span className="font-mono text-xs font-bold w-6 text-center" style={{ color: 'var(--pink)' }}>#{i + 1}</span>
              <div className="flex-1">
                <span className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>{p.recommended_facility}</span>
                <span className="text-xs ml-2" style={{ color: 'var(--text-muted)' }}>{p.region}</span>
              </div>
              <span className="cyber-badge cyber-badge-pink">{p.facilities_served} served</span>
            </div>
          ))}
        </div>
      )}

      {/* New facility placement — suggestions (maximin) */}
      {action === 'new_facility_placement' && data.suggestions && (
        <div className="space-y-2">
          <div className="flex gap-6 flex-wrap items-end">
            <StatBlock value={data.total_suggestions} label="SUGGESTED LOCATIONS" color="var(--cyan)" />
            {data.algorithm && (
              <span className="cyber-badge cyber-badge-purple mb-1" style={{ fontSize: '0.6rem' }}>📐 {data.algorithm}</span>
            )}
          </div>
          {data.suggestions.map((s, i) => (
            <div key={i} className="rounded-lg p-3" style={{ background: 'var(--bg-surface)', borderLeft: `3px solid ${s.priority === 'critical' ? 'var(--pink)' : s.priority === 'high' ? 'var(--yellow)' : 'var(--green)'}` }}>
              <div className="flex justify-between items-center">
                <div className="flex items-center gap-2">
                  {s.rank && <span className="font-mono text-xs font-bold" style={{ color: 'var(--cyan)' }}>#{s.rank}</span>}
                  <span className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>{s.region}</span>
                </div>
                <span className={`cyber-badge ${s.priority === 'critical' ? 'cyber-badge-pink' : s.priority === 'high' ? 'cyber-badge-yellow' : 'cyber-badge-green'}`}>{s.priority}</span>
              </div>
              <div className="flex gap-4 mt-2 flex-wrap font-mono text-xs" style={{ color: 'var(--text-secondary)' }}>
                {s.nearest_existing_facility_km != null && (
                  <span>Gap: <span className="neon-text">{s.nearest_existing_facility_km} km</span> to nearest</span>
                )}
                <span>{s.current_facilities_with_specialty} w/ specialty • {s.total_facilities_in_region} total</span>
              </div>
              {s.suggested_lat != null && s.suggested_lng != null && (
                <div className="text-xs font-mono mt-1" style={{ color: 'var(--text-muted)' }}>
                  📍 ({s.suggested_lat.toFixed(4)}, {s.suggested_lng.toFixed(4)})
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Capacity planning — regions */}
      {action === 'capacity_planning' && data.regions && (
        <div className="space-y-2">
          <div className="flex gap-6">
            <StatBlock value={data.total_regions} label="REGIONS" color="var(--cyan)" />
            <StatBlock value={data.critical_regions} label="CRITICAL" color="var(--pink)" />
          </div>
          {data.regions.map((r, i) => (
            <div key={i} className="rounded-lg p-3" style={{ background: 'var(--bg-surface)', borderLeft: `3px solid ${r.status === 'critical' ? 'var(--pink)' : r.status === 'warning' ? 'var(--yellow)' : 'var(--green)'}` }}>
              <div className="flex justify-between items-center">
                <span className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>{r.region}</span>
                <span className={`cyber-badge ${r.status === 'critical' ? 'cyber-badge-pink' : r.status === 'warning' ? 'cyber-badge-yellow' : 'cyber-badge-green'}`}>
                  {r.status}
                </span>
              </div>
              <div className="flex gap-4 mt-1 font-mono text-xs" style={{ color: 'var(--text-secondary)' }}>
                <span>Beds/fac: <span style={{ color: 'var(--cyan)' }}>{r.beds_per_facility}</span></span>
                <span>Docs/fac: <span style={{ color: 'var(--green)' }}>{r.doctors_per_facility}</span></span>
                <span>Total: <span style={{ color: 'var(--purple)' }}>{r.facilities}</span></span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Action steps */}
      {data.action_steps && data.action_steps.length > 0 && (
        <div className="mt-3">
          <span className="font-mono text-[0.6rem] tracking-[0.15em] uppercase font-semibold" style={{ color: 'var(--text-muted)' }}>
            ▸ Action Steps
          </span>
          <div className="mt-2 space-y-1">
            {data.action_steps.map((step, i) => (
              <div key={i} className="flex items-start gap-2 text-xs py-1" style={{ color: 'var(--text-secondary)' }}>
                <span className="font-mono font-bold" style={{ color: 'var(--green)' }}>{i + 1}.</span>
                <span>{step}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

/* ── Sub-components ────────────────────────────────────────── */
function StatBlock({ value, label, color }) {
  return (
    <div>
      <div className="stat-number text-2xl" style={{ color, textShadow: `0 0 12px ${color}40` }}>
        {value}
      </div>
      <div className="font-mono text-[0.55rem] tracking-[0.15em] uppercase" style={{ color: 'var(--text-muted)' }}>
        {label}
      </div>
    </div>
  )
}

function ConfidenceBadge({ value }) {
  const pct = (value * 100).toFixed(0)
  let color = 'var(--green)'
  let bg = 'rgba(6,255,165,0.1)'
  let border = 'rgba(6,255,165,0.3)'

  if (pct < 30) {
    color = 'var(--pink)'
    bg = 'rgba(255,0,110,0.1)'
    border = 'rgba(255,0,110,0.3)'
  } else if (pct < 60) {
    color = 'var(--yellow)'
    bg = 'rgba(255,214,10,0.1)'
    border = 'rgba(255,214,10,0.3)'
  }

  return (
    <span className="cyber-badge" style={{ background: bg, color, border: `1px solid ${border}` }}>
      {pct}% conf
    </span>
  )
}

function FacilityTable({ facilities }) {
  const [page, setPage] = useState(0)
  const PAGE_SIZE = 20

  if (!facilities || facilities.length === 0) return null

  const hasScore = facilities.some(f => f.rrf_score != null || f.score != null)
  const totalPages = Math.ceil(facilities.length / PAGE_SIZE)
  const pageItems = facilities.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE)

  return (
    <div className="overflow-x-auto rounded-lg" style={{ background: 'var(--bg-surface)' }}>
      <table className="w-full text-xs">
        <thead>
          <tr style={{ borderBottom: '1px solid var(--border-dim)' }}>
            <th className="text-left py-2 px-3 font-mono text-[0.6rem] tracking-wider uppercase" style={{ color: 'var(--text-muted)' }}>Name</th>
            <th className="text-left py-2 px-3 font-mono text-[0.6rem] tracking-wider uppercase" style={{ color: 'var(--text-muted)' }}>City</th>
            <th className="text-left py-2 px-3 font-mono text-[0.6rem] tracking-wider uppercase" style={{ color: 'var(--text-muted)' }}>Region</th>
            <th className="text-left py-2 px-3 font-mono text-[0.6rem] tracking-wider uppercase" style={{ color: 'var(--text-muted)' }}>Type</th>
            <th className="text-left py-2 px-3 font-mono text-[0.6rem] tracking-wider uppercase" style={{ color: 'var(--text-muted)' }}>Specialties</th>
            {hasScore && (
              <th className="text-right py-2 px-3 font-mono text-[0.6rem] tracking-wider uppercase" style={{ color: 'var(--text-muted)' }}>Match</th>
            )}
          </tr>
        </thead>
        <tbody>
          {pageItems.map((f, i) => (
            <tr key={i} style={{ borderBottom: '1px solid var(--border-dim)' }}
                className="transition-colors"
                onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-card-hover)'}
                onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
              <td className="py-2 px-3 font-medium" style={{ color: 'var(--text-primary)' }}>
                {f.name || f.facility}
              </td>
              <td className="py-2 px-3" style={{ color: 'var(--text-secondary)' }}>
                {f.city || f.address_city || '—'}
              </td>
              <td className="py-2 px-3" style={{ color: 'var(--text-secondary)' }}>
                {f.region || f.address_stateOrRegion || '—'}
              </td>
              <td className="py-2 px-3" style={{ color: 'var(--text-secondary)' }}>
                {f.type || f.facility_type || f.facilityTypeId || '—'}
              </td>
              <td className="py-2 px-3">
                <div className="flex flex-wrap gap-1">
                  {(f.specialties || []).slice(0, 3).map((s, j) => (
                    <span key={j} className="cyber-badge cyber-badge-cyan">{s}</span>
                  ))}
                  {(f.specialties || []).length > 3 && (
                    <span className="cyber-badge cyber-badge-purple" title={(f.specialties || []).slice(3).join(', ')}>
                      +{f.specialties.length - 3}
                    </span>
                  )}
                </div>
              </td>
              {hasScore && (
                <td className="py-2 px-3 text-right font-mono" style={{ color: 'var(--cyan)' }}>
                  {(() => {
                    const s = f.rrf_score ?? f.score
                    if (s == null) return '—'
                    return `${Math.round(Math.min(100, s * 100))}%`
                  })()}
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
      {/* Pagination controls */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between py-2 px-3" style={{ borderTop: '1px solid var(--border-dim)' }}>
          <span className="text-xs font-mono" style={{ color: 'var(--text-muted)' }}>
            {page * PAGE_SIZE + 1}–{Math.min((page + 1) * PAGE_SIZE, facilities.length)} of {facilities.length}
          </span>
          <div className="flex gap-1">
            <button
              onClick={() => setPage(p => Math.max(0, p - 1))}
              disabled={page === 0}
              className="cyber-badge cyber-badge-cyan cursor-pointer disabled:opacity-30 disabled:cursor-not-allowed"
            >
              ◂ Prev
            </button>
            <button
              onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
              disabled={page >= totalPages - 1}
              className="cyber-badge cyber-badge-cyan cursor-pointer disabled:opacity-30 disabled:cursor-not-allowed"
            >
              Next ▸
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

function Citations({ citations }) {
  if (!citations || citations.length === 0) return null

  return (
    <details className="mt-3 rounded-lg p-3" style={{ background: 'var(--bg-surface)' }}>
      <summary className="cursor-pointer font-mono text-[0.65rem] tracking-wider font-semibold" style={{ color: 'var(--green)' }}>
        ▸ {citations.length} CITATIONS
      </summary>
      <div className="mt-2 space-y-1 pl-3" style={{ borderLeft: '1px solid var(--border-dim)' }}>
        {citations.map((c, i) => (
          <div key={i} className="text-xs py-0.5" style={{ color: 'var(--text-secondary)' }}>
            <span className="font-mono" style={{ color: 'var(--cyan-dim)' }}>
              [{c.source || c.facility || i + 1}]
            </span>{' '}
            {c.text || c.name || c.evidence || JSON.stringify(c).slice(0, 120)}
          </div>
        ))}
      </div>
    </details>
  )
}
