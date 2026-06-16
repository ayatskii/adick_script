import sqlite3

from edvibe_bot.state.store import LedgerEntry, Store


def _store(tmp_path):
    s = Store(str(tmp_path / "t.sqlite"))
    s.init_schema()
    return s


def _entry(status, *, submitted=False, score=7, run_id="r1"):
    return LedgerEntry(
        student_id="s1",
        lesson_id="l1",
        exercise_id="e1",
        student_name="Anel",
        lesson_name="Lesson 14",
        exercise_no="3",
        type="audio",
        proposed_score=score,
        proposed_comment="Good work",
        confidence=0.9,
        submitted=submitted,
        dry_run=not submitted,
        run_id=run_id,
        status=status,
    )


def test_record_graded_is_done(tmp_path):
    s = _store(tmp_path)
    s.record_exercise(_entry("graded"))
    assert s.get_exercise_status("s1", "l1", "e1") == "graded"
    assert s.is_exercise_done("s1", "l1", "e1") is True
    assert s.is_exercise_attempted("s1", "l1", "e1") is True


def test_record_in_progress_attempted_but_not_done(tmp_path):
    s = _store(tmp_path)
    s.record_exercise(_entry("in_progress"))
    assert s.is_exercise_attempted("s1", "l1", "e1") is True
    assert s.is_exercise_done("s1", "l1", "e1") is False


def test_record_flagged_not_done(tmp_path):
    s = _store(tmp_path)
    s.record_exercise(_entry("flagged"))
    assert s.is_exercise_done("s1", "l1", "e1") is False
    assert s.is_exercise_attempted("s1", "l1", "e1") is True


def test_missing_exercise_status_and_flags(tmp_path):
    s = _store(tmp_path)
    assert s.get_exercise_status("s1", "l1", "nope") is None
    assert s.is_exercise_done("s1", "l1", "nope") is False
    assert s.is_exercise_attempted("s1", "l1", "nope") is False


def test_submitted_true_stamps_submitted_at(tmp_path):
    db = str(tmp_path / "t.sqlite")
    s = Store(db)
    s.init_schema()
    s.record_exercise(_entry("graded", submitted=True))
    con = sqlite3.connect(db)
    row = con.execute(
        "SELECT submitted, submitted_at FROM ledger WHERE exercise_id='e1'"
    ).fetchone()
    con.close()
    assert row[0] == 1
    assert row[1] is not None


def test_submitted_false_leaves_submitted_at_null(tmp_path):
    db = str(tmp_path / "t.sqlite")
    s = Store(db)
    s.init_schema()
    s.record_exercise(_entry("flagged", submitted=False))
    con = sqlite3.connect(db)
    row = con.execute(
        "SELECT submitted, submitted_at FROM ledger WHERE exercise_id='e1'"
    ).fetchone()
    con.close()
    assert row[0] == 0
    assert row[1] is None


def test_upsert_replaces_in_place_no_duplicate_rows(tmp_path):
    db = str(tmp_path / "t.sqlite")
    s = Store(db)
    s.init_schema()
    s.record_exercise(_entry("in_progress", submitted=False, run_id="r1"))
    s.record_exercise(_entry("graded", submitted=True, score=9, run_id="r2"))
    con = sqlite3.connect(db)
    rows = con.execute(
        "SELECT proposed_score, status, run_id, submitted FROM ledger "
        "WHERE student_id='s1' AND lesson_id='l1' AND exercise_id='e1'"
    ).fetchall()
    con.close()
    assert len(rows) == 1
    assert rows[0] == (9, "graded", "r2", 1)
