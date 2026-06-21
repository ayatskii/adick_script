import { useEffect, useState } from 'react'
import type { CSSProperties } from 'react'
import type { ScreenProps, RunRow, TimelineEntry } from '../types'
import { useApp } from '../AppContext'
import { getRun } from '../api'
import StatusBadge from '../components/StatusBadge'

// ============================================================
// Local helpers
// ============================================================

type HistoryTab = 'runs' | 'reconcile'

const MINCHO = "'Shippori Mincho B1', serif"
const MONO = "'JetBrains Mono', monospace"

/** A run is "dry" when its mode badge uses the dryrun status. */
function isDryRun(run: RunRow): boolean {
  return run.modeBadgeStatus === 'dryrun'
}

/** Node dot color by status (spec §3.6). */
function nodeDotColor(status: TimelineEntry['status']): string {
  switch (status) {
    case 'graded':
      return '#2f8f6b'
    case 'flagged':
      return '#cf9a36'
    case 'error':
      return '#c62d1f'
    default:
      return 'var(--c-skip)'
  }
}

/** Pad a number to two digits. */
function pad2(n: number): string {
  return n < 10 ? `0${n}` : `${n}`
}

/**
 * Build a mono timestamp for a timeline node: the selected run's HH:MM start
 * time plus the entry's tsOffset (seconds). Falls back to "+{offset}s" when the
 * run's started string has no parseable clock time.
 */
function nodeTimestamp(started: string, tsOffset: number): string {
  const m = started.match(/(\d{1,2}):(\d{2})/)
  if (!m) return `+${tsOffset}s`
  const base = parseInt(m[1], 10) * 3600 + parseInt(m[2], 10) * 60
  const t = base + tsOffset
  const hh = Math.floor(t / 3600) % 24
  const mm = Math.floor((t % 3600) / 60)
  const ss = t % 60
  return `${pad2(hh)}:${pad2(mm)}:${pad2(ss)}`
}

// ============================================================
// History / Audit screen (spec §3.6)
// ============================================================

export function History(props: ScreenProps) {
  const { showToast } = props
  const { runRows: RUN_ROWS, timelineEntries: TIMELINE_ENTRIES, reconcileRows: RECONCILE_ROWS } = useApp()
  const [tab, setTab] = useState<HistoryTab>('runs')
  const [selectedId, setSelectedId] = useState<string>(() => RUN_ROWS[0]?.id ?? '')

  const selectedRun = RUN_ROWS.find((r) => r.id === selectedId) ?? RUN_ROWS[0]
  const dry = selectedRun ? isDryRun(selectedRun) : false

  // Fetch the REAL per-run timeline for the selected run (seed shown only until
  // it loads / when the backend is offline).
  const [realTimeline, setRealTimeline] = useState<TimelineEntry[] | null>(null)
  useEffect(() => {
    const id = selectedRun?.id
    if (!id) return
    let cancelled = false
    getRun(id)
      .then((d) => { if (!cancelled) setRealTimeline(d.timeline ?? []) })
      .catch(() => { if (!cancelled) setRealTimeline(null) })
    return () => { cancelled = true }
  }, [selectedRun?.id])

  const tabBtnStyle = (active: boolean): CSSProperties => ({
    display: 'inline-flex',
    alignItems: 'center',
    gap: '8px',
    padding: '9px 16px',
    border: '1.5px solid var(--line)',
    borderRadius: '5px',
    background: active ? 'var(--violet)' : 'var(--panel2)',
    color: active ? '#fff' : 'var(--ink)',
    fontFamily: MINCHO,
    fontWeight: 700,
    fontSize: '14px',
    boxShadow: active ? '3px 3px 13px var(--shadowc)' : undefined,
  })

  return (
    <div>
      {/* Tabs */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '18px' }}>
        <button
          className="squish"
          style={tabBtnStyle(tab === 'runs')}
          onClick={() => setTab('runs')}
        >
          Runs
        </button>
        <button
          className="squish"
          style={tabBtnStyle(tab === 'reconcile')}
          onClick={() => setTab('reconcile')}
        >
          Reconcile
          <span
            style={{
              minWidth: '20px',
              textAlign: 'center',
              padding: '1px 6px',
              borderRadius: '99px',
              border: '1px solid var(--line)',
              background: 'var(--yellow)',
              color: '#3a2600',
              fontFamily: MINCHO,
              fontWeight: 800,
              fontSize: '11px',
              lineHeight: 1.4,
            }}
          >
            1
          </span>
        </button>
      </div>

      {tab === 'runs' ? (
        <RunsTab
          runRows={RUN_ROWS}
          timelineEntries={realTimeline ?? TIMELINE_ENTRIES}
          selectedRun={selectedRun}
          selectedId={selectedId}
          onSelect={setSelectedId}
          dry={dry}
          onExport={() => showToast('ok', `Exported run ${selectedRun?.id ?? ''} as CSV`)}
        />
      ) : (
        <ReconcileTab reconcileRows={RECONCILE_ROWS} />
      )}
    </div>
  )
}

// ============================================================
// Runs tab
// ============================================================

interface RunsTabProps {
  runRows: RunRow[]
  timelineEntries: TimelineEntry[]
  selectedRun: RunRow | undefined
  selectedId: string
  onSelect: (id: string) => void
  dry: boolean
  onExport: () => void
}

function RunsTab({ runRows: RUN_ROWS, timelineEntries: TIMELINE_ENTRIES, selectedRun, selectedId, onSelect, dry, onExport }: RunsTabProps) {
  if (!selectedRun) return null
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.1fr', gap: '18px', alignItems: 'start' }}>
      {/* Left — All runs table */}
      <div
        style={{
          background: 'var(--panel)',
          border: '1.5px solid var(--line)',
          borderRadius: '7px',
          boxShadow: '5px 5px 16px var(--shadowc)',
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            background: 'var(--panel2)',
            borderBottom: '1.5px solid var(--line)',
            padding: '13px 18px',
          }}
        >
          <span style={{ fontFamily: MINCHO, fontWeight: 800, fontSize: '16px', color: 'var(--ink)' }}>
            All runs
          </span>
        </div>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12.5px' }}>
          <thead>
            <tr>
              {['Mode', 'Started', 'Counts', 'Status'].map((h) => (
                <th
                  key={h}
                  style={{
                    textAlign: 'left',
                    padding: '8px 14px',
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
            {RUN_ROWS.map((run, i) => {
              const isSel = run.id === selectedId
              return (
                <tr
                  key={run.id}
                  className="squish"
                  onClick={() => onSelect(run.id)}
                  style={{
                    background: isSel ? 'var(--chip)' : i % 2 === 0 ? 'var(--panel)' : 'var(--panel2)',
                    borderTop: '1px solid var(--line)',
                    cursor: 'pointer',
                  }}
                >
                  <td style={{ padding: '9px 14px', verticalAlign: 'middle' }}>
                    <StatusBadge status={run.modeBadgeStatus} label={run.modeBadgeLabel} />
                  </td>
                  <td style={{ padding: '9px 14px', verticalAlign: 'middle', color: 'var(--ink)' }}>
                    <div style={{ fontWeight: 600 }}>{run.started}</div>
                    <div style={{ color: 'var(--ink-soft)', fontFamily: MONO, fontSize: '11.5px' }}>
                      {run.duration}
                    </div>
                  </td>
                  <td
                    style={{
                      padding: '9px 14px',
                      verticalAlign: 'middle',
                      color: 'var(--ink)',
                      fontVariantNumeric: 'tabular-nums',
                    }}
                  >
                    {run.counts}
                  </td>
                  <td style={{ padding: '9px 14px', verticalAlign: 'middle' }}>
                    <StatusBadge status={run.statusBadgeStatus} label={run.statusBadgeLabel} />
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* Right — Run timeline */}
      <div
        style={{
          background: 'var(--panel)',
          border: '1.5px solid var(--line)',
          borderRadius: '7px',
          boxShadow: '5px 5px 16px var(--shadowc)',
          overflow: 'hidden',
        }}
      >
        {/* Header */}
        <div
          style={{
            background: 'var(--panel2)',
            borderBottom: '1.5px solid var(--line)',
            padding: '12px 18px',
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
          }}
        >
          <span style={{ fontFamily: MINCHO, fontWeight: 800, fontSize: '16px', color: 'var(--ink)' }}>
            Run timeline
          </span>
          <StatusBadge status={selectedRun.modeBadgeStatus} label={selectedRun.modeBadgeLabel} />
          <button
            className="squish"
            onClick={onExport}
            style={{
              marginLeft: 'auto',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '7px 13px',
              border: '1.5px solid var(--line)',
              borderRadius: '4px',
              background: 'var(--sky)',
              color: '#fff',
              fontFamily: MINCHO,
              fontWeight: 700,
              fontSize: '12.5px',
              boxShadow: '2px 2px 13px var(--shadowc)',
            }}
          >
            <span aria-hidden="true">⬇</span> Export
          </button>
        </div>

        {/* Dry-run hatch banner */}
        {dry && (
          <div
            style={{
              padding: '9px 18px',
              background:
                'repeating-linear-gradient(45deg,rgba(164,92,247,.16),rgba(164,92,247,.16) 8px,transparent 8px,transparent 16px)',
              borderBottom: '1.5px dashed var(--violet)',
              fontFamily: MINCHO,
              fontWeight: 700,
              fontSize: '13px',
              color: 'var(--ink)',
            }}
          >
            <span aria-hidden="true" style={{ marginRight: '6px' }}>
              👻
            </span>
            Dry-run — proposed scores were computed but nothing was submitted.
          </div>
        )}

        {/* Timeline */}
        <div style={{ padding: '18px 20px' }}>
          <div style={{ position: 'relative', paddingLeft: '24px' }}>
            {/* Vertical rail */}
            <div
              style={{
                position: 'absolute',
                left: '6px',
                top: '6px',
                bottom: '6px',
                width: '3px',
                background: 'var(--chip)',
                borderRadius: '99px',
              }}
            />
            {TIMELINE_ENTRIES.map((entry, i) => (
              <TimelineNode
                key={`${entry.student}-${entry.ex}-${i}`}
                entry={entry}
                dry={dry}
                started={selectedRun.started}
                last={i === TIMELINE_ENTRIES.length - 1}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

// ============================================================
// Timeline node
// ============================================================

interface TimelineNodeProps {
  entry: TimelineEntry
  dry: boolean
  started: string
  last: boolean
}

function TimelineNode({ entry, dry, started, last }: TimelineNodeProps) {
  const proposed = entry.proposedScore === null ? '—' : String(entry.proposedScore)
  // For a dry run, nothing is submitted: submitted always shows "—".
  const submitted = dry || entry.submittedScore === null ? '—' : String(entry.submittedScore)
  const submittedMuted = submitted === '—'

  return (
    <div style={{ position: 'relative', marginBottom: last ? 0 : '18px' }}>
      {/* Node dot */}
      <div
        style={{
          position: 'absolute',
          left: '-24px',
          top: '2px',
          width: '13px',
          height: '13px',
          borderRadius: '50%',
          background: nodeDotColor(entry.status),
          border: '1.5px solid var(--line)',
          boxShadow: '0 0 0 3px var(--panel)',
        }}
      />
      {/* Row 1: student · ex + HUMAN EDITED + timestamp */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
        <span style={{ fontFamily: MINCHO, fontWeight: 700, fontSize: '13.5px', color: 'var(--ink)' }}>
          {entry.student} · {entry.ex}
        </span>
        {entry.humanEdited && (
          <span
            style={{
              padding: '2px 7px',
              borderRadius: '3px',
              border: '1px solid var(--line)',
              background: 'var(--yellow)',
              color: '#3a2600',
              fontFamily: MINCHO,
              fontWeight: 800,
              fontSize: '10px',
              letterSpacing: '.4px',
              textTransform: 'uppercase',
              lineHeight: 1,
            }}
          >
            Human edited
          </span>
        )}
        <span
          style={{
            marginLeft: 'auto',
            fontFamily: MONO,
            fontSize: '11.5px',
            color: 'var(--ink-soft)',
          }}
        >
          {nodeTimestamp(started, entry.tsOffset)}
        </span>
      </div>
      {/* Row 2: proposed → submitted */}
      <div style={{ marginTop: '3px', fontSize: '12.5px', color: 'var(--ink-soft)' }}>
        proposed{' '}
        <span style={{ color: 'var(--ink)', fontWeight: 600, fontVariantNumeric: 'tabular-nums' }}>
          {proposed}
        </span>{' '}
        → submitted{' '}
        <span
          style={{
            color: submittedMuted ? 'var(--ink-soft)' : 'var(--ink)',
            fontWeight: 600,
            fontVariantNumeric: 'tabular-nums',
          }}
        >
          {submitted}
        </span>
      </div>
    </div>
  )
}

// ============================================================
// Reconcile tab
// ============================================================

function ReconcileTab({ reconcileRows: RECONCILE_ROWS }: { reconcileRows: import('../types').ReconcileRow[] }) {
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
      {/* Header */}
      <div
        style={{
          background: 'var(--panel2)',
          borderBottom: '1.5px solid var(--line)',
          padding: '14px 18px',
        }}
      >
        <div style={{ fontFamily: MINCHO, fontWeight: 800, fontSize: '16px', color: 'var(--ink)' }}>
          Reconcile · what's complete on Edvibe
        </div>
        <div style={{ marginTop: '4px', fontSize: '13px', color: 'var(--ink-soft)' }}>
          Read-only view. Anything the bot completed unexpectedly is flagged for your attention.
        </div>
      </div>

      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
        <thead>
          <tr>
            {['Student', 'Lesson', 'Completed by', ''].map((h, idx) => (
              <th
                key={idx}
                style={{
                  textAlign: 'left',
                  padding: '9px 18px',
                  fontFamily: MINCHO,
                  fontWeight: 700,
                  fontSize: '11px',
                  letterSpacing: '.4px',
                  textTransform: 'uppercase',
                  color: 'var(--ink-soft)',
                  background: 'var(--panel3)',
                  borderBottom: '1px solid var(--line)',
                }}
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {RECONCILE_ROWS.map((row, i) => (
            <tr
              key={`${row.student}-${row.lesson}-${i}`}
              style={{
                background: i % 2 === 0 ? 'var(--panel)' : 'var(--panel2)',
                borderTop: '1px solid var(--line)',
              }}
            >
              <td
                style={{
                  padding: '11px 18px',
                  fontFamily: MINCHO,
                  fontWeight: 700,
                  fontSize: '14px',
                  color: 'var(--ink)',
                  verticalAlign: 'middle',
                }}
              >
                {row.student}
              </td>
              <td style={{ padding: '11px 18px', color: 'var(--ink)', verticalAlign: 'middle' }}>
                {row.lesson}
              </td>
              <td style={{ padding: '11px 18px', color: 'var(--ink-soft)', verticalAlign: 'middle' }}>
                {row.completedBy}
              </td>
              <td style={{ padding: '11px 18px', verticalAlign: 'middle' }}>
                {row.flagStatus && (
                  <StatusBadge status={row.flagStatus} label={row.flagLabel ?? undefined} />
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default History
