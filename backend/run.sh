#!/usr/bin/env bash
# Launch the Edvibe Grader backend (FastAPI) on :8000.
#
# Prefers a project-local virtualenv at ../.venv if present (Arch's Python is
# externally managed; see README-dev.md). Falls back to whatever `uvicorn` is
# on PATH.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$HERE")"

if [ -x "$ROOT/.venv/bin/uvicorn" ]; then
  UVICORN="$ROOT/.venv/bin/uvicorn"
else
  UVICORN="uvicorn"
fi

cd "$ROOT"
exec "$UVICORN" backend.app:app --reload --port 8000 "$@"
