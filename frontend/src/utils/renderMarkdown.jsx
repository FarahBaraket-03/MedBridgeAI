/**
 * Shared markdown renderer — converts LLM markdown text into styled JSX.
 *
 * Handles:
 *  - **bold** → <strong>
 *  - Lines starting with  - / • / * → bullet <li>
 *  - Lines starting with  ### / ## / #  → heading
 *  - Blank-line paragraph breaks
 *  - Numeric lists  1. 2. 3. → ordered <li>
 */

/**
 * Convert a plain-text markdown string into React elements.
 * @param {string} text  – raw LLM output
 * @param {object} [opts]
 * @param {string} [opts.textColor]  – CSS color for body text  (default: inherit)
 * @param {string} [opts.boldColor]  – CSS color for **bold** text (default: --text-primary)
 * @returns {JSX.Element|string|null}
 */
export default function renderMarkdown(text, opts = {}) {
  if (!text) return null

  const {
    textColor = 'inherit',
    boldColor = 'var(--text-primary)',
  } = opts

  // ── 1.  Split into lines ──────────────────────────────────────
  const lines = text.split('\n')

  const elements = []
  let bulletBuffer = []  // accumulate consecutive bullet lines
  let orderedBuffer = [] // accumulate consecutive ordered-list lines
  let key = 0

  const flushBullets = () => {
    if (bulletBuffer.length === 0) return
    elements.push(
      <ul key={key++} style={{ margin: '6px 0 6px 1.1rem', padding: 0, listStyleType: 'disc' }}>
        {bulletBuffer.map((b, i) => (
          <li key={i} style={{ color: textColor, fontSize: 'inherit', lineHeight: 1.6, marginBottom: 2 }}>
            {inlineBold(b, boldColor)}
          </li>
        ))}
      </ul>,
    )
    bulletBuffer = []
  }

  const flushOrdered = () => {
    if (orderedBuffer.length === 0) return
    elements.push(
      <ol key={key++} style={{ margin: '6px 0 6px 1.1rem', padding: 0, listStyleType: 'decimal' }}>
        {orderedBuffer.map((b, i) => (
          <li key={i} style={{ color: textColor, fontSize: 'inherit', lineHeight: 1.6, marginBottom: 2 }}>
            {inlineBold(b, boldColor)}
          </li>
        ))}
      </ol>,
    )
    orderedBuffer = []
  }

  for (const raw of lines) {
    const line = raw.trimEnd()

    // ── Blank line → paragraph break ────────────────────────────
    if (line.trim() === '') {
      flushBullets()
      flushOrdered()
      elements.push(<div key={key++} style={{ height: 6 }} />)
      continue
    }

    // ── Heading  ###  ──────────────────────────────────────────
    const headingMatch = line.match(/^(#{1,3})\s+(.+)/)
    if (headingMatch) {
      flushBullets()
      flushOrdered()
      const level = headingMatch[1].length
      const fontSize = level === 1 ? '0.95rem' : level === 2 ? '0.85rem' : '0.8rem'
      elements.push(
        <div
          key={key++}
          style={{
            fontSize,
            fontWeight: 700,
            color: boldColor,
            marginTop: 8,
            marginBottom: 2,
            letterSpacing: '0.02em',
          }}
        >
          {inlineBold(headingMatch[2], boldColor)}
        </div>,
      )
      continue
    }

    // ── Unordered bullet  - / • / *  ────────────────────────────
    const bulletMatch = line.match(/^\s*[-•*]\s+(.+)/)
    if (bulletMatch) {
      flushOrdered()
      bulletBuffer.push(bulletMatch[1])
      continue
    }

    // ── Ordered list  1.  2.  ───────────────────────────────────
    const orderedMatch = line.match(/^\s*\d+[.)]\s+(.+)/)
    if (orderedMatch) {
      flushBullets()
      orderedBuffer.push(orderedMatch[1])
      continue
    }

    // ── Normal paragraph line ───────────────────────────────────
    flushBullets()
    flushOrdered()
    elements.push(
      <p key={key++} style={{ color: textColor, margin: '2px 0', lineHeight: 1.6 }}>
        {inlineBold(line, boldColor)}
      </p>,
    )
  }

  // Flush anything remaining
  flushBullets()
  flushOrdered()

  return <>{elements}</>
}

// ── Inline: convert **bold** segments → <strong> ──────────────────
function inlineBold(text, boldColor) {
  if (!text) return text
  const parts = text.split(/\*\*(.+?)\*\*/g)
  if (parts.length === 1) return text
  return parts.map((part, i) =>
    i % 2 === 1
      ? <strong key={i} style={{ color: boldColor, fontWeight: 600 }}>{part}</strong>
      : part,
  )
}
