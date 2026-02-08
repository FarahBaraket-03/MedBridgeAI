export default function StatsBar({ stats }) {
  if (!stats) {
    return (
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {[1, 2, 3, 4].map(i => (
          <div
            key={i}
            className="glass-card h-20 animate-pulse"
            style={{ background: 'var(--bg-card)' }}
          />
        ))}
      </div>
    )
  }

  const items = [
    { label: 'FACILITIES', value: stats.total_facilities, color: 'var(--cyan)', icon: '⬡' },
    { label: 'REGIONS', value: stats.top_regions?.length || 16, color: 'var(--purple)', icon: '◈' },
    { label: 'SPECIALTIES', value: stats.unique_specialties, color: 'var(--green)', icon: '✦' },
    { label: 'BED CAPACITY', value: stats.total_beds, color: 'var(--pink)', icon: '△' },
  ]

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
      {items.map(item => (
        <div
          key={item.label}
          className="glass-card p-4 flex flex-col justify-between"
          style={{ borderColor: `${item.color}20` }}
        >
          <div className="flex items-center justify-between mb-2">
            <span
              className="font-mono text-[0.6rem] tracking-[0.15em] uppercase font-semibold"
              style={{ color: 'var(--text-muted)' }}
            >
              {item.label}
            </span>
            <span style={{ color: item.color, opacity: 0.6, fontSize: '1rem' }}>
              {item.icon}
            </span>
          </div>
          <span
            className="stat-number"
            style={{ color: item.color, textShadow: `0 0 15px ${item.color}40` }}
          >
            {item.value != null ? item.value.toLocaleString() : '—'}
          </span>
        </div>
      ))}
    </div>
  )
}
