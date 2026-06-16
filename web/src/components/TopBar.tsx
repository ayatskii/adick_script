import type { ScreenId, RunState } from '../types'
import { IconSun, IconMoon, IconPadlock } from './icons'

const SCREEN_TITLES: Record<ScreenId, string> = {
  dashboard: 'Dashboard',
  new: 'New Run',
  live: 'Live Monitor',
  review: 'Review Queue',
  students: 'Students',
  history: 'History & Audit',
  flagged: 'Flagged',
  settings: 'Settings',
}

interface TopBarProps {
  screen: ScreenId
  theme: 'light' | 'dark'
  run: RunState
  onThemeToggle: () => void
  onRunPillClick: () => void
}

function getRunPillStyle(run: RunState): {
  label: string
  dotColor: string
  bg: string
  fg: string
} {
  if (!run.active && !run.finished) {
    return { label: 'Idle', dotColor: 'var(--c-skip)', bg: 'var(--chip)', fg: 'var(--ink)' }
  }
  if (run.finished) {
    return { label: 'Done', dotColor: '#2f8f6b', bg: '#2f8f6b', fg: '#fff' }
  }
  switch (run.mode) {
    case 'dryrun':
      return { label: 'Dry-run', dotColor: '#6a5a9e', bg: '#3f72b0', fg: '#fff' }
    case 'review':
      return { label: 'Drafting', dotColor: '#3f72b0', bg: '#3f72b0', fg: '#fff' }
    case 'full':
      return { label: 'Running', dotColor: '#cf9a36', bg: '#cf9a36', fg: '#3a2600' }
  }
}

export function TopBar({ screen, theme, run, onThemeToggle, onRunPillClick }: TopBarProps) {
  const pill = getRunPillStyle(run)

  return (
    <header
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '14px',
        padding: '13px 22px',
        background: 'var(--panel)',
        borderBottom: '1.5px solid var(--line)',
        zIndex: 15,
        flexShrink: 0,
      }}
    >
      <h1
        style={{
          margin: 0,
          fontFamily: "'Shippori Mincho B1', serif",
          fontWeight: 800,
          fontSize: '20px',
          letterSpacing: '-.4px',
          color: 'var(--ink)',
          whiteSpace: 'nowrap',
        }}
      >
        {SCREEN_TITLES[screen]}
      </h1>

      {/* Localhost pill */}
      <span
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '6px',
          padding: '3px 10px',
          border: '1.5px solid var(--line)',
          borderRadius: '99px',
          background: 'var(--lime)',
          color: '#fff',
          fontFamily: "'Shippori Mincho B1', serif",
          fontWeight: 700,
          fontSize: '11.5px',
          boxShadow: '1.5px 1.5px 13px var(--shadowc)',
          whiteSpace: 'nowrap',
        }}
      >
        <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#fff', display: 'inline-block' }} />
        Localhost
      </span>

      <div style={{ flex: 1 }} />

      {/* RUN STATUS pill */}
      <button
        className="squish"
        onClick={onRunPillClick}
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '8px',
          padding: '7px 9px 7px 14px',
          border: '1.5px solid var(--line)',
          borderRadius: '99px',
          background: pill.bg,
          color: pill.fg,
          boxShadow: '3px 3px 13px var(--shadowc)',
          fontFamily: "'Shippori Mincho B1', serif",
          fontWeight: 700,
          fontSize: '14px',
          cursor: 'pointer',
        }}
      >
        <span
          style={{
            width: '11px',
            height: '11px',
            borderRadius: '50%',
            background: pill.dotColor,
            border: '1px solid var(--line)',
            flexShrink: 0,
          }}
        />
        {pill.label}
        {run.active && (
          <span
            style={{
              padding: '2px 9px',
              borderRadius: '99px',
              background: 'rgba(0,0,0,.18)',
              fontSize: '12px',
              fontWeight: 600,
            }}
          >
            {run.studentsDone}/{run.students} students
          </span>
        )}
      </button>

      {/* Theme toggle */}
      <button
        className="squish"
        onClick={onThemeToggle}
        aria-label={theme === 'light' ? 'Switch to dark theme' : 'Switch to light theme'}
        style={{
          width: '42px',
          height: '42px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          border: '1.5px solid var(--line)',
          borderRadius: '4px',
          background: theme === 'light' ? 'var(--yellow)' : 'var(--indigo)',
          boxShadow: '2.5px 2.5px 13px var(--shadowc)',
          cursor: 'pointer',
          flexShrink: 0,
        }}
      >
        {theme === 'light' ? <IconSun /> : <IconMoon />}
      </button>

      {/* Local credentials lock chip */}
      <div
        title="Credentials stored locally only"
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '6px',
          padding: '7px 11px',
          border: '1.5px solid var(--line)',
          borderRadius: '4px',
          background: 'var(--panel2)',
          boxShadow: '2px 2px 13px var(--shadowc)',
          color: 'var(--ink-soft)',
          flexShrink: 0,
        }}
      >
        <IconPadlock />
        <span
          style={{
            fontFamily: 'Inter, system-ui, sans-serif',
            fontSize: '11px',
            fontWeight: 600,
            color: 'var(--ink-soft)',
          }}
        >
          local
        </span>
      </div>
    </header>
  )
}

export default TopBar
