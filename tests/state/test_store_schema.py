import sqlite3

from edvibe_bot.state.store import Store


def _store(tmp_path):
    s = Store(str(tmp_path / "t.sqlite"))
    s.init_schema()
    return s


def test_init_schema_creates_runs_ledger_audit(tmp_path):
    db = str(tmp_path / "t.sqlite")
    s = Store(db)
    s.init_schema()
    con = sqlite3.connect(db)
    names = {
        row[0]
        for row in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    con.close()
    assert {"runs", "ledger", "audit"}.issubset(names)
    # queue + settings are DEFERRED to the web-app plan
    assert "queue" not in names
    assert "settings" not in names


def test_init_schema_is_idempotent(tmp_path):
    s = _store(tmp_path)
    s.init_schema()  # second call must not raise


def test_create_run_returns_uuid4_hex(tmp_path):
    s = _store(tmp_path)
    run_id = s.create_run("dry_run", {"students": ["x"]})
    assert isinstance(run_id, str)
    assert len(run_id) == 32
    int(run_id, 16)  # hex


def test_create_run_persists_row(tmp_path):
    db = str(tmp_path / "t.sqlite")
    s = Store(db)
    s.init_schema()
    run_id = s.create_run("full_auto", {"max": 1})
    con = sqlite3.connect(db)
    row = con.execute(
        "SELECT mode, scope_json, status, finished_at FROM runs WHERE id=?",
        (run_id,),
    ).fetchone()
    con.close()
    assert row[0] == "full_auto"
    assert '"max": 1' in row[1]
    assert row[2] == "running"
    assert row[3] is None


def test_finish_run_updates_status_and_counts(tmp_path):
    db = str(tmp_path / "t.sqlite")
    s = Store(db)
    s.init_schema()
    run_id = s.create_run("dry_run", {})
    s.finish_run(run_id, "done", {"graded": 2, "flagged": 1})
    con = sqlite3.connect(db)
    row = con.execute(
        "SELECT status, counts_json, finished_at FROM runs WHERE id=?",
        (run_id,),
    ).fetchone()
    con.close()
    assert row[0] == "done"
    assert '"graded": 2' in row[1]
    assert row[2] is not None


def test_append_audit_inserts_row(tmp_path):
    db = str(tmp_path / "t.sqlite")
    s = Store(db)
    s.init_schema()
    run_id = s.create_run("dry_run", {})
    s.append_audit(run_id, "evaluate", '{"ex": "1"}', '{"score": 7}', "2026-06-16T00:00:00+00:00")
    con = sqlite3.connect(db)
    row = con.execute(
        "SELECT run_id, action, target_json, detail_json, ts FROM audit"
    ).fetchone()
    con.close()
    assert row == (run_id, "evaluate", '{"ex": "1"}', '{"score": 7}', "2026-06-16T00:00:00+00:00")
