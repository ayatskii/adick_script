// ============================================================
// Screen routing
// ============================================================
export type ScreenId =
  | 'dashboard'
  | 'new'
  | 'live'
  | 'review'
  | 'students'
  | 'history'
  | 'flagged'
  | 'settings'

// ============================================================
// Status kinds (spec §4 + §2.3)
// ============================================================
export type StatusKind =
  | 'evaluating'
  | 'graded'
  | 'skipped'
  | 'flagged'
  | 'error'
  | 'dryrun'
  | 'idle'
  | 'queued'
  | 'running'

// ============================================================
// Run modes
// ============================================================
export type RunMode = 'dryrun' | 'full' | 'review'

// ============================================================
// Run state (lives in App.tsx)
// ============================================================
export interface RunState {
  /** Whether a run is currently active */
  active: boolean
  mode: RunMode
  /** Total exercises in this run */
  total: number
  /** Exercises processed so far */
  current: number
  /** Students finished */
  studentsDone: number
  /** Total students in this run */
  students: number
  /** Whether the run has completed */
  finished: boolean
}

// ============================================================
// Toast
// ============================================================
export type ToastKind = 'ok' | 'err' | 'warn' | 'info'

export interface ToastState {
  kind: ToastKind
  message: string
}

// ============================================================
// Dialog
// ============================================================
export type DialogKind = 'full' | 'stop' | null

// ============================================================
// Dashboard: run rows (spec §3.1 recent runs + §3.6 history)
// ============================================================
export interface RunRow {
  id: string
  /** RunMode for the MODE badge (with the non-literal quirk: full→'flagged', review→'queued') */
  modeBadgeStatus: StatusKind
  modeBadgeLabel: string
  started: string
  duration: string
  counts: string
  /** Status for the STATUS badge */
  statusBadgeStatus: StatusKind
  statusBadgeLabel: string
}

// ============================================================
// Review Queue items (spec §3.4)
// ============================================================
export type ReviewItemType = 'audio' | 'text'
export type ReviewItemStatus = 'pending' | 'approved' | 'rejected' | 'submitted'

export interface ReviewItem {
  id: string
  student: string
  lesson: string
  section: string
  ex: string
  type: ReviewItemType
  duration?: string  // for audio items e.g. "02:04"
  score: number
  conf: number
  transcript: string
  comment: string
  status: ReviewItemStatus
  edited: boolean
}

// ============================================================
// Students (spec §3.5)
// ============================================================
export interface LessonEntry {
  name: string
  status: StatusKind
}

export interface StudentRow {
  id: string
  name: string
  awaiting: number
  lastActivity: string
  lessons: LessonEntry[]
}

// ============================================================
// History (spec §3.6)
// ============================================================
export interface TimelineEntry {
  student: string
  ex: string
  proposedScore: number | null
  submittedScore: number | null
  status: StatusKind
  humanEdited: boolean
  /** Relative timestamp offset in seconds from run start (for display) */
  tsOffset: number
}

export interface ReconcileRow {
  student: string
  lesson: string
  completedBy: string
  flagStatus: StatusKind | null
  flagLabel: string | null
}

// ============================================================
// Flagged cards (spec §3.7)
// ============================================================
export interface FlaggedItem {
  id: string
  student: string
  lesson: string
  ex: string
  reason: string
  severity: string
  detail: string
}

// ============================================================
// App-level props interface (passed to all screens)
// ============================================================
export interface AppHandlers {
  showToast: (kind: ToastKind, message: string) => void
  startRun: (mode: RunMode) => void
  stopRun: () => void
  openDialog: (kind: DialogKind) => void
  setScreen: (screen: ScreenId) => void
}

export interface AppSharedState {
  screen: ScreenId
  theme: 'light' | 'dark'
  run: RunState
  /** mascot name, editor-tweakable */
  mascotName: string
  /** default run mode, editor-tweakable */
  defaultRunMode: RunMode
}

/** Props all screen components receive */
export interface ScreenProps extends AppHandlers, AppSharedState {}
