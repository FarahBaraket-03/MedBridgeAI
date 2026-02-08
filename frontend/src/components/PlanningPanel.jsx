import { useState } from 'react'

const SCENARIOS = [
  {
    id: 'emergency_routing',
    icon: '🚑',
    name: 'Emergency Routing',
    desc: 'Find nearest capable facility for emergency cases',
    color: 'var(--pink)',
    query: 'Emergency routing for cardiac patient in Tamale',
  },
  {
    id: 'specialist_deployment',
    icon: '👨‍⚕️',
    name: 'Specialist Deployment',
    desc: 'Optimal deployment route for specialist teams',
    color: 'var(--cyan)',
    query: 'Deploy cardiology specialist team across Ghana',
  },
  {
    id: 'equipment_distribution',
    icon: '🏥',
    name: 'Equipment Distribution',
    desc: 'Priority regions for equipment distribution',
    color: 'var(--purple)',
    query: 'Distribute ventilators across Ghana regions',
  },
  {
    id: 'new_facility_placement',
    icon: '📍',
    name: 'New Facility Placement',
    desc: 'Optimal locations for new facilities',
    color: 'var(--green)',
    query: 'Where should we place new neurosurgery facilities?',
  },
  {
    id: 'capacity_planning',
    icon: '📊',
    name: 'Capacity Planning',
    desc: 'Regional capacity analysis and expansion',
    color: 'var(--yellow)',
    query: 'Capacity planning analysis across all regions',
  },
]

export default function PlanningPanel({ onRunScenario, loading }) {
  const [hoveredId, setHoveredId] = useState(null)

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2 mb-3 px-1">
        <span
          className="font-mono text-[0.6rem] tracking-[0.15em] uppercase font-semibold"
          style={{ color: 'var(--text-muted)' }}
        >
          ▸ Planning Scenarios
        </span>
      </div>

      {SCENARIOS.map(s => {
        const isHovered = hoveredId === s.id
        return (
          <button
            key={s.id}
            className="w-full text-left rounded-lg p-3 transition-all duration-200 cursor-pointer group"
            style={{
              background: isHovered ? 'var(--bg-card-hover)' : 'var(--bg-card)',
              border: `1px solid ${isHovered ? `${s.color}40` : 'var(--border-dim)'}`,
              boxShadow: isHovered ? `0 0 12px ${s.color}15` : 'none',
            }}
            onClick={() => onRunScenario(s.query)}
            onMouseEnter={() => setHoveredId(s.id)}
            onMouseLeave={() => setHoveredId(null)}
            disabled={loading}
          >
            <div className="flex items-center gap-2.5">
              <span
                className="w-8 h-8 rounded-md flex items-center justify-center text-sm shrink-0"
                style={{
                  background: `${s.color}12`,
                  border: `1px solid ${s.color}25`,
                }}
              >
                {s.icon}
              </span>
              <div className="flex-1 min-w-0">
                <div
                  className="font-mono text-xs font-bold tracking-wider"
                  style={{ color: isHovered ? s.color : 'var(--text-primary)' }}
                >
                  {s.name}
                </div>
                <p
                  className="text-[0.65rem] mt-0.5 leading-snug"
                  style={{ color: 'var(--text-muted)' }}
                >
                  {s.desc}
                </p>
              </div>
              <span
                className="text-xs transition-transform duration-200"
                style={{
                  color: s.color,
                  opacity: isHovered ? 1 : 0,
                  transform: isHovered ? 'translateX(0)' : 'translateX(-4px)',
                }}
              >
                ▸
              </span>
            </div>
          </button>
        )
      })}
    </div>
  )
}
