// ────────────────────────────────────────────────────────────────
// ResultsPanel — Cyberpunk-styled results display
// ────────────────────────────────────────────────────────────────

export default function ResultsPanel({ result }) {
  if (!result) return null

  const response = result.response

  // Multi-agent response
  if (response?.multi_agent_response) {
    return (
      <div className="space-y-4">
        {Object.entries(response.results || {}).map(([agent, data]) => (
          <div key={agent} className="glass-card p-4">
            <div className="flex items-center gap-2 mb-3">
              <span className="font-mono text-xs font-bold tracking-wider neon-text">
                {agent.replace(/_/g, ' ').toUpperCase()}
              </span>
            </div>
            <AgentResult data={data} />
          </div>
        ))}
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
        <div className="flex gap-6">
          <StatBlock value={data.anomalies_found} label="ANOMALIES" color="var(--yellow)" />
          <StatBlock value={data.total_checked} label="SCANNED" color="var(--cyan)" />
        </div>
        {data.results?.map((r, i) => (
          <div key={i} className="rounded-lg p-3" style={{ background: 'var(--bg-surface)', borderLeft: '3px solid var(--yellow)' }}>
            <div className="flex justify-between items-start">
              <div>
                <h4 className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>{r.facility}</h4>
                <p className="text-xs font-mono" style={{ color: 'var(--text-muted)' }}>{r.city}</p>
              </div>
              <span className="cyber-badge cyber-badge-yellow">
                Score: {r.anomaly_score}
              </span>
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
          <StatBlock value={data.facilities_with_issues} label="WITH ISSUES" color="var(--pink)" />
          <StatBlock value={data.total_checked} label="CHECKED" color="var(--cyan)" />
          {data.summary?.avg_confidence != null && (
            <StatBlock value={`${(data.summary.avg_confidence * 100).toFixed(0)}%`} label="AVG CONFIDENCE" color="var(--green)" />
          )}
        </div>
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
  if (action === 'coverage_gap_analysis' && data.coverage_percentage != null) {
    return (
      <div className="space-y-3">
        <div className="flex gap-6 flex-wrap">
          <StatBlock value={`${data.coverage_percentage}%`} label="COVERAGE" color="var(--cyan)" />
          <StatBlock value={data.cold_spots_found} label="COLD SPOTS" color="var(--pink)" />
        </div>
        {data.worst_cold_spots?.map((spot, i) => (
          <div key={i} className="flex justify-between items-center py-2 px-3 rounded" style={{ background: 'var(--bg-surface)' }}>
            <span className="font-mono text-xs" style={{ color: 'var(--text-secondary)' }}>
              ({spot.grid_lat?.toFixed(2)}, {spot.grid_lng?.toFixed(2)})
            </span>
            <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
              → {spot.nearest_facility}
            </span>
            <span className="cyber-badge cyber-badge-pink">{spot.distance_km?.toFixed(1)} km</span>
          </div>
        ))}
      </div>
    )
  }

  // Medical deserts
  if (action === 'medical_desert_detection') {
    return (
      <div className="space-y-3">
        <StatBlock value={data.deserts_found} label="MEDICAL DESERTS" color="var(--pink)" />
        {data.deserts?.map((d, i) => (
          <div key={i} className="rounded-lg p-3 flex justify-between items-center" style={{ background: 'var(--bg-surface)', borderLeft: `3px solid ${d.severity === 'critical' ? 'var(--pink)' : 'var(--yellow)'}` }}>
            <div>
              <h4 className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>{d.region}</h4>
              <p className="text-xs font-mono" style={{ color: 'var(--text-muted)' }}>{d.nearest_distance_km?.toFixed(1)} km to nearest</p>
            </div>
            <span className={`cyber-badge ${d.severity === 'critical' ? 'cyber-badge-pink' : 'cyber-badge-yellow'}`}>
              {d.severity}
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
            <div className="flex gap-4 font-mono text-xs" style={{ color: 'var(--text-secondary)' }}>
              <span><span style={{ color: 'var(--cyan)' }}>{r.total_facilities}</span> fac</span>
              <span><span style={{ color: 'var(--green)' }}>{r.total_doctors}</span> doc</span>
              <span><span style={{ color: 'var(--purple)' }}>{r.total_beds}</span> beds</span>
              <span><span style={{ color: 'var(--yellow)' }}>{r.unique_specialties}</span> spec</span>
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
        <StatBlock value={data.facilities_flagged} label="FLAGGED" color="var(--yellow)" />
        {data.results?.map((f, i) => (
          <div key={i} className="rounded-lg p-3" style={{ background: 'var(--bg-surface)', borderLeft: '3px solid var(--yellow)' }}>
            <h4 className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>{f.facility}</h4>
            <p className="text-xs" style={{ color: 'var(--text-muted)' }}>{f.city} — {f.recommendation}</p>
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
        <StatBlock value={data.critical_specialties} label="CRITICAL SPECIALTIES" color="var(--pink)" />
        {data.results?.map((r, i) => (
          <div key={i} className="rounded-lg p-3" style={{ background: 'var(--bg-surface)', borderLeft: `3px solid ${r.risk_level === 'critical' ? 'var(--pink)' : 'var(--yellow)'}` }}>
            <div className="flex justify-between items-center">
              <h4 className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>{r.specialty}</h4>
              <span className={`cyber-badge ${r.risk_level === 'critical' ? 'cyber-badge-pink' : 'cyber-badge-yellow'}`}>
                {r.facility_count} {r.facility_count === 1 ? 'facility' : 'facilities'}
              </span>
            </div>
            <div className="text-xs mt-1" style={{ color: 'var(--text-secondary)' }}>
              {r.facilities?.map(f => f.name).join(', ')}
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
          <div className="rounded-lg p-4 neon-border" style={{ background: 'var(--bg-surface)' }}>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-lg">🚑</span>
              <span className="font-mono text-xs font-bold tracking-wider neon-text">PRIMARY FACILITY</span>
            </div>
            <h4 className="text-base font-semibold" style={{ color: 'var(--text-primary)' }}>
              {data.primary_facility.facility}
            </h4>
            <div className="text-xs" style={{ color: 'var(--text-muted)' }}>
              {data.primary_facility.city} • {data.primary_facility.region}
            </div>
            <div className="flex gap-4 mt-2 font-mono text-xs" style={{ color: 'var(--text-secondary)' }}>
              <span>Distance: <span className="neon-text">{data.primary_facility.distance_km?.toFixed(1)} km</span></span>
              <span>Travel: <span className="neon-text">{data.primary_facility.est_travel_min} min</span></span>
              <span>Match: <span className="neon-text-green">{data.primary_facility.capability_match}%</span></span>
            </div>
          </div>
          {data.backup_facility && (
            <div className="rounded-lg p-3" style={{ background: 'var(--bg-surface)', borderLeft: '3px solid var(--yellow)' }}>
              <span className="font-mono text-[0.6rem] tracking-wider" style={{ color: 'var(--yellow)' }}>BACKUP</span>
              <div className="text-sm font-medium mt-1" style={{ color: 'var(--text-primary)' }}>{data.backup_facility.facility}</div>
              <div className="text-xs" style={{ color: 'var(--text-muted)' }}>{data.backup_facility.city} — {data.backup_facility.distance_km?.toFixed(1)} km</div>
            </div>
          )}
          {data.alternatives?.length > 0 && (
            <div className="space-y-1">
              <span className="font-mono text-[0.6rem] tracking-wider" style={{ color: 'var(--text-muted)' }}>OTHER OPTIONS</span>
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
          <div className="flex gap-6">
            <StatBlock value={data.total_stops} label="STOPS" color="var(--cyan)" />
            <StatBlock value={`${data.total_distance_km?.toFixed(0)} km`} label="TOTAL DISTANCE" color="var(--green)" />
            <StatBlock value={`${data.est_total_days} days`} label="DURATION" color="var(--purple)" />
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

      {/* New facility placement — suggestions */}
      {action === 'new_facility_placement' && data.suggestions && (
        <div className="space-y-2">
          <StatBlock value={data.total_suggestions} label="SUGGESTED LOCATIONS" color="var(--cyan)" />
          {data.suggestions.map((s, i) => (
            <div key={i} className="rounded-lg p-3" style={{ background: 'var(--bg-surface)', borderLeft: `3px solid ${s.priority === 'critical' ? 'var(--pink)' : 'var(--yellow)'}` }}>
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>{s.region}</span>
                <span className={`cyber-badge ${s.priority === 'critical' ? 'cyber-badge-pink' : 'cyber-badge-yellow'}`}>{s.priority}</span>
              </div>
              <div className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>
                {s.current_facilities_with_specialty} facilities w/ specialty, {s.total_facilities_in_region} total
              </div>
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
  if (!facilities || facilities.length === 0) return null

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
          </tr>
        </thead>
        <tbody>
          {facilities.slice(0, 20).map((f, i) => (
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
                    <span className="cyber-badge cyber-badge-purple">
                      +{f.specialties.length - 3}
                    </span>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {facilities.length > 20 && (
        <p className="text-xs py-2 px-3 font-mono" style={{ color: 'var(--text-muted)' }}>
          Showing 20 of {facilities.length}
        </p>
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
