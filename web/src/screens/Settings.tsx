import type { CSSProperties, ReactNode } from 'react'
import type { ScreenProps } from '../types'
import { SETTINGS_DEFAULTS } from '../data'

// ============================================================
// Shared style fragments (spec §3.8 + §5.4)
// ============================================================
const MINCHO = "'Shippori Mincho B1', serif"

const cardStyle: CSSProperties = {
  background: 'var(--panel)',
  border: '1.5px solid var(--line)',
  borderRadius: '7px',
  boxShadow: '5px 5px 16px var(--shadowc)',
  overflow: 'hidden',
}

const cardHeaderStyle: CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '11px',
  background: 'var(--panel2)',
  borderBottom: '1.5px solid var(--line)',
  padding: '13px 18px',
}

const cardTitleStyle: CSSProperties = {
  fontFamily: MINCHO,
  fontWeight: 800,
  fontSize: '17px',
  color: 'var(--ink)',
  margin: 0,
}

const cardBodyStyle: CSSProperties = {
  padding: '18px',
}

const fieldLabelStyle: CSSProperties = {
  display: 'block',
  fontFamily: MINCHO,
  fontWeight: 700,
  fontSize: '12px',
  letterSpacing: '.4px',
  textTransform: 'uppercase',
  color: 'var(--ink-soft)',
  marginBottom: '6px',
}

// All inputs per spec §3.8 first paragraph
const inputBase: CSSProperties = {
  width: '100%',
  border: '1.5px solid var(--line)',
  borderRadius: '3px',
  background: 'var(--panel2)',
  fontSize: '13.5px',
  color: 'var(--ink)',
  padding: '9px 11px',
  fontFamily: 'Inter, system-ui, sans-serif',
  outline: 'none',
}

const monoInput: CSSProperties = {
  ...inputBase,
  fontFamily: "'JetBrains Mono', monospace",
  letterSpacing: '.3px',
}

// ============================================================
// Inline padlock SVG (spec §6) — stroke currentColor, 18×18
// ============================================================
function PadlockIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.3" strokeLinecap="round" strokeLinejoin="round">
      <rect x="4" y="10.5" width="16" height="10" rx="2" />
      <path d="M7.5 10.5V7.5a4.5 4.5 0 0 1 9 0v3" />
      <circle cx="12" cy="15" r="1.1" fill="currentColor" stroke="none" />
    </svg>
  )
}

// ============================================================
// Section sub-label (uppercase Mincho-700 13px, ink-soft)
// ============================================================
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
        marginBottom: '12px',
      }}
    >
      {children}
    </div>
  )
}

// ============================================================
// Field — label + child input
// ============================================================
function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label style={{ display: 'block' }}>
      <span style={fieldLabelStyle}>{label}</span>
      {children}
    </label>
  )
}

// ============================================================
// SETTINGS SCREEN (spec §3.8)
// ============================================================
export function Settings(props: ScreenProps) {
  const { showToast } = props
  const d = SETTINGS_DEFAULTS

  return (
    <div
      style={{
        maxWidth: '760px',
        margin: '0 auto',
        display: 'flex',
        flexDirection: 'column',
        gap: '16px',
      }}
    >
      {/* ---------- Credentials ---------- */}
      <section style={cardStyle}>
        <div style={cardHeaderStyle}>
          {/* lime padlock icon tile */}
          <span
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '30px',
              height: '30px',
              border: '1.5px solid var(--line)',
              borderRadius: '3px',
              background: 'var(--lime)',
              color: '#ffffff',
              flex: 'none',
            }}
          >
            <PadlockIcon />
          </span>
          <h2 style={cardTitleStyle}>Credentials</h2>
          {/* stored-locally chip */}
          <span
            style={{
              marginLeft: 'auto',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '5px',
              padding: '3px 10px',
              border: '1.5px solid var(--line)',
              borderRadius: '99px',
              background: 'var(--lime)',
              color: '#ffffff',
              fontFamily: MINCHO,
              fontWeight: 700,
              fontSize: '11.5px',
              whiteSpace: 'nowrap',
            }}
          >
            🔒 stored locally only
          </span>
        </div>
        <div style={cardBodyStyle}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <Field label="Edvibe login">
              <input type="text" defaultValue={d.edvibeLogin} style={inputBase} />
            </Field>
            <Field label="Edvibe password">
              <input type="password" defaultValue={d.edvibePassword} style={monoInput} />
            </Field>
            <div style={{ gridColumn: '1 / -1' }}>
              <Field label="OpenAI API key">
                <input type="password" defaultValue={d.openaiApiKey} style={monoInput} />
              </Field>
            </div>
          </div>
        </div>
      </section>

      {/* ---------- Models + Grading ---------- */}
      <section style={cardStyle}>
        <div style={cardHeaderStyle}>
          <h2 style={cardTitleStyle}>Models &amp; Grading</h2>
        </div>
        <div style={cardBodyStyle}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            {/* Models column */}
            <div>
              <SectionLabel>Models</SectionLabel>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                <Field label="Transcription model">
                  <input type="text" defaultValue={d.transcriptionModel} style={monoInput} />
                </Field>
                <Field label="Evaluation model">
                  <input type="text" defaultValue={d.evaluationModel} style={monoInput} />
                </Field>
              </div>
            </div>
            {/* Grading column */}
            <div>
              <SectionLabel>Grading</SectionLabel>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                <Field label="Score scale">
                  <input type="text" defaultValue={d.scoreScale} style={inputBase} />
                </Field>
                <Field label="Confidence threshold">
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    max="1"
                    defaultValue={d.confidenceThreshold}
                    style={{ ...inputBase, fontFamily: MINCHO, fontWeight: 700, fontSize: '16px' }}
                  />
                </Field>
                <Field label="Rubric notes">
                  <textarea
                    defaultValue={d.rubricNotes}
                    style={{ ...inputBase, minHeight: '72px', resize: 'vertical', lineHeight: 1.5 }}
                  />
                </Field>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ---------- Behavior ---------- */}
      <section style={cardStyle}>
        <div style={cardHeaderStyle}>
          <h2 style={cardTitleStyle}>Behavior</h2>
        </div>
        <div style={cardBodyStyle}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <Field label="Default mode">
              <input type="text" defaultValue={d.defaultMode} style={inputBase} />
            </Field>
            <Field label="Pacing delay (ms)">
              <input
                type="number"
                defaultValue={d.pacingDelayMs}
                style={{ ...inputBase, fontFamily: MINCHO, fontWeight: 700, fontSize: '16px' }}
              />
            </Field>
            <Field label="Marathon">
              <input type="text" defaultValue={d.marathon} style={inputBase} />
            </Field>
            <Field label="Curator">
              <input type="text" defaultValue={d.curator} style={inputBase} />
            </Field>
          </div>
        </div>
      </section>

      {/* ---------- Danger zone ---------- */}
      <section
        style={{
          ...cardStyle,
          border: '1.5px solid #c62d1f',
        }}
      >
        {/* hazard-stripe header */}
        <div
          style={{
            padding: '13px 18px',
            background:
              'repeating-linear-gradient(45deg,#c62d1f,#c62d1f 14px,#3a0a0a 14px,#3a0a0a 28px)',
            borderBottom: '1.5px solid #c62d1f',
          }}
        >
          <span
            style={{
              fontFamily: MINCHO,
              fontWeight: 800,
              fontSize: '17px',
              color: '#ffffff',
              textShadow: '1px 1px 0 #3a0a0a',
            }}
          >
            ⚠️ Danger zone
          </span>
        </div>
        <div style={cardBodyStyle}>
          {/* Row 1 — Clear all local data */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '16px',
              paddingBottom: '16px',
              borderBottom: '1px dashed #c62d1f',
            }}
          >
            <div style={{ flex: 1 }}>
              <div style={{ fontFamily: MINCHO, fontWeight: 800, fontSize: '14.5px', color: 'var(--ink)' }}>
                Clear all local data
              </div>
              <div style={{ fontSize: '13px', color: 'var(--ink-soft)', marginTop: '3px' }}>
                Wipes credentials, run history and settings from this machine.
              </div>
            </div>
            <button
              className="squish"
              onClick={() => showToast('warn', 'Local data cleared')}
              style={dangerButtonStyle}
            >
              Clear data
            </button>
          </div>

          {/* Row 2 — Reset bot to defaults */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '16px',
              paddingTop: '16px',
            }}
          >
            <div style={{ flex: 1 }}>
              <div style={{ fontFamily: MINCHO, fontWeight: 800, fontSize: '14.5px', color: 'var(--ink)' }}>
                Reset bot to defaults
              </div>
              <div style={{ fontSize: '13px', color: 'var(--ink-soft)', marginTop: '3px' }}>
                Restores all behavior settings, keeps your credentials.
              </div>
            </div>
            <button
              className="squish"
              onClick={() => showToast('info', 'Bot reset to defaults')}
              style={dangerButtonStyle}
            >
              Reset
            </button>
          </div>
        </div>
      </section>
    </div>
  )
}

// red-text danger-zone buttons (spec §3.8: background #fff, color #c00)
const dangerButtonStyle: CSSProperties = {
  flex: 'none',
  padding: '9px 18px',
  border: '1.5px solid var(--line)',
  borderRadius: '4px',
  background: '#ffffff',
  color: '#c00',
  fontFamily: MINCHO,
  fontWeight: 800,
  fontSize: '13.5px',
  boxShadow: '2px 2px 13px var(--shadowc)',
  whiteSpace: 'nowrap',
}

export default Settings
