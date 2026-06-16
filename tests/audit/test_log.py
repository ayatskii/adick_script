import json
import logging

from edvibe_bot.audit.log import AuditLog, get_logger


class FakeStore:
    def __init__(self):
        self.calls = []

    def append_audit(self, run_id, action, target_json, detail_json, ts):
        self.calls.append((run_id, action, target_json, detail_json, ts))


def test_get_logger_returns_named_logger():
    log = get_logger("edvibe_bot.test")
    assert isinstance(log, logging.Logger)
    assert log.name == "edvibe_bot.test"


def test_record_appends_one_jsonl_line_and_calls_store(tmp_path):
    store = FakeStore()
    jsonl = tmp_path / "nested" / "audit.jsonl"   # parent dir does not exist yet
    audit = AuditLog(store, str(jsonl))
    audit.record("run1", "evaluate", {"ex": "e1"}, {"score": 7, "dry_run": True})

    assert len(store.calls) == 1
    run_id, action, target_json, detail_json, ts = store.calls[0]
    assert run_id == "run1"
    assert action == "evaluate"
    assert json.loads(target_json) == {"ex": "e1"}
    assert json.loads(detail_json) == {"score": 7, "dry_run": True}
    assert ts.endswith("+00:00")  # UTC isoformat

    lines = jsonl.read_text().splitlines()
    assert len(lines) == 1
    rec = json.loads(lines[0])
    assert rec["run_id"] == "run1"
    assert rec["action"] == "evaluate"
    assert rec["target"] == {"ex": "e1"}
    assert rec["detail"] == {"score": 7, "dry_run": True}
    assert rec["ts"] == ts


def test_record_twice_appends_second_line(tmp_path):
    store = FakeStore()
    jsonl = tmp_path / "audit.jsonl"
    audit = AuditLog(store, str(jsonl))
    audit.record("run1", "submit", {"ex": "e1"}, {"dry_run": False})
    audit.record("run1", "complete", {"lesson": "l1"}, {"dry_run": False})

    assert len(store.calls) == 2
    lines = jsonl.read_text().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["action"] == "submit"
    assert json.loads(lines[1])["action"] == "complete"
