import type { ScreenProps } from '../types'
import { useApp } from '../AppContext'
import { StatusBadge } from '../components/StatusBadge'

// ============================================================
// DASHBOARD (spec §3.1)
// 4 stat tiles (WIN hanko star on "Last run"), advisory reconcile
// banner, violet hero card, and the Recent-runs zebra table.
// ============================================================

const MINCHO = "'Shippori Mincho B1', serif"

// ------------------------------------------------------------
// WIN hanko stamp — vermilion disc + white ring + "WIN" (spec §3.1 Region 1)
// ------------------------------------------------------------
function WinStar() {
  return (
    <div
      aria-hidden="true"
      style={{
        position: 'absolute',
        top: '-13px',
        right: '-11px',
        width: '46px',
        height: '46px',
        animation: 'wiggle 2.6s infinite',
        pointerEvents: 'none',
      }}
    >
      <svg width="46" height="46" viewBox="0 0 46 46" fill="none">
        <circle cx="23" cy="23" r="22" fill="var(--sun)" />
        <circle cx="23" cy="23" r="18" fill="none" stroke="#ffffff" strokeWidth="1.5" opacity="0.55" />
        <text
          x="23"
          y="23"
          textAnchor="middle"
          dominantBaseline="central"
          fill="#ffffff"
          style={{ fontFamily: MINCHO, fontWeight: 800, fontSize: '12px', letterSpacing: '.5px' }}
        >
          WIN
        </text>
      </svg>
    </div>
  )
}

// ------------------------------------------------------------
// Advisory raised-eyebrow amber face (spec §3.1 Region 2 / §6)
// ------------------------------------------------------------
function AdvisoryFace() {
  return (
    <div
      aria-hidden="true"
      style={{
        flex: 'none',
        width: '42px',
        height: '42px',
        borderRadius: '50%',
        background: 'var(--yellow)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        animation: 'bob 2.4s infinite',
      }}
    >
      <svg width="26" height="26" viewBox="0 0 26 26" fill="none" stroke="#3a2600" strokeWidth="2" strokeLinecap="round">
        <path d="M6 7 Q9 4.5 12 7" />
        <path d="M14 6.5 Q17 4.5 20 6.5" />
        <circle cx="9.5" cy="11.5" r="1.4" fill="#3a2600" stroke="none" />
        <circle cx="16.5" cy="11.5" r="1.4" fill="#3a2600" stroke="none" />
        <path d="M8.5 17 Q13 20 17.5 17" />
      </svg>
    </div>
  )
}

// ------------------------------------------------------------
// Hero play-triangle glyph
// ------------------------------------------------------------
function PlayTriangle({ fill = '#3a2600', size = 14 }: { fill?: string; size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 14 14" fill={fill} aria-hidden="true">
      <path d="M3 2 L12 7 L3 12 Z" />
    </svg>
  )
}

// ------------------------------------------------------------
// Hero decorative scene — sun disc + ring + 2-layer mountains
// ------------------------------------------------------------
function HeroScene() {
  return (
    <div
      aria-hidden="true"
      style={{ position: 'absolute', inset: 0, overflow: 'hidden', borderRadius: '7px', pointerEvents: 'none' }}
    >
      {/* sun disc (top-right) */}
      <div
        style={{
          position: 'absolute',
          top: '-44px',
          right: '-40px',
          width: '148px',
          height: '148px',
          borderRadius: '50%',
          background: 'var(--sun)',
          opacity: 0.85,
        }}
      />
      {/* white ring */}
      <div
        style={{
          position: 'absolute',
          top: '-58px',
          right: '-54px',
          width: '176px',
          height: '176px',
          borderRadius: '50%',
          border: '4px solid #ffffff',
          opacity: 0.18,
        }}
      />
      {/* mountains (bottom) */}
      <svg
        viewBox="0 0 340 120"
        preserveAspectRatio="none"
        style={{ position: 'absolute', left: 0, right: 0, bottom: 0, width: '100%', height: '120px' }}
      >
        <path d="M0 120 L0 70 L70 30 L140 75 L210 35 L280 78 L340 48 L340 120 Z" fill="#0c1226" opacity="0.5" />
        <path d="M0 120 L0 92 L60 62 L130 98 L200 66 L270 100 L340 74 L340 120 Z" fill="#080d1c" opacity="0.5" />
      </svg>
    </div>
  )
}

// ------------------------------------------------------------
// Stat tile
// ------------------------------------------------------------
interface StatTile {
  label: string
  value: string
  sub: string
  tileBg: string
  glyph: string
  iconBg: string
  valueFg: string
  labelFg?: string
  subFg?: string
  star?: boolean
}

const STAT_TILES: StatTile[] = [
  {
    label: 'Pending students',
    value: '17',
    sub: 'of 43',
    tileBg: 'var(--panel)',
    glyph: '🧑‍🎓',
    iconBg: 'var(--sky)',
    valueFg: 'var(--ink)',
  },
  {
    label: 'Lessons awaiting',
    value: '41',
    sub: 'to grade',
    tileBg: 'var(--panel)',
    glyph: '📚',
    iconBg: 'var(--pink)',
    valueFg: 'var(--ink)',
  },
  {
    label: 'Last run',
    value: 'OK',
    sub: 'today 09:14',
    tileBg: '#dde7d8',
    glyph: '🚀',
    iconBg: 'var(--lime)',
    valueFg: '#1a7a2e',
    labelFg: '#3a5a3a',
    subFg: '#3a5a3a',
    star: true,
  },
  {
    label: 'Flagged',
    value: '5',
    sub: 'need review',
    tileBg: '#ece0c0',
    glyph: '⚑',
    iconBg: 'var(--yellow)',
    valueFg: '#a06a00',
    labelFg: '#7a5a10',
  },
]

function StatTileCard({ t }: { t: StatTile }) {
  return (
    <div
      style={{
        position: 'relative',
        background: t.tileBg,
        border: '1.5px solid var(--line)',
        borderRadius: '7px',
        boxShadow: '5px 5px 16px var(--shadowc)',
        padding: '16px 17px',
      }}
    >
      {t.star && <WinStar />}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '10px' }}>
        <span
          style={{
            fontFamily: MINCHO,
            fontWeight: 700,
            fontSize: '12.5px',
            letterSpacing: '.4px',
            textTransform: 'uppercase',
            color: t.labelFg ?? 'var(--ink)',
          }}
        >
          {t.label}
        </span>
        <span
          aria-hidden="true"
          style={{
            flex: 'none',
            width: '30px',
            height: '30px',
            border: '1.5px solid var(--line)',
            borderRadius: '3px',
            background: t.iconBg,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '16px',
            lineHeight: 1,
          }}
        >
          {t.glyph}
        </span>
      </div>
      <div
        style={{
          marginTop: '10px',
          fontFamily: MINCHO,
          fontWeight: 800,
          fontSize: '42px',
          lineHeight: 1,
          fontVariantNumeric: 'tabular-nums',
          color: t.valueFg,
        }}
      >
        {t.value}
      </div>
      <div style={{ marginTop: '6px', fontSize: '13px', fontWeight: 600, color: t.subFg ?? 'var(--ink-soft)' }}>
        {t.sub}
      </div>
    </div>
  )
}

// ------------------------------------------------------------
// Dashboard screen
// ------------------------------------------------------------
export function Dashboard({ setScreen, startRun }: ScreenProps) {
  const { runRows: RUN_ROWS } = useApp()
  return (
    <div>
      {/* Region 1 — Stat tiles */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
        {STAT_TILES.map((t) => (
          <StatTileCard key={t.label} t={t} />
        ))}
      </div>

      {/* Region 2 — Advisory banner */}
      <div
        style={{
          marginTop: '18px',
          display: 'flex',
          alignItems: 'center',
          gap: '16px',
          background: '#ece0c0',
          border: '1.5px solid var(--line)',
          borderRadius: '6px',
          boxShadow: '4px 4px 16px var(--shadowc)',
          padding: '14px 18px',
        }}
      >
        <AdvisoryFace />
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontFamily: MINCHO, fontWeight: 800, fontSize: '15px', color: '#3a2600' }}>
            Heads up — there's something to reconcile
          </div>
          <div style={{ marginTop: '4px', fontSize: '13.5px', color: '#3a2600' }}>
            1 lesson was completed by a previous run. It looks like a leftover — review it in the{' '}
            <strong>Reconcile</strong> tab before your next full-auto run.
          </div>
        </div>
        <button
          className="squish"
          onClick={() => setScreen('history')}
          style={{
            flex: 'none',
            background: 'var(--yellow)',
            color: '#3a2600',
            border: '1.5px solid var(--line)',
            borderRadius: '4px',
            boxShadow: '2px 2px 13px var(--shadowc)',
            fontFamily: MINCHO,
            fontWeight: 700,
            fontSize: '13.5px',
            padding: '9px 15px',
          }}
        >
          Reconcile →
        </button>
      </div>

      {/* Region 3 — Hero + Recent runs */}
      <div
        style={{
          marginTop: '18px',
          display: 'grid',
          gridTemplateColumns: '340px 1fr',
          gap: '18px',
          alignItems: 'start',
        }}
      >
        {/* HERO (left) */}
        <div
          style={{
            position: 'relative',
            border: '1.5px solid var(--line)',
            borderRadius: '7px',
            boxShadow: '6px 6px 16px var(--shadowc)',
            background: 'var(--violet)',
            padding: '22px 20px',
            overflow: 'hidden',
          }}
        >
          <HeroScene />
          <div style={{ position: 'relative' }}>
            <div style={{ fontFamily: MINCHO, fontWeight: 800, fontSize: '22px', color: '#ffffff' }}>
              Ready to grade?
            </div>
            <div style={{ marginTop: '8px', fontSize: '13px', color: '#e9e3d2', lineHeight: 1.45 }}>
              17 students are waiting with 41 lessons. Kick off a run — start with a safe Dry-run.
            </div>
            <button
              className="squish"
              onClick={() => setScreen('new')}
              style={{
                marginTop: '18px',
                width: '100%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '9px',
                background: 'var(--yellow)',
                color: '#3a2600',
                border: '1.5px solid var(--line)',
                borderRadius: '5px',
                boxShadow: '4px 4px 13px var(--shadowc)',
                fontFamily: MINCHO,
                fontWeight: 800,
                fontSize: '18px',
                padding: '13px 16px',
              }}
            >
              <PlayTriangle fill="#3a2600" size={16} />
              Start a run
            </button>
            <button
              className="squish"
              onClick={() => startRun('dryrun')}
              style={{
                marginTop: '10px',
                width: '100%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '7px',
                background: 'rgba(255,255,255,.16)',
                color: '#ffffff',
                border: '1.5px solid var(--line)',
                borderRadius: '4px',
                fontFamily: MINCHO,
                fontWeight: 700,
                fontSize: '12.5px',
                padding: '9px 12px',
              }}
            >
              ⚡ Quick Dry-run
            </button>
          </div>
        </div>

        {/* RECENT RUNS (right) */}
        <div
          style={{
            background: 'var(--panel)',
            border: '1.5px solid var(--line)',
            borderRadius: '7px',
            boxShadow: '5px 5px 16px var(--shadowc)',
            overflow: 'hidden',
          }}
        >
          {/* header strip */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: '12px',
              background: 'var(--panel2)',
              borderBottom: '1.5px solid var(--line)',
              padding: '13px 18px',
            }}
          >
            <span style={{ fontFamily: MINCHO, fontWeight: 800, fontSize: '16px', color: 'var(--ink)' }}>
              Recent runs
            </span>
            <button
              className="squish"
              onClick={() => setScreen('history')}
              style={{
                background: 'transparent',
                border: 'none',
                padding: 0,
                fontFamily: MINCHO,
                fontWeight: 700,
                fontSize: '13px',
                color: 'var(--violet)',
              }}
            >
              View all →
            </button>
          </div>

          {/* table */}
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
            <thead>
              <tr>
                {['Mode', 'Started', 'Counts', 'Status'].map((h) => (
                  <th
                    key={h}
                    style={{
                      textAlign: 'left',
                      padding: '10px 18px',
                      fontFamily: MINCHO,
                      fontWeight: 700,
                      fontSize: '11px',
                      letterSpacing: '.4px',
                      textTransform: 'uppercase',
                      color: 'var(--ink-soft)',
                      borderBottom: '1px solid var(--line)',
                    }}
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {RUN_ROWS.map((r, i) => (
                <tr
                  key={r.id}
                  className="squish"
                  onClick={() => setScreen('history')}
                  style={{
                    background: i % 2 === 0 ? 'var(--panel)' : 'var(--panel2)',
                    borderTop: '1px solid var(--line)',
                  }}
                >
                  <td style={{ padding: '9px 18px' }}>
                    <StatusBadge status={r.modeBadgeStatus} label={r.modeBadgeLabel} />
                  </td>
                  <td style={{ padding: '9px 18px', color: 'var(--ink)' }}>
                    <div style={{ fontWeight: 600 }}>{r.started}</div>
                    <div style={{ fontSize: '12px', color: 'var(--ink-soft)' }}>{r.duration}</div>
                  </td>
                  <td
                    style={{
                      padding: '9px 18px',
                      color: 'var(--ink-soft)',
                      fontVariantNumeric: 'tabular-nums',
                    }}
                  >
                    {r.counts}
                  </td>
                  <td style={{ padding: '9px 18px' }}>
                    <StatusBadge status={r.statusBadgeStatus} label={r.statusBadgeLabel} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default Dashboard
