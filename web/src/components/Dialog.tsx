import React from 'react'
import type { DialogKind, RunMode } from '../types'

interface DialogProps {
  kind: DialogKind
  onCancel: () => void
  onConfirm: (mode?: RunMode) => void
}

function WorriedFace() {
  return (
    <svg width="32" height="32" viewBox="0 0 32 32" fill="none" stroke="#3a2600" strokeWidth="1.8" strokeLinecap="round">
      <path d="M10 10 L14 12M14 10 L10 12" />
      <path d="M18 10 L22 12M22 10 L18 12" />
      <circle cx="12" cy="15" r="1.5" fill="#3a2600" stroke="none" />
      <circle cx="20" cy="15" r="1.5" fill="#3a2600" stroke="none" />
      <path d="M11 22 Q16 20 21 22" />
    </svg>
  )
}

interface DialogConfig {
  title: string
  body: string
  note: string
  confirmLabel: string
  confirmBg: string
  confirmFg: string
  headerBg: string
}

const DIALOG_CONFIGS: Record<NonNullable<DialogKind>, DialogConfig> = {
  full: {
    title: 'Start a Full-auto run?',
    body: 'This will submit REAL grades and mark lessons complete on edvibe.com. These actions are irreversible.',
    note: 'Credentials are stored locally only — nothing leaves this machine except grade submissions to Edvibe.',
    confirmLabel: 'Yes, run full-auto',
    confirmBg: '#cf9a36',
    confirmFg: '#3a2600',
    headerBg: 'repeating-linear-gradient(45deg,#ffe0a3,#ffe0a3 12px,#ffd27d 12px,#ffd27d 24px)',
  },
  stop: {
    title: 'Stop this run?',
    body: 'The bot will finish the current exercise and halt. Already-submitted grades stay submitted; remaining students will be left untouched.',
    note: 'You can resume later from New Run — completed students are skipped automatically.',
    confirmLabel: 'Stop the run',
    confirmBg: '#c62d1f',
    confirmFg: '#fff',
    headerBg: '#e8d8d2',
  },
}

export function Dialog({ kind, onCancel, onConfirm }: DialogProps) {
  if (!kind) return null

  const config = DIALOG_CONFIGS[kind]

  function handleBackdropClick(e: React.MouseEvent) {
    if (e.target === e.currentTarget) onCancel()
  }

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 70,
        background: 'rgba(18,14,28,.55)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
      onClick={handleBackdropClick}
    >
      <div
        style={{
          width: '440px',
          maxWidth: '95vw',
          background: 'var(--panel)',
          border: '1.5px solid var(--line)',
          borderRadius: '7px',
          boxShadow: '8px 8px 16px var(--shadowc)',
          animation: 'popin .28s ease both',
          overflow: 'hidden',
        }}
        onClick={e => e.stopPropagation()}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '14px',
            padding: '16px 20px',
            background: config.headerBg,
          }}
        >
          <div
            style={{
              width: '52px',
              height: '52px',
              borderRadius: '50%',
              background: '#fff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}
          >
            <WorriedFace />
          </div>
          <h2
            style={{
              margin: 0,
              fontFamily: "'Shippori Mincho B1', serif",
              fontWeight: 800,
              fontSize: '19px',
              color: '#3a2600',
            }}
          >
            {config.title}
          </h2>
        </div>

        <div style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <p style={{ margin: 0, fontSize: '14.5px', color: 'var(--ink)', lineHeight: 1.5 }}>
            {config.body}
          </p>
          <div
            style={{
              border: '1.5px dashed var(--line)',
              borderRadius: '4px',
              padding: '10px 14px',
              fontSize: '13px',
              color: 'var(--ink-soft)',
              lineHeight: 1.5,
            }}
          >
            🔒 {config.note}
          </div>
        </div>

        <div
          style={{
            display: 'flex',
            gap: '10px',
            padding: '0 20px 20px',
            justifyContent: 'flex-end',
          }}
        >
          <button
            className="squish"
            onClick={onCancel}
            style={{
              padding: '10px 18px',
              borderRadius: '4px',
              border: '1.5px solid var(--line)',
              background: 'var(--panel2)',
              color: 'var(--ink)',
              fontFamily: "'Shippori Mincho B1', serif",
              fontWeight: 700,
              fontSize: '14px',
              cursor: 'pointer',
            }}
          >
            Cancel
          </button>
          <button
            className="squish"
            onClick={() => onConfirm(kind === 'full' ? 'full' : undefined)}
            style={{
              padding: '10px 18px',
              borderRadius: '4px',
              border: '1.5px solid var(--line)',
              background: config.confirmBg,
              color: config.confirmFg,
              fontFamily: "'Shippori Mincho B1', serif",
              fontWeight: 700,
              fontSize: '14px',
              cursor: 'pointer',
              boxShadow: '3px 3px 13px var(--shadowc)',
            }}
          >
            {config.confirmLabel}
          </button>
        </div>
      </div>
    </div>
  )
}

export default Dialog
