import { Fragment, useState } from 'react'
import type { ScreenProps, StudentRow } from '../types'
import { STUDENT_ROWS } from '../data'
import StatusBadge from '../components/StatusBadge'

const mincho = "'Shippori Mincho B1', serif"

// Uppercase 11px Mincho table header cells
const headStyle: React.CSSProperties = {
  fontFamily: mincho,
  fontWeight: 700,
  fontSize: '11px',
  letterSpacing: '.4px',
  textTransform: 'uppercase',
  color: 'var(--ink-soft)',
  textAlign: 'left',
  padding: '9px 14px',
  whiteSpace: 'nowrap',
}

function ExpandedRow({ student }: { student: StudentRow }) {
  return (
    <div style={{ background: 'var(--panel3)', padding: '14px 18px 16px 44px' }}>
      <div
        style={{
          fontFamily: mincho,
          fontWeight: 700,
          fontSize: '11px',
          letterSpacing: '.4px',
          textTransform: 'uppercase',
          color: 'var(--ink-soft)',
          marginBottom: '10px',
        }}
      >
        Awaiting lessons
      </div>
      {student.lessons.length === 0 ? (
        <div
          style={{
            fontStyle: 'italic',
            fontSize: '13.5px',
            color: 'var(--ink-soft)',
          }}
        >
          No awaiting lessons — all caught up. 🎉
        </div>
      ) : (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
          {student.lessons.map((lesson, i) => (
            <div
              key={i}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
                padding: '6px 9px',
                border: '1px solid var(--line)',
                borderRadius: '4px',
                background: 'var(--panel)',
                fontSize: '13px',
                color: 'var(--ink)',
              }}
            >
              <span style={{ fontFamily: mincho, fontWeight: 700 }}>{lesson.name}</span>
              <StatusBadge status={lesson.status} />
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export function Students({ showToast }: ScreenProps) {
  const [expanded, setExpanded] = useState<Set<string>>(new Set())

  function toggle(id: string) {
    setExpanded((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  function runStudent(e: React.MouseEvent, name: string) {
    e.stopPropagation()
    showToast('ok', `Queued a run for ${name}`)
  }

  return (
    <div
      style={{
        background: 'var(--panel)',
        border: '1.5px solid var(--line)',
        borderRadius: '7px',
        boxShadow: '5px 5px 16px var(--shadowc)',
        overflow: 'hidden',
      }}
    >
      {/* Header strip */}
      <div
        style={{
          background: 'var(--panel2)',
          borderBottom: '1.5px solid var(--line)',
          padding: '14px 18px',
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
        }}
      >
        <h2
          style={{
            margin: 0,
            fontFamily: mincho,
            fontWeight: 800,
            fontSize: '17px',
            color: 'var(--ink)',
          }}
        >
          Students
        </h2>
        <span
          style={{
            padding: '3px 10px',
            borderRadius: '99px',
            background: 'var(--sky)',
            color: '#fff',
            fontFamily: mincho,
            fontWeight: 700,
            fontSize: '11.5px',
            whiteSpace: 'nowrap',
          }}
        >
          43 in marathon
        </span>
        <span
          style={{
            marginLeft: 'auto',
            fontSize: '12.5px',
            color: 'var(--ink-soft)',
            whiteSpace: 'nowrap',
          }}
        >
          Marathon: Pre-IELTS · Curator: Mister Adilet
        </span>
      </div>

      {/* Table */}
      <table
        style={{
          width: '100%',
          borderCollapse: 'collapse',
          fontSize: '13.5px',
          color: 'var(--ink)',
        }}
      >
        <thead>
          <tr style={{ background: 'var(--panel3)' }}>
            <th style={{ ...headStyle, width: '36px', padding: '9px 0 9px 14px' }} />
            <th style={headStyle}>Student</th>
            <th style={headStyle}>Awaiting</th>
            <th style={headStyle}>Last activity</th>
            <th style={headStyle}>Curator</th>
            <th style={{ ...headStyle, textAlign: 'right' }}>Action</th>
          </tr>
        </thead>
        <tbody>
          {STUDENT_ROWS.map((student, idx) => {
            const isOpen = expanded.has(student.id)
            const zebra = idx % 2 === 0 ? 'var(--panel)' : 'var(--panel2)'
            return (
              <Fragment key={student.id}>
                <tr
                  onClick={() => toggle(student.id)}
                  style={{
                    background: zebra,
                    borderTop: '1px solid var(--line)',
                    cursor: 'pointer',
                  }}
                >
                  {/* Chevron */}
                  <td
                    style={{
                      padding: '9px 0 9px 14px',
                      color: 'var(--ink-soft)',
                      fontSize: '12px',
                      lineHeight: 1,
                      userSelect: 'none',
                    }}
                  >
                    {isOpen ? '▾' : '▸'}
                  </td>
                  {/* Name */}
                  <td
                    style={{
                      padding: '9px 14px',
                      fontFamily: mincho,
                      fontWeight: 700,
                      fontSize: '14.5px',
                    }}
                  >
                    {student.name}
                  </td>
                  {/* Awaiting — StatusBadge, label = raw count (idle if 0 else queued) */}
                  <td style={{ padding: '9px 14px' }}>
                    <StatusBadge
                      status={student.awaiting === 0 ? 'idle' : 'queued'}
                      label={String(student.awaiting)}
                    />
                  </td>
                  {/* Last activity */}
                  <td style={{ padding: '9px 14px', color: 'var(--ink-soft)' }}>
                    {student.lastActivity}
                  </td>
                  {/* Curator */}
                  <td style={{ padding: '9px 14px' }}>Mister Adilet</td>
                  {/* Action */}
                  <td style={{ padding: '9px 14px', textAlign: 'right' }}>
                    <button
                      className="squish"
                      onClick={(e) => runStudent(e, student.name)}
                      style={{
                        background: 'var(--violet)',
                        color: '#fff',
                        border: '1.5px solid var(--line)',
                        borderRadius: '4px',
                        padding: '5px 12px',
                        fontFamily: mincho,
                        fontWeight: 700,
                        fontSize: '12px',
                        boxShadow: '2px 2px 13px var(--shadowc)',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      ▶ Run
                    </button>
                  </td>
                </tr>
                {isOpen && (
                  <tr style={{ borderTop: '1px solid var(--line)' }}>
                    <td colSpan={6} style={{ padding: 0 }}>
                      <ExpandedRow student={student} />
                    </td>
                  </tr>
                )}
              </Fragment>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

export default Students
