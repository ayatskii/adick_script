import { useState, useCallback, useEffect, useRef } from 'react'
import type {
  ScreenId, RunState, RunMode, ToastState, ToastKind, DialogKind,
  AppHandlers, AppSharedState, RunStartOpts,
  RunRow, ReviewItem, StudentRow, TimelineEntry, ReconcileRow, FlaggedItem,
} from './types'
import type { RunEvent } from './api'
import { AppContext } from './AppContext'
import {
  getHealth, listRuns, listStudents, listQueue, listFlagged,
  listReconcile, startRun as apiStartRun, stopRun as apiStopRun,
  openRunStream, toRunRow,
} from './api'
import { Backdrop } from './components/Backdrop'
import { Sidebar } from './components/Sidebar'
import { TopBar } from './components/TopBar'
import { ModeBanner } from './components/ModeBanner'
import { Toast } from './components/Toast'
import { Dialog } from './components/Dialog'
import { Dashboard } from './screens/Dashboard'
import { NewRun } from './screens/NewRun'
import { LiveMonitor } from './screens/LiveMonitor'
import { ReviewQueue } from './screens/ReviewQueue'
import { Students } from './screens/Students'
import { History } from './screens/History'
import { Flagged } from './screens/Flagged'
import { Settings } from './screens/Settings'
import {
  RUN_ROWS, REVIEW_ITEMS, STUDENT_ROWS, TIMELINE_ENTRIES,
  RECONCILE_ROWS, FLAGGED_ITEMS,
} from './data'

const INITIAL_RUN: RunState = {
  active: false,
  mode: 'dryrun',
  total: 0,
  current: 0,
  studentsDone: 0,
  students: 0,
  finished: false,
}

function ScreenRenderer(props: AppSharedState & AppHandlers) {
  switch (props.screen) {
    case 'dashboard': return <Dashboard {...props} />
    case 'new': return <NewRun {...props} />
    case 'live': return <LiveMonitor {...props} />
    case 'review': return <ReviewQueue {...props} />
    case 'students': return <Students {...props} />
    case 'history': return <History {...props} />
    case 'flagged': return <Flagged {...props} />
    case 'settings': return <Settings {...props} />
  }
}

export function App() {
  const [screen, setScreen] = useState<ScreenId>('dashboard')
  const [theme, setTheme] = useState<'light' | 'dark'>('light')
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [run, setRun] = useState<RunState>(INITIAL_RUN)
  const [toast, setToast] = useState<ToastState | null>(null)
  const [dialog, setDialog] = useState<DialogKind>(null)

  // editor-tweakable props
  const mascotName = 'Vibe-Bot'
  const defaultRunMode: RunMode = 'dryrun'

  // ---- API data state ----
  const [online, setOnline] = useState(false)
  const [phase0Done, setPhase0Done] = useState(false)
  const [runRows, setRunRows] = useState<RunRow[]>(RUN_ROWS)
  const [reviewItems, setReviewItems] = useState<ReviewItem[]>(REVIEW_ITEMS)
  const [studentRows, setStudentRows] = useState<StudentRow[]>(STUDENT_ROWS)
  const [timelineEntries] = useState<TimelineEntry[]>(TIMELINE_ENTRIES)
  const [reconcileRows, setReconcileRows] = useState<ReconcileRow[]>(RECONCILE_ROWS)
  const [flaggedItems, setFlaggedItems] = useState<FlaggedItem[]>(FLAGGED_ITEMS)

  // ---- Live run state ----
  const [activeRunId, setActiveRunId] = useState<string | null>(null)
  const [liveEvents, setLiveEvents] = useState<RunEvent[]>([])
  const wsRef = useRef<WebSocket | null>(null)

  // ---- Fetch on mount ----
  useEffect(() => {
    let cancelled = false

    async function fetchAll() {
      try {
        // health check first — if it throws, we're offline
        const health = await getHealth()
        if (!cancelled) setPhase0Done(health.phase0_done)

        const [runs, students, queue, flagged, reconcile] = await Promise.all([
          listRuns(),
          listStudents(),
          listQueue(),
          listFlagged(),
          listReconcile(),
        ])

        if (cancelled) return

        setOnline(true)
        if (runs.length > 0) setRunRows(runs.map(toRunRow))
        if (students.length > 0) setStudentRows(students)
        if (queue.length > 0) setReviewItems(queue)
        if (flagged.length > 0) setFlaggedItems(flagged)
        if (reconcile.length > 0) setReconcileRows(reconcile)
      } catch {
        // Backend offline — keep seed data, stay offline
        if (!cancelled) setOnline(false)
      }
    }

    void fetchAll()
    return () => { cancelled = true }
  }, [])

  // ---- Handlers ----

  const showToast = useCallback((kind: ToastKind, message: string) => {
    setToast({ kind, message })
  }, [])

  const dismissToast = useCallback(() => setToast(null), [])

  const startRun = useCallback(async (mode: RunMode, opts?: RunStartOpts) => {
    // Transition to the live screen. Totals start at 0 and fill in from the
    // backend's real `progress` events — no hardcoded counts.
    setRun({
      active: true,
      mode,
      total: 0,
      current: 0,
      studentsDone: 0,
      students: 0,
      finished: false,
    })
    setDialog(null)
    setScreen('live')
    setLiveEvents([])

    if (!online) return  // offline — use local simulation only

    try {
      // Before Phase 0 the real runner can't drive a browser, so run the
      // backend's no-op demo simulator instead of a real (failing) run.
      const apiMode = phase0Done ? mode : 'demo'
      if (!phase0Done) {
        showToast('info', 'Phase 0 not done — running a simulated demo (nothing is submitted).')
      }
      const scopeAll = opts?.scopeAll ?? true
      const resp = await apiStartRun({
        mode: apiMode,
        scope: { all: scopeAll, students: scopeAll ? null : (opts?.students ?? []) },
        max_students: opts?.maxStudents ?? null,
        max_lessons: opts?.maxLessons ?? null,
        headed: opts?.headed ?? false,
        confidence_threshold: opts?.conf ?? 0.70,
      })

      setActiveRunId(resp.run_id)

      // Open WebSocket stream
      if (wsRef.current) {
        wsRef.current.close()
        wsRef.current = null
      }

      const ws = openRunStream(resp.run_id, (ev) => {
        setLiveEvents(prev => [...prev, ev])

        // Mirror progress events into the shared RunState
        if (ev.type === 'progress' && ev.data) {
          const { current, total, students_done, students } = ev.data
          setRun(prev => ({
            ...prev,
            current: typeof current === 'number' ? current : prev.current,
            total: typeof total === 'number' ? total : prev.total,
            studentsDone: typeof students_done === 'number' ? students_done : prev.studentsDone,
            students: typeof students === 'number' ? students : prev.students,
          }))
        }

        if (ev.type === 'run_complete') {
          setRun(prev => ({ ...prev, active: false, finished: true }))
          // Refresh run list after completion
          listRuns().then(runs => {
            if (runs.length > 0) setRunRows(runs.map(toRunRow))
          }).catch(() => undefined)
        }
      })

      wsRef.current = ws
    } catch (err) {
      showToast('warn', 'Could not reach backend — using offline simulation')
    }
  }, [online, phase0Done, showToast])

  const stopRun = useCallback(async () => {
    setRun(prev => ({ ...prev, active: false, finished: true }))
    setDialog(null)
    showToast('warn', 'Run stopped — in-progress exercise will finish, then halt.')

    if (activeRunId && online) {
      try {
        await apiStopRun(activeRunId)
      } catch {
        // best-effort
      }
    }

    // Close WS
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    setActiveRunId(null)
  }, [activeRunId, online, showToast])

  // Clean up WS on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [])

  const openDialog = useCallback((kind: DialogKind) => {
    setDialog(kind)
  }, [])

  const handleDialogConfirm = useCallback((mode?: RunMode) => {
    if (dialog === 'full') {
      void startRun(mode ?? 'full')
    } else if (dialog === 'stop') {
      void stopRun()
    }
  }, [dialog, startRun, stopRun])

  const handleRunPillClick = useCallback(() => {
    if (run.active) {
      openDialog('stop')
    } else {
      setScreen('live')
    }
  }, [run.active, openDialog])

  // ---- Derived counts for nav badges ----
  const reviewCount = reviewItems.filter(r => r.status === 'pending').length
  const flaggedCount = flaggedItems.length

  // ---- Shared state + handlers ----

  const sharedState: AppSharedState = {
    screen,
    theme,
    run,
    mascotName,
    defaultRunMode,
    online,
    runRows,
    reviewItems,
    studentRows,
    timelineEntries,
    reconcileRows,
    flaggedItems,
    activeRunId,
    liveEvents,
  }

  const handlers: AppHandlers = {
    showToast,
    startRun: (mode: RunMode, opts?: RunStartOpts) => { void startRun(mode, opts) },
    stopRun: () => { void stopRun() },
    openDialog,
    setScreen,
  }

  const screenProps = { ...sharedState, ...handlers }

  return (
    <AppContext.Provider value={screenProps}>
      {/* Root flex container — data-theme drives CSS variable switching */}
      <div
        data-theme={theme}
        style={{
          display: 'flex',
          height: '100vh',
          width: '100%',
          overflow: 'hidden',
          background: 'var(--bg)',
          color: 'var(--ink)',
          position: 'relative',
        }}
      >
        {/* Atmospheric backdrop (fixed, z-0) */}
        <Backdrop />

        {/* Sidebar (z-20) */}
        <Sidebar
          screen={screen}
          open={sidebarOpen}
          onNavigate={setScreen}
          onToggle={() => setSidebarOpen(o => !o)}
          reviewCount={reviewCount}
          flaggedCount={flaggedCount}
        />

        {/* Main column */}
        <div
          style={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            position: 'relative',
            zIndex: 1,
          }}
        >
          {/* Top bar */}
          <TopBar
            screen={screen}
            theme={theme}
            run={run}
            onThemeToggle={() => setTheme(t => t === 'light' ? 'dark' : 'light')}
            onRunPillClick={handleRunPillClick}
          />

          {/* Mode banner (only when run is active) */}
          {run.active && (
            <ModeBanner mode={run.mode} />
          )}

          {/* Main content area with halftone dot pattern */}
          <main
            style={{
              flex: 1,
              overflowY: 'auto',
              backgroundImage: 'radial-gradient(var(--dot) 1.6px, transparent 1.7px)',
              backgroundSize: '20px 20px',
            }}
          >
            {/* Inner wrapper */}
            <div
              style={{
                maxWidth: '1240px',
                margin: '0 auto',
                padding: '26px 28px 60px',
              }}
            >
              <ScreenRenderer {...screenProps} />
            </div>
          </main>
        </div>

        {/* Overlays */}
        {toast && (
          <Toast kind={toast.kind} message={toast.message} onDismiss={dismissToast} />
        )}

        <Dialog
          kind={dialog}
          onCancel={() => setDialog(null)}
          onConfirm={handleDialogConfirm}
        />
      </div>
    </AppContext.Provider>
  )
}

export default App
