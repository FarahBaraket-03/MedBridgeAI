import { useEffect, useRef } from 'react'
import L from 'leaflet'

// Fix default marker icons
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
})

// ── Color-coded circle markers by facility type ──────────────
const TYPE_COLORS = {
  hospital: '#00f3ff',      // cyan
  clinic: '#06ffa5',        // green
  health_center: '#8338ec', // purple
  pharmacy: '#ffd60a',      // yellow
  ngo: '#ff006e',           // pink
  laboratory: '#ff8500',    // orange
  default: '#00b8c9',       // cyan dim
}

function getTypeColor(facility) {
  const t = (facility.type || facility.facility_type || facility.facilityTypeId || '').toLowerCase()
  if (t.includes('hospital')) return TYPE_COLORS.hospital
  if (t.includes('clinic')) return TYPE_COLORS.clinic
  if (t.includes('health') && t.includes('center')) return TYPE_COLORS.health_center
  if (t.includes('pharmacy')) return TYPE_COLORS.pharmacy
  if (t.includes('ngo') || t.includes('foundation')) return TYPE_COLORS.ngo
  if (t.includes('lab')) return TYPE_COLORS.laboratory
  return TYPE_COLORS.default
}

export default function MapView({ facilities, routeData, medicalDeserts, coldSpots, showLegend = true }) {
  const mapRef = useRef(null)
  const mapInstance = useRef(null)
  const markersRef = useRef(null)
  const routeLayerRef = useRef(null)
  const desertsLayerRef = useRef(null)

  // Initialize map
  useEffect(() => {
    if (!mapRef.current) return

    if (!mapInstance.current) {
      mapInstance.current = L.map(mapRef.current, {
        zoomControl: true,
        attributionControl: true,
      }).setView([7.9465, -1.0232], 7)

      // CARTO dark tiles
      L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com/">CARTO</a>',
        subdomains: 'abcd',
        maxZoom: 19,
      }).addTo(mapInstance.current)
    }

    return () => {}
  }, [])

  // Update markers
  useEffect(() => {
    if (!mapInstance.current || !facilities) return

    if (markersRef.current) {
      markersRef.current.clearLayers()
    }

    const markers = L.layerGroup()

    const validFacilities = facilities.filter(
      f => f.latitude != null && f.longitude != null &&
           !isNaN(f.latitude) && !isNaN(f.longitude)
    )

    validFacilities.forEach(f => {
      const color = getTypeColor(f)
      const marker = L.circleMarker([f.latitude, f.longitude], {
        radius: 5,
        fillColor: color,
        color: color,
        weight: 1,
        opacity: 0.9,
        fillOpacity: 0.7,
      })

      const name = f.name || f.facility || 'Unknown'
      const city = f.city || f.address_city || ''
      const type = f.type || f.facility_type || ''
      const specs = (f.specialties || []).slice(0, 5).join(', ')
      const dist = f.distance_km != null ? `<div style="margin-top:4px;color:#00f3ff;font-weight:bold">${f.distance_km.toFixed(1)} km</div>` : ''
      const confidence = f.confidence != null ? `<div style="margin-top:2px;color:${f.confidence > 0.6 ? '#06ffa5' : '#ff006e'}">${(f.confidence * 100).toFixed(0)}% confidence</div>` : ''

      marker.bindPopup(`
        <div style="font-family:'Inter',sans-serif;min-width:160px">
          <div style="font-weight:600;font-size:0.85rem;color:#e8edf5;margin-bottom:4px">${name}</div>
          <div style="font-size:0.75rem;color:#8892a8">${city}${type ? ` • ${type}` : ''}</div>
          ${specs ? `<div style="font-size:0.7rem;color:#505a70;margin-top:4px">${specs}</div>` : ''}
          ${dist}
          ${confidence}
        </div>
      `)
      markers.addLayer(marker)
    })

    mapInstance.current.addLayer(markers)
    markersRef.current = markers

    // Auto-fit bounds to shown facilities (skip for full-dataset displays)
    if (validFacilities.length > 0 && validFacilities.length <= 500) {
      const bounds = L.latLngBounds(
        validFacilities.map(f => [f.latitude, f.longitude])
      )
      mapInstance.current.fitBounds(bounds, { padding: [30, 30], maxZoom: 12 })
    }
  }, [facilities])

  // Draw route if provided
  useEffect(() => {
    if (!mapInstance.current) return

    if (routeLayerRef.current) {
      routeLayerRef.current.clearLayers()
    }

    if (!routeData || !routeData.length) return

    const routeGroup = L.layerGroup()

    // Normalize coordinate field names
    const normalized = routeData.map(r => ({
      ...r,
      latitude: r.latitude ?? r.lat,
      longitude: r.longitude ?? r.lng,
    }))

    // Draw line connecting route points
    const coords = normalized
      .filter(r => r.latitude && r.longitude)
      .map(r => [r.latitude, r.longitude])

    if (coords.length > 1) {
      // Glow layer (wide, transparent)
      routeGroup.addLayer(L.polyline(coords, {
        color: '#00f3ff', weight: 8, opacity: 0.15,
      }))
      // Main route line
      routeGroup.addLayer(L.polyline(coords, {
        color: '#00f3ff', weight: 3, opacity: 0.9, dashArray: '8, 6',
      }))
    }

    // Add numbered stop markers
    normalized.forEach((stop, i) => {
      if (!stop.latitude || !stop.longitude) return

      const isFirst = i === 0
      const isLast = i === normalized.length - 1

      const marker = L.circleMarker([stop.latitude, stop.longitude], {
        radius: isFirst || isLast ? 8 : 6,
        fillColor: isFirst ? '#06ffa5' : isLast ? '#ff006e' : '#00f3ff',
        color: '#fff',
        weight: 2,
        fillOpacity: 0.9,
      })

      marker.bindPopup(`
        <div style="font-family:'Inter',sans-serif">
          <div style="font-weight:700;color:#00f3ff;font-size:0.7rem">STOP ${i + 1}</div>
          <div style="font-weight:600;color:#e8edf5">${stop.name || 'Unknown'}</div>
          <div style="font-size:0.75rem;color:#8892a8">${stop.city || ''}</div>
          ${stop.distance_from_prev_km ? `<div style="color:#00f3ff;font-size:0.75rem;margin-top:4px">${stop.distance_from_prev_km.toFixed(1)} km from prev</div>` : ''}
        </div>
      `)

      routeGroup.addLayer(marker)
    })

    mapInstance.current.addLayer(routeGroup)
    routeLayerRef.current = routeGroup

    if (coords.length > 0) {
      mapInstance.current.fitBounds(L.latLngBounds(coords), { padding: [40, 40] })
    }
  }, [routeData])

  // ── Draw medical deserts + cold spots ──────────────────────────
  useEffect(() => {
    if (!mapInstance.current) return

    if (desertsLayerRef.current) {
      desertsLayerRef.current.clearLayers()
    }

    const hasDeserts = medicalDeserts && medicalDeserts.length > 0
    const hasCold = coldSpots && coldSpots.length > 0
    if (!hasDeserts && !hasCold) return

    const group = L.layerGroup()

    // Medical desert circles
    if (hasDeserts) {
      medicalDeserts.forEach(d => {
        const lat = d.center_lat ?? d.latitude
        const lng = d.center_lng ?? d.longitude
        if (lat == null || lng == null) return

        const severity = (d.severity || 'medium').toLowerCase()
        const radius = severity === 'critical' ? 45000 : severity === 'high' ? 35000 : 25000
        const color = severity === 'critical' ? '#ff006e' : severity === 'high' ? '#ff8500' : '#ffd60a'

        const circle = L.circle([lat, lng], {
          radius,
          color,
          fillColor: color,
          fillOpacity: 0.12,
          weight: 1.5,
          dashArray: '6, 4',
        })

        circle.bindPopup(`
          <div style="font-family:'Inter',sans-serif">
            <div style="font-weight:700;color:${color};font-size:0.7rem">⚠ MEDICAL DESERT</div>
            <div style="font-weight:600;color:#e8edf5">${d.region || 'Unknown region'}</div>
            <div style="font-size:0.75rem;color:#8892a8;margin-top:4px">
              Nearest facility: ${d.nearest_distance_km?.toFixed(1) || '?'} km
            </div>
            <div style="font-size:0.7rem;color:${color};margin-top:2px;text-transform:uppercase;font-weight:600">
              ${severity} severity
            </div>
          </div>
        `)
        group.addLayer(circle)
      })
    }

    // Coverage cold spots (small red dots)
    if (hasCold) {
      coldSpots.forEach(cs => {
        const lat = cs.grid_lat ?? cs.latitude
        const lng = cs.grid_lng ?? cs.longitude
        if (lat == null || lng == null) return

        const dot = L.circleMarker([lat, lng], {
          radius: 4,
          fillColor: '#ff006e',
          color: '#ff006e',
          weight: 0.5,
          fillOpacity: 0.5,
        })

        dot.bindPopup(`
          <div style="font-family:'Inter',sans-serif">
            <div style="font-weight:700;color:#ff006e;font-size:0.7rem">COVERAGE GAP</div>
            <div style="font-size:0.75rem;color:#8892a8">
              Nearest: ${cs.nearest_facility || '?'} (${cs.distance_km?.toFixed(1) || '?'} km)
            </div>
          </div>
        `)
        group.addLayer(dot)
      })
    }

    mapInstance.current.addLayer(group)
    desertsLayerRef.current = group
  }, [medicalDeserts, coldSpots])

  return (
    <div className="relative w-full h-full">
      <div ref={mapRef} style={{ height: '100%', width: '100%' }} />

      {/* Legend */}
      {showLegend && (
        <div className="map-legend">
          <div className="font-mono text-[0.55rem] tracking-[0.12em] uppercase mb-2" style={{ color: 'var(--text-muted)' }}>
            Facility Types
          </div>
          {Object.entries({
            Hospital: TYPE_COLORS.hospital,
            Clinic: TYPE_COLORS.clinic,
            'Health Center': TYPE_COLORS.health_center,
            Pharmacy: TYPE_COLORS.pharmacy,
            NGO: TYPE_COLORS.ngo,
            Laboratory: TYPE_COLORS.laboratory,
          }).map(([name, color]) => (
            <div key={name} className="flex items-center gap-2 py-0.5">
              <span
                className="w-2.5 h-2.5 rounded-full inline-block"
                style={{ background: color, boxShadow: `0 0 4px ${color}60` }}
              />
              <span className="text-[0.65rem]" style={{ color: 'var(--text-secondary)' }}>{name}</span>
            </div>
          ))}
          {/* Desert legend entries when deserts are shown */}
          {medicalDeserts && medicalDeserts.length > 0 && (
            <>
              <div className="font-mono text-[0.55rem] tracking-[0.12em] uppercase mt-3 mb-1" style={{ color: 'var(--text-muted)' }}>
                Medical Deserts
              </div>
              {[['Critical', '#ff006e'], ['High', '#ff8500'], ['Medium', '#ffd60a']].map(([label, c]) => (
                <div key={label} className="flex items-center gap-2 py-0.5">
                  <span className="w-2.5 h-2.5 rounded-full inline-block" style={{ background: c, opacity: 0.7, boxShadow: `0 0 4px ${c}60` }} />
                  <span className="text-[0.65rem]" style={{ color: 'var(--text-secondary)' }}>{label}</span>
                </div>
              ))}
            </>
          )}
        </div>
      )}

      {/* Route overlay info */}
      {routeData && routeData.length > 0 && (
        <div className="route-overlay">
          <div className="font-mono text-[0.6rem] tracking-[0.12em] uppercase mb-2 neon-text">
            Route Analysis
          </div>
          <div className="space-y-1 text-xs" style={{ color: 'var(--text-secondary)' }}>
            <div className="flex justify-between">
              <span>Origin</span>
              <span style={{ color: 'var(--green)' }}>{routeData[0]?.name || '—'}</span>
            </div>
            <div className="flex justify-between">
              <span>Destination</span>
              <span style={{ color: 'var(--pink)' }}>{routeData[routeData.length - 1]?.name || '—'}</span>
            </div>
            <div className="flex justify-between">
              <span>Stops</span>
              <span className="neon-text">{routeData.length}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
