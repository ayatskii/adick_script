"""Read-only SQLite adapter over the bot-core store (edvibe.sqlite).

The bot-core ``Store`` exposes only write methods; this adapter opens the SAME
file read-only and runs SELECT queries. It NEVER writes. If the DB file or the
expected tables don't exist yet (true before any real run), every method
returns empty so callers fall back to seed data.

Table shapes (must match edvibe_bot/state/store.py):
- runs(id, mode, scope_json, started_at, finished_at, status, counts_json)
- ledger(student_id, lesson_id, exercise_id, student_name, lesson_name,
         exercise_no, type, proposed_score, proposed_comment, confidence,
         submitted, submitted_at, dry_run, run_id, status)
- audit(id, ts, run_id, actor, action, target_json, detail_json)
"""

from __future__ import annotations

import json
import os
import sqlite3
from typing import Any, Optional

from edvibe_bot.state.store import LESSON_SENTINEL, LedgerStatus


class StoreReader:
    def __init__(self, db_path: str) -> None:
        self._db_path = db_path

    # -- low-level helpers ------------------------------------------------

    def _exists(self) -> bool:
        return os.path.exists(self._db_path)

    def _connect(self) -> Optional[sqlite3.Connection]:
        if not self._exists():
            return None
        # Read-only via URI so we never create or mutate the file.
        try:
            con = sqlite3.connect(
                f"file:{self._db_path}?mode=ro", uri=True
            )
        except sqlite3.OperationalError:
            return None
        con.row_factory = sqlite3.Row
        return con

    def _has_table(self, con: sqlite3.Connection, name: str) -> bool:
        row = con.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
        ).fetchone()
        return row is not None

    def _query(self, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
        con = self._connect()
        if con is None:
            return []
        try:
            # Guard: a table referenced in `sql` may not exist on a fresh DB.
            return list(con.execute(sql, params).fetchall())
        except sqlite3.OperationalError:
            return []
        finally:
            con.close()

    @staticmethod
    def _loads(value: Any, default: Any) -> Any:
        if not value:
            return default
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return default

    # -- runs -------------------------------------------------------------

    def list_runs(self) -> list[dict]:
        rows = self._query(
            "SELECT id, mode, scope_json, started_at, finished_at, status, "
            "counts_json FROM runs ORDER BY started_at DESC"
        )
        return [self._run_dict(r) for r in rows]

    def get_run(self, run_id: str) -> Optional[dict]:
        rows = self._query(
            "SELECT id, mode, scope_json, started_at, finished_at, status, "
            "counts_json FROM runs WHERE id=?",
            (run_id,),
        )
        if not rows:
            return None
        return self._run_dict(rows[0])

    def _run_dict(self, r: sqlite3.Row) -> dict:
        counts = self._loads(
            r["counts_json"],
            {"graded": 0, "skipped": 0, "flagged": 0, "errors": 0, "completed_lessons": 0},
        )
        # Normalize "running"/"done" -> contract status surface; keep raw too.
        status = r["status"]
        return {
            "id": r["id"],
            "mode": r["mode"],
            "started_at": r["started_at"],
            "finished_at": r["finished_at"],
            "status": status,
            "duration": self._duration(r["started_at"], r["finished_at"]),
            "counts": {
                "graded": int(counts.get("graded", 0) or 0),
                "skipped": int(counts.get("skipped", 0) or 0),
                "flagged": int(counts.get("flagged", 0) or 0),
                "errors": int(counts.get("errors", 0) or 0),
                "completed_lessons": int(counts.get("completed_lessons", 0) or 0),
            },
        }

    @staticmethod
    def _duration(started: Optional[str], finished: Optional[str]) -> Optional[str]:
        if not started or not finished:
            return None
        from datetime import datetime

        try:
            a = datetime.fromisoformat(started)
            b = datetime.fromisoformat(finished)
        except ValueError:
            return None
        secs = int((b - a).total_seconds())
        if secs < 0:
            return None
        m, s = divmod(secs, 60)
        return f"{m}m {s:02d}s"

    # -- ledger -----------------------------------------------------------

    def ledger_for_run(self, run_id: str) -> list[dict]:
        rows = self._query(
            "SELECT * FROM ledger WHERE run_id=? ORDER BY student_name, "
            "lesson_name, exercise_no",
            (run_id,),
        )
        return [dict(r) for r in rows]

    def all_ledger(self) -> list[dict]:
        rows = self._query("SELECT * FROM ledger")
        return [dict(r) for r in rows]

    def ledger_by_status(self, *statuses: str) -> list[dict]:
        if not statuses:
            return []
        placeholders = ",".join("?" for _ in statuses)
        rows = self._query(
            f"SELECT * FROM ledger WHERE status IN ({placeholders}) "
            "AND exercise_id != ?",
            (*statuses, LESSON_SENTINEL),
        )
        return [dict(r) for r in rows]

    # -- derived views ----------------------------------------------------

    def timeline_for_run(self, run_id: str) -> list[dict]:
        """Map per-exercise ledger rows (excluding the lesson sentinel) into
        the frontend's TimelineEntry shape."""
        out: list[dict] = []
        for r in self.ledger_for_run(run_id):
            if r.get("exercise_id") == LESSON_SENTINEL:
                continue
            submitted = bool(r.get("submitted"))
            score = r.get("proposed_score")
            out.append(
                {
                    "student": r.get("student_name") or r.get("student_id"),
                    "ex": r.get("exercise_no") or "",
                    "proposedScore": score,
                    "submittedScore": score if submitted else None,
                    "status": r.get("status"),
                    "humanEdited": False,
                    "tsOffset": 0,
                }
            )
        return out

    def audit_for_run(self, run_id: str) -> list[dict]:
        rows = self._query(
            "SELECT id, ts, run_id, actor, action, target_json, detail_json "
            "FROM audit WHERE run_id=? ORDER BY id",
            (run_id,),
        )
        return [self._audit_dict(r) for r in rows]

    def all_audit(self) -> list[dict]:
        rows = self._query(
            "SELECT id, ts, run_id, actor, action, target_json, detail_json "
            "FROM audit ORDER BY id DESC"
        )
        return [self._audit_dict(r) for r in rows]

    def _audit_dict(self, r: sqlite3.Row) -> dict:
        return {
            "id": r["id"],
            "ts": r["ts"],
            "run_id": r["run_id"],
            "actor": r["actor"],
            "action": r["action"],
            "target": self._loads(r["target_json"], {}),
            "detail": self._loads(r["detail_json"], {}),
        }

    def flagged_items(self) -> list[dict]:
        """Ledger rows with status='flagged' -> FlaggedItem shape."""
        out: list[dict] = []
        for r in self.ledger_by_status(LedgerStatus.FLAGGED.value):
            out.append(
                {
                    "id": f"{r['student_id']}:{r['lesson_id']}:{r['exercise_id']}",
                    "student": r.get("student_name") or r.get("student_id"),
                    "lesson": r.get("lesson_name") or r.get("lesson_id"),
                    "ex": r.get("exercise_no") or "",
                    "reason": r.get("proposed_comment") or "Flagged",
                    "severity": "Needs a look",
                    "detail": r.get("proposed_comment") or "",
                }
            )
        return out

    def queue_items(self) -> list[dict]:
        """Items awaiting human review -> ReviewItem shape. Sourced from the real
        ledger: every FLAGGED row (needs attention) plus every un-submitted
        PROPOSAL (a SKIPPED row carrying a proposed score — dry_run and review
        record evaluations as skipped). Lesson-sentinel rows are excluded."""
        out: list[dict] = []
        for r in self.ledger_by_status(
            LedgerStatus.FLAGGED.value, LedgerStatus.SKIPPED.value
        ):
            if r.get("exercise_id") == LESSON_SENTINEL:
                continue
            is_flagged = r.get("status") == LedgerStatus.FLAGGED.value
            has_proposal = r.get("proposed_score") is not None
            # skipped rows are only reviewable when they're a real proposal.
            if not is_flagged and not has_proposal:
                continue
            ex_type = "audio" if (r.get("type") == "audio") else "text"
            out.append(
                {
                    "id": f"{r['student_id']}:{r['lesson_id']}:{r['exercise_id']}",
                    "student": r.get("student_name") or r.get("student_id"),
                    "lesson": r.get("lesson_name") or r.get("lesson_id"),
                    "section": "",
                    "ex": r.get("exercise_no") or "",
                    "type": ex_type,
                    "score": r.get("proposed_score") or 0,
                    "conf": r.get("confidence") or 0.0,
                    "transcript": "",
                    "comment": r.get("proposed_comment")
                    or ("Flagged for review" if is_flagged else ""),
                    "status": "pending",
                    "edited": False,
                    "flagged": bool(is_flagged and not has_proposal),
                }
            )
        return out

    def reconcile_rows(self) -> list[dict]:
        """Completed-lesson sentinel rows -> ReconcileRow shape."""
        rows = self._query(
            "SELECT * FROM ledger WHERE exercise_id=? ",
            (LESSON_SENTINEL,),
        )
        out: list[dict] = []
        for r in rows:
            rd = dict(r)
            completed = rd.get("status") == LedgerStatus.COMPLETED.value
            out.append(
                {
                    "student": rd.get("student_name") or rd.get("student_id"),
                    "lesson": rd.get("lesson_name") or rd.get("lesson_id"),
                    "completedBy": "This bot" if completed else "In progress",
                    "flagStatus": None if completed else "flagged",
                    "flagLabel": None if completed else "Incomplete — check",
                }
            )
        return out

    def students(self) -> list[dict]:
        """Aggregate ledger rows into the StudentRow shape (best-effort)."""
        by_student: dict[str, dict] = {}
        for r in self.all_ledger():
            if r.get("exercise_id") == LESSON_SENTINEL:
                continue
            sid = r.get("student_id")
            if sid is None:
                continue
            entry = by_student.setdefault(
                sid,
                {
                    "id": sid,
                    "name": r.get("student_name") or sid,
                    "awaiting": 0,
                    "lastActivity": "",
                    "_lessons": {},
                },
            )
            lname = r.get("lesson_name") or r.get("lesson_id")
            status = r.get("status")
            # Map ledger status -> a frontend StatusKind for the lesson chip.
            entry["_lessons"][lname] = status
        out: list[dict] = []
        for entry in by_student.values():
            lessons = [
                {"name": name, "status": status}
                for name, status in entry.pop("_lessons").items()
            ]
            awaiting = sum(
                1
                for l in lessons
                if l["status"] in (LedgerStatus.FLAGGED.value, "queued")
            )
            entry["lessons"] = lessons
            entry["awaiting"] = awaiting
            out.append(entry)
        return out
