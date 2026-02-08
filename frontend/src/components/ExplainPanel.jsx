// ────────────────────────────────────────────────────────────────
// ExplainPanel — Plain-language explanations for NGO planners
// ────────────────────────────────────────────────────────────────

import renderMarkdown from '../utils/renderMarkdown'

/**
 * Transforms technical agent output from medical_reasoning and planning
 * into clear, actionable explanations that non-technical NGO personnel
 * can understand and act on immediately.
 */
export default function ExplainPanel({ result }) {
  if (!result?.response) return <EmptyState />

  const resp = result.response
  const sections = []

  // ── Collect agent results ──────────────────────────────────────────
  if (resp.multi_agent_response && resp.results) {
    for (const [agent, data] of Object.entries(resp.results)) {
      if (!data || typeof data !== 'object') continue
      sections.push(...buildExplanations(agent, data))
    }
  } else {
    sections.push(...buildExplanations(resp.agent || 'unknown', resp))
  }

  if (sections.length === 0) return <EmptyState />

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="glass-card p-4" style={{
        borderLeft: '3px solid var(--green)',
        background: 'linear-gradient(135deg, rgba(6,255,165,0.06), rgba(0,243,255,0.03))',
      }}>
        <div className="flex items-center gap-2 mb-1">
          <span style={{ fontSize: '1.1rem' }}>📋</span>
          <span className="font-mono text-[0.65rem] tracking-[0.15em] uppercase font-bold"
            style={{ color: 'var(--green)' }}>
            Plain-Language Explanation
          </span>
        </div>
        <p className="text-xs leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
          Here's what the AI found, explained in simple terms so your team can take action.
        </p>
      </div>

      {sections.map((sec, i) => (
        <ExplainCard key={i} {...sec} />
      ))}
    </div>
  )
}

// ── Card renderer ────────────────────────────────────────────────────
function ExplainCard({ icon, title, paragraphs, actions, severity, highlights }) {
  const borderColor = severity === 'critical' ? 'var(--pink)'
    : severity === 'warning' ? 'var(--yellow)'
    : severity === 'good' ? 'var(--green)'
    : 'var(--cyan)'

  return (
    <div className="glass-card p-5 space-y-3" style={{ borderLeft: `3px solid ${borderColor}` }}>
      <div className="flex items-center gap-2">
        <span style={{ fontSize: '1.1rem' }}>{icon}</span>
        <h3 className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>{title}</h3>
      </div>

      {paragraphs?.map((p, i) => (
        <p key={i} className="text-sm leading-relaxed" style={{ color: 'var(--text-secondary)' }}>{renderMarkdown(p)}</p>
      ))}

      {highlights && highlights.length > 0 && (
        <div className="space-y-2 mt-2">
          {highlights.map((h, i) => (
            <div key={i} className="flex items-start gap-2 py-2 px-3 rounded-lg"
              style={{ background: 'var(--bg-surface)' }}>
              <span style={{ color: borderColor, flexShrink: 0 }}>{h.icon || '▸'}</span>
              <div>
                {h.label && (
                  <span className="text-xs font-semibold block" style={{ color: 'var(--text-primary)' }}>
                    {h.label}
                  </span>
                )}
                <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>{h.text}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {actions && actions.length > 0 && (
        <div className="mt-3 p-3 rounded-lg" style={{ background: 'rgba(6,255,165,0.05)', border: '1px solid rgba(6,255,165,0.15)' }}>
          <div className="flex items-center gap-1 mb-2">
            <span style={{ color: 'var(--green)', fontSize: '0.8rem' }}>✅</span>
            <span className="font-mono text-[0.6rem] tracking-wider uppercase font-bold"
              style={{ color: 'var(--green)' }}>What You Can Do</span>
          </div>
          {actions.map((a, i) => (
            <div key={i} className="flex items-start gap-2 py-1">
              <span className="text-xs font-bold" style={{ color: 'var(--green)', flexShrink: 0 }}>{i + 1}.</span>
              <span className="text-xs leading-relaxed" style={{ color: 'var(--text-secondary)' }}>{a}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function EmptyState() {
  return (
    <div className="glass-card p-6 text-center">
      <span style={{ fontSize: '1.5rem' }}>📋</span>
      <p className="text-sm mt-2" style={{ color: 'var(--text-muted)' }}>
        Run a query to see plain-language explanations of the results.
      </p>
    </div>
  )
}

// ── Explanation builder ──────────────────────────────────────────────
function buildExplanations(agent, data) {
  const sections = []
  const action = data.action || data.scenario || ''

  // ═══ MEDICAL REASONING EXPLANATIONS ════════════════════════════════
  if (agent === 'medical_reasoning' || data.agent === 'medical_reasoning') {

    // Constraint validation
    if (action === 'constraint_validation') {
      const flagged = data.facilities_with_issues || 0
      const total = data.total_checked || 0
      const pct = total > 0 ? ((flagged / total) * 100).toFixed(0) : 0
      const avgConf = data.summary?.avg_confidence
      const highSev = data.summary?.high_severity || 0
      const medSev = data.summary?.medium_severity || 0

      sections.push({
        icon: '🔍', title: 'Facility Verification Results',
        severity: flagged > 10 ? 'critical' : flagged > 3 ? 'warning' : 'good',
        paragraphs: [
          `We checked ${total} healthcare facilities in Ghana to see if their claimed capabilities match what they actually have (equipment, bed capacity, staff).`,
          flagged > 0
            ? `${flagged} facilities (${pct}%) have potential issues — they claim to offer services but may lack the required resources to deliver them safely.`
            : `Great news — all facilities appear to have the resources needed for their claimed services.`,
          highSev > 0 ? `⚠️ ${highSev} issues are high-severity, meaning patients could be at risk if these services are relied upon without verification.` : null,
        ].filter(Boolean),
        highlights: data.flagged_facilities?.slice(0, 5).map(f => ({
          icon: f.confidence < 0.5 ? '🔴' : '🟡',
          label: f.facility,
          text: f.issues?.map(i => i.message).join(' • ') || 'Needs review',
        })),
        actions: [
          flagged > 0 ? `Contact the ${Math.min(flagged, 5)} most concerning facilities for on-site verification` : null,
          highSev > 0 ? `Prioritize the ${highSev} high-severity issues — these involve missing critical equipment` : null,
          medSev > 0 ? `Review ${medSev} medium-severity issues during your next facility assessment round` : null,
          avgConf != null && avgConf < 0.7 ? `Overall confidence is ${(avgConf * 100).toFixed(0)}% — consider a comprehensive audit` : null,
          'Update the facility database after each verification visit',
        ].filter(Boolean),
      })
    }

    // Anomaly detection
    if (action === 'anomaly_detection') {
      const anomalies = data.anomalies_found || 0
      const total = data.total_checked || 0

      sections.push({
        icon: '🔬', title: 'Unusual Facility Patterns Detected',
        severity: anomalies > 5 ? 'warning' : 'good',
        paragraphs: [
          `Our AI scanned ${total} facilities using a two-stage statistical pipeline: first, an **Isolation Forest** algorithm flags statistical outliers, then **Mahalanobis distance** validation confirms only the true anomalies (filtering out false positives).`,
          anomalies > 0
            ? `${anomalies} facilities were confirmed as genuinely unusual by both stages.${data.stage1_outliers ? ` (Stage 1 initially flagged ${data.stage1_outliers}, but only ${data.stage2_confirmed || anomalies} survived the Mahalanobis check.)` : ''}`
            : `No unusual patterns were detected. All facilities have consistent data profiles.`,
          'Common reasons for anomalies: a facility claims many specialties but has very little equipment, or has a very high patient-to-doctor ratio.',
        ],
        highlights: data.results?.slice(0, 5).map(r => ({
          icon: '⚡',
          label: `${r.facility} (${r.city || 'Unknown'})`,
          text: r.reasons?.join('. ') || 'Statistical outlier',
        })),
        actions: anomalies > 0 ? [
          `Review the top ${Math.min(anomalies, 5)} flagged facilities for data accuracy`,
          'Some anomalies may simply be data entry errors — verify with local staff',
          'Update records for any confirmed data issues',
        ] : ['No action needed — facility data looks consistent'],
      })
    }

    // Red flags
    if (action === 'red_flag_detection') {
      const flagged = data.facilities_flagged || 0
      sections.push({
        icon: '🚩', title: 'Language Warning Flags',
        severity: flagged > 5 ? 'warning' : 'good',
        paragraphs: [
          `We scanned facility descriptions for language that suggests services might be temporary, visiting-only, or vaguely described.`,
          flagged > 0
            ? `${flagged} facilities use language patterns that suggest their services may not be permanently available (e.g., "visiting specialist," "mobile clinic," "campaign-based").`
            : `No concerning language patterns found. Facility descriptions appear clear and specific.`,
          'This matters because communities need reliable, permanent access to healthcare — not just occasional visits.',
        ],
        highlights: data.results?.slice(0, 5).map(f => ({
          icon: '🚩',
          label: f.facility,
          text: f.recommendation || 'Review language patterns',
        })),
        actions: flagged > 0 ? [
          'Verify which flagged facilities offer permanent vs. temporary services',
          'For temporary services, ensure communities know the schedule and alternatives',
          'Consider whether permanent staffing could replace visiting arrangements',
        ] : ['No action needed'],
      })
    }

    // Coverage gaps
    if (action === 'coverage_gap_analysis') {
      const gaps = data.gaps_found || data.cold_spots_found || 0
      const coverage = data.coverage_percentage
      const specialty = data.specialty

      sections.push({
        icon: '🗺️', title: `Healthcare Coverage Analysis${specialty && specialty !== 'all' ? ` — ${specialty}` : ''}`,
        severity: gaps > 5 ? 'critical' : gaps > 2 ? 'warning' : 'good',
        paragraphs: [
          coverage != null
            ? `Currently, ${coverage}% of Ghana's area has reasonable access to ${specialty || 'healthcare'} (within acceptable travel distance).`
            : `We analyzed which regions lack adequate access to ${specialty || 'healthcare services'}.`,
          gaps > 0
            ? `${gaps} areas were identified where people would need to travel unreasonably far to reach care. These are "coverage gaps" that leave communities vulnerable.`
            : `Coverage appears adequate across all analyzed regions.`,
        ],
        highlights: (data.gaps || data.worst_cold_spots)?.slice(0, 5).map(g => ({
          icon: '📍',
          label: g.region || `Area (${g.grid_lat?.toFixed(1)}, ${g.grid_lng?.toFixed(1)})`,
          text: g.gap_severity === 'critical'
            ? `No ${specialty || ''} facilities at all — critical gap`
            : g.distance_km
              ? `Nearest facility is ${g.distance_km.toFixed(0)} km away — too far for emergencies`
              : `Limited coverage — needs attention`,
        })),
        actions: gaps > 0 ? [
          'Share these findings with regional health authorities',
          'Consider mobile clinic deployments to underserved areas',
          'Explore partnerships with NGOs already operating in gap regions',
          'Use this data to support funding applications for new facilities',
        ] : ['Continue monitoring — coverage can shift as populations move'],
      })
    }

    // Single point of failure
    if (action === 'single_point_of_failure') {
      const critical = data.critical_specialties || 0
      sections.push({
        icon: '⚠️', title: 'Services At Risk of Disruption',
        severity: critical > 3 ? 'critical' : critical > 0 ? 'warning' : 'good',
        paragraphs: [
          `We looked for medical specialties that depend on just one or two facilities in the entire country.`,
          critical > 0
            ? `${critical} specialties are dangerously concentrated — if even one facility closes or loses staff, an entire region (or the whole country) could lose access to that type of care.`
            : `No single-point-of-failure risks detected. Specialties are reasonably distributed.`,
          'This is critical for disaster planning and long-term healthcare resilience.',
        ],
        highlights: data.results?.slice(0, 5).map(r => ({
          icon: r.risk_level === 'critical' ? '🔴' : '🟡',
          label: r.specialty,
          text: `Only ${r.facility_count} ${r.facility_count === 1 ? 'facility' : 'facilities'} in ${r.regions_covered?.join(', ') || 'Ghana'} — ${r.risk_level} risk`,
        })),
        actions: critical > 0 ? [
          'Identify backup arrangements for critical specialties',
          'Work with training institutions to build capacity in vulnerable specialties',
          'Consider telemedicine links to international partners for the rarest specialties',
          'Create contingency plans in case a single-provider facility goes offline',
        ] : ['No immediate action needed — continue monitoring'],
      })
    }

    // Comprehensive analysis (combined)
    if (action === 'comprehensive_analysis') {
      if (data.validation) sections.push(...buildExplanations(agent, data.validation))
      if (data.anomalies) sections.push(...buildExplanations(agent, data.anomalies))
    }
  }

  // ═══ PLANNING AGENT EXPLANATIONS ═══════════════════════════════════
  if (agent === 'planning' || data.agent === 'planning') {

    // Emergency routing
    if (action === 'emergency_routing') {
      const pf = data.primary_facility
      const backup = data.backup_facility

      sections.push({
        icon: '🚑', title: 'Emergency Patient Routing Plan',
        severity: pf ? 'good' : 'critical',
        paragraphs: [
          pf
            ? `The closest facility that can handle this case is **${pf.facility}** in ${pf.city || 'Ghana'}, which is ${pf.distance_km?.toFixed(1)} km away (about ${pf.est_travel_min} minutes by road).`
            : `No suitable facility was found for this emergency — escalate immediately to regional emergency services.`,
          pf?.capability_match != null
            ? `This facility scored ${pf.capability_match}% on capability match, meaning it has ${pf.capability_match >= 75 ? 'most of' : pf.capability_match >= 50 ? 'some of' : 'limited'} the equipment and staff needed.`
            : null,
          backup
            ? `If ${pf?.facility} is unavailable, the backup option is ${backup.facility} in ${backup.city || 'Ghana'} (${backup.distance_km?.toFixed(1)} km away).`
            : null,
        ].filter(Boolean),
        highlights: [
          pf ? { icon: '🏥', label: pf.facility, text: `${pf.distance_km?.toFixed(1)} km • ${pf.est_travel_min} min • ${pf.capability_match}% match` } : null,
          backup ? { icon: '🏥', label: `Backup: ${backup.facility}`, text: `${backup.distance_km?.toFixed(1)} km away` } : null,
          ...(data.alternatives || []).slice(0, 2).map(a => ({
            icon: '📍', label: a.facility, text: `${a.distance_km?.toFixed(1)} km • ${a.capability_match}% match`,
          })),
        ].filter(Boolean),
        actions: [
          pf ? `Call ${pf.facility} immediately to confirm they can receive the patient` : 'Contact regional emergency coordination',
          pf ? `Arrange transport — estimated ${pf.est_travel_min} minutes drive time` : null,
          'Ensure patient records and referral documents are prepared',
          backup ? `Have ${backup.facility} on standby as backup` : null,
          'Notify the receiving facility of the patient\'s condition and ETA',
        ].filter(Boolean),
      })
    }

    // Specialist deployment
    if (action === 'specialist_deployment') {
      const stops = data.stops || data.route || []
      const dist = data.total_distance_km

      sections.push({
        icon: '👨‍⚕️', title: `Specialist Rotation Plan — ${data.specialty || 'General'}`,
        severity: 'good',
        paragraphs: [
          `We've designed an optimized travel route for a visiting ${data.specialty || ''} specialist to reach ${stops.length} underserved facilities.`,
          dist ? `The total route covers ${dist.toFixed(0)} km.${data.optimisation ? ` The route was optimised using a **greedy nearest-neighbour** algorithm followed by **2-opt local search**, which reverses route segments to reduce backtracking (typically 20–25% shorter than naïve ordering).` : ' The route is ordered to minimize travel time, starting from Accra.'}` : null,
          'Each stop represents a facility that currently does NOT have this specialty — meaning communities there have no local access to this type of care.',
        ].filter(Boolean),
        highlights: stops.slice(0, 6).map((s, i) => ({
          icon: i === 0 ? '🟢' : i === stops.length - 1 ? '🔴' : '📍',
          label: `Stop ${s.stop || i + 1}: ${s.facility || s.name}`,
          text: `${s.city || ''} ${s.region ? `(${s.region})` : ''} — ${s.distance_from_prev_km?.toFixed(0) || '?'} km from previous stop`,
        })),
        actions: [
          `Schedule the specialist for ${stops.length} facility visits along this route`,
          'Contact each facility in advance to prepare patient lists',
          'Arrange accommodation at midpoint for multi-day rotations',
          dist > 500 ? 'Consider splitting into 2 trips given the total distance' : null,
          'Set up telemedicine follow-up for patients seen during the rotation',
        ].filter(Boolean),
      })
    }

    // Equipment distribution
    if (action === 'equipment_distribution') {
      const equip = data.equipment || 'Equipment'
      const placements = data.placements || []
      const withEquip = data.facilities_with || 0
      const withoutEquip = data.facilities_without || 0

      sections.push({
        icon: '🏗️', title: `${equip} Distribution Plan`,
        severity: withoutEquip > withEquip ? 'warning' : 'good',
        paragraphs: [
          `Currently, ${withEquip} facilities already have a ${equip}, while ${withoutEquip} facilities need one.`,
          placements.length > 0
            ? `We identified the ${placements.length} best locations to place new ${equip} units for maximum community impact.`
            : 'No optimal placement locations identified.',
          'Placements are chosen to serve the most facilities and communities with the shortest travel distances.',
        ],
        highlights: placements.slice(0, 5).map((p, i) => ({
          icon: '📍',
          label: p.recommended_facility || p.name || `Placement ${i + 1}`,
          text: `Would serve ${p.facilities_served || '?'} nearby facilities${p.city ? ` — ${p.city}` : ''}`,
        })),
        actions: [
          `Procure ${Math.min(placements.length, 3)} ${equip} units for highest-impact placements`,
          'Coordinate with facility management for installation requirements',
          'Ensure trained operators are available at each placement site',
          'Set up maintenance schedules and supply chains for each unit',
        ],
      })
    }

    // New facility placement
    if (action === 'new_facility_placement') {
      const suggestions = data.suggestions || []
      const criticalCount = suggestions.filter(s => s.priority === 'critical').length

      sections.push({
        icon: '📍', title: `New Facility Recommendations — ${data.specialty || 'General'}`,
        severity: criticalCount > 2 ? 'critical' : criticalCount > 0 ? 'warning' : 'good',
        paragraphs: [
          `We analyzed the geographic distribution of ${data.specialty || 'healthcare'} facilities across all regions of Ghana${data.algorithm ? ` using the **maximin placement algorithm** — it finds the points farthest from any existing facility, ensuring new placements maximise coverage` : ''}.`,
          criticalCount > 0
            ? `${criticalCount} locations are more than 100 km from any existing facility — these are the most urgent areas to address.`
            : 'All regions have at least some coverage, though many could benefit from expansion.',
          `In total, ${suggestions.length} optimal sites were identified, each with exact GPS coordinates for field teams.`,
        ],
        highlights: suggestions.slice(0, 5).map(s => ({
          icon: s.priority === 'critical' ? '🔴' : '🟡',
          label: s.region,
          text: s.current_facilities_with_specialty === 0
            ? 'No facilities at all — critical need'
            : `Only ${s.current_facilities_with_specialty} facility out of ${s.total_facilities_in_region} total`,
        })),
        actions: [
          criticalCount > 0 ? `Prioritize the ${criticalCount} regions with zero coverage` : 'Focus on regions with the lowest coverage',
          'Use the GPS coordinates provided to evaluate potential construction sites',
          'Engage local government for land and infrastructure support',
          'Consider mobile clinics as an interim solution while facilities are built',
          'Use these findings in grant applications and donor reports',
        ],
      })
    }

    // Capacity planning
    if (action === 'capacity_planning') {
      const regions = data.regions || []
      const criticalRegions = regions.filter(r => r.status === 'critical')

      sections.push({
        icon: '📊', title: 'Regional Capacity Analysis',
        severity: criticalRegions.length > 3 ? 'critical' : criticalRegions.length > 0 ? 'warning' : 'good',
        paragraphs: [
          `We analyzed bed capacity and doctor staffing across ${regions.length} regions in Ghana.`,
          criticalRegions.length > 0
            ? `${criticalRegions.length} regions are critically under-resourced — they have too few beds and doctors relative to the number of facilities and population they serve.`
            : 'All regions appear to have adequate staffing levels.',
          'Regions with fewer beds per facility and lower doctor ratios should be prioritized for resource allocation.',
        ],
        highlights: regions.slice(0, 6).map(r => ({
          icon: r.status === 'critical' ? '🔴' : r.status === 'warning' ? '🟡' : '🟢',
          label: r.region,
          text: `${r.facilities} facilities • ${r.total_beds} beds • ${r.total_doctors} doctors — ${r.beds_per_facility} beds/facility`,
        })),
        actions: criticalRegions.length > 0 ? [
          `Focus bed expansion on the ${criticalRegions.length} critical regions`,
          'Recruit doctors for regions with the lowest doctor-to-facility ratios',
          'Explore partnerships to share resources between nearby facilities',
          'Use this data to justify budget allocations at the regional level',
        ] : ['Monitor trends — capacity needs change with population growth'],
      })
    }
  }

  // ═══ GEOSPATIAL EXPLANATIONS ═══════════════════════════════════════
  if (agent === 'geospatial' || data.agent === 'geospatial') {

    if (action === 'medical_desert_detection') {
      const deserts = data.deserts || []
      sections.push({
        icon: '🏜️', title: 'Medical Desert Analysis',
        severity: deserts.length > 3 ? 'critical' : deserts.length > 0 ? 'warning' : 'good',
        paragraphs: [
          `A "medical desert" is an area where people must travel an unreasonably long distance (${data.threshold_km || 75}+ km) to reach the nearest healthcare facility.`,
          deserts.length > 0
            ? `${deserts.length} medical deserts were identified in Ghana. People in these areas face dangerous delays when they need medical care.`
            : `No medical deserts detected at the current threshold. All regions have facilities within reasonable distance.`,
        ],
        highlights: deserts.slice(0, 5).map(d => ({
          icon: d.severity === 'critical' ? '🔴' : '🟡',
          label: d.region,
          text: `Nearest facility is ${d.nearest_distance_km?.toFixed(0)} km away — ${d.severity} severity`,
        })),
        actions: deserts.length > 0 ? [
          'Deploy mobile health clinics to the most severe desert areas',
          'Advocate for new facility construction in critical deserts',
          'Set up emergency transport networks for patients in these areas',
          'Consider telemedicine as a bridge solution',
        ] : ['Continue monitoring as facilities open and close'],
      })
    }

    if (action === 'coverage_gap_analysis') {
      const coldSpots = data.worst_cold_spots || []
      sections.push({
        icon: '📡', title: 'Coverage Gap Analysis',
        severity: (data.coverage_percentage || 100) < 70 ? 'critical' : (data.coverage_percentage || 100) < 85 ? 'warning' : 'good',
        paragraphs: [
          `We divided Ghana into a grid and checked how far each area is from the nearest ${data.specialty || ''} facility.`,
          data.coverage_percentage != null
            ? `${data.coverage_percentage}% of areas are covered (within ${data.max_acceptable_km || 50} km of a facility). The remaining ${(100 - data.coverage_percentage).toFixed(1)}% are underserved.`
            : null,
          coldSpots.length > 0
            ? `The ${coldSpots.length} worst "cold spots" are listed below — these are the areas most in need of new services.`
            : null,
        ].filter(Boolean),
        highlights: coldSpots.slice(0, 5).map(cs => ({
          icon: '❄️',
          label: cs.nearest_facility || 'Underserved area',
          text: `${cs.distance_km?.toFixed(0)} km from nearest facility • Location: (${cs.grid_lat?.toFixed(1)}, ${cs.grid_lng?.toFixed(1)})`,
        })),
        actions: [
          'Prioritize mobile clinic deployments to the worst cold spots',
          'Share coverage maps with regional health directorates',
          'Use these coordinates for planning new facility locations',
        ],
      })
    }

    if (action === 'regional_equity_analysis') {
      const regions = data.regions || []
      sections.push({
        icon: '⚖️', title: 'Regional Healthcare Equity',
        severity: 'good',
        paragraphs: [
          `We compared healthcare resources across ${data.total_regions || regions.length} regions to identify inequities.`,
          'Regions with fewer facilities, doctors, and specialties relative to their size may need targeted investment.',
        ],
        highlights: regions.slice(0, 5).map(r => ({
          icon: '📊',
          label: r.region,
          text: `${r.total_facilities} facilities • ${r.total_doctors} doctors • ${r.unique_specialties} specialties`,
        })),
        actions: [
          'Compare these numbers against regional population data',
          'Lobby for equitable resource distribution based on these findings',
          'Partner with local NGOs in underserved regions',
        ],
      })
    }

    if (action === 'distance_between_cities') {
      sections.push({
        icon: '📏', title: 'Distance Calculation',
        severity: 'good',
        paragraphs: [
          data.distance_km
            ? `The distance between ${data.city_a || '?'} and ${data.city_b || '?'} is approximately ${data.distance_km} km.`
            : data.error || 'Could not calculate distance.',
        ],
        actions: [],
      })
    }
  }

  // ═══ VECTOR SEARCH / GENIE EXPLANATIONS ════════════════════════════
  if (agent === 'vector_search' || data.agent === 'vector_search') {
    const count = data.count || data.results?.length || 0
    const method = data.search_method === 'reciprocal_rank_fusion' ? 'Reciprocal Rank Fusion (RRF)' : 'semantic'
    const vectorCount = data.vectors_queried?.length || 1
    sections.push({
      icon: '🔎', title: 'Search Results Explained',
      severity: 'good',
      paragraphs: [
        `We searched our database of healthcare facilities and found ${count} matching results.`,
        vectorCount > 1
          ? `Results were ranked using **${method}** across ${vectorCount} independent embedding vectors (clinical detail, specialties context, and full document). This means your query was matched from multiple angles simultaneously for more accurate ranking.`
          : 'Results are ranked by how closely they match your question, using AI-powered semantic search.',
      ],
      actions: [
        count > 0 ? 'Review the Results tab for the full list of matching facilities' : 'Try rephrasing your question or broadening the search criteria',
      ],
    })
  }

  if (agent === 'genie' || data.agent === 'genie') {
    const count = data.count ?? data.results?.length ?? null
    sections.push({
      icon: '🧞', title: 'Data Query Results',
      severity: 'good',
      paragraphs: [
        `Your question was converted into a database query to get an exact answer.`,
        count != null ? `The query found ${count} matching records.` : null,
      ].filter(Boolean),
      actions: [
        'Check the Results tab for detailed data',
      ],
    })
  }

  return sections
}
