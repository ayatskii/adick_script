import React from 'react'
import type { ScreenId } from '../types'
import {
  IconDashboard, IconNewRun, IconLive, IconReview,
  IconStudents, IconHistory, IconFlagged, IconSettings,
} from './icons'

interface SidebarProps {
  screen: ScreenId
  open: boolean
  onNavigate: (screen: ScreenId) => void
  onToggle: () => void
  reviewCount: number
  flaggedCount: number
}

const NAV_ITEMS: Array<{
  id: ScreenId
  label: string
  Icon: React.FC
  countKey?: 'review' | 'flagged'
}> = [
  { id: 'dashboard', label: 'Dashboard', Icon: IconDashboard },
  { id: 'new', label: 'New Run', Icon: IconNewRun },
  { id: 'live', label: 'Live Monitor', Icon: IconLive },
  { id: 'review', label: 'Review Queue', Icon: IconReview, countKey: 'review' },
  { id: 'students', label: 'Students', Icon: IconStudents },
  { id: 'history', label: 'History', Icon: IconHistory },
  { id: 'flagged', label: 'Flagged', Icon: IconFlagged, countKey: 'flagged' },
  { id: 'settings', label: 'Settings', Icon: IconSettings },
]

export function Sidebar({ screen, open, onNavigate, onToggle, reviewCount, flaggedCount }: SidebarProps) {
  const width = open ? '232px' : '74px'

  function getCount(key?: 'review' | 'flagged') {
    if (key === 'review') return reviewCount
    if (key === 'flagged') return flaggedCount
    return 0
  }

  return (
    <aside
      style={{
        width,
        minWidth: width,
        transition: 'width .18s ease',
        background: 'var(--panel)',
        borderRight: '1.5px solid var(--line)',
        display: 'flex',
        flexDirection: 'column',
        zIndex: 20,
        overflow: 'hidden',
      }}
    >
      {/* Logo block */}
      <div
        style={{
          padding: open ? '18px 14px 14px' : '18px 17px 14px',
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          borderBottom: '1.5px solid var(--line)',
          flexShrink: 0,
        }}
      >
        {/* Emblem SVG: indigo square + vermilion sun + mountain path */}
        <svg
          width="40"
          height="40"
          viewBox="0 0 40 40"
          style={{
            borderRadius: '4px',
            boxShadow: '2.5px 2.5px 13px var(--shadowc)',
            flexShrink: 0,
          }}
        >
          <rect width="40" height="40" fill="#1f2a44" rx="4" />
          <circle cx="20" cy="15" r="9" fill="var(--sun)" />
          <path d="M0 40 L0 30 L12 22 L20 28 L28 18 L40 28 L40 40 Z" fill="#10121a" />
        </svg>

        {open && (
          <div style={{ overflow: 'hidden', minWidth: 0 }}>
            <div
              style={{
                fontFamily: "'Yuji Syuku', serif",
                fontSize: '21px',
                color: 'var(--ink)',
                letterSpacing: '.5px',
                lineHeight: 1.1,
                whiteSpace: 'nowrap',
              }}
            >
              Edvibe Grader
            </div>
            <div
              style={{
                fontSize: '10px',
                color: 'var(--ink-soft)',
                fontFamily: "'Shippori Mincho B1', serif",
                fontWeight: 600,
                textTransform: 'uppercase',
                letterSpacing: '1.5px',
                whiteSpace: 'nowrap',
              }}
            >
              Grading Mission-Control
            </div>
          </div>
        )}
      </div>

      {/* Nav items */}
      <nav
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '12px 10px',
          display: 'flex',
          flexDirection: 'column',
          gap: '5px',
        }}
      >
        {NAV_ITEMS.map(({ id, label, Icon, countKey }) => {
          const isActive = screen === id
          const count = countKey ? getCount(countKey) : 0

          return (
            <button
              key={id}
              className="squish"
              onClick={() => onNavigate(id)}
              title={open ? undefined : label}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '11px',
                padding: '9px 11px',
                borderRadius: '4px',
                border: isActive ? '2.5px solid var(--line)' : '2.5px solid transparent',
                background: isActive ? 'var(--violet)' : 'transparent',
                color: isActive ? '#fff' : 'var(--ink)',
                boxShadow: isActive ? '3px 3px 13px var(--shadowc)' : 'none',
                fontFamily: "'Shippori Mincho B1', serif",
                fontWeight: 700,
                fontSize: '14.5px',
                textAlign: 'left',
                cursor: 'pointer',
                width: '100%',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
              }}
            >
              <span style={{ flexShrink: 0, display: 'flex' }}>
                <Icon />
              </span>
              {open && (
                <>
                  <span style={{ flex: 1 }}>{label}</span>
                  {count > 0 && (
                    <span
                      style={{
                        minWidth: '20px',
                        fontFamily: "'Shippori Mincho B1', serif",
                        fontSize: '11px',
                        fontWeight: 800,
                        padding: '1px 6px',
                        borderRadius: '99px',
                        border: '1px solid var(--line)',
                        background: 'var(--yellow)',
                        color: '#3a2600',
                        textAlign: 'center',
                        flexShrink: 0,
                      }}
                    >
                      {count}
                    </span>
                  )}
                </>
              )}
            </button>
          )
        })}
      </nav>

      {/* Collapse toggle */}
      <div style={{ padding: '10px', borderTop: '1.5px solid var(--line)', flexShrink: 0 }}>
        <button
          className="squish"
          onClick={onToggle}
          style={{
            width: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: open ? 'flex-start' : 'center',
            gap: '8px',
            padding: '8px 11px',
            borderRadius: '4px',
            border: '1.5px solid var(--line)',
            background: 'var(--panel2)',
            boxShadow: '2px 2px 13px var(--shadowc)',
            color: 'var(--ink)',
            fontFamily: "'Shippori Mincho B1', serif",
            fontWeight: 700,
            fontSize: '13px',
            cursor: 'pointer',
          }}
        >
          <span>{open ? '«' : '»'}</span>
          {open && <span>Collapse</span>}
        </button>
      </div>
    </aside>
  )
}

export default Sidebar
