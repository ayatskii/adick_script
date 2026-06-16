"""Health endpoint: 200 + shape, reflecting selectors.py CONFIRM state and
the OpenAI key presence."""

from __future__ import annotations


def test_health_ok(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert set(body) >= {"ok", "phase0_done", "openai_key_set"}
    assert isinstance(body["phase0_done"], bool)
    assert isinstance(body["openai_key_set"], bool)


def test_health_phase0_reflects_selectors():
    # selectors.py currently still contains "# CONFIRM" markers (pre-Phase 0),
    # so phase0_done must be False.
    from backend.app import phase0_done

    assert phase0_done() is False
