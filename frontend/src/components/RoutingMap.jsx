import { useState, useEffect, useRef, useCallback } from 'react'
import L from 'leaflet'
import { fetchRoutingMap, fetchFacilities } from '../api/client'

// ── Scenarios ─────────────────────────────────────────────────────────────────
const SCENARIOS = [
  {
    id: 'emergency_routing', title: 'Emergency: Cardiac Patient',
    desc: 'Route patient from rural area to nearest cardiology facility with catheterization capability',
    specialty: 'cardiology', origin: 'Tamale', icon: '🚑',
  },
  {
    id: 'specialist_deployment', title: 'Specialist Rotation',
    desc: 'Optimize cardiologist route to cover underserved facilities',
    specialty: 'cardiology', origin: null, icon: '👨‍⚕️',
  },
  {
    id: 'emergency_routing', title: 'Trauma Transfer',
    desc: 'Multi-hop routing from clinic → district hospital → trauma center',
    specialty: 'emergencyMedicine', origin: 'Kumasi', icon: '🏥',
  },
  {
    id: 'equipment_distribution', title: 'Equipment Distribution',
    desc: 'Route mobile CT scanner to maximize coverage',
    specialty: null, origin: null, icon: '🏗️',
  },
  {
    id: 'new_facility_placement', title: 'Medical Desert Analysis',
    desc: 'Identify gaps and suggest new facility locations',
    specialty: 'neurosurgery', origin: null, icon: '📍',
  },
]

const TYPE_COLORS = {
  hospital: '#00f3ff',
  clinic: '#06ffa5',
  health_center: '#8338ec',
  pharmacy: '#ffd60a',
  ngo: '#ff006e',
  default: '#00b8c9',
}

function getFacilityColor(f) {
  const t = (f.facility_type || f.type || '').toLowerCase()
  if (t.includes('hospital')) return TYPE_COLORS.hospital
  if (t.includes('clinic')) return TYPE_COLORS.clinic
  if (t.includes('health') && t.includes('center')) return TYPE_COLORS.health_center
  if (t.includes('pharmacy')) return TYPE_COLORS.pharmacy
  if (t.includes('ngo') || t.includes('foundation')) return TYPE_COLORS.ngo
  return TYPE_COLORS.default
}

export default function RoutingMap() {
  const mapRef = useRef(null)
  const mapInstance = useRef(null)
  const markersLayer = useRef(null)
  const routeLayer = useRef(null)
  const desertLayer = useRef(null)
  const routeMarkersLayer = useRef(null)

  const [activeScenario, setActiveScenario] = useState(0)
  const [loading, setLoading] = useState(false)
  const [routingData, setRoutingData] = useState(null)
  const [allFacilities, setAllFacilities] = useState([])
  const [stats, setStats] = useState({ distance: 0, time: 0, facilities: 0 })
  const [reasoning, setReasoning] = useState([])
  const [routeInfo, setRouteInfo] = useState(null)
  const [showAllFacs, setShowAllFacs] = useState(true)

  // ── Init map ────────────────────────────────────────────────────────────
  useEffect(() => {
    if (!mapRef.current || mapInstance.current) return
    const map = L.map(mapRef.current, { zoomControl: true }).setView([7.9465, -1.0232], 7)
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      attribution: '© OSM © CARTO', maxZoom: 19,
    }).addTo(map)
    mapInstance.current = map
    markersLayer.current = L.layerGroup().addTo(map)
    routeLayer.current = L.layerGroup().addTo(map)
    desertLayer.current = L.layerGroup().addTo(map)
    routeMarkersLayer.current = L.layerGroup().addTo(map)
  }, [])

  // ── Load all facilities once ────────────────────────────────────────────
  useEffect(() => {
    fetchFacilities()
      .then(data => setAllFacilities(data.facilities || []))
      .catch(console.error)
  }, [])

  // ── Draw facility markers ──────────────────────────────────────────────
  useEffect(() => {
    if (!mapInstance.current || !markersLayer.current) return
    markersLayer.current.clearLayers()
    if (!showAllFacs) return

    const facs = routingData?.facilities || allFacilities
    facs.forEach(f => {
      if (f.latitude == null || f.longitude == null) return
      const color = getFacilityColor(f)
      const marker = L.circleMarker([f.latitude, f.longitude], {
        radius: 4, fillColor: color, color: color, weight: 1, opacity: 0.7, fillOpacity: 0.5,
      })
      const name = f.name || 'Unknown'
      const specs = (f.specialties || []).slice(0, 4).join(', ')
      marker.bindPopup(`
        <div style="font-family:'Inter',sans-serif;min-width:180px">
          <div style="font-weight:700;color:#00f3ff;margin-bottom:4px">${name}</div>
          <div style="font-size:0.8rem;color:#8892a8">${f.city || ''} • ${f.facility_type || f.type || ''}</div>
          ${specs ? `<div style="font-size:0.75rem;color:#505a70;margin-top:4px">${specs}</div>` : ''}
          ${f.capacity ? `<div style="font-size:0.75rem;color:#505a70;margin-top:2px">Capacity: ${f.capacity} beds</div>` : ''}
        </div>
      `)
      markersLayer.current.addLayer(marker)
    })
  }, [allFacilities, routingData, showAllFacs])

  // ── Load scenario ─────────────────────────────────────────────────────
  const loadScenario = useCallback(async (idx) => {
    setActiveScenario(idx)
    setLoading(true)
    setRouteInfo(null)

    const s = SCENARIOS[idx]
    try {
      const data = await fetchRoutingMap(s.id, s.specialty, s.origin)
      setRoutingData(data)
      setReasoning(data.reasoning || [])
      setStats({
        distance: data.stats?.distance_km || 0,
        time: data.stats?.time_min || 0,
        facilities: data.stats?.facilities_count || 0,
      })

      // Draw route
      drawRoute(data.route || [], data.deserts || [], data.plan)
    } catch (err) {
      console.error('Routing map error:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  // ── Draw route on map ─────────────────────────────────────────────────
  const drawRoute = useCallback((route, deserts, plan) => {
    if (!mapInstance.current) return
    routeLayer.current.clearLayers()
    desertLayer.current.clearLayers()
    routeMarkersLayer.current.clearLayers()

    // Draw medical deserts as red circles
    deserts.forEach(d => {
      if (!d.center_lat || !d.center_lng) return
      const severity = d.severity === 'critical' ? 80000 : d.severity === 'high' ? 60000 : 40000
      const circle = L.circle([d.center_lat, d.center_lng], {
        radius: severity,
        fillColor: '#ff4500', color: '#ff4500',
        fillOpacity: 0.15, weight: 1, opacity: 0.4,
        dashArray: '5, 8',
      })
      circle.bindPopup(`
        <div style="font-family:'Inter',sans-serif;min-width:180px">
          <div style="font-weight:700;color:#ff4500;margin-bottom:4px">⚠ Medical Desert</div>
          <div style="font-weight:600;color:#e8edf5">${d.region}</div>
          <div style="font-size:0.8rem;color:#8892a8;margin-top:4px">
            Nearest facility: ${d.nearest_distance_km} km away
          </div>
          <div style="font-size:0.8rem;color:#ff4500;margin-top:2px;font-weight:600">
            Severity: ${d.severity?.toUpperCase()}
          </div>
          <div style="font-size:0.75rem;color:#505a70;margin-top:2px">
            Facilities in region: ${d.total_facilities_in_region}
          </div>
        </div>
      `)
      desertLayer.current.addLayer(circle)
    })

    // Draw route polyline
    const coords = route.filter(r => r.lat && r.lng).map(r => [r.lat, r.lng])
    if (coords.length > 1) {
      const polyline = L.polyline(coords, {
        color: '#00f3ff', weight: 3, opacity: 0.8, dashArray: '10, 8',
        className: 'animated-route',
      })
      routeLayer.current.addLayer(polyline)

      // Glow effect
      const glow = L.polyline(coords, {
        color: '#00f3ff', weight: 8, opacity: 0.15,
      })
      routeLayer.current.addLayer(glow)
    }

    // Draw route markers
    route.forEach((stop, i) => {
      if (!stop.lat || !stop.lng) return
      const isFirst = i === 0
      const isLast = i === route.length - 1
      const color = isFirst ? '#06ffa5' : isLast ? '#ff006e'
        : stop.type === 'suggestion' ? '#ffd60a'
        : stop.type === 'placement' ? '#9d00ff' : '#00f3ff'
      const radius = (isFirst || isLast) ? 10 : stop.type === 'suggestion' ? 8 : 7

      const marker = L.circleMarker([stop.lat, stop.lng], {
        radius, fillColor: color, color: '#fff', weight: 2, fillOpacity: 0.9,
      })

      // Add pulsing effect for first/last
      if (isFirst || isLast) {
        const pulse = L.circleMarker([stop.lat, stop.lng], {
          radius: radius + 6, fillColor: color, color: color,
          weight: 1, fillOpacity: 0.15, opacity: 0.3,
        })
        routeMarkersLayer.current.addLayer(pulse)
      }

      const label = isFirst ? 'ORIGIN' : isLast ? 'DESTINATION' : `STOP ${i + 1}`
      marker.bindPopup(`
        <div style="font-family:'Inter',sans-serif;min-width:200px">
          <div style="font-weight:700;color:${color};font-size:0.7rem;margin-bottom:4px">${label}</div>
          <div style="font-weight:600;color:#e8edf5;font-size:0.9rem">${stop.name || 'Unknown'}</div>
          <div style="font-size:0.8rem;color:#8892a8">${stop.city || ''}</div>
          ${stop.distance_km ? `<div style="color:#00f3ff;font-size:0.8rem;margin-top:4px;font-weight:600">${stop.distance_km.toFixed(1)} km</div>` : ''}
          ${stop.distance_from_prev_km ? `<div style="color:#00f3ff;font-size:0.8rem;margin-top:4px">${stop.distance_from_prev_km.toFixed(1)} km from prev</div>` : ''}
          ${stop.capability_match ? `<div style="color:#06ffa5;font-size:0.8rem;margin-top:2px">Capability: ${stop.capability_match}%</div>` : ''}
          ${stop.priority ? `<div style="color:#ffd60a;font-size:0.8rem;margin-top:2px">Priority: ${stop.priority}</div>` : ''}
        </div>
      `)
      routeMarkersLayer.current.addLayer(marker)
    })

    // Update route info
    if (route.length > 0) {
      setRouteInfo({
        origin: route[0]?.name || '—',
        destination: route[route.length - 1]?.name || '—',
        distance: plan?.total_distance_km || plan?.primary_facility?.distance_km || 0,
        time: plan?.primary_facility?.est_travel_min || route.length * 30,
        match: plan?.primary_facility?.capability_match || '—',
      })
    }

    // Fit map to content
    const allCoords = [
      ...coords,
      ...deserts.filter(d => d.center_lat).map(d => [d.center_lat, d.center_lng]),
    ]
    if (allCoords.length > 0) {
      mapInstance.current.fitBounds(L.latLngBounds(allCoords), { padding: [60, 60] })
    }
  }, [])

  // ── Clear routes ──────────────────────────────────────────────────────
  const clearRoutes = () => {
    routeLayer.current?.clearLayers()
    desertLayer.current?.clearLayers()
    routeMarkersLayer.current?.clearLayers()
    setRouteInfo(null)
    setReasoning([])
    setRoutingData(null)
  }

  // ── Load initial scenario ─────────────────────────────────────────────
  useEffect(() => { loadScenario(0) }, [loadScenario])

  return (
    <div style={{
      display: 'grid', gridTemplateColumns: '350px 1fr',
      height: '100vh', position: 'relative', zIndex: 1,
    }}>
      {/* ── Sidebar ────────────────────────────────────────────────── */}
      <div style={{
        background: 'var(--bg-main)', borderRight: '1px solid var(--border-dim)',
        display: 'flex', flexDirection: 'column', overflow: 'hidden',
      }}>
        {/* Header */}
        <div style={{
          padding: '24px 20px',
          background: 'linear-gradient(135deg, rgba(0,243,255,0.08), rgba(131,56,236,0.06))',
          borderBottom: '1px solid var(--border-dim)',
        }}>
          <div style={{
            fontSize: '1.6em', fontWeight: 800, fontFamily: 'var(--font-mono)',
            background: 'linear-gradient(135deg, var(--cyan), var(--purple))',
            WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
            marginBottom: 6,
          }}>⚕ VIRTUE AI</div>
          <div style={{
            fontSize: '0.85em', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)',
            letterSpacing: '0.08em',
          }}>Intelligent Healthcare Routing</div>
        </div>

        {/* Scenarios */}
        <div style={{
          padding: '16px 16px 8px', borderBottom: '1px solid var(--border-dim)',
        }}>
          <div className="font-mono" style={{
            fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '1.5px',
            color: 'var(--cyan)', marginBottom: 12, fontWeight: 600,
          }}>🎯 Routing Scenarios</div>

          {SCENARIOS.map((s, i) => (
            <button key={i} onClick={() => loadScenario(i)} disabled={loading}
              style={{
                display: 'block', width: '100%', textAlign: 'left',
                background: i === activeScenario
                  ? 'linear-gradient(135deg, rgba(0,243,255,0.12), rgba(131,56,236,0.1))'
                  : 'rgba(0,243,255,0.04)',
                border: `1px solid ${i === activeScenario ? 'var(--cyan)' : 'var(--border-dim)'}`,
                borderRadius: 10, padding: '12px 14px', marginBottom: 8,
                cursor: 'pointer', transition: 'all 0.3s',
                boxShadow: i === activeScenario ? '0 0 16px rgba(0,243,255,0.2)' : 'none',
              }}
              onMouseEnter={e => {
                if (i !== activeScenario) e.currentTarget.style.borderColor = 'rgba(0,243,255,0.4)'
              }}
              onMouseLeave={e => {
                if (i !== activeScenario) e.currentTarget.style.borderColor = 'var(--border-dim)'
              }}
            >
              <div style={{
                fontWeight: 600, color: 'var(--cyan)', fontSize: '0.85em', marginBottom: 3,
              }}>{s.icon} {s.title}</div>
              <div style={{
                fontSize: '0.75em', color: 'var(--text-muted)', lineHeight: 1.4,
              }}>{s.desc}</div>
            </button>
          ))}
        </div>

        {/* Reasoning Steps */}
        <div style={{ padding: '16px', flex: 1, overflowY: 'auto' }}>
          <div className="font-mono" style={{
            fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '1.5px',
            color: 'var(--cyan)', marginBottom: 12, fontWeight: 600,
          }}>⟐ AI Reasoning Trace</div>

          {loading && (
            <div style={{ textAlign: 'center', padding: '30px 0' }}>
              <div className="cyber-spinner" style={{ width: 28, height: 28, borderWidth: 3, margin: '0 auto 12px' }} />
              <div className="font-mono" style={{ fontSize: '0.7rem', color: 'var(--cyan)', letterSpacing: '0.12em' }}>
                COMPUTING ROUTE...
              </div>
            </div>
          )}

          {!loading && reasoning.map((step, i) => (
            <div key={i} style={{
              background: 'rgba(0,243,255,0.05)', borderLeft: '3px solid var(--cyan)',
              borderRadius: 8, padding: '12px 14px', marginBottom: 12,
              animation: `slideIn 0.4s ease-out ${i * 0.1}s both`,
            }}>
              <div style={{ display: 'flex', alignItems: 'center', marginBottom: 6 }}>
                <span style={{
                  display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                  background: 'var(--cyan)', color: 'var(--bg-deep)',
                  width: 24, height: 24, borderRadius: '50%', fontWeight: 700,
                  fontSize: '0.75em', marginRight: 10, fontFamily: 'var(--font-mono)',
                }}>{step.step}</span>
                <span style={{ fontWeight: 600, fontSize: '0.85em', color: 'var(--text-primary)' }}>
                  {step.title}
                </span>
              </div>
              <div style={{ fontSize: '0.8em', color: 'var(--text-secondary)', paddingLeft: 34, lineHeight: 1.5 }}>
                {step.content}
              </div>
              {step.data && (
                <div style={{
                  background: 'rgba(0,0,0,0.3)', padding: '8px 10px', borderRadius: 6,
                  marginTop: 6, marginLeft: 34, fontFamily: 'var(--font-mono)',
                  fontSize: '0.75em', color: 'var(--purple)',
                }}>{step.data}</div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* ── Map Area ───────────────────────────────────────────────── */}
      <div style={{ position: 'relative', height: '100vh' }}>
        <div ref={mapRef} style={{ width: '100%', height: '100%' }} />

        {/* Stats Bar */}
        <div style={{
          position: 'absolute', top: 16, left: 16, zIndex: 1000,
          display: 'flex', gap: 12,
        }}>
          {[
            { label: 'Distance (km)', value: stats.distance?.toFixed?.(1) || '—', color: 'var(--cyan)' },
            { label: 'Est. Time (min)', value: stats.time || '—', color: 'var(--green)' },
            { label: 'Facilities', value: stats.facilities || '—', color: 'var(--purple)' },
          ].map((s, i) => (
            <div key={i} style={{
              background: 'rgba(10,14,26,0.92)', border: '1px solid var(--border-med)',
              borderRadius: 10, padding: '12px 18px', backdropFilter: 'blur(10px)',
            }}>
              <div style={{
                fontSize: '1.6em', fontWeight: 700, fontFamily: 'var(--font-mono)', color: s.color,
              }}>{s.value}</div>
              <div style={{
                fontSize: '0.65rem', color: 'var(--text-muted)', textTransform: 'uppercase',
                letterSpacing: '0.1em', marginTop: 4,
              }}>{s.label}</div>
            </div>
          ))}
        </div>

        {/* Map Controls */}
        <div style={{
          position: 'absolute', top: 16, right: 16, zIndex: 1000,
          display: 'flex', flexDirection: 'column', gap: 8,
        }}>
          <button onClick={() => setShowAllFacs(!showAllFacs)}
            className="font-mono" style={{
              background: 'rgba(10,14,26,0.92)', border: '1px solid var(--border-med)',
              color: 'var(--cyan)', padding: '10px 16px', borderRadius: 8,
              cursor: 'pointer', fontWeight: 600, fontSize: '0.8em',
              backdropFilter: 'blur(10px)', letterSpacing: '0.05em',
            }}>
            🏥 {showAllFacs ? 'Hide' : 'Show'} Facilities
          </button>
          <button onClick={clearRoutes}
            className="font-mono" style={{
              background: 'rgba(10,14,26,0.92)', border: '1px solid var(--border-med)',
              color: 'var(--cyan)', padding: '10px 16px', borderRadius: 8,
              cursor: 'pointer', fontWeight: 600, fontSize: '0.8em',
              backdropFilter: 'blur(10px)', letterSpacing: '0.05em',
            }}>
            🗑️ Clear Routes
          </button>
        </div>

        {/* Legend */}
        <div style={{
          position: 'absolute', bottom: 16, right: 16, zIndex: 1000,
          background: 'rgba(10,14,26,0.92)', border: '1px solid var(--border-med)',
          borderRadius: 10, padding: '14px 18px', backdropFilter: 'blur(10px)', maxWidth: 220,
        }}>
          <div className="font-mono" style={{
            fontWeight: 700, marginBottom: 8, color: 'var(--cyan)', fontSize: '0.8em',
          }}>Legend</div>
          {[
            { label: 'Emergency/Trauma', color: '#ff006e' },
            { label: 'Cardiology', color: '#00f3ff' },
            { label: 'Hospital', color: '#8338ec' },
            { label: 'Clinic', color: '#06ffa5' },
            { label: 'Medical Desert', color: '#ff4500' },
            { label: 'Suggested Site', color: '#ffd60a' },
          ].map(item => (
            <div key={item.label} style={{ display: 'flex', alignItems: 'center', margin: '6px 0' }}>
              <span style={{
                width: 14, height: 14, borderRadius: '50%', marginRight: 10,
                background: item.color, boxShadow: `0 0 6px ${item.color}50`,
                display: 'inline-block',
              }} />
              <span style={{ fontSize: '0.78em', color: 'var(--text-secondary)' }}>{item.label}</span>
            </div>
          ))}
        </div>

        {/* Route Info Panel */}
        {routeInfo && (
          <div style={{
            position: 'absolute', bottom: 16, left: 16, zIndex: 1000,
            background: 'rgba(10,14,26,0.92)', border: '1px solid var(--border-med)',
            borderRadius: 10, padding: '18px', backdropFilter: 'blur(10px)', maxWidth: 320,
            animation: 'fadeInUp 0.4s ease-out',
          }}>
            <div className="font-mono" style={{
              fontWeight: 700, marginBottom: 12, color: 'var(--cyan)', fontSize: '0.9em',
            }}>🚑 Route Analysis</div>
            {[
              { label: 'Origin', value: routeInfo.origin, color: 'var(--green)' },
              { label: 'Destination', value: routeInfo.destination, color: 'var(--pink)' },
              { label: 'Distance', value: `${routeInfo.distance?.toFixed?.(1) || routeInfo.distance} km`, color: 'var(--text-primary)' },
              { label: 'Est. Time', value: `${routeInfo.time} min`, color: 'var(--text-primary)' },
              { label: 'Capability Match', value: `${routeInfo.match}${typeof routeInfo.match === 'number' ? '%' : ''}`, color: 'var(--green)' },
            ].map((r, i) => (
              <div key={i} style={{
                display: 'flex', justifyContent: 'space-between', margin: '8px 0', fontSize: '0.85em',
              }}>
                <span style={{ color: 'var(--text-muted)' }}>{r.label}:</span>
                <span style={{
                  color: r.color, fontWeight: 600, fontFamily: 'var(--font-mono)',
                  maxWidth: '55%', textAlign: 'right', overflow: 'hidden',
                  textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                }}>{r.value}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
