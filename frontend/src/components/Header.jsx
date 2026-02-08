export default function Header() {
  return (
    <header
      className="relative px-6 pt-10 pb-8 flex flex-col items-center justify-center"
      style={{
        background: 'linear-gradient(180deg, rgba(0,243,255,0.07) 0%, transparent 100%)',
        borderBottom: '1px solid var(--border-dim)',
      }}
    >
      {/* Centered logo + title */}
      <div className="flex items-center gap-3 mb-2">
        <span
          className="font-mono text-2xl"
          style={{ color: 'var(--cyan)', textShadow: '0 0 18px rgba(0,243,255,0.5)' }}
        >
          ⚕
        </span>
        <h1
          className="font-mono text-3xl font-extrabold tracking-[0.25em] leading-tight"
          style={{ color: 'var(--cyan)', textShadow: '0 0 14px rgba(0,243,255,0.4)' }}
        >
          VIRTUE AI
        </h1>
      </div>
      <p
        className="font-mono text-xs tracking-[0.2em] uppercase"
        style={{ color: 'var(--text-muted)' }}
      >
        Healthcare Intelligence Layer
      </p>
    </header>
  )
}
