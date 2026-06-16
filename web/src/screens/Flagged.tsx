import type { ScreenProps } from '../types'
import { FLAGGED_ITEMS } from '../data'

// ============================================================
// Raised-eyebrow mascot face — 28×28 round amber avatar glyph
// (one-off SVG per spec §6; strokes #3a2600 on var(--yellow))
// ============================================================
function MascotRaisedBrow() {
  return (
    <svg
      width="28"
      height="28"
      viewBox="0 0 28 28"
      fill="none"
      stroke="#3a2600"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {/* raised + flat brows */}
      <path d="M7 9 Q9.5 6.5 12 9" />
      <path d="M15 8.5 Q17.5 7.5 20 8.5" />
      {/* eyes */}
      <circle cx="9.5" cy="13" r="1.4" fill="#3a2600" stroke="none" />
      <circle cx="18" cy="13" r="1.4" fill="#3a2600" stroke="none" />
      {/* small wry smile */}
      <path d="M9.5 19 Q14 22 18.5 19" />
    </svg>
  )
}

// ============================================================
// FLAGGED (spec §3.7) — 2-column grid of 5 amber notice cards
// ============================================================
export function Flagged(props: ScreenProps) {
  const { showToast } = props

  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(2, 1fr)',
        gap: '14px',
        alignItems: 'start',
      }}
    >
      {FLAGGED_ITEMS.map((f) => (
        <div
          key={f.id}
          style={{
            display: 'flex',
            gap: '15px',
            background: '#ece2cf',
            border: '1.5px solid var(--line)',
            borderRadius: '6px',
            boxShadow: '4px 4px 16px var(--shadowc)',
            padding: '18px',
          }}
        >
          {/* Left — amber raised-eyebrow mascot avatar (bob) */}
          <div
            style={{
              flex: 'none',
              width: '46px',
              height: '46px',
              borderRadius: '50%',
              background: 'var(--yellow)',
              border: '1.5px solid var(--line)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              animation: 'bob 2.6s ease-in-out infinite',
            }}
          >
            <MascotRaisedBrow />
          </div>

          {/* Right — content */}
          <div style={{ flex: 1, minWidth: 0 }}>
            {/* Reason title + severity badge */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                flexWrap: 'wrap',
              }}
            >
              <span
                style={{
                  fontFamily: "'Shippori Mincho B1', serif",
                  fontWeight: 800,
                  fontSize: '15px',
                  color: '#3a2600',
                }}
              >
                {f.reason}
              </span>
              <span
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  padding: '3px 9px',
                  borderRadius: '99px',
                  border: '1.5px solid var(--line)',
                  background: '#fff',
                  color: '#a06a00',
                  fontFamily: "'Shippori Mincho B1', serif",
                  fontWeight: 700,
                  fontSize: '11px',
                  letterSpacing: '.4px',
                  textTransform: 'uppercase',
                  lineHeight: 1,
                  whiteSpace: 'nowrap',
                }}
              >
                {f.severity}
              </span>
            </div>

            {/* Meta line */}
            <div
              style={{
                marginTop: '5px',
                fontSize: '12.5px',
                fontWeight: 600,
                color: '#7a5a10',
              }}
            >
              {f.student} · {f.lesson} · ex {f.ex}
            </div>

            {/* Detail paragraph */}
            <p
              style={{
                margin: '11px 0 0',
                fontSize: '13.5px',
                lineHeight: 1.5,
                color: '#3a2600',
              }}
            >
              {f.detail}
            </p>

            {/* Footer buttons */}
            <div style={{ display: 'flex', gap: '9px', marginTop: '15px' }}>
              <button
                className="squish"
                onClick={() =>
                  showToast('info', `Opening ${f.student} ${f.ex} for manual review`)
                }
                style={{
                  flex: 1,
                  padding: '9px 14px',
                  border: '1.5px solid var(--line)',
                  borderRadius: '4px',
                  background: 'var(--violet)',
                  color: '#fff',
                  fontFamily: "'Shippori Mincho B1', serif",
                  fontWeight: 700,
                  fontSize: '13px',
                  boxShadow: '2px 2px 13px var(--shadowc)',
                }}
              >
                Resolve manually
              </button>
              <button
                className="squish"
                onClick={() => showToast('info', `Retrying ${f.student} ${f.ex}…`)}
                style={{
                  flex: 'none',
                  padding: '9px 14px',
                  border: '1.5px solid var(--line)',
                  borderRadius: '4px',
                  background: '#fff',
                  color: '#3a2600',
                  fontFamily: "'Shippori Mincho B1', serif",
                  fontWeight: 700,
                  fontSize: '13px',
                  boxShadow: '2px 2px 13px var(--shadowc)',
                }}
              >
                ↻ Retry
              </button>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

export default Flagged
