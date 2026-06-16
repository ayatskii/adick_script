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
    # Exercise-ledger UPSERT methods (Task 5)
    # ------------------------------------------------------------------

    # ledger keyed by (student_id, lesson_id, exercise_id); UPSERTs in place;
    # submitted_at stamped iff submitted=True (NULL otherwise).
    def record_exercise(self, entry: LedgerEntry) -> None:
        submitted_at = _utc_now_iso() if entry.submitted else None
        con = self._connect()
        try:
            con.execute(
                """
                INSERT INTO ledger (
                    student_id, lesson_id, exercise_id,
                    student_name, lesson_name, exercise_no, type,
                    proposed_score, proposed_comment, confidence,
                    submitted, submitted_at, dry_run, run_id, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(student_id, lesson_id, exercise_id) DO UPDATE SET
                    student_name     = excluded.student_name,
                    lesson_name      = excluded.lesson_name,
                    exercise_no      = excluded.exercise_no,
                    type             = excluded.type,
                    proposed_score   = excluded.proposed_score,
                    proposed_comment = excluded.proposed_comment,
                    confidence       = excluded.confidence,
                    submitted        = excluded.submitted,
                    submitted_at     = excluded.submitted_at,
                    dry_run          = excluded.dry_run,
                    run_id           = excluded.run_id,
                    status           = excluded.status
                """,
                (
                    entry.student_id,
                    entry.lesson_id,
                    entry.exercise_id,
                    entry.student_name,
                    entry.lesson_name,
                    entry.exercise_no,
                    entry.type,
                    entry.proposed_score,
                    entry.proposed_comment,
                    entry.confidence,
                    1 if entry.submitted else 0,
                    submitted_at,
                    1 if entry.dry_run else 0,
                    entry.run_id,
                    entry.status,
                ),
            )
            con.commit()
        finally:
            con.close()

    def get_exercise_status(
        self, student_id: str, lesson_id: str, exercise_id: str
    ) -> "str | None":
        con = self._connect()
        try:
            row = con.execute(
                "SELECT status FROM ledger "
                "WHERE student_id=? AND lesson_id=? AND exercise_id=?",
                (student_id, lesson_id, exercise_id),
            ).fetchone()
        finally:
            con.close()
        return row[0] if row is not None else None

    def is_exercise_done(
        self, student_id: str, lesson_id: str, exercise_id: str
    ) -> bool:
        # True ONLY for terminal states.
        status = self.get_exercise_status(student_id, lesson_id, exercise_id)
        return status in {LedgerStatus.GRADED.value, LedgerStatus.COMPLETED.value}

    def is_exercise_attempted(
        self, student_id: str, lesson_id: str, exercise_id: str
    ) -> bool:
        # Any row exists (including in_progress).
        return self.get_exercise_status(student_id, lesson_id, exercise_id) is not None

    # ------------------------------------------------------------------
    # Lesson completion sentinel methods (Task 6)
    # ------------------------------------------------------------------

    # Lesson completion is tracked by a sentinel ledger row (exercise_id == LESSON_SENTINEL).
    def record_lesson_completion_intent(
        self, student_id: str, lesson_id: str, run_id: str
    ) -> None:
        # status=in_progress, written BEFORE the irreversible "Завершить урок" click.
        self.record_exercise(
            LedgerEntry(
                student_id=student_id,
                lesson_id=lesson_id,
                exercise_id=LESSON_SENTINEL,
                student_name="",
                lesson_name="",
                exercise_no="",
                type="",
                proposed_score=None,
                proposed_comment=None,
                confidence=None,
                submitted=False,
                dry_run=False,
                run_id=run_id,
                status=LedgerStatus.IN_PROGRESS.value,
            )
        )

    def record_lesson_completed(
        self, student_id: str, lesson_id: str, run_id: str, dry_run: bool
    ) -> None:
        # status=completed, written AFTER the click returns. A real (non-dry)
        # completion counts as submitted; dry-run never submits.
        self.record_exercise(
            LedgerEntry(
                student_id=student_id,
                lesson_id=lesson_id,
                exercise_id=LESSON_SENTINEL,
                student_name="",
                lesson_name="",
                exercise_no="",
                type="",
                proposed_score=None,
                proposed_comment=None,
                confidence=None,
                submitted=not dry_run,
                dry_run=dry_run,
                run_id=run_id,
                status=LedgerStatus.COMPLETED.value,
            )
        )

    def get_lesson_status(self, student_id: str, lesson_id: str) -> "str | None":
        return self.get_exercise_status(student_id, lesson_id, LESSON_SENTINEL)

    def is_lesson_completed(self, student_id: str, lesson_id: str) -> bool:
        # True ONLY when the sentinel reached the terminal completed state.
        return self.get_lesson_status(student_id, lesson_id) == LedgerStatus.COMPLETED.value

    def is_lesson_completion_attempted(self, student_id: str, lesson_id: str) -> bool:
        # Any sentinel row exists (including in_progress).
        return self.get_lesson_status(student_id, lesson_id) is not None
