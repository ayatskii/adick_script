import React from 'react'
import type { StatusKind } from '../types'

interface StatusBadgeProps {
  status: StatusKind
  label?: string
}

// ============================================================
// Face icon components — 15×15, stroke currentColor
// ============================================================

function FaceSmiley() {
  return (
    <svg width="15" height="15" viewBox="0 0 15 15" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
      <circle cx="5.5" cy="6" r="0.8" fill="currentColor" stroke="none" />
      <circle cx="9.5" cy="6" r="0.8" fill="currentColor" stroke="none" />
      <path d="M4.5 9.5 Q7.5 12 10.5 9.5" fill="none" />
    </svg>
  )
}

function FaceBlinkingDots() {
  return (
    <svg width="15" height="15" viewBox="0 0 15 15" fill="currentColor">
      <circle cx="3.5" cy="7.5" r="1.5" style={{ animation: 'sbblink 1.1s 0s infinite' }} />
      <circle cx="7.5" cy="7.5" r="1.5" style={{ animation: 'sbblink 1.1s 0.18s infinite', opacity: 0.7 }} />
      <circle cx="11.5" cy="7.5" r="1.5" style={{ animation: 'sbblink 1.1s 0.36s infinite', opacity: 0.45 }} />
    </svg>
  )
}

function FaceNeutral() {
  return (
    <svg width="15" height="15" viewBox="0 0 15 15" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
      <circle cx="5.5" cy="6" r="0.8" fill="currentColor" stroke="none" />
      <circle cx="9.5" cy="6" r="0.8" fill="currentColor" stroke="none" />
      <line x1="5" y1="10" x2="10" y2="10" />
    </svg>
  )
}

function FaceRaisedBrow() {
  return (
    <svg width="15" height="15" viewBox="0 0 15 15" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
      <path d="M4 4.5 Q5.5 3 7 4.5" />
      <path d="M8 4 Q9.5 3.5 11 4" />
      <circle cx="5.5" cy="6.5" r="0.8" fill="currentColor" stroke="none" />
      <circle cx="9.5" cy="6.5" r="0.8" fill="currentColor" stroke="none" />
      <path d="M5 10 Q7.5 11.5 10 10" />
    </svg>
  )
}

function FaceXEyes() {
  return (
    <svg width="15" height="15" viewBox="0 0 15 15" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
      <line x1="3.5" y1="4.5" x2="6.5" y2="7.5" />
      <line x1="6.5" y1="4.5" x2="3.5" y2="7.5" />
      <line x1="8.5" y1="4.5" x2="11.5" y2="7.5" />
      <line x1="11.5" y1="4.5" x2="8.5" y2="7.5" />
      <path d="M4.5 11 Q7.5 9 10.5 11" />
    </svg>
  )
}

function FaceGhost() {
  return (
    <svg width="15" height="15" viewBox="0 0 15 15" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 12 Q3 3 7.5 3 Q12 3 12 12 Q10.5 11 9 12 Q7.5 13 6 12 Q4.5 11 3 12Z" />
      <circle cx="5.5" cy="7.5" r="1" fill="currentColor" stroke="none" />
      <circle cx="9.5" cy="7.5" r="1" fill="currentColor" stroke="none" />
    </svg>
  )
}

function FaceSleepy() {
  return (
    <svg width="15" height="15" viewBox="0 0 15 15" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
      <path d="M4 5 Q5.5 4 7 5" />
      <path d="M8 5 Q9.5 4 11 5" />
      <line x1="4.5" y1="7.5" x2="7" y2="7.5" />
      <line x1="8" y1="7.5" x2="10.5" y2="7.5" />
      <line x1="5" y1="10.5" x2="10" y2="10.5" />
    </svg>
  )
}

// ============================================================
// Variant table (verbatim from spec §4)
// ============================================================
interface Variant {
  defaultLabel: string
  bg: string
  fg: string
  border: string
  face: React.ReactNode
}

function getVariant(status: StatusKind): Variant {
  switch (status) {
    case 'evaluating':
      return { defaultLabel: 'Evaluating', bg: '#3f72b0', fg: '#ffffff', border: 'none', face: <FaceBlinkingDots /> }
    case 'graded':
      return { defaultLabel: 'Graded', bg: '#2f8f6b', fg: '#ffffff', border: 'none', face: <FaceSmiley /> }
    case 'running':
      return { defaultLabel: 'Running', bg: '#3f72b0', fg: '#ffffff', border: 'none', face: <FaceSmiley /> }
    case 'skipped':
      return { defaultLabel: 'Skipped', bg: 'var(--c-skip)', fg: 'var(--ink)', border: 'none', face: <FaceNeutral /> }
    case 'flagged':
      return { defaultLabel: 'Flagged', bg: '#cf9a36', fg: '#241a00', border: 'none', face: <FaceRaisedBrow /> }
    case 'error':
      return { defaultLabel: 'Error', bg: '#c62d1f', fg: '#ffffff', border: 'none', face: <FaceXEyes /> }
    case 'dryrun':
      return {
        defaultLabel: 'Dry-run',
        bg: 'repeating-linear-gradient(45deg,#6a5a9e,#6a5a9e 6px,#4e4179 6px,#4e4179 12px)',
        fg: '#ffffff',
        border: '1.5px dashed rgba(255,255,255,.6)',
        face: <FaceGhost />,
      }
    case 'idle':
      return { defaultLabel: 'Idle', bg: 'var(--chip)', fg: 'var(--ink)', border: 'none', face: <FaceSleepy /> }
    case 'queued':
      return { defaultLabel: 'Queued', bg: 'var(--chip)', fg: 'var(--ink-soft)', border: 'none', face: <FaceSleepy /> }
  }
}

// ============================================================
// StatusBadge component
// ============================================================

export function StatusBadge({ status, label }: StatusBadgeProps) {
  const v = getVariant(status)
  const displayLabel = label ?? v.defaultLabel

  return (
    <span
      data-status={status}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '5px',
        padding: '3px 9px 3px 6px',
        border: v.border === 'none' ? undefined : v.border,
        borderRadius: '3px',
        background: v.bg,
        color: v.fg,
        fontFamily: "'Shippori Mincho B1', serif",
        fontWeight: 700,
        fontSize: '11px',
        letterSpacing: '.4px',
        textTransform: 'uppercase',
        lineHeight: 1,
        whiteSpace: 'nowrap',
      }}
    >
      {v.face}
      {displayLabel}
    </span>
  )
}

export default StatusBadge
