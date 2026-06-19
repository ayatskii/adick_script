// ============================================================
// api.ts — REST + WebSocket client
// Base URL: VITE_API_BASE env var or http://localhost:8010
// (8010 default avoids the common :8000 clash; matches backend/run.sh.)
// ============================================================

import type {
  RunRow,
  ReviewItem,
  StudentRow,
  TimelineEntry,
  ReconcileRow,
  FlaggedItem,
} from './types'

const BASE = (import.meta.env.VITE_API_BASE as string | undefined) ?? 'http://localhost:8010'

// ---- REST helpers ----

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`)
  if (!res.ok) throw new Error(`GET ${path} → ${res.status}`)
  return res.json() as Promise<T>
}

async function post<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: body !== undefined ? { 'Content-Type': 'application/json' } : {},
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })
  if (!res.ok) throw new Error(`POST ${path} → ${res.status}`)
  return res.json() as Promise<T>
}

async function put<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`PUT ${path} → ${res.status}`)
  return res.json() as Promise<T>
}

// ---- API response shapes (matching backend contract) ----

export interface HealthResponse {
  ok: boolean
  phase0_done: boolean
  openai_key_set: boolean
}

export interface RunApiRecord {
  id: string
  mode: string
  started_at: string
  finished_at: string | null
  status: string
  duration?: string
  counts: {
    graded: number
    skipped: number
    flagged: number
    errors: number
    completed_lessons: number
  }
}

export interface StartRunBody {
  mode: string
  scope: { all: boolean; students: string[] | null }
  max_students?: number | null
  max_lessons?: number | null
  headed: boolean
  confidence_threshold: number
}

export interface StartRunResponse {
  run_id: string
  status: string
}

export interface DecisionBody {
  decision: 'approved' | 'rejected' | 'edited'
  score?: number
  comment?: string
}

export interface Settings {
  [key: string]: unknown
}

// ---- RunEvent (WebSocket) ----

export interface RunEvent {
  type: string
  ts: string
  message?: string
  data?: {
    level?: 'info' | 'ok' | 'warn' | 'err'
    message?: string
    current?: number
    total?: number
    students_done?: number
    students?: number
    pct?: number
    counts?: Record<string, number>
    student?: string
    lesson?: string
    exercise?: string
    score?: number
    conf?: number
    transcript?: string
    comment?: string
    reason?: string
    [key: string]: unknown
  }
}

// ---- Exported API functions ----

export const getHealth = (): Promise<HealthResponse> => get('/api/health')

export const listRuns = (): Promise<RunApiRecord[]> => get('/api/runs')

export const getRun = (runId: string): Promise<{ run: RunApiRecord; timeline: TimelineEntry[]; audit: AuditRow[] }> =>
  get(`/api/runs/${runId}`)

export const startRun = (body: StartRunBody): Promise<StartRunResponse> => post('/api/runs', body)

export const stopRun = (runId: string): Promise<{ ok: boolean; note: string }> =>
  post(`/api/runs/${runId}/stop`)

export const listStudents = (): Promise<StudentRow[]> => get('/api/students')

export const listQueue = (): Promise<ReviewItem[]> => get('/api/queue')

export const decideQueue = (itemId: string, body: DecisionBody): Promise<{ ok: boolean }> =>
  post(`/api/queue/${itemId}/decision`, body)

export const submitQueue = (): Promise<{ submitted: number }> => post('/api/queue/submit')

export const listFlagged = (): Promise<FlaggedItem[]> => get('/api/flagged')

export const listReconcile = (): Promise<ReconcileRow[]> => get('/api/reconcile')

export const listAudit = (): Promise<AuditRow[]> => get('/api/audit')

export const getSettings = (): Promise<Settings> => get('/api/settings')

export const putSettings = (body: Partial<Settings>): Promise<Settings> => put('/api/settings', body)

// ---- Audit row type ----
export interface AuditRow {
  [key: string]: unknown
}

// ---- Run rows adapter ----
// Convert backend RunApiRecord to the frontend RunRow shape for display.
export function toRunRow(r: RunApiRecord): RunRow {
  const { graded = 0, skipped = 0, flagged = 0, errors = 0 } = r.counts ?? {}

  // mode → badge
  const modeMap: Record<string, { status: RunRow['modeBadgeStatus']; label: string }> = {
    dryrun: { status: 'dryrun', label: 'Dry-run' },
    dry_run: { status: 'dryrun', label: 'Dry-run' },
    full: { status: 'flagged', label: 'Full-auto' },
    full_auto: { status: 'flagged', label: 'Full-auto' },
    review: { status: 'queued', label: 'Review' },
    demo: { status: 'dryrun', label: 'Demo' },
  }
  const modeBadge = modeMap[r.mode] ?? { status: 'idle' as const, label: r.mode }

  // status → badge
  const statusMap: Record<string, { status: RunRow['statusBadgeStatus']; label: string }> = {
    success: { status: 'graded', label: 'Success' },
    completed: { status: 'graded', label: 'Success' },
    running: { status: 'running', label: 'Running' },
    stopped: { status: 'skipped', label: 'Stopped' },
    error: { status: 'error', label: `${errors} error${errors !== 1 ? 's' : ''}` },
    flagged: { status: 'flagged', label: `${flagged} flagged` },
  }
  const statusBadge = statusMap[r.status] ?? { status: 'idle' as const, label: r.status }

  // format started_at
  const started = r.started_at
    ? new Date(r.started_at).toLocaleString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false })
    : '—'

  const counts = [
    graded ? `${graded} ✓` : null,
    skipped ? `${skipped} skip` : null,
    flagged ? `${flagged} ⚑` : null,
    errors ? `${errors} ✗` : null,
  ]
    .filter(Boolean)
    .join(' · ') || '—'

  return {
    id: r.id,
    modeBadgeStatus: modeBadge.status,
    modeBadgeLabel: modeBadge.label,
    started,
    duration: r.duration ?? '—',
    counts,
    statusBadgeStatus: statusBadge.status,
    statusBadgeLabel: statusBadge.label,
  }
}

// ---- WebSocket stream ----

export function openRunStream(runId: string, onEvent: (e: RunEvent) => void): WebSocket {
  const wsBase = BASE.replace(/^http/, 'ws')
  const ws = new WebSocket(`${wsBase}/api/runs/${runId}/stream`)
  ws.onmessage = (ev) => {
    try {
      const parsed = JSON.parse(ev.data as string) as RunEvent
      onEvent(parsed)
    } catch {
      // ignore malformed frames
    }
  }
  return ws
}
