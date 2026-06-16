import sqlite3

from edvibe_bot.state.store import LESSON_SENTINEL, Store


def _store(tmp_path):
    s = Store(str(tmp_path / "t.sqlite"))
    s.init_schema()
    return s


def test_no_sentinel_means_not_attempted_not_completed(tmp_path):
    s = _store(tmp_path)
    assert s.get_lesson_status("s1", "l1") is None
    assert s.is_lesson_completed("s1", "l1") is False
    assert s.is_lesson_completion_attempted("s1", "l1") is False


def test_intent_writes_in_progress_sentinel(tmp_path):
    db = str(tmp_path / "t.sqlite")
    s = Store(db)
    s.init_schema()
    s.record_lesson_completion_intent("s1", "l1", "r1")
    assert s.get_lesson_status("s1", "l1") == "in_progress"
    assert s.is_lesson_completion_attempted("s1", "l1") is True
    assert s.is_lesson_completed("s1", "l1") is False
    con = sqlite3.connect(db)
    row = con.execute(
        "SELECT exercise_id, submitted, submitted_at FROM ledger "
        "WHERE student_id='s1' AND lesson_id='l1'"
    ).fetchone()
    con.close()
    assert row[0] == LESSON_SENTINEL
    assert row[1] == 0
    assert row[2] is None


def test_intent_then_completed_transition(tmp_path):
    db = str(tmp_path / "t.sqlite")
    s = Store(db)
    s.init_schema()
    s.record_lesson_completion_intent("s1", "l1", "r1")
    s.record_lesson_completed("s1", "l1", "r1", dry_run=False)
    assert s.get_lesson_status("s1", "l1") == "completed"
    assert s.is_lesson_completed("s1", "l1") is True
    assert s.is_lesson_completion_attempted("s1", "l1") is True
    con = sqlite3.connect(db)
    rows = con.execute(
        "SELECT submitted, submitted_at, dry_run FROM ledger "
        "WHERE student_id='s1' AND lesson_id='l1'"
    ).fetchall()
    con.close()
    assert len(rows) == 1            # sentinel UPSERTed in place
    assert rows[0][0] == 1           # submitted=True for a real (non-dry) completion
    assert rows[0][1] is not None    # submitted_at stamped
    assert rows[0][2] == 0           # dry_run=False


def test_dry_run_completion_not_submitted(tmp_path):
    db = str(tmp_path / "t.sqlite")
    s = Store(db)
    s.init_schema()
    s.record_lesson_completion_intent("s1", "l1", "r1")
    s.record_lesson_completed("s1", "l1", "r1", dry_run=True)
    assert s.is_lesson_completed("s1", "l1") is True
    con = sqlite3.connect(db)
    row = con.execute(
        "SELECT submitted, submitted_at, dry_run FROM ledger "
        "WHERE student_id='s1' AND lesson_id='l1'"
    ).fetchone()
    con.close()
    assert row[0] == 0           # dry-run never submits
    assert row[1] is None
    assert row[2] == 1


def test_lesson_sentinel_isolated_from_exercise_rows(tmp_path):
    db = str(tmp_path / "t.sqlite")
    s = Store(db)
    s.init_schema()
    s.record_lesson_completion_intent("s1", "l1", "r1")
    # An exercise on the same lesson must not collide with the sentinel.
    assert s.is_exercise_attempted("s1", "l1", "e1") is False
    assert s.get_exercise_status("s1", "l1", LESSON_SENTINEL) == "in_progress"
