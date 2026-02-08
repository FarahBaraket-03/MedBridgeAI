export default function StatsBar({ stats }) {
  if (!stats) {
    return (
      <div className="flex justify-center gap-12 py-3">
        {[1, 2, 3, 4].map(i => (
          <div key={i} className="w-24 h-14 animate-pulse rounded" style={{ background: 'var(--bg-card)' }} />
        ))}
      </div>
    )
  }

  const items = [
    { label: 'FACILITIES', value: stats.total_facilities, color: 'var(--cyan)' },
    { label: 'REGIONS', value: stats.top_regions?.length || 16, color: 'var(--purple)' },
    { label: 'SPECIALTIES', value: '45+', color: 'var(--green)' },
    { label: 'BED CAPACITY', value: stats.total_beds, color: 'var(--pink)' },
  ]

  return (
    <div className="flex justify-center gap-12 py-3">
      {items.map(item => (
        <div key={item.label} className="flex flex-col items-center">
          <span
            className="font-mono text-2xl font-extrabold"
            style={{ color: item.color, textShadow: `0 0 12px rgba(0,243,255,0.35)` }}
          >
            {typeof item.value === 'number' ? item.value.toLocaleString() : item.value}
          </span>
          <span
            className="font-mono text-[0.6rem] tracking-[0.18em] uppercase mt-1"
            style={{ color: 'var(--text-muted)' }}
          >
            {item.label}
          </span>
        </div>
      ))}
    </div>
  )
}
