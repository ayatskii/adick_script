#!/usr/bin/env bash
# Launch the Edvibe Grader backend (FastAPI). Default port 8010 to avoid the
# very common :8000 collision (e.g. another local API). Override with PORT=...
# The frontend must point at the same port — see web/.env (VITE_API_BASE).
#
# Prefers a project-local virtualenv at ../.venv if present (Arch's Python is
# externally managed; see README-dev.md). Falls back to whatever `uvicorn` is
# on PATH.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$HERE")"
PORT="${PORT:-8010}"

if [ -x "$ROOT/.venv/bin/uvicorn" ]; then
  UVICORN="$ROOT/.venv/bin/uvicorn"
else
  UVICORN="uvicorn"
fi

cd "$ROOT"
exec "$UVICORN" backend.app:app --reload --port "$PORT" "$@"
