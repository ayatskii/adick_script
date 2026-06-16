import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum


class LedgerStatus(str, Enum):
    IN_PROGRESS = "in_progress"   # claim written BEFORE an irreversible click
    GRADED = "graded"
    SKIPPED = "skipped"
    FLAGGED = "flagged"
    ERROR = "error"
    COMPLETED = "completed"


# Sentinel exercise_id used for the per-lesson completion ledger row.
LESSON_SENTINEL = "__lesson__"


@dataclass
class LedgerEntry:
    student_id: str
    lesson_id: str
    exercise_id: str
    student_name: str
    lesson_name: str
    exercise_no: str
    type: str            # ExerciseType value
    proposed_score: "int | None"
    proposed_comment: "str | None"
    confidence: "float | None"
    submitted: bool
    dry_run: bool
    run_id: str
    status: str          # LedgerStatus value


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class Store:
    def __init__(self, db_path: str) -> None:
        self._db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self._db_path)
        con.execute("PRAGMA foreign_keys = ON")
        return con

    def init_schema(self) -> None:
        # Tables: runs, ledger, audit.
        # The §6 `queue` and `settings` tables are DEFERRED to the web-app plan
        # and are intentionally NOT created here.
        con = self._connect()
        try:
            con.executescript(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    id          TEXT PRIMARY KEY,
                    mode        TEXT NOT NULL,
                    scope_json  TEXT NOT NULL,
                    started_at  TEXT NOT NULL,
                    finished_at TEXT,
                    status      TEXT NOT NULL,
                    counts_json TEXT
                );

                CREATE TABLE IF NOT EXISTS ledger (
                    student_id       TEXT NOT NULL,
                    lesson_id        TEXT NOT NULL,
                    exercise_id      TEXT NOT NULL,
                    student_name     TEXT,
                    lesson_name      TEXT,
                    exercise_no      TEXT,
                    type             TEXT,
                    proposed_score   INTEGER,
                    proposed_comment TEXT,
                    confidence       REAL,
                    submitted        INTEGER NOT NULL DEFAULT 0,
                    submitted_at     TEXT,
                    dry_run          INTEGER NOT NULL DEFAULT 0,
                    run_id           TEXT NOT NULL,
                    status           TEXT NOT NULL,
                    PRIMARY KEY (student_id, lesson_id, exercise_id)
                );

                CREATE TABLE IF NOT EXISTS audit (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts          TEXT NOT NULL,
                    run_id      TEXT NOT NULL,
                    actor       TEXT NOT NULL DEFAULT 'bot',
                    action      TEXT NOT NULL,
                    target_json TEXT NOT NULL,
                    detail_json TEXT NOT NULL
                );
                """
            )
            con.commit()
        finally:
            con.close()

    def create_run(self, mode: str, scope: dict) -> str:
        run_id = uuid.uuid4().hex
        con = self._connect()
        try:
            con.execute(
                "INSERT INTO runs (id, mode, scope_json, started_at, finished_at, status, counts_json) "
                "VALUES (?, ?, ?, ?, NULL, 'running', NULL)",
                (run_id, mode, json.dumps(scope), _utc_now_iso()),
            )
            con.commit()
        finally:
            con.close()
        return run_id

    def finish_run(self, run_id: str, status: str, counts: dict) -> None:
        con = self._connect()
        try:
            con.execute(
                "UPDATE runs SET status=?, counts_json=?, finished_at=? WHERE id=?",
                (status, json.dumps(counts), _utc_now_iso(), run_id),
            )
            con.commit()
        finally:
            con.close()

    def append_audit(
        self, run_id: str, action: str, target_json: str, detail_json: str, ts: str
    ) -> None:
        # PUBLIC seam used by AuditLog: inserts exactly one audit row.
        con = self._connect()
        try:
            con.execute(
                "INSERT INTO audit (ts, run_id, actor, action, target_json, detail_json) "
                "VALUES (?, ?, 'bot', ?, ?, ?)",
                (ts, run_id, action, target_json, detail_json),
            )
            con.commit()
        finally:
            con.close()

    # ------------------------------------------------------------------
    # Task 5 stubs: exercise-ledger UPSERT methods (NOT implemented here)
    # Task 6 stubs: lesson-completion-sentinel methods (NOT implemented here)
    # ------------------------------------------------------------------
