"""StoreReader against a real tmp sqlite populated via the bot-core Store."""

from __future__ import annotations

import pytest

from edvibe_bot.state.store import LedgerEntry, LedgerStatus, Store
from backend.store_read import StoreReader


@pytest.fixture()
def populated_db(tmp_path):
    db = str(tmp_path / "edvibe.sqlite")
    store = Store(db)
    store.init_schema()

    run_id = store.create_run("dry_run", {"max_students": 2})

    # One graded, one flagged, one skipped exercise + a completed lesson.
    store.record_exercise(
        LedgerEntry(
            student_id="s1", lesson_id="l1", exercise_id="e1",
            student_name="Анель", lesson_name="Lesson 14 — Entertainment",
            exercise_no="1.2", type="audio",
            proposed_score=7, proposed_comment="Good job", confidence=0.84,
            submitted=True, dry_run=True, run_id=run_id,
            status=LedgerStatus.GRADED.value,
        )
    )
    store.record_exercise(
        LedgerEntry(
            student_id="s1", lesson_id="l1", exercise_id="e2",
            student_name="Анель", lesson_name="Lesson 14 — Entertainment",
            exercise_no="2.1", type="text",
            proposed_score=5, proposed_comment="low_confidence", confidence=0.55,
            submitted=False, dry_run=True, run_id=run_id,
            status=LedgerStatus.FLAGGED.value,
        )
    )
    store.record_exercise(
        LedgerEntry(
            student_id="s2", lesson_id="l1", exercise_id="e3",
            student_name="Dias", lesson_name="Lesson 14 — Entertainment",
            exercise_no="1.1", type="text",
            proposed_score=8, proposed_comment="ok", confidence=0.7,
            submitted=False, dry_run=True, run_id=run_id,
            status=LedgerStatus.SKIPPED.value,
        )
    )
    store.record_lesson_completion_intent("s1", "l1", run_id)
    store.record_lesson_completed("s1", "l1", run_id, dry_run=True)

    store.append_audit(
        run_id, "grade", '{"student_id":"s1"}', '{"score":7}', "2026-06-16T09:14:00+00:00"
    )
    store.finish_run(
        run_id, "done",
        {"graded": 1, "skipped": 1, "flagged": 1, "errors": 0, "completed_lessons": 1},
    )
    return db, run_id


def test_list_and_get_run(populated_db):
    db, run_id = populated_db
    reader = StoreReader(db)

    runs = reader.list_runs()
    assert len(runs) == 1
    r = runs[0]
    assert r["id"] == run_id
    assert r["mode"] == "dry_run"
    assert r["counts"]["graded"] == 1
    assert r["counts"]["completed_lessons"] == 1

    assert reader.get_run(run_id)["id"] == run_id
    assert reader.get_run("missing") is None


def test_timeline_excludes_sentinel(populated_db):
    db, run_id = populated_db
    tl = StoreReader(db).timeline_for_run(run_id)
    # 3 exercises, the lesson sentinel is excluded.
    assert len(tl) == 3
    graded = next(e for e in tl if e["ex"] == "1.2")
    assert graded["proposedScore"] == 7
    assert graded["submittedScore"] == 7  # submitted=True
    assert graded["status"] == "graded"


def test_flagged_and_queue_views(populated_db):
    db, _ = populated_db
    reader = StoreReader(db)

    flagged = reader.flagged_items()
    assert len(flagged) == 1
    assert flagged[0]["student"] == "Анель"
    assert flagged[0]["ex"] == "2.1"

    # The review queue surfaces the flagged row AND the skipped PROPOSAL (it
    # carries a proposed score), so a reviewer sees everything awaiting a decision.
    queue = reader.queue_items()
    assert len(queue) == 2
    by_ex = {q["ex"]: q for q in queue}
    assert set(by_ex) == {"2.1", "1.1"}
    assert by_ex["1.1"]["score"] == 8           # skipped proposal surfaces its score
    assert all(q["status"] == "pending" for q in queue)
    assert all(q["type"] == "text" for q in queue)


def test_audit_and_reconcile(populated_db):
    db, run_id = populated_db
    reader = StoreReader(db)

    audit = reader.audit_for_run(run_id)
    assert len(audit) == 1
    assert audit[0]["action"] == "grade"
    assert audit[0]["target"] == {"student_id": "s1"}
    assert audit[0]["detail"] == {"score": 7}

    recon = reader.reconcile_rows()
    assert len(recon) == 1
    # The bot-core writes the lesson-completion sentinel with empty
    # student_name/lesson_name, so the reader falls back to the ids.
    assert recon[0]["lesson"] == "l1"
    assert recon[0]["flagStatus"] is None  # completed


def test_missing_db_returns_empty(tmp_path):
    reader = StoreReader(str(tmp_path / "nope.sqlite"))
    assert reader.list_runs() == []
    assert reader.flagged_items() == []
    assert reader.get_run("x") is None
    assert reader.students() == []
