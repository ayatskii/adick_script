// ============================================================
// NAV ICONS — 20×20, stroke currentColor, strokeWidth 2.3
// ============================================================

export function IconDashboard() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2.3" strokeLinecap="round" strokeLinejoin="round">
      {/* 4 rounded squares in a 2×2 grid */}
      <rect x="2" y="2" width="6" height="6" rx="1.5" />
      <rect x="12" y="2" width="6" height="6" rx="1.5" />
      <rect x="2" y="12" width="6" height="6" rx="1.5" />
      <rect x="12" y="12" width="6" height="6" rx="1.5" />
    </svg>
  )
}

export function IconNewRun() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2.3" strokeLinecap="round" strokeLinejoin="round">
      {/* vertical bar (pause-like) left + play triangle right */}
      <line x1="4" y1="4" x2="4" y2="16" />
      <polygon points="8,4 17,10 8,16" />
    </svg>
  )
}

export function IconLive() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2.3" strokeLinecap="round" strokeLinejoin="round">
      {/* broadcast arcs (concentric) + center dot */}
      <circle cx="10" cy="10" r="1.5" fill="currentColor" stroke="none" />
      <path d="M6.5 13.5a5 5 0 0 1 0-7" />
      <path d="M13.5 13.5a5 5 0 0 0 0-7" />
      <path d="M3.5 16.5a9.5 9.5 0 0 1 0-13" />
      <path d="M16.5 16.5a9.5 9.5 0 0 0 0-13" />
    </svg>
  )
}

export function IconReview() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2.3" strokeLinecap="round" strokeLinejoin="round">
      {/* clipboard body */}
      <rect x="4" y="4" width="12" height="14" rx="1.5" />
      {/* clipboard top tab */}
      <path d="M7 4V3a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v1" />
      {/* check mark */}
      <polyline points="7,11 9,13 13,9" />
    </svg>
  )
}

export function IconStudents() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2.3" strokeLinecap="round" strokeLinejoin="round">
      {/* primary person */}
      <circle cx="8" cy="7" r="2.5" />
      <path d="M3 17c0-3 2-5 5-5s5 2 5 5" />
      {/* secondary person */}
      <circle cx="14" cy="7" r="2" />
      <path d="M14 12c1.5 0 3 1 3.5 3" />
    </svg>
  )
}

export function IconHistory() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2.3" strokeLinecap="round" strokeLinejoin="round">
      {/* clock face */}
      <circle cx="10" cy="10" r="7.5" />
      {/* clock hands */}
      <polyline points="10,5.5 10,10 13.5,12.5" />
    </svg>
  )
}

export function IconFlagged() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2.3" strokeLinecap="round" strokeLinejoin="round">
      {/* flag pole */}
      <line x1="5" y1="3" x2="5" y2="18" />
      {/* flag */}
      <path d="M5 3 L16 6 L5 9 Z" />
    </svg>
  )
}

export function IconSettings() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2.3" strokeLinecap="round" strokeLinejoin="round">
      {/* gear: circle + spokes */}
      <circle cx="10" cy="10" r="3" />
      <path d="M10 2v2M10 16v2M2 10h2M16 10h2M4.22 4.22l1.42 1.42M14.36 14.36l1.42 1.42M4.22 15.78l1.42-1.42M14.36 5.64l1.42-1.42" />
    </svg>
  )
}

// ============================================================
// THEME ICONS — Sun (light) and Moon (dark), cartoon faces
// ============================================================

/** Smiling sun face: disc #ffce2e, features stroked #3a2600 */
export function IconSun() {
  return (
    <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
      <circle cx="11" cy="11" r="7" fill="#ffce2e" stroke="#3a2600" strokeWidth="1.5" />
      <line x1="11" y1="1" x2="11" y2="3.5" stroke="#3a2600" strokeWidth="1.5" strokeLinecap="round" />
      <line x1="11" y1="18.5" x2="11" y2="21" stroke="#3a2600" strokeWidth="1.5" strokeLinecap="round" />
      <line x1="1" y1="11" x2="3.5" y2="11" stroke="#3a2600" strokeWidth="1.5" strokeLinecap="round" />
      <line x1="18.5" y1="11" x2="21" y2="11" stroke="#3a2600" strokeWidth="1.5" strokeLinecap="round" />
      <line x1="3.64" y1="3.64" x2="5.47" y2="5.47" stroke="#3a2600" strokeWidth="1.5" strokeLinecap="round" />
      <line x1="16.53" y1="16.53" x2="18.36" y2="18.36" stroke="#3a2600" strokeWidth="1.5" strokeLinecap="round" />
      <line x1="3.64" y1="18.36" x2="5.47" y2="16.53" stroke="#3a2600" strokeWidth="1.5" strokeLinecap="round" />
      <line x1="16.53" y1="5.47" x2="18.36" y2="3.64" stroke="#3a2600" strokeWidth="1.5" strokeLinecap="round" />
      <circle cx="8.5" cy="10" r="1" fill="#3a2600" />
      <circle cx="13.5" cy="10" r="1" fill="#3a2600" />
      <path d="M8 13 Q11 15.5 14 13" stroke="#3a2600" strokeWidth="1.2" strokeLinecap="round" fill="none" />
    </svg>
  )
}

/** Crescent moon face: fill #d6a23f, stroke #3a2600 */
export function IconMoon() {
  return (
    <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
      <path d="M17 11.5A7 7 0 1 1 10.5 4a5.5 5.5 0 0 0 6.5 7.5z" fill="#d6a23f" stroke="#3a2600" strokeWidth="1.5" strokeLinejoin="round" />
      <circle cx="9" cy="10" r="0.9" fill="#3a2600" />
      <circle cx="13" cy="9" r="0.9" fill="#3a2600" />
      <path d="M8.5 12.5 Q11 14.5 13.5 12.5" stroke="#3a2600" strokeWidth="1.1" strokeLinecap="round" fill="none" />
    </svg>
  )
}

// ============================================================
// PADLOCK — TopBar "local credentials" chip, 17×17, stroke currentColor
// ============================================================

export function IconPadlock() {
  return (
    <svg width="17" height="17" viewBox="0 0 17 17" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M4.5 7V5.5a4 4 0 0 1 8 0V7" />
      <rect x="2.5" y="7" width="12" height="8.5" rx="1.5" />
      <circle cx="8.5" cy="11.5" r="1.2" fill="currentColor" stroke="none" />
    </svg>
  )
}
