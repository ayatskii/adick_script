import { useEffect, useMemo, useRef, useState } from 'react'
import type { ScreenProps, RunMode, StatusKind } from '../types'
import type { RunEvent } from '../api'
import { useApp } from '../AppContext'
import { StatusBadge } from '../components/StatusBadge'

// ============================================================
// Live Monitor — REAL, event-driven.
// Every number, row, score and log line is derived from the live
// run events streamed over the WebSocket (App.tsx `liveEvents`).
// There is NO simulation and NO seed/hardcoded data here: if no run
// has produced events, we show the napping state.
//
// Event shapes (from backend/jobs.normalize_runner_event):
//   progress  data:{students_done,students,current,total}
//   student   data:{student_name,student_id,index,students_total}
//   graded/skipped/flagged
//             data:{student_name,lesson_name,exercise_no,type,score,
//                   score_max,comment,confidence,reason}
//   log       data:{level,message}
// ============================================================

type LogLevel = 'info' | 'ok' | 'warn' | 'err'
type ExType = 'audio' | 'text'

interface ExNode {
  ex: string
  type: ExType
  status: StatusKind            // graded | skipped | flagged
  score: number | null
  scoreMax: number | null
  conf: number | null
  comment: string
  reason?: string
}
interface LessonGroup { lesson: string; lessonShort: string; nodes: ExNode[] }
interface StudentGroup { student: string; lessons: LessonGroup[]; active: boolean }

const EX_STATUSES = new Set(['graded', 'skipped', 'flagged'])

function lessonShortOf(name: string): string {
  return name.split(' — ')[0].split(':')[0].trim()
}

// ---- derive the whole view from the event stream ----
function deriveFromEvents(events: RunEvent[]) {
  const students: StudentGroup[] = []
  const upsert = (name: string): StudentGroup => {
    let s = students.find(x => x.student === name)
    if (!s) { s = { student: name, lessons: [], active: false }; students.push(s) }
    return s
  }
  let activeStudent: string | null = null
  const counts = { graded: 0, skipped: 0, flagged: 0 }
  let latestEx: { node: ExNode; student: string; lesson: string } | null = null

  for (const ev of events) {
    const d = (ev.data ?? {}) as Record<string, unknown>
    if (ev.type === 'student') {
      activeStudent = (d.student_name as string) || (d.student_id as string) || activeStudent
      if (activeStudent) upsert(activeStudent)
      continue
    }
    if (EX_STATUSES.has(ev.type)) {
      const sname = (d.student_name as string) || (d.student_id as string) || activeStudent || '—'
      const sg = upsert(sname)
      const lname = (d.lesson_name as string) || (d.lesson_id ? `Lesson ${d.lesson_id}` : 'Lesson')
      let lg = sg.lessons.find(l => l.lesson === lname)
      if (!lg) { lg = { lesson: lname, lessonShort: lessonShortOf(lname), nodes: [] }; sg.lessons.push(lg) }
      const node: ExNode = {
        ex: (d.exercise_no as string) || '—',
        type: d.type === 'audio' ? 'audio' : 'text',
        status: ev.type as StatusKind,
        score: typeof d.score === 'number' ? d.score : null,
        scoreMax: typeof d.score_max === 'number' ? d.score_max : null,
        conf: typeof d.confidence === 'number' ? d.confidence : null,
        comment: (d.comment as string) || '',
        reason: d.reason as string | undefined,
      }
      lg.nodes.push(node)
      counts[ev.type as 'graded' | 'skipped' | 'flagged']++
      latestEx = { node, student: sname, lesson: lg.lessonShort }
    }
  }
  for (const s of students) s.active = s.student === activeStudent
  const processed = counts.graded + counts.skipped + counts.flagged
  return { tree: students, counts, processed, activeStudent, latestEx }
}

function progressFromEvents(events: RunEvent[]): { done: number; total: number } | null {
  for (let i = events.length - 1; i >= 0; i--) {
    const ev = events[i]
    if (ev.type === 'progress' && ev.data) {
      const d = ev.data as Record<string, unknown>
      const done = (d.students_done as number) ?? (d.current as number) ?? 0
      const total = (d.students as number) ?? (d.total as number) ?? 0
      return { done, total }
    }
  }
  return null
}

function logFromEvents(events: RunEvent[]): { id: number; ts: string; level: LogLevel; text: string }[] {
  let id = 0
  const out: { id: number; ts: string; level: LogLevel; text: string }[] = []
  for (const ev of events) {
    if (ev.type === 'progress' || ev.type === 'student') continue  // not log noise
    const d = (ev.data ?? {}) as Record<string, unknown>
    let level: LogLevel = 'info'
    if (ev.type === 'graded') level = 'ok'
    else if (ev.type === 'skipped') level = 'warn'
    else if (ev.type === 'flagged') level = 'warn'
    else if (d.level === 'error' || d.level === 'err') level = 'err'
    else if (d.level === 'ok') level = 'ok'
    else if (d.level === 'warn') level = 'warn'
    const text = (d.message as string) || ev.message || ev.type
    const ts = ev.ts ? new Date(ev.ts).toISOString().substr(11, 8) : ''
    out.push({ id: id++, ts, level, text })
  }
  return out
}

function actionText(status: StatusKind, mode: RunMode): string {
  switch (status) {
    case 'skipped': return mode === 'dryrun' || mode === 'review'
      ? 'Proposed — awaiting your review' : 'Skipped'
    case 'flagged': return 'Flagged — needs human review'
    case 'error': return 'Error — see log'
    case 'graded': return mode === 'dryrun'
      ? 'Graded — NOT submitted (dry-run)' : 'Graded & submitted ✓'
    default: return ''
  }
}
function actionColor(status: StatusKind): string {
  switch (status) {
    case 'skipped': return 'var(--c-skip)'
    case 'flagged': return 'var(--yellow)'
    case 'error': return 'var(--pink)'
    case 'graded': return 'var(--lime)'
    default: return 'var(--ink-soft)'
  }
}
function modeBadge(mode: RunMode): { status: StatusKind; label: string } {
  if (mode === 'full') return { status: 'flagged', label: 'Full-auto' }
  if (mode === 'review') return { status: 'queued', label: 'Review' }
  return { status: 'dryrun', label: 'Dry-run' }
}

const LOG_COLORS: Record<LogLevel, string> = {
  info: '#8fd0ff', ok: '#7bf0a0', warn: '#ffd27d', err: '#ff8f8f',
}

function SleepingRobot() {
  return (
    <svg width="140" height="140" viewBox="0 0 140 140" fill="none"
      style={{ animation: 'float 4s ease-in-out infinite' }} aria-hidden="true">
      <circle cx="70" cy="66" r="58" fill="var(--sun)" opacity="0.08" />
      <line x1="70" y1="40" x2="70" y2="26" stroke="var(--ink-soft)" strokeWidth="3" strokeLinecap="round" />
      <circle cx="70" cy="22" r="6" fill="var(--sun)" />
      <rect x="36" y="40" width="68" height="60" rx="12" fill="var(--indigo)" stroke="var(--line)" strokeWidth="1.5" />
      <rect x="46" y="52" width="48" height="34" rx="7" fill="var(--panel)" />
      <path d="M54 70 Q60 76 66 70" fill="none" stroke="var(--ink)" strokeWidth="3" strokeLinecap="round" />
      <path d="M74 70 Q80 76 86 70" fill="none" stroke="var(--ink)" strokeWidth="3" strokeLinecap="round" />
      <text x="104" y="44" fontFamily="serif" fontWeight="800" fontSize="16" fill="var(--ink-soft)">z</text>
    </svg>
  )
}
function StopGlyph() {
  return <svg width="12" height="12" viewBox="0 0 12 12" fill="#fff" aria-hidden="true"><rect x="1.5" y="1.5" width="9" height="9" rx="1.5" /></svg>
}

export function LiveMonitor(props: ScreenProps) {
  const { run, mascotName, showToast, openDialog, startRun, defaultRunMode } = props
  const { activeRunId, liveEvents } = useApp()

  // Napping unless a run is active OR we already have events to show.
  if (!run.active && liveEvents.length === 0) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center',
        justifyContent: 'center', textAlign: 'center', padding: '60px 20px', gap: '6px', minHeight: '420px' }}>
        <SleepingRobot />
        <h2 style={{ margin: '8px 0 0', fontFamily: "'Shippori Mincho B1', serif", fontWeight: 800, fontSize: '22px', color: 'var(--ink)' }}>
          {mascotName} is napping
        </h2>
        <p style={{ margin: 0, maxWidth: '420px', fontSize: '13.5px', lineHeight: 1.5, color: 'var(--ink-soft)' }}>
          No run is in progress. Start one from New Run and the live tree + log will light up here — from the real bot.
        </p>
        <button className="squish" onClick={() => startRun(defaultRunMode)}
          style={{ marginTop: '14px', padding: '11px 20px', border: '1.5px solid var(--line)', borderRadius: '5px',
            background: 'var(--violet)', color: '#fff', fontFamily: "'Shippori Mincho B1', serif", fontWeight: 800,
            fontSize: '14.5px', boxShadow: '4px 4px 13px var(--shadowc)' }}>
          Start a run →
        </button>
      </div>
    )
  }

  return <ActiveMonitor run={run} mode={run.mode} active={run.active} finished={run.finished}
    showToast={showToast} openDialog={openDialog} activeRunId={activeRunId} liveEvents={liveEvents} />
}

interface ActiveProps {
  run: ScreenProps['run']
  mode: RunMode
  active: boolean
  finished: boolean
  showToast: ScreenProps['showToast']
  openDialog: ScreenProps['openDialog']
  activeRunId: string | null
  liveEvents: RunEvent[]
}

function ActiveMonitor(props: ActiveProps) {
  const { mode, active, finished, showToast, openDialog, activeRunId, liveEvents } = props

  const [filter, setFilter] = useState<'all' | LogLevel>('all')

  const { tree, counts, processed, latestEx } = useMemo(() => deriveFromEvents(liveEvents), [liveEvents])
  const prog = useMemo(() => progressFromEvents(liveEvents), [liveEvents])
  const logLines = useMemo(() => logFromEvents(liveEvents), [liveEvents])

  const studentsDone = prog?.done ?? 0
  const studentsTotal = prog?.total ?? tree.length
  const runFinished = finished || (!active && activeRunId !== null)
  const pct = runFinished ? 100 : (studentsTotal > 0 ? Math.round((studentsDone / studentsTotal) * 100) : 0)
  const eta = runFinished ? 'done' : active ? 'running…' : '—'

  // completion toast (once)
  const toastRef = useRef(false)
  useEffect(() => {
    if (!runFinished || toastRef.current) return
    toastRef.current = true
    if (mode === 'dryrun' || mode === 'review') {
      showToast('info', `Run finished — ${counts.graded + counts.skipped} proposals, ${counts.flagged} flagged, nothing submitted`)
    } else {
      showToast('ok', `Run finished — ${counts.graded} grades submitted, ${counts.flagged} flagged`)
    }
  }, [runFinished, mode, counts, showToast])

  const filteredLog = filter === 'all' ? logLines : logLines.filter(l => l.level === filter)
  const logBodyRef = useRef<HTMLDivElement>(null)
  useEffect(() => {
    const el = logBodyRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [logLines.length, filter])

  const mb = modeBadge(mode)
  const showStop = active && activeRunId !== null

  const studentDot = (sg: StudentGroup): string => {
    if (sg.active && active) return '#3f72b0'
    if (sg.lessons.some(l => l.nodes.length)) return '#2f8f6b'
    return 'var(--c-skip)'
  }

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr', gap: '18px', alignItems: 'start' }}>
      {/* LEFT — REAL run tree */}
      <section style={{ background: 'var(--panel)', border: '1.5px solid var(--line)', borderRadius: '7px',
        boxShadow: '5px 5px 16px var(--shadowc)', overflow: 'hidden' }}>
        <header style={{ background: 'var(--panel2)', borderBottom: '1.5px solid var(--line)', padding: '12px 16px',
          fontFamily: "'Shippori Mincho B1', serif", fontWeight: 800, fontSize: '15px', color: 'var(--ink)' }}>
          Run tree
        </header>
        <div style={{ maxHeight: '560px', overflowY: 'auto', padding: '14px 14px 16px' }}>
          {tree.length === 0 ? (
            <div style={{ fontSize: '13px', color: 'var(--ink-soft)' }}>Waiting for the first student…</div>
          ) : tree.map((sg, si) => (
            <div key={sg.student} style={{ marginBottom: si === tree.length - 1 ? 0 : '14px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '9px' }}>
                <span style={{ width: '11px', height: '11px', borderRadius: '50%', background: studentDot(sg),
                  border: '1px solid var(--line)', flex: 'none' }} />
                <span style={{ fontFamily: "'Shippori Mincho B1', serif", fontWeight: 700, fontSize: '14px', color: 'var(--ink)' }}>
                  {sg.student}
                </span>
              </div>
              {sg.lessons.map(lg => (
                <div key={lg.lesson} style={{ marginLeft: '18px', borderLeft: '1.5px solid var(--chip)', paddingLeft: '10px', marginTop: '6px' }}>
                  <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--ink-soft)', margin: '2px 0 4px' }}>{lg.lessonShort}</div>
                  {lg.nodes.map((n, ni) => (
                    <div key={`${n.ex}-${ni}`} style={{ display: 'flex', alignItems: 'center', gap: '8px',
                      padding: '4px 7px', borderRadius: '3px', marginBottom: '3px' }}>
                      <span style={{ fontSize: '12px', lineHeight: 1, flex: 'none' }}>{n.type === 'audio' ? '🔊' : '✎'}</span>
                      <span style={{ fontSize: '12px', flex: 1, minWidth: 0, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                        <span style={{ fontWeight: 700, color: 'var(--ink)' }}>{n.ex}</span>{' '}
                        <span style={{ color: 'var(--ink-soft)' }}>{n.type === 'audio' ? 'Audio' : 'Written'}</span>
                        {n.score != null && <span style={{ color: 'var(--ink-soft)' }}> · {n.score}{n.scoreMax ? `/${n.scoreMax}` : ''}</span>}
                      </span>
                      <StatusBadge status={n.status} />
                    </div>
                  ))}
                </div>
              ))}
            </div>
          ))}
        </div>
      </section>

      {/* RIGHT */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {/* PROGRESS (real, student-based) */}
        <section style={{ background: 'var(--panel)', border: '1.5px solid var(--line)', borderRadius: '7px',
          boxShadow: '5px 5px 16px var(--shadowc)', padding: '16px 18px 18px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap', marginBottom: '14px' }}>
            <h3 style={{ margin: 0, fontFamily: "'Shippori Mincho B1', serif", fontWeight: 800, fontSize: '17px', color: 'var(--ink)' }}>Progress</h3>
            <StatusBadge status={mb.status} label={mb.label} />
            <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--ink-soft)' }}>
              {studentsDone}/{studentsTotal} students · ETA {eta}
            </span>
            <span style={{ flex: 1 }} />
            {showStop && (
              <button className="squish" onClick={() => openDialog('stop')}
                style={{ display: 'inline-flex', alignItems: 'center', gap: '7px', padding: '8px 13px', border: '1.5px solid var(--line)',
                  borderRadius: '4px', background: '#c62d1f', color: '#fff', fontFamily: "'Shippori Mincho B1', serif", fontWeight: 800,
                  fontSize: '13px', boxShadow: '3px 3px 13px var(--shadowc)' }}>
                <StopGlyph /> Stop
              </button>
            )}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            <div style={{ flex: 1, height: '24px', border: '1.5px solid var(--line)', borderRadius: '99px', background: 'var(--panel2)', overflow: 'hidden' }}>
              <div style={{ height: '100%', width: `${pct}%`,
                background: 'repeating-linear-gradient(45deg,var(--violet),var(--violet) 11px,#4a5d8f 11px,#4a5d8f 22px)',
                borderRadius: '99px', transition: 'width .5s ease' }} />
            </div>
            <span style={{ minWidth: '54px', textAlign: 'right', fontFamily: "'Shippori Mincho B1', serif", fontWeight: 800,
              fontSize: '22px', fontVariantNumeric: 'tabular-nums', color: 'var(--violet)' }}>{pct}%</span>
          </div>
          <div style={{ marginTop: '9px', fontSize: '12.5px', color: 'var(--ink-soft)' }}>
            {processed} exercises processed · <span style={{ color: 'var(--lime)' }}>{counts.graded} graded</span>
            {' · '}<span style={{ color: 'var(--c-skip)' }}>{counts.skipped} proposed</span>
            {' · '}<span style={{ color: 'var(--yellow)' }}>{counts.flagged} flagged</span>
          </div>
        </section>

        {/* DETAIL — latest real outcome */}
        {latestEx && (
          <section style={{ background: 'var(--panel)', border: '1.5px solid var(--line)', borderRadius: '7px',
            boxShadow: '5px 5px 16px var(--shadowc)', overflow: 'hidden' }}>
            <header style={{ background: 'var(--panel2)', borderBottom: '1.5px solid var(--line)', padding: '11px 16px',
              display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
              <span style={{ fontFamily: "'Shippori Mincho B1', serif", fontWeight: 800, fontSize: '14.5px', color: 'var(--ink)' }}>
                {latestEx.student} · {latestEx.lesson} · {latestEx.node.ex}
              </span>
              <span style={{ padding: '2px 9px', borderRadius: '99px', border: '1px solid var(--line)', background: 'var(--chip)',
                color: 'var(--ink-soft)', fontSize: '11px', fontWeight: 600 }}>
                {latestEx.node.type === 'audio' ? 'Audio answer' : 'Written answer'}
              </span>
              <span style={{ flex: 1 }} />
              <StatusBadge status={latestEx.node.status} />
            </header>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 130px', gap: '16px', padding: '16px 18px 18px' }}>
              <div style={{ minWidth: 0 }}>
                <div style={{ fontSize: '11px', fontWeight: 700, letterSpacing: '.4px', textTransform: 'uppercase', color: 'var(--ink-soft)', marginBottom: '5px' }}>AI comment</div>
                <p style={{ margin: '0 0 14px', fontSize: '13px', lineHeight: 1.55, color: 'var(--ink)' }}>
                  {latestEx.node.comment || (latestEx.node.reason ? `(${latestEx.node.reason})` : '—')}
                </p>
                <span style={{ display: 'inline-block', padding: '4px 11px', borderRadius: '4px', border: '1.5px solid var(--line)',
                  background: 'var(--panel2)', fontFamily: "'Shippori Mincho B1', serif", fontWeight: 700, fontSize: '12px',
                  color: actionColor(latestEx.node.status) }}>
                  {actionText(latestEx.node.status, mode)}
                </span>
              </div>
              <div style={{ background: 'var(--panel3)', border: '1.5px solid var(--line)', borderRadius: '6px', padding: '13px 12px',
                textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                <div style={{ fontSize: '11px', fontWeight: 700, letterSpacing: '.6px', color: 'var(--ink-soft)' }}>SCORE</div>
                <div style={{ fontFamily: "'Shippori Mincho B1', serif", fontWeight: 800, fontSize: '46px', lineHeight: 1.05,
                  fontVariantNumeric: 'tabular-nums', color: 'var(--ink)' }}>
                  {latestEx.node.score != null ? latestEx.node.score : '—'}
                  <span style={{ fontSize: '20px', color: 'var(--ink-soft)' }}>/{latestEx.node.scoreMax ?? '?'}</span>
                </div>
                <div style={{ marginTop: '6px', fontFamily: "'JetBrains Mono', monospace", fontSize: '11px', color: 'var(--ink-soft)' }}>
                  {latestEx.node.conf != null ? `CONF ${latestEx.node.conf.toFixed(2)}` : ''}
                </div>
              </div>
            </div>
          </section>
        )}

        {/* LOG — real event stream */}
        <section style={{ background: 'var(--logbg)', border: '1.5px solid var(--line)', borderRadius: '7px',
          boxShadow: '5px 5px 16px var(--shadowc)', overflow: 'hidden' }}>
          <header style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap', padding: '10px 14px',
            borderBottom: '2px solid rgba(255,255,255,.12)' }}>
            <span style={{ fontFamily: "'JetBrains Mono', monospace", fontWeight: 600, fontSize: '12.5px', color: '#7bf0a0' }}>● live log</span>
            <span style={{ flex: 1 }} />
            {(['all', 'info', 'ok', 'warn', 'err'] as const).map(lv => {
              const label = lv === 'all' ? 'All' : lv === 'info' ? 'Info' : lv === 'ok' ? 'OK' : lv === 'warn' ? 'Warn' : 'Error'
              const activeF = filter === lv
              return (
                <button key={lv} className="squish" onClick={() => setFilter(lv)}
                  style={{ padding: '3px 10px', borderRadius: '4px', border: 'none', background: activeF ? 'var(--violet)' : 'rgba(255,255,255,.08)',
                    color: activeF ? '#fff' : 'var(--logink)', fontFamily: "'Shippori Mincho B1', serif", fontWeight: 700, fontSize: '11.5px' }}>
                  {label}
                </button>
              )
            })}
          </header>
          <div ref={logBodyRef} style={{ maxHeight: '220px', overflowY: 'auto', padding: '12px 14px',
            fontFamily: "'JetBrains Mono', monospace", fontSize: '12px', lineHeight: 1.65 }}>
            {filteredLog.length === 0 ? (
              <div style={{ color: '#6a6090' }}>— no {filter === 'all' ? '' : filter + ' '}lines yet —</div>
            ) : filteredLog.map(l => (
              <div key={l.id} style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                <span style={{ color: '#6a6090' }}>{l.ts}</span>{' '}
                <span style={{ color: LOG_COLORS[l.level] }}>{l.text}</span>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  )
}

export default LiveMonitor
