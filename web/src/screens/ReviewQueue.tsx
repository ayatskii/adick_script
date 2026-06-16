import { useState } from 'react'
import type { ScreenProps, ReviewItem, ReviewItemType, ReviewItemStatus } from '../types'
import { useApp } from '../AppContext'
import StatusBadge from '../components/StatusBadge'

// ============================================================
// Local UI types (not in shared types) — filter selection
// ============================================================
type TypeFilter = 'all' | ReviewItemType

const MINCHO = "'Shippori Mincho B1', serif"
const MONO = "'JetBrains Mono', monospace"

// ============================================================
// Confidence color thresholds (spec §3.4): ≥0.85 green / ≥0.70 blue / else ochre
// ============================================================
function confColor(conf: number): string {
  if (conf >= 0.85) return '#2f8f6b'
  if (conf >= 0.7) return '#3f72b0'
  return '#cf9a36'
}

function clampScore(n: number): number {
  return Math.max(0, Math.min(10, n))
}

// ============================================================
// One-off inline SVGs (spec §6)
// ============================================================
function CheckCircle() {
  // 120px bobbing green check-circle, empty/all-done state
  return (
    <svg
      width="120"
      height="120"
      viewBox="0 0 120 120"
      fill="none"
      style={{ animation: 'bob 2.4s ease-in-out infinite' }}
    >
      <circle cx="60" cy="60" r="52" fill="var(--lime)" />
      <path
        d="M38 62 L54 78 L84 44"
        fill="none"
        stroke="#ffffff"
        strokeWidth="9"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

function PlayGlyph({ color }: { color: string }) {
  return (
    <svg width="13" height="13" viewBox="0 0 13 13" fill={color}>
      <path d="M3 2 L11 6.5 L3 11 Z" />
    </svg>
  )
}

function XGlyph({ color }: { color: string }) {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round">
      <line x1="3" y1="3" x2="11" y2="11" />
      <line x1="11" y1="3" x2="3" y2="11" />
    </svg>
  )
}

function ThumbsUpGlyph({ color }: { color: string }) {
  return (
    <svg width="15" height="15" viewBox="0 0 15 15" fill="none" stroke={color} strokeWidth="1.6" strokeLinejoin="round" strokeLinecap="round">
      <path d="M4 7 L4 13 L11 13 Q12 13 12.3 12 L13.4 8.2 Q13.6 7 12.3 7 L8.5 7 L9 4 Q9.1 2 7.6 2 Q7 2 6.7 2.7 L4 7 Z" />
      <line x1="1.5" y1="7" x2="4" y2="7" />
      <line x1="1.5" y1="13" x2="4" y2="13" />
    </svg>
  )
}

function TypeIcon({ type }: { type: ReviewItemType }) {
  return (
    <span style={{ fontSize: '16px', lineHeight: 1 }} aria-hidden="true">
      {type === 'audio' ? '🔊' : '✎'}
    </span>
  )
}

// ============================================================
// Mapping per-item status → its StatusBadge (spec §3.4)
// ============================================================
function statusBadgeFor(status: ReviewItemStatus) {
  switch (status) {
    case 'approved':
      return <StatusBadge status="graded" label="Approved" />
    case 'rejected':
      return <StatusBadge status="error" label="Rejected" />
    case 'submitted':
      return <StatusBadge status="graded" label="Submitted" />
    default:
      return null
  }
}

// ============================================================
// Card body background per status (spec §3.4)
// ============================================================
function cardBg(status: ReviewItemStatus): string {
  switch (status) {
    case 'approved':
      return 'rgba(31,207,93,.08)'
    case 'rejected':
      return 'rgba(255,77,77,.07)'
    case 'submitted':
      return 'var(--panel2)'
    default:
      return 'var(--panel)'
  }
}

export function ReviewQueue(props: ScreenProps) {
  const { showToast } = props
  const { reviewItems: seedItems } = useApp()

  // Per-item editable state (status, score, comment, edited) — local
  const [items, setItems] = useState<ReviewItem[]>(() =>
    seedItems.map((it) => ({ ...it })),
  )
  const [typeFilter, setTypeFilter] = useState<TypeFilter>('all')

  const allDone = items.every((it) => it.status === 'submitted')

  const approvedN = items.filter((it) => it.status === 'approved').length
  const editedN = items.filter((it) => it.edited && it.status !== 'submitted').length
  const rejectedN = items.filter((it) => it.status === 'rejected').length

  const visible = items.filter((it) => {
    if (it.status === 'submitted') return false
    if (typeFilter === 'all') return true
    return it.type === typeFilter
  })

  function patch(id: string, fields: Partial<ReviewItem>) {
    setItems((prev) => prev.map((it) => (it.id === id ? { ...it, ...fields } : it)))
  }

  function setScore(id: string, next: number) {
    const clamped = clampScore(next)
    setItems((prev) =>
      prev.map((it) =>
        it.id === id
          ? { ...it, score: clamped, edited: clamped !== it.score ? true : it.edited }
          : it,
      ),
    )
  }

  function setComment(id: string, original: string, value: string) {
    setItems((prev) =>
      prev.map((it) =>
        it.id === id
          ? { ...it, comment: value, edited: value !== original ? true : it.edited }
          : it,
      ),
    )
  }

  function approve(id: string) {
    patch(id, { status: 'approved' })
  }

  function reject(id: string) {
    patch(id, { status: 'rejected' })
  }

  function approveHighConfidence() {
    let n = 0
    setItems((prev) =>
      prev.map((it) => {
        if (it.status !== 'submitted' && it.conf >= 0.85) {
          n += 1
          return { ...it, status: 'approved' }
        }
        return it
      }),
    )
    showToast('ok', `Approved ${n} high-confidence ${n === 1 ? 'grade' : 'grades'}`)
  }

  function approveAll() {
    let n = 0
    setItems((prev) =>
      prev.map((it) => {
        if (it.status !== 'submitted') {
          n += 1
          return { ...it, status: 'approved' }
        }
        return it
      }),
    )
    showToast('ok', `Approved ${n} ${n === 1 ? 'grade' : 'grades'}`)
  }

  function submit() {
    if (approvedN === 0) {
      showToast('warn', 'Nothing approved yet — approve some grades first.')
      return
    }
    setItems((prev) =>
      prev.map((it) => (it.status === 'approved' ? { ...it, status: 'submitted' } : it)),
    )
    showToast('ok', `Submitted ${approvedN} ${approvedN === 1 ? 'grade' : 'grades'}`)
  }

  // ----------------------------------------------------------
  // ALL-DONE / EMPTY STATE
  // ----------------------------------------------------------
  if (allDone) {
    return (
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          textAlign: 'center',
          padding: '64px 20px',
          gap: '6px',
        }}
      >
        <CheckCircle />
        <h2
          style={{
            margin: '14px 0 0',
            fontFamily: MINCHO,
            fontWeight: 800,
            fontSize: '24px',
            color: 'var(--ink)',
          }}
        >
          Queue&apos;s all clear!
        </h2>
        <p style={{ margin: 0, fontSize: '14px', color: 'var(--ink-soft)', maxWidth: '420px' }}>
          Every proposed grade has been reviewed and submitted. Nice work.
        </p>
      </div>
    )
  }

  // ----------------------------------------------------------
  // ACTIVE STATE
  // ----------------------------------------------------------
  const typePills: { key: TypeFilter; label: string }[] = [
    { key: 'all', label: 'All types' },
    { key: 'audio', label: '🔊 Audio' },
    { key: 'text', label: '✎ Text' },
  ]

  return (
    <div>
      {/* ===== FILTER BAR ===== */}
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          gap: '9px',
          marginBottom: '16px',
        }}
      >
        <span
          style={{
            fontFamily: MINCHO,
            fontWeight: 700,
            fontSize: '12px',
            letterSpacing: '.5px',
            textTransform: 'uppercase',
            color: 'var(--ink-soft)',
          }}
        >
          Filter
        </span>

        {typePills.map((p) => {
          const active = typeFilter === p.key
          return (
            <button
              key={p.key}
              className="squish"
              onClick={() => setTypeFilter(p.key)}
              style={{
                fontFamily: MINCHO,
                fontWeight: 700,
                fontSize: '12.5px',
                padding: '7px 13px',
                border: '1.5px solid var(--line)',
                borderRadius: '99px',
                boxShadow: '2px 2px 13px var(--shadowc)',
                background: active ? 'var(--violet)' : 'var(--panel)',
                color: active ? '#fff' : 'var(--ink)',
              }}
            >
              {p.label}
            </button>
          )
        })}

        {/* divider */}
        <span
          aria-hidden="true"
          style={{ width: '1.5px', height: '22px', background: 'var(--line)', margin: '0 3px' }}
        />

        {/* decorative dropdowns */}
        {['Student ▾', 'Confidence ▾'].map((label) => (
          <button
            key={label}
            className="squish"
            type="button"
            style={{
              fontFamily: MINCHO,
              fontWeight: 700,
              fontSize: '12.5px',
              padding: '7px 13px',
              border: '1.5px solid var(--line)',
              borderRadius: '99px',
              boxShadow: '2px 2px 13px var(--shadowc)',
              background: 'var(--panel)',
              color: 'var(--ink)',
            }}
          >
            {label}
          </button>
        ))}

        <span style={{ flex: 1 }} />

        <button
          className="squish"
          onClick={approveHighConfidence}
          style={{
            fontFamily: MINCHO,
            fontWeight: 700,
            fontSize: '12.5px',
            padding: '7px 13px',
            border: '1.5px solid var(--line)',
            borderRadius: '99px',
            boxShadow: '2px 2px 13px var(--shadowc)',
            background: 'var(--sky)',
            color: '#fff',
          }}
        >
          ⚡ Approve high-confidence
        </button>
        <button
          className="squish"
          onClick={approveAll}
          style={{
            fontFamily: MINCHO,
            fontWeight: 700,
            fontSize: '12.5px',
            padding: '7px 13px',
            border: '1.5px solid var(--line)',
            borderRadius: '99px',
            boxShadow: '2px 2px 13px var(--shadowc)',
            background: 'var(--lime)',
            color: '#fff',
          }}
        >
          ✓ Approve all
        </button>
      </div>

      {/* ===== CARDS ===== */}
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '14px',
          paddingBottom: '80px',
        }}
      >
        {visible.map((it) => {
          const cColor = confColor(it.conf)
          const litSegments = Math.round(it.conf * 5)
          const contentLabel = it.type === 'audio' ? 'Transcript' : 'Written answer'
          return (
            <div
              key={it.id}
              style={{
                border: '1.5px solid var(--line)',
                borderRadius: '6px',
                boxShadow: '4px 4px 16px var(--shadowc)',
                background: cardBg(it.status),
                overflow: 'hidden',
              }}
            >
              {/* card header */}
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                  padding: '12px 18px',
                  background: 'var(--panel2)',
                  borderBottom: '1.5px solid var(--line)',
                }}
              >
                <TypeIcon type={it.type} />
                <span
                  style={{
                    fontFamily: MINCHO,
                    fontWeight: 800,
                    fontSize: '15px',
                    color: 'var(--ink)',
                  }}
                >
                  {it.student}
                </span>
                <span style={{ fontSize: '12.5px', color: 'var(--ink-soft)' }}>
                  {it.lesson} · {it.section} · ex {it.ex}
                </span>

                <span style={{ flex: 1 }} />

                {it.edited && it.status !== 'submitted' && (
                  <span
                    style={{
                      fontFamily: MINCHO,
                      fontWeight: 800,
                      fontSize: '10.5px',
                      letterSpacing: '.4px',
                      textTransform: 'uppercase',
                      padding: '3px 8px',
                      borderRadius: '3px',
                      background: 'var(--yellow)',
                      color: '#3a2600',
                    }}
                  >
                    Edited
                  </span>
                )}
                {statusBadgeFor(it.status)}
              </div>

              {/* card body */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr 200px',
                  gap: '0',
                }}
              >
                {/* left column */}
                <div style={{ padding: '15px 18px', display: 'flex', flexDirection: 'column', gap: '11px' }}>
                  {it.type === 'audio' && (
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '11px',
                        padding: '9px 11px',
                        border: '1.5px solid var(--line)',
                        borderRadius: '4px',
                        background: 'var(--panel)',
                      }}
                    >
                      <button
                        className="squish"
                        type="button"
                        aria-label="Play audio"
                        style={{
                          width: '32px',
                          height: '32px',
                          flex: 'none',
                          display: 'inline-flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          borderRadius: '50%',
                          border: '1.5px solid var(--line)',
                          background: 'var(--violet)',
                        }}
                      >
                        <PlayGlyph color="#fff" />
                      </button>
                      <div
                        style={{
                          flex: 1,
                          height: '8px',
                          borderRadius: '99px',
                          background: 'var(--chip)',
                          overflow: 'hidden',
                        }}
                      >
                        <div style={{ width: '24%', height: '100%', background: 'var(--violet)' }} />
                      </div>
                      <span style={{ fontFamily: MONO, fontSize: '12px', color: 'var(--ink-soft)' }}>
                        0:00 / {it.duration}
                      </span>
                    </div>
                  )}

                  <div
                    style={{
                      fontFamily: MINCHO,
                      fontWeight: 700,
                      fontSize: '11px',
                      letterSpacing: '.4px',
                      textTransform: 'uppercase',
                      color: 'var(--ink-soft)',
                    }}
                  >
                    {contentLabel}
                  </div>
                  <p
                    style={{
                      margin: 0,
                      fontStyle: 'italic',
                      fontSize: '13px',
                      lineHeight: 1.55,
                      color: 'var(--ink)',
                    }}
                  >
                    {it.transcript}
                  </p>

                  <div
                    style={{
                      fontFamily: MINCHO,
                      fontWeight: 700,
                      fontSize: '11px',
                      letterSpacing: '.4px',
                      textTransform: 'uppercase',
                      color: 'var(--ink-soft)',
                    }}
                  >
                    AI comment · editable
                  </div>
                  <textarea
                    value={it.comment}
                    onChange={(e) => setComment(it.id, seedItems.find((r) => r.id === it.id)?.comment ?? it.comment, e.target.value)}
                    style={{
                      minHeight: '58px',
                      resize: 'vertical',
                      fontFamily: 'Inter, system-ui, sans-serif',
                      fontSize: '13px',
                      lineHeight: 1.5,
                      color: 'var(--ink)',
                      padding: '9px 11px',
                      border: '1.5px solid var(--line)',
                      borderRadius: '4px',
                      background: 'var(--panel)',
                    }}
                  />
                </div>

                {/* right column — score */}
                <div
                  style={{
                    background: 'var(--panel3)',
                    borderLeft: '1.5px solid var(--line)',
                    padding: '15px 16px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '12px',
                  }}
                >
                  <div
                    style={{
                      fontFamily: MINCHO,
                      fontWeight: 700,
                      fontSize: '11px',
                      letterSpacing: '.4px',
                      textTransform: 'uppercase',
                      color: 'var(--ink-soft)',
                    }}
                  >
                    Score
                  </div>

                  {/* stepper */}
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
                    <button
                      className="squish"
                      type="button"
                      aria-label="Decrease score"
                      onClick={() => setScore(it.id, it.score - 1)}
                      style={{
                        width: '34px',
                        height: '34px',
                        flex: 'none',
                        fontFamily: MINCHO,
                        fontWeight: 800,
                        fontSize: '20px',
                        lineHeight: 1,
                        color: 'var(--ink)',
                        border: '1.5px solid var(--line)',
                        borderRadius: '4px',
                        background: 'var(--panel)',
                      }}
                    >
                      −
                    </button>
                    <span
                      style={{
                        width: '58px',
                        textAlign: 'center',
                        fontFamily: MINCHO,
                        fontWeight: 800,
                        fontSize: '40px',
                        lineHeight: 1,
                        fontVariantNumeric: 'tabular-nums',
                        color: 'var(--ink)',
                      }}
                    >
                      {it.score}
                    </span>
                    <button
                      className="squish"
                      type="button"
                      aria-label="Increase score"
                      onClick={() => setScore(it.id, it.score + 1)}
                      style={{
                        width: '34px',
                        height: '34px',
                        flex: 'none',
                        fontFamily: MINCHO,
                        fontWeight: 800,
                        fontSize: '20px',
                        lineHeight: 1,
                        color: 'var(--ink)',
                        border: '1.5px solid var(--line)',
                        borderRadius: '4px',
                        background: 'var(--panel)',
                      }}
                    >
                      ＋
                    </button>
                  </div>
                  <div style={{ textAlign: 'center', fontSize: '12px', color: 'var(--ink-soft)' }}>
                    out of 10
                  </div>

                  {/* confidence meter */}
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <span
                      style={{
                        fontFamily: MINCHO,
                        fontWeight: 700,
                        fontSize: '11px',
                        letterSpacing: '.4px',
                        textTransform: 'uppercase',
                        color: 'var(--ink-soft)',
                      }}
                    >
                      Confidence
                    </span>
                    <span
                      style={{
                        fontFamily: MINCHO,
                        fontWeight: 800,
                        fontSize: '13px',
                        fontVariantNumeric: 'tabular-nums',
                        color: cColor,
                      }}
                    >
                      {Math.round(it.conf * 100)}%
                    </span>
                  </div>
                  <div
                    style={{
                      display: 'flex',
                      gap: '3px',
                      height: '11px',
                      padding: '0',
                    }}
                  >
                    {[0, 1, 2, 3, 4].map((seg) => (
                      <span
                        key={seg}
                        style={{
                          flex: 1,
                          borderRadius: '4px',
                          border: '1px solid var(--line)',
                          background: seg < litSegments ? cColor : 'var(--chip)',
                        }}
                      />
                    ))}
                  </div>

                  {/* reject / approve */}
                  <div style={{ display: 'flex', gap: '8px', marginTop: 'auto' }}>
                    <button
                      className="squish"
                      type="button"
                      onClick={() => reject(it.id)}
                      style={{
                        flex: 1,
                        display: 'inline-flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '5px',
                        padding: '8px',
                        fontFamily: MINCHO,
                        fontWeight: 700,
                        fontSize: '12.5px',
                        border: '1.5px solid var(--line)',
                        borderRadius: '4px',
                        background: it.status === 'rejected' ? '#c62d1f' : 'var(--panel2)',
                        color: it.status === 'rejected' ? '#fff' : 'var(--ink)',
                      }}
                    >
                      <XGlyph color={it.status === 'rejected' ? '#fff' : 'var(--ink)'} />
                      Reject
                    </button>
                    <button
                      className="squish"
                      type="button"
                      onClick={() => approve(it.id)}
                      style={{
                        flex: 1,
                        display: 'inline-flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '5px',
                        padding: '8px',
                        fontFamily: MINCHO,
                        fontWeight: 700,
                        fontSize: '12.5px',
                        border: '1.5px solid var(--line)',
                        borderRadius: '4px',
                        background: it.status === 'approved' ? '#2f8f6b' : 'var(--panel2)',
                        color: it.status === 'approved' ? '#fff' : 'var(--ink)',
                      }}
                    >
                      <ThumbsUpGlyph color={it.status === 'approved' ? '#fff' : 'var(--ink)'} />
                      Approve
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* ===== STICKY FOOTER ===== */}
      <div
        style={{
          position: 'sticky',
          bottom: 0,
          margin: '0 -28px -60px',
          padding: '14px 28px',
          background: 'var(--panel)',
          borderTop: '1.5px solid var(--line)',
          boxShadow: '0 -8px 16px rgba(35,30,20,.10)',
          display: 'flex',
          alignItems: 'center',
          gap: '18px',
        }}
      >
        <span style={{ fontFamily: MINCHO, fontWeight: 700, fontSize: '14px', color: '#1a7a2e' }}>
          {approvedN} approved
        </span>
        <span style={{ fontFamily: MINCHO, fontWeight: 700, fontSize: '14px', color: 'var(--ink-soft)' }}>
          {editedN} edited
        </span>
        <span style={{ fontFamily: MINCHO, fontWeight: 700, fontSize: '14px', color: '#c63' }}>
          {rejectedN} rejected
        </span>

        <span style={{ flex: 1 }} />

        <button
          className="squish"
          type="button"
          onClick={submit}
          style={{
            fontFamily: MINCHO,
            fontWeight: 800,
            fontSize: '15px',
            padding: '11px 22px',
            border: '1.5px solid var(--line)',
            borderRadius: '5px',
            boxShadow: '3px 3px 13px var(--shadowc)',
            background: 'var(--lime)',
            color: '#fff',
          }}
        >
          Submit {approvedN} grades →
        </button>
      </div>
    </div>
  )
}

export default ReviewQueue
