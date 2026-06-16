import { useState, useCallback } from 'react'
import type {
  ScreenId, RunState, RunMode, ToastState, ToastKind, DialogKind,
  AppHandlers, AppSharedState,
} from './types'
import { AppContext } from './AppContext'
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
import { REVIEW_ITEMS, FLAGGED_ITEMS } from './data'

// Count of pending review items for nav badge (seed = 6)
const INITIAL_REVIEW_COUNT = REVIEW_ITEMS.filter(r => r.status === 'pending').length
const INITIAL_FLAGGED_COUNT = FLAGGED_ITEMS.length

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
  const [reviewCount] = useState(INITIAL_REVIEW_COUNT)
  const [flaggedCount] = useState(INITIAL_FLAGGED_COUNT)

  // editor-tweakable props (can be overridden via Settings in future)
  const mascotName = 'Vibe-Bot'
  const defaultRunMode: RunMode = 'dryrun'

  // ============================================================
  // Handlers
  // ============================================================

  const showToast = useCallback((kind: ToastKind, message: string) => {
    setToast({ kind, message })
  }, [])

  const dismissToast = useCallback(() => setToast(null), [])

  const startRun = useCallback((mode: RunMode) => {
    setRun({
      active: true,
      mode,
      total: 41, // spec: 41 lessons awaiting
      current: 0,
      studentsDone: 0,
      students: 17, // spec: 17 pending students
      finished: false,
    })
    setDialog(null)
    setScreen('live')
  }, [])

  const stopRun = useCallback(() => {
    setRun(prev => ({ ...prev, active: false, finished: true }))
    setDialog(null)
    showToast('warn', 'Run stopped — in-progress exercise will finish, then halt.')
  }, [showToast])

  const openDialog = useCallback((kind: DialogKind) => {
    setDialog(kind)
  }, [])

  const handleDialogConfirm = useCallback((mode?: RunMode) => {
    if (dialog === 'full') {
      startRun(mode ?? 'full')
    } else if (dialog === 'stop') {
      stopRun()
    }
  }, [dialog, startRun, stopRun])

  const handleRunPillClick = useCallback(() => {
    if (run.active) {
      openDialog('stop')
    } else {
      setScreen('live')
    }
  }, [run.active, openDialog])

  // ============================================================
  // Shared state + handlers (passed to screens)
  // ============================================================

  const sharedState: AppSharedState = {
    screen,
    theme,
    run,
    mascotName,
    defaultRunMode,
  }

  const handlers: AppHandlers = {
    showToast,
    startRun,
    stopRun,
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
