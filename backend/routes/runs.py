"""/api/runs* endpoints + the per-run WebSocket stream."""

from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from .. import config as backend_config
from ..jobs import _STREAM_END, manager
from ..schemas import (
    Run,
    RunDetail,
    StartRunRequest,
    StartRunResponse,
    StopResponse,
)
from ..seed_data import SEED_RUNS, SEED_TIMELINE
from ..store_read import StoreReader

router = APIRouter(prefix="/api", tags=["runs"])


def _reader() -> StoreReader:
    return StoreReader(backend_config.db_path())


def _handle_to_run(h) -> dict:
    return {
        "id": h.run_id,
        "mode": h.mode,
        "started_at": h.started_at,
        "finished_at": h.finished_at,
        "status": h.status if not h.done else "done",
        "duration": None,
        "counts": h.counts,
    }


@router.post("/runs", response_model=StartRunResponse)
async def start_run(req: StartRunRequest) -> StartRunResponse:
    handle = await manager.start(
        mode=req.mode,
        scope_all=req.scope.all,
        students=req.scope.students,
        max_students=req.max_students,
        max_lessons=req.max_lessons,
        headed=req.headed,
        confidence_threshold=req.confidence_threshold,
    )
    return StartRunResponse(run_id=handle.run_id, status="running")


@router.get("/runs", response_model=list[Run])
async def list_runs() -> list[Run]:
    # In-memory handles (active + recently finished this process) first.
    live = [_handle_to_run(h) for h in manager.all_handles()]
    live_ids = {r["id"] for r in live}

    store_runs = [r for r in _reader().list_runs() if r["id"] not in live_ids]

    combined = live + store_runs
    if not combined:
        combined = SEED_RUNS  # empty-store fallback
    return [Run(**r) for r in combined]


@router.get("/runs/{run_id}", response_model=RunDetail)
async def get_run(run_id: str) -> RunDetail:
    reader = _reader()

    handle = manager.get(run_id)
    run_dict = None
    if handle is not None:
        run_dict = _handle_to_run(handle)
    else:
        run_dict = reader.get_run(run_id)

    if run_dict is None:
        # Fall back to a seed run if the id matches; else synthesize empty.
        seed = next((r for r in SEED_RUNS if r["id"] == run_id), None)
        run_dict = seed or {
            "id": run_id,
            "mode": "demo",
            "started_at": None,
            "finished_at": None,
            "status": "unknown",
            "duration": None,
            "counts": {"graded": 0, "skipped": 0, "flagged": 0, "errors": 0, "completed_lessons": 0},
        }

    timeline = reader.timeline_for_run(run_id)
    audit = reader.audit_for_run(run_id)
    if not timeline and run_dict.get("id") in {r["id"] for r in SEED_RUNS}:
        timeline = SEED_TIMELINE  # seed fallback for the demo/history view

    return RunDetail(run=Run(**run_dict), timeline=timeline, audit=audit)


@router.post("/runs/{run_id}/stop", response_model=StopResponse)
async def stop_run(run_id: str) -> StopResponse:
    ok = manager.stop(run_id)
    if not ok:
        return StopResponse(
            ok=False, note=f"No active run {run_id} to stop (already finished?)."
        )
    return StopResponse(
        ok=True,
        note=(
            "Stop flag set (best-effort). Mid-Playwright cancellation is a "
            "documented v1 limitation; the run stops at the next safe point."
        ),
    )


@router.websocket("/runs/{run_id}/stream")
async def run_stream(ws: WebSocket, run_id: str) -> None:
    await ws.accept()
    queue = manager.subscribe(run_id)
    if queue is None:
        await ws.send_json(
            {
                "type": "error",
                "ts": "",
                "message": f"Unknown run {run_id}",
                "data": {"level": "err"},
            }
        )
        await ws.close()
        return

    try:
        while True:
            item = await queue.get()
            if item is _STREAM_END:
                break
            await ws.send_json(item)
            if item.get("type") == "run_complete":
                # The stream end sentinel follows; loop will break on it.
                continue
    except WebSocketDisconnect:
        pass
    finally:
        try:
            await ws.close()
        except RuntimeError:
            pass
