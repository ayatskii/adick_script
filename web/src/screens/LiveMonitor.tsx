import { useEffect, useMemo, useRef, useState } from 'react'
import type { ScreenProps, RunMode, StatusKind, StudentRow, ReviewItem } from '../types'
import type { RunEvent } from '../api'
import { useApp } from '../AppContext'
import { StatusBadge } from '../components/StatusBadge'

// ============================================================
// Live Monitor — §3.3
// Empty (napping mascot) state + active/done state:
//   left run-tree · right progress card / detail card / log console
//   + a 900ms tick simulation that drives progress, tree highlight,
//   detail record and a streaming filterable log.
//
// NOTE: the global `run` state (App.tsx) owns active/finished/mode/
// total/students but is NOT mutated over time and exposes no setter
// to screens. So this screen keeps its OWN local simulation state
// (queue index, per-node status, log lines), seeded from run.total /
// run.students / run.mode, and advances it on a setInterval tick.
// ============================================================

// ---- local-only types (not added to shared types.ts) ----
type LogLevel = 'info' | 'ok' | 'warn' | 'err'

interface LogLine {
  id: number
  ts: string
  level: LogLevel
  text: string
}

type ExType = 'audio' | 'text'

interface SimNode {
  /** flat queue index */
  i: number
  studentIdx: number
  student: string
  /** short lesson name e.g. "Lesson 14" */
  lessonShort: string
  /** full lesson name e.g. "Lesson 14 — Entertainment" */
  lesson: string
  ex: string
  type: ExType
  /** resolved terminal status for this node once processed */
  outcome: StatusKind
  score: number
  conf: number
  transcript: string
  comment: string
}

// per-node live status: 'queued' until reached, 'evaluating' while
// current, then its terminal outcome.
type NodeStatus = StatusKind

// ============================================================
// Build a deterministic simulation queue.
// We span run.students students and run.total exercises so the tree,
// progress %, student-done count and ETA all stay coherent.
// Exercise rows / scores / comments are pulled from the review seed
// where a (student, ex) pair matches, else sensible defaults.
// ============================================================
function buildQueue(total: number, students: number, studentRows: StudentRow[], reviewItems: ReviewItem[]): SimNode[] {
  const STUDENT_ROWS = studentRows
  const REVIEW_ITEMS = reviewItems
  const exTemplates: { ex: string; type: ExType }[] = [
    { ex: '1.2', type: 'audio' },
    { ex: '2.1', type: 'text' },
    { ex: '3.4', type: 'text' },
    { ex: '3.1', type: 'audio' },
    { ex: '1.1', type: 'text' },
    { ex: '1.3', type: 'audio' },
  ]

  const roster = STUDENT_ROWS.slice(0, Math.max(1, Math.min(students, STUDENT_ROWS.length)))
  const queue: SimNode[] = []

  // distribute `total` exercises across `students` students as evenly
  // as possible (extra exercises land on the earliest students).
  const base = Math.floor(total / students)
  const extra = total % students

  let i = 0
  for (let s = 0; s < students && i < total; s++) {
    const rosterIdx = s % roster.length
    const student = roster[rosterIdx]
    const count = base + (s < extra ? 1 : 0)
    // pick a lesson for this student from their roster lesson list,
    // else a default
    const lessonFull = student.lessons.length
      ? student.lessons[s % student.lessons.length].name
      : 'Lesson 14 — Entertainment'
    const lessonShort = lessonFull.split(' — ')[0]

    for (let e = 0; e < count && i < total; e++) {
      const tpl = exTemplates[(s + e) % exTemplates.length]
      const review = REVIEW_ITEMS.find(r => r.student === student.name && r.ex === tpl.ex)

      // deterministic outcome distribution: mostly graded, with the
      // occasional skip / flag / error so all detail variants appear.
      let outcome: StatusKind = 'graded'
      const roll = (i * 7) % 17
      if (roll === 3 || roll === 11) outcome = 'skipped'
      else if (roll === 6) outcome = 'flagged'
      else if (roll === 14) outcome = 'error'

      queue.push({
        i,
        studentIdx: s,
        student: student.name,
        lessonShort,
        lesson: lessonFull,
        ex: tpl.ex,
        type: review?.type ?? tpl.type,
        outcome,
        score: review?.score ?? (6 + ((i * 3) % 4)),
        conf: review?.conf ?? (0.7 + ((i * 5) % 25) / 100),
        transcript: review?.transcript ??
          (tpl.type === 'audio'
            ? 'In my free time I enjoy listening to podcasts and watching documentaries about science and the world around us…'
            : 'If I had more time I would practise speaking every day. She has been studying English since last year.'),
        comment: review?.comment ??
          'Solid response overall — clear ideas and good range. Watch a couple of small grammar slips next time.',
      })
      i++
    }
  }
  return queue
}

// ============================================================
// Detail-card action text per status (§3.3 verbatim)
// ============================================================
function actionText(status: StatusKind, mode: RunMode): string {
  switch (status) {
    case 'skipped': return 'Skipped — already auto-checked'
    case 'flagged': return 'Flagged — confidence below threshold'
    case 'error': return 'Error — audio download failed'
    case 'graded':
      return mode === 'dryrun'
        ? 'Graded — NOT submitted (dry-run)'
        : 'Graded & submitted ✓'
    case 'evaluating': return 'Evaluating…'
    default: return ''
  }
}

function actionColor(status: StatusKind): string {
  switch (status) {
    case 'skipped': return 'var(--c-skip)'
    case 'flagged': return 'var(--yellow)'
    case 'error': return 'var(--pink)'
    case 'graded': return 'var(--lime)'
    case 'evaluating': return 'var(--sky)'
    default: return 'var(--ink-soft)'
  }
}

// mode → mode-badge status + label (§3.3, honoring the §10.1 quirk:
// full→flagged(ochre), review→queued(neutral), dryrun→dryrun)
function modeBadge(mode: RunMode): { status: StatusKind; label: string } {
  if (mode === 'full') return { status: 'flagged', label: 'Full-auto' }
  if (mode === 'review') return { status: 'queued', label: 'Review' }
  return { status: 'dryrun', label: 'Dry-run' }
}

// timestamp like 00:01.8 (mono) for log lines
function fmtTs(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  const t = Math.floor((seconds * 10) % 10)
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}.${t}`
}

const TICK_MS = 900

const LOG_COLORS: Record<LogLevel, string> = {
  info: '#8fd0ff',
  ok: '#7bf0a0',
  warn: '#ffd27d',
  err: '#ff8f8f',
}

// ============================================================
// One-off inline SVGs (§6)
// ============================================================

function SleepingRobot() {
  return (
    <svg
      width="140"
      height="140"
      viewBox="0 0 140 140"
      fill="none"
      style={{ animation: 'float 4s ease-in-out infinite' }}
      aria-hidden="true"
    >
      {/* faint sun halo */}
      <circle cx="70" cy="66" r="58" fill="var(--sun)" opacity="0.08" />
      <circle cx="70" cy="66" r="58" fill="none" stroke="var(--sun)" strokeWidth="2" opacity="0.10" />
      {/* antenna */}
      <line x1="70" y1="40" x2="70" y2="26" stroke="var(--ink-soft)" strokeWidth="3" strokeLinecap="round" />
      <circle cx="70" cy="22" r="6" fill="var(--sun)" />
      {/* body / head */}
      <rect x="36" y="40" width="68" height="60" rx="12" fill="var(--indigo)" stroke="var(--line)" strokeWidth="1.5" />
      {/* screen face */}
      <rect x="46" y="52" width="48" height="34" rx="7" fill="var(--panel)" />
      {/* two closed-eye arcs */}
      <path d="M54 70 Q60 76 66 70" fill="none" stroke="var(--ink)" strokeWidth="3" strokeLinecap="round" />
      <path d="M74 70 Q80 76 86 70" fill="none" stroke="var(--ink)" strokeWidth="3" strokeLinecap="round" />
      {/* ears */}
      <rect x="28" y="58" width="9" height="22" rx="3" fill="var(--indigo)" stroke="var(--line)" strokeWidth="1.5" />
      <rect x="103" y="58" width="9" height="22" rx="3" fill="var(--indigo)" stroke="var(--line)" strokeWidth="1.5" />
      {/* feet */}
      <rect x="48" y="100" width="16" height="10" rx="3" fill="var(--indigo)" stroke="var(--line)" strokeWidth="1.5" />
      <rect x="76" y="100" width="16" height="10" rx="3" fill="var(--indigo)" stroke="var(--line)" strokeWidth="1.5" />
      {/* z's */}
      <text x="104" y="44" fontFamily="'Shippori Mincho B1', serif" fontWeight="800" fontSize="16" fill="var(--ink-soft)" style={{ animation: 'blinkz 2.4s ease-in-out infinite' }}>z</text>
      <text x="116" y="32" fontFamily="'Shippori Mincho B1', serif" fontWeight="800" fontSize="12" fill="var(--ink-soft)" style={{ animation: 'blinkz 2.4s ease-in-out 0.4s infinite' }}>z</text>
    </svg>
  )
}

function StopGlyph() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="#fff" aria-hidden="true">
      <rect x="1.5" y="1.5" width="9" height="9" rx="1.5" />
    </svg>
  )
}

// ============================================================
// Component
// ============================================================
export function LiveMonitor(props: ScreenProps) {
  const { run, mascotName, showToast, openDialog, startRun, defaultRunMode } = props
  const { activeRunId, liveEvents, studentRows, reviewItems } = useApp()

  // ---- EMPTY STATE ----
  if (run.total === 0) {
    return (
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          textAlign: 'center',
          padding: '60px 20px',
          gap: '6px',
          minHeight: '420px',
        }}
      >
        <SleepingRobot />
        <h2
          style={{
            margin: '8px 0 0',
            fontFamily: "'Shippori Mincho B1', serif",
            fontWeight: 800,
            fontSize: '22px',
            color: 'var(--ink)',
          }}
        >
          {mascotName} is napping
        </h2>
        <p
          style={{
            margin: 0,
            maxWidth: '420px',
            fontSize: '13.5px',
            lineHeight: 1.5,
            color: 'var(--ink-soft)',
          }}
        >
          No run is in progress. Start one from New Run and the live tree + log will
          light up here.
        </p>
        <button
          className="squish"
          onClick={() => startRun(defaultRunMode)}
          style={{
            marginTop: '14px',
            padding: '11px 20px',
            border: '1.5px solid var(--line)',
            borderRadius: '5px',
            background: 'var(--violet)',
            color: '#fff',
            fontFamily: "'Shippori Mincho B1', serif",
            fontWeight: 800,
            fontSize: '14.5px',
            boxShadow: '4px 4px 13px var(--shadowc)',
          }}
        >
          Start a run →
        </button>
      </div>
    )
  }

  return (
    <ActiveMonitor
      total={run.total}
      students={run.students}
      mode={run.mode}
      active={run.active}
      finished={run.finished}
      showToast={showToast}
      openDialog={openDialog}
      activeRunId={activeRunId}
      liveEvents={liveEvents}
      studentRows={studentRows}
      reviewItems={reviewItems}
    />
  )
}

// ============================================================
// Active / Done view — owns the simulation (fallback) and WS-driven mode
// ============================================================
interface ActiveProps {
  total: number
  students: number
  mode: RunMode
  active: boolean
  finished: boolean
  showToast: ScreenProps['showToast']
  openDialog: ScreenProps['openDialog']
  /** When non-null, a real backend run is in progress */
  activeRunId: string | null
  /** Incoming WS events from the backend */
  liveEvents: RunEvent[]
  studentRows: StudentRow[]
  reviewItems: ReviewItem[]
}

function ActiveMonitor(props: ActiveProps) {
  const { total, students, mode, active, finished, showToast, openDialog,
    activeRunId, liveEvents, studentRows, reviewItems } = props

  // Determine if we're in WS-driven mode (real backend run)
  const wsMode = activeRunId !== null

  // queue is stable for the lifetime of this run config (simulation fallback)
  const queue = useMemo(() => buildQueue(total, students, studentRows, reviewItems), [total, students, studentRows, reviewItems])
  const studentNames = useMemo(() => {
    const seen: string[] = []
    for (const n of queue) if (!seen.includes(n.student)) seen.push(n.student)
    return seen
  }, [queue])

  // ---- simulation state ----
  // cursor = number of nodes fully processed so far; also the index of
  // the node currently being evaluated (queue[cursor]). When
  // cursor === queue.length the run is finished.
  const [cursor, setCursor] = useState(0)
  const [logLines, setLogLines] = useState<LogLine[]>([])
  const [filter, setFilter] = useState<'all' | LogLevel>('all')
  const [done, setDone] = useState(false)

  const logIdRef = useRef(0)
  const elapsedRef = useRef(0)
  const completedToastRef = useRef(false)
  // guards each queue index so a step is only logged once (StrictMode-safe)
  const loggedStepRef = useRef(-1)
  const startLoggedRef = useRef(false)

  // append several lines atomically (one elapsed bump per line)
  const appendLines = (entries: { level: LogLevel; text: string }[]) => {
    setLogLines(prev => {
      const out = [...prev]
      for (const e of entries) {
        elapsedRef.current += 0.9
        out.push({ id: logIdRef.current++, ts: fmtTs(elapsedRef.current), level: e.level, text: e.text })
      }
      return out
    })
  }

  // start-of-run log line (once)
  useEffect(() => {
    if (startLoggedRef.current) return
    startLoggedRef.current = true
    setLogLines([
      {
        id: logIdRef.current++,
        ts: fmtTs(0),
        level: 'info',
        text: `Run started · mode=${mode} · ${students} students queued · headed=no`,
      },
    ])
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // ---- the 900ms tick (simulation fallback — disabled when WS is active) ----
  // Each cursor value drives one timer: after TICK_MS we log the node at
  // `cursor`, then advance the cursor (which re-runs this effect). When
  // we run past the end we emit the completion line and set `done`.
  useEffect(() => {
    if (!active || done) return
    if (wsMode) return  // WS-driven: skip simulation tick
    if (cursor >= queue.length) return

    const id = setTimeout(() => {
      const node = queue[cursor]
      // only build/append log lines the first time we hit this index
      if (loggedStepRef.current < cursor) {
        loggedStepRef.current = cursor
        const exLabel = `${node.student} ${node.ex}`
        const lines: { level: LogLevel; text: string }[] = []

        lines.push({
          level: 'info',
          text:
            node.type === 'audio'
              ? `${node.student} ▸ ${node.lessonShort} ▸ ${node.ex} — transcribing audio…`
              : `${node.student} ▸ ${node.lessonShort} ▸ ${node.ex} — evaluating answer…`,
        })

        if (node.outcome === 'graded') {
          lines.push({
            level: 'ok',
            text:
              mode === 'dryrun'
                ? `  → ${exLabel} scored ${node.score}/10 · NOT submitted (dry-run)`
                : `  → ${exLabel} scored ${node.score}/10 · submitted ✓`,
          })
        } else if (node.outcome === 'skipped') {
          lines.push({ level: 'warn', text: `  → ${exLabel} already auto-checked · skipped` })
        } else if (node.outcome === 'flagged') {
          lines.push({ level: 'warn', text: `  ⚑ ${exLabel} low confidence (0.61) · flagged for review` })
        } else if (node.outcome === 'error') {
          lines.push({ level: 'err', text: `  ✗ ${exLabel} audio download failed · error (screenshot saved)` })
        }

        if (cursor + 1 >= queue.length) {
          lines.push({ level: 'info', text: `Run complete · ${queue.length} processed` })
        }
        appendLines(lines)
      }

      const next = cursor + 1
      setCursor(next)
      if (next >= queue.length) setDone(true)
    }, TICK_MS)

    return () => clearTimeout(id)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [active, done, cursor, queue])

  // fire completion toast once
  useEffect(() => {
    if (!done || completedToastRef.current) return
    completedToastRef.current = true
    if (mode === 'dryrun') {
      showToast('info', 'Dry-run finished — nothing was submitted')
    } else {
      const graded = queue.filter(n => n.outcome === 'graded').length
      showToast('ok', `Run finished — ${graded} grades submitted`)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [done])

  // ============================================================
  // WS-driven state: derived from liveEvents when wsMode is active
  // ============================================================

  // Build log lines from WS events
  const wsLogLines = useMemo((): LogLine[] => {
    if (!wsMode) return []
    let id = 0
    return liveEvents
      .filter(ev => ev.type === 'log' || ev.type === 'run_started' || ev.type === 'run_complete')
      .map(ev => {
        const level: LogLevel = (() => {
          if (ev.type === 'run_started') return 'info'
          if (ev.type === 'run_complete') return 'ok'
          if (ev.data?.level) return ev.data.level as LogLevel
          return 'info'
        })()
        const text = ev.data?.message ?? ev.message ?? ev.type
        return { id: id++, ts: ev.ts ? new Date(ev.ts).toISOString().substr(11, 8) : '00:00:00', level, text }
      })
  }, [wsMode, liveEvents])

  // Extract latest progress from WS events
  const wsProgress = useMemo(() => {
    if (!wsMode) return null
    const prog = [...liveEvents].reverse().find(ev => ev.type === 'progress')
    if (!prog?.data) return null
    return {
      current: typeof prog.data.current === 'number' ? prog.data.current : 0,
      total: typeof prog.data.total === 'number' ? prog.data.total : total,
      studentsDone: typeof prog.data.students_done === 'number' ? prog.data.students_done : 0,
      students: typeof prog.data.students === 'number' ? prog.data.students : students,
      pct: typeof prog.data.pct === 'number' ? prog.data.pct : 0,
    }
  }, [wsMode, liveEvents, total, students])

  // Most recent exercise event for detail card
  const wsCurrentExercise = useMemo(() => {
    if (!wsMode) return null
    const ev = [...liveEvents].reverse().find(e => e.type === 'exercise' || e.type === 'graded' || e.type === 'flagged')
    if (!ev?.data) return null
    return ev
  }, [wsMode, liveEvents])

  // Map WS events to per-node statuses for the tree
  // Each node key = `${student}|${lesson}|${ex}`
  const wsNodeStatusMap = useMemo((): Map<string, StatusKind> => {
    const map = new Map<string, StatusKind>()
    if (!wsMode) return map
    for (const ev of liveEvents) {
      if (!ev.data) continue
      const key = `${ev.data.student ?? ''}|${ev.data.lesson ?? ''}|${ev.data.exercise ?? ''}`
      if (ev.type === 'exercise') map.set(key, 'evaluating')
      else if (ev.type === 'graded') map.set(key, 'graded')
      else if (ev.type === 'skipped') map.set(key, 'skipped')
      else if (ev.type === 'flagged') map.set(key, 'flagged')
      else if (ev.type === 'error') map.set(key, 'error')
    }
    return map
  }, [wsMode, liveEvents])

  // ---- derived progress numbers ----
  // when the global run is finished (stopped/completed), pin progress
  // to its observed processed count.
  const runFinished = finished || done
  const current = wsMode && wsProgress
    ? wsProgress.current
    : Math.min(cursor, total)
  const pct = wsMode && wsProgress
    ? wsProgress.pct
    : (total > 0 ? Math.round((current / total) * 100) : 0)

  // students fully done = students whose every queued node is processed (sim fallback)
  const simStudentsDone = useMemo(() => {
    if (current >= total) return students
    let count = 0
    for (let s = 0; s < studentNames.length; s++) {
      const last = queue.filter(n => n.student === studentNames[s]).reduce((m, n) => Math.max(m, n.i), -1)
      if (last >= 0 && last < current) count++
    }
    return Math.min(count, students)
  }, [current, total, students, studentNames, queue])
  const studentsDone = wsMode && wsProgress ? wsProgress.studentsDone : simStudentsDone

  const eta = runFinished
    ? 'done'
    : active
      ? `${Math.max(1, Math.ceil((total - current) * 0.9))}s`
      : '—'

  // the node to show in the detail card: the one currently evaluating
  // while active, else the last processed node.
  const currentNode: SimNode | undefined = (() => {
    if (active && !done && cursor < queue.length) return queue[cursor]
    if (current > 0) return queue[Math.min(current, queue.length) - 1]
    return queue[0]
  })()

  // status of the detail node: 'evaluating' while it's the live cursor,
  // else its terminal outcome.
  const detailStatus: StatusKind = (() => {
    if (wsMode && wsCurrentExercise) {
      if (wsCurrentExercise.type === 'exercise') return 'evaluating'
      if (wsCurrentExercise.type === 'graded') return 'graded'
      if (wsCurrentExercise.type === 'flagged') return 'flagged'
      if (wsCurrentExercise.type === 'error') return 'error'
    }
    return active && !done && currentNode && currentNode.i === cursor
      ? 'evaluating'
      : currentNode?.outcome ?? 'queued'
  })()

  // ---- per-node live status helper for the tree ----
  const nodeStatus = (n: SimNode): NodeStatus => {
    if (wsMode) {
      const key = `${n.student}|${n.lesson}|${n.ex}`
      return wsNodeStatusMap.get(key) ?? 'queued'
    }
    if (active && !done && n.i === cursor) return 'evaluating'
    if (n.i < current) return n.outcome
    return 'queued'
  }

  const mb = modeBadge(mode)
  const showStop = active && (!done || wsMode)

  // Use WS log lines when in WS mode, else simulation log lines
  const activeLogLines = wsMode ? wsLogLines : logLines
  const filteredLog = filter === 'all' ? activeLogLines : activeLogLines.filter(l => l.level === filter)

  // auto-scroll log to bottom when new lines arrive
  const logBodyRef = useRef<HTMLDivElement>(null)
  useEffect(() => {
    const el = logBodyRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [logLines.length, filter])

  // ============================================================
  // Tree grouping: Student ▸ Lesson ▸ Exercise
  // ============================================================
  interface LessonGroup {
    lesson: string
    lessonShort: string
    nodes: SimNode[]
  }
  interface StudentGroup {
    student: string
    lessons: LessonGroup[]
  }
  const tree: StudentGroup[] = useMemo(() => {
    const out: StudentGroup[] = []
    for (const n of queue) {
      let sg = out.find(s => s.student === n.student)
      if (!sg) { sg = { student: n.student, lessons: [] }; out.push(sg) }
      let lg = sg.lessons.find(l => l.lesson === n.lesson)
      if (!lg) { lg = { lesson: n.lesson, lessonShort: n.lessonShort, nodes: [] }; sg.lessons.push(lg) }
      lg.nodes.push(n)
    }
    return out
  }, [queue])

  // a student's dot: active if any node evaluating, done if all processed
  const studentDotColor = (sg: StudentGroup): string => {
    const idxs = sg.lessons.flatMap(l => l.nodes.map(n => n.i))
    const evaluating = active && !done && idxs.includes(cursor)
    const allDone = idxs.every(i => i < current)
    if (evaluating) return '#3f72b0'
    if (allDone) return '#2f8f6b'
    return 'var(--c-skip)'
  }

  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: '300px 1fr',
        gap: '18px',
        alignItems: 'start',
      }}
    >
      {/* ====================== LEFT — RUN TREE ====================== */}
      <section
        style={{
          background: 'var(--panel)',
          border: '1.5px solid var(--line)',
          borderRadius: '7px',
          boxShadow: '5px 5px 16px var(--shadowc)',
          overflow: 'hidden',
        }}
      >
        <header
          style={{
            background: 'var(--panel2)',
            borderBottom: '1.5px solid var(--line)',
            padding: '12px 16px',
            fontFamily: "'Shippori Mincho B1', serif",
            fontWeight: 800,
            fontSize: '15px',
            color: 'var(--ink)',
          }}
        >
          Run tree
        </header>
        <div style={{ maxHeight: '560px', overflowY: 'auto', padding: '14px 14px 16px' }}>
          {tree.map((sg, si) => (
            <div key={sg.student} style={{ marginBottom: si === tree.length - 1 ? 0 : '14px' }}>
              {/* student row */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '9px' }}>
                <span
                  style={{
                    width: '11px',
                    height: '11px',
                    borderRadius: '50%',
                    background: studentDotColor(sg),
                    border: '1px solid var(--line)',
                    flex: 'none',
                  }}
                />
                <span
                  style={{
                    fontFamily: "'Shippori Mincho B1', serif",
                    fontWeight: 700,
                    fontSize: '14px',
                    color: 'var(--ink)',
                  }}
                >
                  {sg.student}
                </span>
              </div>

              {/* lesson groups */}
              {sg.lessons.map(lg => (
                <div
                  key={lg.lesson}
                  style={{
                    marginLeft: '18px',
                    borderLeft: '1.5px solid var(--chip)',
                    paddingLeft: '10px',
                    marginTop: '6px',
                  }}
                >
                  <div
                    style={{
                      fontSize: '12px',
                      fontWeight: 600,
                      color: 'var(--ink-soft)',
                      margin: '2px 0 4px',
                    }}
                  >
                    {lg.lessonShort}
                  </div>

                  {/* exercise rows */}
                  {lg.nodes.map(n => {
                    const st = nodeStatus(n)
                    const isEval = st === 'evaluating'
                    return (
                      <div
                        key={n.i}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '8px',
                          padding: '4px 7px',
                          borderRadius: '3px',
                          marginBottom: '3px',
                          background: isEval ? 'var(--chip)' : 'transparent',
                          animation: isEval ? 'bob 0.9s ease-in-out infinite' : undefined,
                        }}
                      >
                        <span style={{ fontSize: '12px', lineHeight: 1, flex: 'none' }}>
                          {n.type === 'audio' ? '🔊' : '✎'}
                        </span>
                        <span style={{ fontSize: '12px', flex: 1, minWidth: 0, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                          <span style={{ fontWeight: 700, color: 'var(--ink)' }}>{n.ex}</span>{' '}
                          <span style={{ color: 'var(--ink-soft)' }}>
                            {n.type === 'audio' ? 'Audio' : 'Written'}
                          </span>
                        </span>
                        <StatusBadge status={st} />
                      </div>
                    )
                  })}
                </div>
              ))}
            </div>
          ))}
        </div>
      </section>

      {/* ====================== RIGHT COLUMN ====================== */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {/* ---------------- PROGRESS CARD ---------------- */}
        <section
          style={{
            background: 'var(--panel)',
            border: '1.5px solid var(--line)',
            borderRadius: '7px',
            boxShadow: '5px 5px 16px var(--shadowc)',
            padding: '16px 18px 18px',
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              flexWrap: 'wrap',
              marginBottom: '14px',
            }}
          >
            <h3
              style={{
                margin: 0,
                fontFamily: "'Shippori Mincho B1', serif",
                fontWeight: 800,
                fontSize: '17px',
                color: 'var(--ink)',
              }}
            >
              Progress
            </h3>
            <StatusBadge status={mb.status} label={mb.label} />
            <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--ink-soft)' }}>
              {studentsDone}/{students} students · ETA {eta}
            </span>
            <span style={{ flex: 1 }} />
            {showStop && (
              <button
                className="squish"
                onClick={() => openDialog('stop')}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '7px',
                  padding: '8px 13px',
                  border: '1.5px solid var(--line)',
                  borderRadius: '4px',
                  background: '#c62d1f',
                  color: '#fff',
                  fontFamily: "'Shippori Mincho B1', serif",
                  fontWeight: 800,
                  fontSize: '13px',
                  boxShadow: '3px 3px 13px var(--shadowc)',
                }}
              >
                <StopGlyph />
                Stop
              </button>
            )}
          </div>

          {/* progress tube + pct */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            <div
              style={{
                flex: 1,
                height: '24px',
                border: '1.5px solid var(--line)',
                borderRadius: '99px',
                background: 'var(--panel2)',
                overflow: 'hidden',
              }}
            >
              <div
                style={{
                  height: '100%',
                  width: `${pct}%`,
                  background:
                    'repeating-linear-gradient(45deg,var(--violet),var(--violet) 11px,#4a5d8f 11px,#4a5d8f 22px)',
                  borderRight: pct > 0 && pct < 100 ? '1.5px solid var(--line)' : undefined,
                  borderRadius: '99px',
                  transition: 'width .5s ease',
                }}
              />
            </div>
            <span
              style={{
                minWidth: '54px',
                textAlign: 'right',
                fontFamily: "'Shippori Mincho B1', serif",
                fontWeight: 800,
                fontSize: '22px',
                fontVariantNumeric: 'tabular-nums',
                color: 'var(--violet)',
              }}
            >
              {pct}%
            </span>
          </div>

          <div style={{ marginTop: '9px', fontSize: '12.5px', color: 'var(--ink-soft)' }}>
            {current} of {total} exercises processed
          </div>
        </section>

        {/* ---------------- DETAIL CARD ---------------- */}
        {currentNode && (
          <section
            style={{
              background: 'var(--panel)',
              border: '1.5px solid var(--line)',
              borderRadius: '7px',
              boxShadow: '5px 5px 16px var(--shadowc)',
              overflow: 'hidden',
            }}
          >
            <header
              style={{
                background: 'var(--panel2)',
                borderBottom: '1.5px solid var(--line)',
                padding: '11px 16px',
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                flexWrap: 'wrap',
              }}
            >
              <span
                style={{
                  fontFamily: "'Shippori Mincho B1', serif",
                  fontWeight: 800,
                  fontSize: '14.5px',
                  color: 'var(--ink)',
                }}
              >
                {currentNode.student} · {currentNode.lessonShort} · {currentNode.ex}
              </span>
              <span
                style={{
                  padding: '2px 9px',
                  borderRadius: '99px',
                  border: '1px solid var(--line)',
                  background: 'var(--chip)',
                  color: 'var(--ink-soft)',
                  fontSize: '11px',
                  fontWeight: 600,
                }}
              >
                {currentNode.type === 'audio' ? 'Audio answer' : 'Written answer'}
              </span>
              <span style={{ flex: 1 }} />
              <StatusBadge status={detailStatus} />
            </header>

            <div
              style={{
                display: 'grid',
                gridTemplateColumns: '1fr 130px',
                gap: '16px',
                padding: '16px 18px 18px',
              }}
            >
              {/* left: transcript + comment + action */}
              <div style={{ minWidth: 0 }}>
                <div
                  style={{
                    fontSize: '11px',
                    fontWeight: 700,
                    letterSpacing: '.4px',
                    textTransform: 'uppercase',
                    color: 'var(--ink-soft)',
                    marginBottom: '5px',
                  }}
                >
                  {currentNode.type === 'audio' ? 'Transcript' : 'Answer'}
                </div>
                <p
                  style={{
                    margin: '0 0 14px',
                    fontStyle: 'italic',
                    fontSize: '13px',
                    lineHeight: 1.55,
                    color: 'var(--ink)',
                  }}
                >
                  {detailStatus === 'evaluating'
                    ? (currentNode.type === 'audio'
                        ? 'Transcribing audio answer…'
                        : 'Reading written answer…')
                    : currentNode.transcript}
                </p>

                <div
                  style={{
                    fontSize: '11px',
                    fontWeight: 700,
                    letterSpacing: '.4px',
                    textTransform: 'uppercase',
                    color: 'var(--ink-soft)',
                    marginBottom: '5px',
                  }}
                >
                  AI comment
                </div>
                <p
                  style={{
                    margin: '0 0 14px',
                    fontSize: '13px',
                    lineHeight: 1.55,
                    color: 'var(--ink)',
                  }}
                >
                  {detailStatus === 'evaluating' ? 'Awaiting model output…' : currentNode.comment}
                </p>

                <span
                  style={{
                    display: 'inline-block',
                    padding: '4px 11px',
                    borderRadius: '4px',
                    border: '1.5px solid var(--line)',
                    background: 'var(--panel2)',
                    fontFamily: "'Shippori Mincho B1', serif",
                    fontWeight: 700,
                    fontSize: '12px',
                    color: actionColor(detailStatus),
                  }}
                >
                  {actionText(detailStatus, mode)}
                </span>
              </div>

              {/* right: score column */}
              <div
                style={{
                  background: 'var(--panel3)',
                  border: '1.5px solid var(--line)',
                  borderRadius: '6px',
                  padding: '13px 12px',
                  textAlign: 'center',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <div
                  style={{
                    fontSize: '11px',
                    fontWeight: 700,
                    letterSpacing: '.6px',
                    color: 'var(--ink-soft)',
                  }}
                >
                  SCORE
                </div>
                <div
                  style={{
                    fontFamily: "'Shippori Mincho B1', serif",
                    fontWeight: 800,
                    fontSize: '46px',
                    lineHeight: 1.05,
                    fontVariantNumeric: 'tabular-nums',
                    color: 'var(--ink)',
                  }}
                >
                  {detailStatus === 'graded' || detailStatus === 'flagged'
                    ? currentNode.score
                    : '—'}
                  <span style={{ fontSize: '20px', color: 'var(--ink-soft)' }}>/10</span>
                </div>
                <div
                  style={{
                    marginTop: '6px',
                    fontFamily: "'JetBrains Mono', monospace",
                    fontSize: '11px',
                    color: 'var(--ink-soft)',
                  }}
                >
                  CONF {currentNode.conf.toFixed(2)}
                </div>
              </div>
            </div>
          </section>
        )}

        {/* ---------------- LOG CONSOLE ---------------- */}
        <section
          style={{
            background: 'var(--logbg)',
            border: '1.5px solid var(--line)',
            borderRadius: '7px',
            boxShadow: '5px 5px 16px var(--shadowc)',
            overflow: 'hidden',
          }}
        >
          <header
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              flexWrap: 'wrap',
              padding: '10px 14px',
              borderBottom: '2px solid rgba(255,255,255,.12)',
            }}
          >
            <span
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontWeight: 600,
                fontSize: '12.5px',
                color: '#7bf0a0',
              }}
            >
              ● live log
            </span>
            <span style={{ flex: 1 }} />
            {(['all', 'info', 'ok', 'warn', 'err'] as const).map(lv => {
              const label =
                lv === 'all' ? 'All' : lv === 'info' ? 'Info' : lv === 'ok' ? 'OK' : lv === 'warn' ? 'Warn' : 'Error'
              const activeF = filter === lv
              return (
                <button
                  key={lv}
                  className="squish"
                  onClick={() => setFilter(lv)}
                  style={{
                    padding: '3px 10px',
                    borderRadius: '4px',
                    border: 'none',
                    background: activeF ? 'var(--violet)' : 'rgba(255,255,255,.08)',
                    color: activeF ? '#fff' : 'var(--logink)',
                    fontFamily: "'Shippori Mincho B1', serif",
                    fontWeight: 700,
                    fontSize: '11.5px',
                  }}
                >
                  {label}
                </button>
              )
            })}
          </header>

          <div
            ref={logBodyRef}
            style={{
              maxHeight: '220px',
              overflowY: 'auto',
              padding: '12px 14px',
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: '12px',
              lineHeight: 1.65,
            }}
          >
            {filteredLog.length === 0 ? (
              <div style={{ color: '#6a6090' }}>— no {filter === 'all' ? '' : filter + ' '}lines yet —</div>
            ) : (
              filteredLog.map(l => (
                <div key={l.id} style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                  <span style={{ color: '#6a6090' }}>{l.ts}</span>{' '}
                  <span style={{ color: LOG_COLORS[l.level] }}>{l.text}</span>
                </div>
              ))
            )}
          </div>
        </section>
      </div>
    </div>
  )
}

export default LiveMonitor
