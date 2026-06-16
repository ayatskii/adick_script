# Edvibe Grader — Dev Run (frontend + backend)

The stack:

```
web (React/Vite, :5173) ──REST+WS──▶ backend (FastAPI, :8000) ──▶ edvibe_bot.runner.run()
```

See `docs/superpowers/specs/2026-06-16-backend-integration-contract.md` for the
binding contract (endpoints, data shapes, WS RunEvent shape).

## 1. Backend (FastAPI, :8000)

This machine's system Python is **externally managed** (PEP 668), so use a
project-local virtualenv:

```bash
python -m venv .venv
.venv/bin/pip install -r requirements-backend.txt
# For REAL run modes (dry_run/full_auto/review) you also need the bot core deps:
#   .venv/bin/pip install -r requirements.txt   (playwright + openai)
#   .venv/bin/playwright install chromium
```

Run it:

```bash
cd backend && ./run.sh           # uses ../.venv/bin/uvicorn if present
# or:
.venv/bin/uvicorn backend.app:app --reload --port 8000
```

Health check: `curl http://localhost:8000/api/health`
→ `{"ok":true,"phase0_done":<bool>,"openai_key_set":<bool>}`

- `phase0_done` is true once no `# CONFIRM` markers remain in
  `edvibe_bot/selectors.py`.
- `openai_key_set` reflects `OPENAI_API_KEY` in env / `.env`.

Read-only GET endpoints and the **demo** run mode work with NO credentials and
WITHOUT playwright/openai installed (those are imported lazily, only when a
real run starts). Demo runs a fully simulated grading session over the WS so
the whole UI is demoable before Phase 0.

Run the backend tests:

```bash
.venv/bin/python -m pytest backend/tests -q
```

## 2. Frontend (Vite, :5173)

```bash
cd web
npm install
echo "VITE_API_BASE=http://localhost:8000" > .env   # if not already present
npm run dev
```

The frontend falls back to the bundled `web/src/data.ts` seed when the backend
is offline, so the design still renders standalone.

## Run modes

| mode | browser | OpenAI | notes |
|---|---|---|---|
| `demo` | no | no | simulated stream, always works |
| `dry_run` | yes | yes | evaluates, never submits |
| `review` | yes | yes | builds a review queue, never submits |
| `full_auto` | yes | yes | the only mode that submits to the platform |

Real modes need `.env` (`EDVIBE_LOGIN`, `EDVIBE_PASSWORD`, `OPENAI_API_KEY`)
and Phase 0 selectors. Before Phase 0 they fail at the browser step — the
backend surfaces that as an `error` + `run_complete` event and keeps running.
