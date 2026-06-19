"""RunManager: start/stop runs, bridge the bot's sync on_event callback to
async WS subscribers, and provide a no-browser/no-OpenAI demo simulator.

Threading model (per the contract):
- The bot's ``runner.run`` is SYNC and drives Playwright. We run it via
  ``asyncio.to_thread`` so the worker thread has NO event loop (Playwright's
  sync API requires that).
- ``on_event`` is called FROM the worker thread. It must not touch async code
  directly; it bridges to the asyncio loop captured before spawning via
  ``loop.call_soon_threadsafe(queue.put_nowait, normalized_event)``.
- Each run fans out normalized RunEvents to N subscriber queues (one per WS
  client). A sentinel (None) closes a subscriber.
- A best-effort stop flag (threading.Event) is exposed; true mid-Playwright
  cancellation is a documented v1 limitation.
"""

from __future__ import annotations

import asyncio
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

# Sentinel pushed to subscriber queues to signal end-of-stream.
_STREAM_END = object()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _event(type_: str, message: "str | None" = None, data: "dict | None" = None) -> dict:
    """Build a normalized RunEvent dict (contract §WebSocket)."""
    ev: dict[str, Any] = {"type": type_, "ts": _now_iso()}
    if message is not None:
        ev["message"] = message
    if data is not None:
        ev["data"] = data
    return ev


# ------------------------------------------------------------------
# on_event(raw dict from runner) -> normalized RunEvent
# ------------------------------------------------------------------
#
# The runner emits these raw payloads (see edvibe_bot/runner.py):
#   {"event": "student",         "student_id": ...}
#   {"event": "lesson_skip",     "student_id": ..., "lesson_id": ...}
#   {"event": "lesson_flag",     "student_id": ..., "lesson_id": ...}
#   {"event": "graded",          "student_id": ..., "lesson_id": ..., "exercise_no": ...}
#   {"event": "lesson_complete", "student_id": ..., "lesson_id": ...}
#
def normalize_runner_event(raw: dict) -> dict:
    """Map a raw runner on_event dict to a normalized RunEvent."""
    kind = raw.get("event")
    data = {k: v for k, v in raw.items() if k != "event"}

    if kind == "student":
        name = raw.get("student_name") or raw.get("student_id")
        return _event("student", message=f"Processing {name}", data=data)
    if kind == "student_error":
        return _event(
            "log",
            message=f"Student {raw.get('student_id')} could not be opened",
            data={"level": "error", **data},
        )
    if kind == "progress":
        done = raw.get("students_done", 0)
        total = raw.get("students_total", 0)
        # current/total are STUDENT-based — real exercise totals aren't known up
        # front (the runner discovers exercises lazily, section by section).
        return _event(
            "progress",
            message=f"{done}/{total} students",
            data={"current": done, "total": total,
                  "students_done": done, "students": total},
        )
    if kind == "exercise":
        status = raw.get("status", "graded")     # graded | skipped | flagged
        no = raw.get("exercise_no")
        score = raw.get("score")
        smax = raw.get("score_max")
        if status == "graded":
            msg = f"Graded {no} → {score}/{smax}"
        elif status == "skipped":
            msg = f"Proposed {no} → {score}/{smax} (awaiting review)"
        else:
            reason = raw.get("reason")
            msg = f"Flagged {no}" + (f" — {reason}" if reason else "")
        return _event(status, message=msg, data=data)
    if kind in ("lesson_skip", "lesson_flag", "lesson_complete"):
        return _event(
            "log",
            message=f"Lesson {raw.get('lesson_id')} {kind.replace('lesson_', '')}",
            data={"level": "info", **data},
        )
    # Unknown raw event -> pass through as a generic log so nothing is lost.
    return _event("log", message=str(raw), data={"level": "info", **data, "raw_event": kind})


@dataclass
class RunHandle:
    run_id: str
    mode: str
    status: str = "running"
    started_at: str = field(default_factory=_now_iso)
    finished_at: Optional[str] = None
    counts: dict = field(default_factory=lambda: {
        "graded": 0, "skipped": 0, "flagged": 0, "errors": 0, "completed_lessons": 0
    })
    # Subscriber fan-out queues (one per WS client).
    subscribers: list[asyncio.Queue] = field(default_factory=list)
    stop_flag: threading.Event = field(default_factory=threading.Event)
    done: bool = False
    # Buffer of events emitted before/without subscribers, so a WS that
    # connects slightly late still sees the full stream (esp. for demo/tests).
    buffer: list[dict] = field(default_factory=list)
    final_event: Optional[dict] = None


class RunManager:
    """Owns in-flight + recent runs and their event fan-out."""

    def __init__(self) -> None:
        self._runs: dict[str, RunHandle] = {}
        self._lock = threading.Lock()

    # -- lifecycle --------------------------------------------------------

    def get(self, run_id: str) -> Optional[RunHandle]:
        return self._runs.get(run_id)

    def active_runs(self) -> list[RunHandle]:
        return [h for h in self._runs.values() if not h.done]

    def all_handles(self) -> list[RunHandle]:
        return list(self._runs.values())

    async def start(
        self,
        *,
        mode: str,
        scope_all: bool,
        students: Optional[list[str]],
        max_students: Optional[int],
        max_lessons: Optional[int],
        headed: bool,
        confidence_threshold: float,
    ) -> RunHandle:
        run_id = uuid.uuid4().hex
        handle = RunHandle(run_id=run_id, mode=mode)
        self._runs[run_id] = handle

        loop = asyncio.get_running_loop()

        if mode == "demo":
            # Pure-async simulator; no thread/browser/OpenAI.
            asyncio.create_task(self._run_demo(handle))
        else:
            student_filter = None if scope_all else (students or [])
            # Real runner on a worker thread (no event loop there).
            asyncio.create_task(
                asyncio.to_thread(
                    self._run_real_blocking,
                    handle,
                    loop,
                    mode,
                    student_filter,
                    max_students,
                    max_lessons,
                    headed,
                    confidence_threshold,
                )
            )
        return handle

    def stop(self, run_id: str) -> bool:
        handle = self._runs.get(run_id)
        if handle is None:
            return False
        handle.stop_flag.set()
        return True

    # -- fan-out ----------------------------------------------------------

    def subscribe(self, run_id: str) -> Optional[asyncio.Queue]:
        handle = self._runs.get(run_id)
        if handle is None:
            return None
        q: asyncio.Queue = asyncio.Queue()
        # Replay any already-buffered events so a late subscriber is consistent.
        for ev in handle.buffer:
            q.put_nowait(ev)
        if handle.done:
            q.put_nowait(_STREAM_END)
        else:
            handle.subscribers.append(q)
        return q

    def _emit_async(self, handle: RunHandle, ev: dict) -> None:
        """Push a normalized event to all subscribers + buffer. MUST run on
        the event loop (called via call_soon_threadsafe from worker thread,
        or directly from the demo coroutine)."""
        handle.buffer.append(ev)
        self._track_counts(handle, ev)
        for q in handle.subscribers:
            q.put_nowait(ev)

    def _finish(self, handle: RunHandle, final_ev: dict) -> None:
        handle.buffer.append(final_ev)
        handle.final_event = final_ev
        handle.done = True
        handle.status = "done"
        handle.finished_at = _now_iso()
        for q in handle.subscribers:
            q.put_nowait(final_ev)
            q.put_nowait(_STREAM_END)
        handle.subscribers.clear()

    @staticmethod
    def _track_counts(handle: RunHandle, ev: dict) -> None:
        t = ev.get("type")
        if t == "graded":
            handle.counts["graded"] += 1
        elif t == "skipped":
            handle.counts["skipped"] += 1
        elif t == "flagged":
            handle.counts["flagged"] += 1
        elif t == "error":
            handle.counts["errors"] += 1
        elif t == "lesson_complete":
            handle.counts["completed_lessons"] += 1

    # -- real runner (worker thread) -------------------------------------

    def _run_real_blocking(
        self,
        handle: RunHandle,
        loop: asyncio.AbstractEventLoop,
        mode: str,
        student_filter: Optional[list[str]],
        max_students: Optional[int],
        max_lessons: Optional[int],
        headed: bool,
        confidence_threshold: float,
    ) -> None:
        """Runs in a worker thread (no event loop). Bridges every event back
        to the loop via call_soon_threadsafe."""

        def bridge(ev: dict) -> None:
            loop.call_soon_threadsafe(self._emit_async, handle, ev)

        def finish(ev: dict) -> None:
            loop.call_soon_threadsafe(self._finish, handle, ev)

        bridge(_event("run_started", message=f"Run started ({mode})",
                      data={"run_id": handle.run_id, "mode": mode}))
        bridge(_event("log", message=f"Starting {mode} run…",
                      data={"level": "info", "message": f"Starting {mode} run…"}))

        try:
            # Lazy imports: real runner needs playwright + openai + creds. These
            # must NOT be required for boot, demo, or read-only endpoints.
            from edvibe_bot.runner import RunConfig, run as runner_run

            from . import config as backend_config

            settings = backend_config.try_load_settings()
            if settings is None:
                raise RuntimeError(
                    "Missing or invalid configuration (.env): real run modes "
                    "require EDVIBE_LOGIN, EDVIBE_PASSWORD and OPENAI_API_KEY."
                )

            if handle.stop_flag.is_set():
                raise RuntimeError("Run stopped before it started.")

            # The frontend uses short mode names ('dryrun'/'full'); the bot-core
            # runner gates submission on the canonical 'dry_run'/'full_auto'.
            canonical_mode = {"dryrun": "dry_run", "full": "full_auto"}.get(mode, mode)
            run_config = RunConfig(
                mode=canonical_mode,
                student_filter=student_filter,
                max_students=max_students,
                max_lessons=max_lessons,
                headed=headed,
                confidence_threshold=confidence_threshold,
            )

            def on_event(raw: dict) -> None:
                # Called from this worker thread by the runner; normalize +
                # bridge. Honour the best-effort stop flag opportunistically.
                bridge(normalize_runner_event(raw))

            report = runner_run(run_config, settings, settings_store(settings), on_event)

            counts = {
                "graded": report.graded,
                "skipped": report.skipped,
                "flagged": report.flagged,
                "errors": report.errors,
                "completed_lessons": report.completed_lessons,
            }
            handle.counts = counts
            finish(_event("run_complete", message="Run complete",
                          data={"counts": counts, "run_id": report.run_id}))
        except Exception as exc:  # noqa: BLE001 - never crash the server
            # Before Phase 0 (and without browser/creds) real runs fail at the
            # browser step; surface it as error + run_complete rather than
            # taking down the worker/server.
            bridge(_event("error", message=str(exc),
                          data={"level": "err", "error": str(exc)}))
            handle.counts["errors"] += 1
            finish(_event("run_complete", message="Run ended with error",
                          data={"counts": handle.counts, "error": str(exc)}))

    # -- demo simulator (no browser, no OpenAI) ---------------------------

    async def _run_demo(self, handle: RunHandle) -> None:
        """Stream a realistic sequence of normalized RunEvents on a timer."""
        tick = 0.18  # seconds between events; keeps tests fast but visible

        students = [
            ("s1", "Анель", "Lesson 14 — Entertainment"),
            ("s2", "Dias", "Lesson 14 — Entertainment"),
            ("s3", "Аружан", "Lesson 12 — Travel"),
        ]
        # (exercise_no, outcome) per lesson
        plan = [
            ("1.2", "graded"),
            ("2.1", "graded"),
            ("3.4", "flagged"),
            ("2.2", "skipped"),
        ]
        total = len(students) * len(plan)
        current = 0
        students_done = 0

        self._emit_async(
            handle,
            _event("run_started", message="Demo run started",
                   data={"run_id": handle.run_id, "mode": "demo"}),
        )
        self._emit_async(
            handle,
            _event("log", message="Launching simulated browser (demo, no real platform)…",
                   data={"level": "info",
                         "message": "Launching simulated browser (demo, no real platform)…"}),
        )
        await asyncio.sleep(tick)

        for sid, sname, lesson in students:
            if handle.stop_flag.is_set():
                break
            self._emit_async(
                handle,
                _event("student", message=f"Opening progress for {sname}",
                       data={"student_id": sid, "student_name": sname}),
            )
            await asyncio.sleep(tick)
            self._emit_async(
                handle,
                _event("lesson", message=f"{sname}: {lesson}",
                       data={"student_id": sid, "lesson_id": lesson}),
            )
            await asyncio.sleep(tick)

            for ex_no, outcome in plan:
                if handle.stop_flag.is_set():
                    break
                self._emit_async(
                    handle,
                    _event("exercise",
                           message=f"{sname}: exercise {ex_no}",
                           data={"student_id": sid, "lesson_id": lesson,
                                 "exercise_no": ex_no}),
                )
                await asyncio.sleep(tick)

                if outcome == "graded":
                    score = 7 + (current % 3)
                    conf = round(0.78 + (current % 4) * 0.04, 2)
                    self._emit_async(
                        handle,
                        _event("graded",
                               message=f"{sname} {ex_no}: scored {score} (conf {conf})",
                               data={"student_id": sid, "lesson_id": lesson,
                                     "exercise_no": ex_no, "score": score,
                                     "confidence": conf}),
                    )
                    self._emit_async(
                        handle,
                        _event("log", message=f"Graded {ex_no} → {score}",
                               data={"level": "ok", "message": f"Graded {ex_no} → {score}"}),
                    )
                elif outcome == "skipped":
                    self._emit_async(
                        handle,
                        _event("skipped",
                               message=f"{sname} {ex_no}: skipped (already done)",
                               data={"student_id": sid, "lesson_id": lesson,
                                     "exercise_no": ex_no, "reason": "already_done"}),
                    )
                elif outcome == "flagged":
                    self._emit_async(
                        handle,
                        _event("flagged",
                               message=f"{sname} {ex_no}: flagged (low confidence)",
                               data={"student_id": sid, "lesson_id": lesson,
                                     "exercise_no": ex_no, "reason": "low_confidence",
                                     "confidence": 0.61}),
                    )
                    self._emit_async(
                        handle,
                        _event("log", message=f"Flagged {ex_no} for human review",
                               data={"level": "warn",
                                     "message": f"Flagged {ex_no} for human review"}),
                    )

                current += 1
                pct = round(current / total * 100) if total else 100
                self._emit_async(
                    handle,
                    _event("progress",
                           data={"current": current, "total": total,
                                 "students_done": students_done,
                                 "students": len(students), "pct": pct}),
                )
                await asyncio.sleep(tick)

            self._emit_async(
                handle,
                _event("lesson_complete",
                       message=f"{sname}: {lesson} complete",
                       data={"student_id": sid, "lesson_id": lesson}),
            )
            students_done += 1
            self._emit_async(
                handle,
                _event("progress",
                       data={"current": current, "total": total,
                             "students_done": students_done,
                             "students": len(students),
                             "pct": round(current / total * 100) if total else 100}),
            )
            await asyncio.sleep(tick)

        stopped = handle.stop_flag.is_set()
        self._emit_async(
            handle,
            _event("log",
                   message="Run stopped by user." if stopped else "All students processed.",
                   data={"level": "warn" if stopped else "ok",
                         "message": "Run stopped by user." if stopped
                         else "All students processed."}),
        )
        self._finish(
            handle,
            _event("run_complete",
                   message="Demo run stopped" if stopped else "Demo run complete",
                   data={"counts": handle.counts, "stopped": stopped,
                         "run_id": handle.run_id}),
        )


def settings_store(settings):
    """Build a bot-core Store bound to the configured DB path. Lazy import so
    boot/demo don't need anything beyond config + store."""
    from edvibe_bot.state.store import Store

    store = Store(settings.db_path)
    store.init_schema()
    return store


# Process-wide singleton used by the routes.
manager = RunManager()
