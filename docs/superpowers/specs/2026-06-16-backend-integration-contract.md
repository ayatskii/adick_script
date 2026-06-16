# Edvibe Grader — Backend Integration Contract

Shared contract for wiring the React frontend (`web/`) ↔ a FastAPI backend (`backend/`) ↔ the bot core (`edvibe_bot/`). Both the backend build and the frontend wiring conform to THIS document.

## Architecture
```
web (React/Vite, :5173) ──REST+WS──▶ backend (FastAPI, :8000) ──calls──▶ edvibe_bot.runner.run()
                                          │                                      │ on_event(dict)
                                          └── reads SQLite store (edvibe.sqlite) ─┘ → WS broadcast
```
- The bot's `runner.run()` is **sync** (drives Playwright). The backend runs it in a worker thread (`asyncio.to_thread`) — that thread has NO event loop, so the Playwright sync API is valid there.
- `on_event(payload: dict)` is called from the worker thread. The backend bridges it to async WS subscribers via `loop.call_soon_threadsafe(queue.put_nowait, payload)` (capture the loop with `asyncio.get_running_loop()` before spawning the thread). Never call async code directly from the worker thread.
- Run modes: `dry_run | full_auto | review` call the REAL runner (these need Phase 0 selectors + `.env` creds + OpenAI key; before Phase 0 they will fail at the browser step — that's expected). **`demo`** runs a SIMULATED run (no browser, no OpenAI) that streams realistic events so the whole stack is demoable NOW.

## REST API (prefix `/api`, JSON, CORS allow `http://localhost:5173`)
| Method | Path | Body → Response |
|---|---|---|
| GET | `/api/health` | → `{ ok: true, phase0_done: bool (no "# CONFIRM" left in selectors.py), openai_key_set: bool }` |
| POST | `/api/runs` | `{ mode, scope: {all: bool, students: string[]|null}, max_students: int|null, max_lessons: int|null, headed: bool, confidence_threshold: float }` → `{ run_id, status }` |
| GET | `/api/runs` | → `Run[]` |
| GET | `/api/runs/{run_id}` | → `{ run: Run, timeline: TimelineEntry[], audit: AuditRow[] }` |
| POST | `/api/runs/{run_id}/stop` | → `{ ok: true, note: string }` (best-effort: sets a stop flag; true mid-Playwright cancellation is a documented v1 limitation) |
| GET | `/api/students` | → `Student[]` |
| GET | `/api/queue` | → `ReviewItem[]` |
| POST | `/api/queue/{item_id}/decision` | `{ decision: "approved"|"rejected"|"edited", score?: int, comment?: string }` → `{ ok: true }` |
| POST | `/api/queue/submit` | → `{ submitted: int }` (records submissions in store; real platform submit needs browser → v1 records intent) |
| GET | `/api/flagged` | → `FlaggedItem[]` |
| GET | `/api/reconcile` | → `ReconcileRow[]` |
| GET | `/api/audit` | → `AuditRow[]` |
| GET | `/api/settings` | → `Settings` (NON-secret subset: models, grading, behavior, marathon/curator; credentials masked) |
| PUT | `/api/settings` | partial `Settings` → updated `Settings` |

## WebSocket
- `WS /api/runs/{run_id}/stream` — server emits one JSON `RunEvent` per message until the run ends, then a final `{ type: "run_complete", ... }` and closes.
- `RunEvent` shape (normalized): `{ type: string, ts: string (ISO), message?: string, data?: object }`. Types: `run_started`, `student`, `lesson`, `exercise`, `graded`, `skipped`, `flagged`, `error`, `lesson_complete`, `log` (with `{level: "info"|"ok"|"warn"|"err", message}`), `progress` (with `{current, total, students_done, students, pct}`), `run_complete` (with `{counts}`). The backend MAPS the runner's raw `on_event` dicts into these.

## Data shapes (TypeScript-ish; match the frontend's existing `web/src/types.ts` where possible)
- `Run`: `{ id, mode: "dryrun"|"full"|"review"|"dry_run"|"full_auto", started_at, finished_at|null, status: StatusKind, duration?, counts: { graded, skipped, flagged, errors, completed_lessons } }`
- `ReviewItem`, `Student`, `FlaggedItem`, `ReconcileRow`, `TimelineEntry`, `AuditRow` — mirror `web/src/types.ts` + `web/src/data.ts`.
- **Seed fallback:** when the SQLite store has no rows for an endpoint (true before any real run), the backend returns the SAME verbatim sample data the frontend currently hardcodes (port `web/src/data.ts` values into `backend/seed_data.py`) so the UI is populated immediately. Once real runs exist, real store data is returned.

## Store reads
The bot-core `Store` has only write methods; do NOT modify it. Add a read-only adapter `backend/store_read.py` that opens the same SQLite file (`settings.db_path`) and runs SELECT queries (list runs, ledger rows per run, audit rows, flagged = ledger where status='flagged', queue = ledger where status in ('flagged') for review, etc.). Read-only; never writes.

## Backend layout
```
backend/
  __init__.py
  app.py            # FastAPI app, CORS, router mounts, /api/health
  config.py         # API settings (reuse edvibe_bot.config.load_settings, but tolerate missing OPENAI for read-only endpoints)
  schemas.py        # pydantic request/response models
  store_read.py     # read-only SQLite adapter
  seed_data.py      # verbatim sample data (ported from web/src/data.ts) for empty-store fallback
  jobs.py           # RunManager: start/stop runs, on_event→asyncio bridge, demo simulator
  routes/runs.py    # /api/runs* + WS
  routes/data.py    # students/queue/flagged/reconcile/audit/settings
  tests/            # pytest: health, runs lifecycle (demo mode), data endpoints, seed fallback
  run.sh            # uvicorn backend.app:app --reload --port 8000
requirements-backend.txt   # fastapi, uvicorn[standard], websockets, httpx (tests)
```

## Frontend wiring
```
web/src/api.ts      # REST + WS client. Base = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000'.
                    # Functions: getHealth, listRuns, getRun, startRun, stopRun, listStudents, listQueue,
                    #   decideQueue, submitQueue, listFlagged, listReconcile, listAudit, getSettings, putSettings,
                    #   openRunStream(runId, onEvent) -> WebSocket.
```
- `AppContext` gains: data state (runs, students, queue, flagged, reconcile, audit, settings) fetched on mount via `api.ts`; `online: boolean` (false if the health/fetch fails → **fall back to the existing `data.ts` seed so the design still renders offline**). `startRun(mode)` → `api.startRun(...)`, store the returned `run_id`, navigate to Live Monitor, open the WS. `stopRun()` → `api.stopRun`.
- `LiveMonitor`: when a real `run_id`+WS is active, drive the tree/log/progress from incoming `RunEvent`s INSTEAD of the local 900ms simulation. Keep the local simulation as the fallback when there is no backend run (so the empty/demo experience still works offline).
- Screens (`Dashboard`, `ReviewQueue`, `Students`, `History`, `Flagged`): read their lists from `useApp()` context (which is API-or-seed) instead of importing `data.ts` directly. Keep `data.ts` as the seed source the context falls back to. Minimal churn: swap the direct `import { X } from '../data'` for `const { x } = useApp()`.
- A `web/.env` example: `VITE_API_BASE=http://localhost:8000`.

## Dev run
- Backend: `cd backend && ./run.sh` (or `uvicorn backend.app:app --port 8000`).
- Frontend: `cd web && npm run dev` (proxy or CORS to :8000).
- Add a root `README-dev.md` or `Makefile` target documenting "run both".

## Non-goals (v1)
- Real platform grade submission from the queue (needs browser; v1 records decisions/intent).
- Auth (localhost single-user).
- True mid-run cancellation (best-effort stop flag only).
