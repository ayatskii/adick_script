import { useState } from 'react'
import type { ReactNode } from 'react'
import type { ScreenProps, RunMode } from '../types'

// ============================================================
// Mincho font helper (used pervasively for headings/labels/buttons)
// ============================================================
const MINCHO = "'Shippori Mincho B1', serif"

// ============================================================
// Mode segment config (verbatim from spec §3.2)
// ============================================================
interface ModeOption {
  mode: RunMode
  face: string // emoji face glyph
  title: string
  desc: string
  borderStyle: 'dashed' | 'solid'
  activeBg: string
  activeFg: string
}

const MODE_OPTIONS: ModeOption[] = [
  {
    mode: 'dryrun',
    face: '👻',
    title: 'Dry-run',
    desc: 'Evaluate everything, submit nothing. Totally safe.',
    borderStyle: 'dashed',
    activeBg: 'repeating-linear-gradient(45deg,#6a5a9e,#6a5a9e 9px,#4e4179 9px,#4e4179 18px)',
    activeFg: '#fff',
  },
  {
    mode: 'full',
    face: '😬',
    title: 'Full-auto',
    desc: 'Grade AND complete lessons. Irreversible.',
    borderStyle: 'solid',
    activeBg: 'repeating-linear-gradient(45deg,#cf9a36,#cf9a36 13px,#e0b85e 13px,#e0b85e 26px)',
    activeFg: '#3a2600',
  },
  {
    mode: 'review',
    face: '📝',
    title: 'Review-queue',
    desc: 'Draft grades for you to approve before submitting.',
    borderStyle: 'solid',
    activeBg: 'var(--sky)',
    activeFg: '#fff',
  },
]

// Scope: pick-students seed data (verbatim from spec §3.2)
const DEFAULT_PICKED = ['Анель', 'Dias', 'Аружан']
const SUGGESTION_POOL = ['Timur', 'Нурайым', 'Madina', 'Ерлан', 'Aizhan', 'Daniyar', 'Алишер', 'Camila']

// Play-triangle icon used on the start button (§6)
function PlayTriangle({ color = 'currentColor' }: { color?: string }) {
  return (
    <svg width="15" height="15" viewBox="0 0 15 15" fill={color} aria-hidden>
      <path d="M3.5 2.5 L12.5 7.5 L3.5 12.5 Z" />
    </svg>
  )
}

// Section label (uppercase Mincho-700 13px, var(--ink-soft))
function SectionLabel({ children }: { children: ReactNode }) {
  return (
    <div
      style={{
        fontFamily: MINCHO,
        fontWeight: 700,
        fontSize: '13px',
        letterSpacing: '.4px',
        textTransform: 'uppercase',
        color: 'var(--ink-soft)',
      }}
    >
      {children}
    </div>
  )
}

export function NewRun(props: ScreenProps) {
  const { defaultRunMode, openDialog, startRun } = props

  const [mode, setMode] = useState<RunMode>(defaultRunMode)
  const [scopeAll, setScopeAll] = useState(true)
  const [picked, setPicked] = useState<string[]>(DEFAULT_PICKED)
  const [maxStudents, setMaxStudents] = useState(43)
  const [maxLessons, setMaxLessons] = useState(5)
  const [headed, setHeaded] = useState(false)
  const [conf, setConf] = useState(0.7)

  const confPct = Math.round(conf * 100)

  function removeChip(name: string) {
    setPicked((p) => p.filter((n) => n !== name))
  }
  function addChip(name: string) {
    setPicked((p) => (p.includes(name) ? p : [...p, name]))
  }

  // Suggestion chips = pool members not yet picked, first 5
  const suggestions = SUGGESTION_POOL.filter((n) => !picked.includes(n)).slice(0, 5)

  // Start button label + colors per mode
  const startConfig: Record<RunMode, { label: string; bg: string; fg: string }> = {
    dryrun: { label: 'Start Dry-run', bg: 'var(--violet)', fg: '#fff' },
    full: { label: 'Start Full-auto run', bg: '#cf9a36', fg: '#3a2600' },
    review: { label: 'Start Review-queue run', bg: 'var(--sky)', fg: '#fff' },
  }
  const startBtn = startConfig[mode]

  function handleStart() {
    const opts = {
      scopeAll,
      students: scopeAll ? null : picked,
      maxStudents,
      maxLessons,
      headed,
      conf,
    }
    // Full mode opens the confirm dialog (§5.1); other modes start immediately.
    if (mode === 'full') {
      openDialog('full')
    } else {
      startRun(mode, opts)
    }
  }

  // Footer note per mode
  const footerNote =
    mode === 'full' ? (
      <span style={{ color: '#a06a00', fontFamily: MINCHO, fontWeight: 700, fontSize: '13px' }}>
        ⚠️ Submits real grades &amp; completes lessons.
      </span>
    ) : (
      <span style={{ color: 'var(--violet)', fontFamily: MINCHO, fontWeight: 700, fontSize: '13px' }}>
        👻 Safe — nothing will be submitted.
      </span>
    )

  return (
    <div
      style={{
        maxWidth: '680px',
        margin: '0 auto',
        background: 'var(--panel)',
        border: '1.5px solid var(--line)',
        borderRadius: '7px',
        boxShadow: '6px 6px 16px var(--shadowc)',
        overflow: 'hidden',
      }}
    >
      {/* ===================== Header ===================== */}
      <div style={{ background: 'var(--panel2)', padding: '16px 22px', borderBottom: '1.5px solid var(--line)' }}>
        <div style={{ fontFamily: MINCHO, fontWeight: 800, fontSize: '20px', color: 'var(--ink)', letterSpacing: '-.2px' }}>
          Set up a new run
        </div>
        <div style={{ fontSize: '13px', color: 'var(--ink-soft)', marginTop: '3px' }}>
          Pick a mode, choose who to grade, set your safety caps.
        </div>
      </div>

      {/* ===================== Body ===================== */}
      <div style={{ padding: '22px', display: 'flex', flexDirection: 'column', gap: '22px' }}>
        {/* --------------- Mode --------------- */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <SectionLabel>Mode</SectionLabel>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: '10px' }}>
            {MODE_OPTIONS.map((opt) => {
              const active = mode === opt.mode
              return (
                <button
                  key={opt.mode}
                  className="squish"
                  onClick={() => setMode(opt.mode)}
                  style={{
                    textAlign: 'left',
                    padding: '13px',
                    border: `3px ${opt.borderStyle} var(--line)`,
                    borderRadius: '5px',
                    background: active ? opt.activeBg : 'var(--panel2)',
                    color: active ? opt.activeFg : 'var(--ink)',
                    boxShadow: active ? '3px 3px 13px var(--shadowc)' : 'none',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '6px',
                  }}
                >
                  <span style={{ display: 'flex', alignItems: 'center', gap: '7px' }}>
                    <span style={{ fontSize: '18px', lineHeight: 1 }}>{opt.face}</span>
                    <span style={{ fontFamily: MINCHO, fontWeight: 800, fontSize: '15px' }}>{opt.title}</span>
                  </span>
                  <span
                    style={{
                      fontSize: '11.5px',
                      lineHeight: 1.4,
                      color: active ? 'inherit' : 'var(--ink-soft)',
                    }}
                  >
                    {opt.desc}
                  </span>
                </button>
              )
            })}
          </div>
        </div>

        {/* --------------- Scope --------------- */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <SectionLabel>Scope</SectionLabel>
          <div style={{ display: 'flex', gap: '10px' }}>
            <button
              className="squish"
              onClick={() => setScopeAll(true)}
              style={{
                flex: 1,
                textAlign: 'left',
                padding: '11px 14px',
                border: '1.5px solid var(--line)',
                borderRadius: '4px',
                fontFamily: MINCHO,
                fontWeight: 700,
                fontSize: '14px',
                background: scopeAll ? 'var(--violet)' : 'var(--panel2)',
                color: scopeAll ? '#fff' : 'var(--ink)',
                boxShadow: scopeAll ? '3px 3px 13px var(--shadowc)' : 'none',
              }}
            >
              All of Mr. Adilet&apos;s Pre-IELTS students
            </button>
            <button
              className="squish"
              onClick={() => setScopeAll(false)}
              style={{
                flex: 'none',
                padding: '11px 14px',
                border: '1.5px solid var(--line)',
                borderRadius: '4px',
                fontFamily: MINCHO,
                fontWeight: 700,
                fontSize: '14px',
                background: !scopeAll ? 'var(--violet)' : 'var(--panel2)',
                color: !scopeAll ? '#fff' : 'var(--ink)',
                boxShadow: !scopeAll ? '3px 3px 13px var(--shadowc)' : 'none',
              }}
            >
              Pick students
            </button>
          </div>

          {/* Chip panel — only when "Pick students" active */}
          {!scopeAll && (
            <div
              style={{
                background: 'var(--panel2)',
                border: '1.5px solid var(--line)',
                borderRadius: '6px',
                padding: '14px',
                display: 'flex',
                flexDirection: 'column',
                gap: '12px',
              }}
            >
              {/* Selected name-tags */}
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                {picked.map((name) => (
                  <span
                    key={name}
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '6px',
                      background: 'var(--lime)',
                      color: '#fff',
                      borderRadius: '99px',
                      padding: '4px 6px 4px 12px',
                      fontFamily: MINCHO,
                      fontWeight: 700,
                      fontSize: '13px',
                    }}
                  >
                    {name}
                    <button
                      className="squish"
                      onClick={() => removeChip(name)}
                      aria-label={`Remove ${name}`}
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        width: '18px',
                        height: '18px',
                        borderRadius: '50%',
                        border: 'none',
                        background: 'rgba(0,0,0,.15)',
                        color: '#fff',
                        fontSize: '12px',
                        lineHeight: 1,
                        padding: 0,
                      }}
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>

              {/* Add more */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <SectionLabel>＋ add more</SectionLabel>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                  {suggestions.map((name) => (
                    <button
                      key={name}
                      className="squish"
                      onClick={() => addChip(name)}
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '4px',
                        background: 'transparent',
                        color: 'var(--ink)',
                        border: '1.5px dashed var(--line)',
                        borderRadius: '99px',
                        padding: '4px 12px',
                        fontFamily: MINCHO,
                        fontWeight: 700,
                        fontSize: '13px',
                      }}
                    >
                      ＋ {name}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* --------------- Safety caps --------------- */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <SectionLabel>Safety caps</SectionLabel>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <label style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--ink-soft)' }}>Max students</span>
              <input
                type="number"
                value={maxStudents}
                onChange={(e) => setMaxStudents(Number(e.target.value))}
                style={{
                  fontFamily: MINCHO,
                  fontWeight: 700,
                  fontSize: '16px',
                  color: 'var(--ink)',
                  background: 'var(--panel2)',
                  border: '1.5px solid var(--line)',
                  borderRadius: '4px',
                  padding: '9px 12px',
                  width: '100%',
                }}
              />
            </label>
            <label style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--ink-soft)' }}>Max lessons / student</span>
              <input
                type="number"
                value={maxLessons}
                onChange={(e) => setMaxLessons(Number(e.target.value))}
                style={{
                  fontFamily: MINCHO,
                  fontWeight: 700,
                  fontSize: '16px',
                  color: 'var(--ink)',
                  background: 'var(--panel2)',
                  border: '1.5px solid var(--line)',
                  borderRadius: '4px',
                  padding: '9px 12px',
                  width: '100%',
                }}
              />
            </label>
          </div>

          {/* Headed toggle */}
          <button
            className="squish"
            onClick={() => setHeaded((h) => !h)}
            aria-pressed={headed}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              width: '100%',
              padding: '11px 14px',
              border: '1.5px solid var(--line)',
              borderRadius: '4px',
              background: 'var(--panel2)',
              color: 'var(--ink)',
              fontFamily: MINCHO,
              fontWeight: 700,
              fontSize: '14px',
            }}
          >
            <span>Run browser visibly (headed)</span>
            <span
              style={{
                position: 'relative',
                flex: 'none',
                width: '50px',
                height: '28px',
                borderRadius: '99px',
                border: '1.5px solid var(--line)',
                background: headed ? 'var(--lime)' : 'var(--c-skip)',
                transition: 'background .18s',
              }}
            >
              <span
                style={{
                  position: 'absolute',
                  top: '50%',
                  left: headed ? '23px' : '1px',
                  width: '20px',
                  height: '20px',
                  borderRadius: '50%',
                  background: '#fff',
                  transform: 'translateY(-50%)',
                  transition: 'left .18s cubic-bezier(.34,1.56,.64,1)',
                  boxShadow: '0 1px 2px rgba(0,0,0,.25)',
                }}
              />
            </span>
          </button>
        </div>

        {/* --------------- Confidence threshold --------------- */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between' }}>
            <SectionLabel>Confidence threshold</SectionLabel>
            <span style={{ fontFamily: MINCHO, fontWeight: 800, fontSize: '18px', color: 'var(--violet)' }}>
              {confPct}%
            </span>
          </div>
          <input
            type="range"
            min="0.4"
            max="0.95"
            step="0.01"
            value={conf}
            onChange={(e) => setConf(Number(e.target.value))}
            style={{ accentColor: '#2b3a5e', width: '100%' }}
          />
          <div style={{ fontSize: '12.5px', color: 'var(--ink-soft)' }}>
            Below this, the bot flags the item for review instead of grading it.
          </div>
        </div>
      </div>

      {/* ===================== Footer ===================== */}
      <div
        style={{
          background: 'var(--panel2)',
          borderTop: '1.5px solid var(--line)',
          padding: '16px 22px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '14px',
        }}
      >
        {footerNote}
        <button
          className="squish"
          onClick={handleStart}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '9px',
            padding: '13px 24px',
            border: '1.5px solid var(--line)',
            borderRadius: '5px',
            fontFamily: MINCHO,
            fontWeight: 800,
            fontSize: '16px',
            background: startBtn.bg,
            color: startBtn.fg,
            boxShadow: '4px 4px 13px var(--shadowc)',
          }}
        >
          <PlayTriangle color={startBtn.fg} />
          {startBtn.label}
        </button>
      </div>
    </div>
  )
}

export default NewRun
