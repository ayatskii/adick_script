"""Data endpoints return verbatim seed data on an empty store, and accept
queue decisions / settings PUT."""

from __future__ import annotations


def test_students_seed_fallback(client):
    rows = client.get("/api/students").json()
    assert len(rows) == 12
    assert rows[0]["name"] == "Анель"
    assert rows[0]["lessons"][0]["name"] == "Lesson 14 — Entertainment"


def test_queue_seed_fallback(client):
    rows = client.get("/api/queue").json()
    assert len(rows) == 6
    assert rows[0]["id"] == "r1"
    assert rows[0]["type"] == "audio"
    assert rows[0]["score"] == 7


def test_flagged_seed_fallback(client):
    rows = client.get("/api/flagged").json()
    assert len(rows) == 5
    assert rows[0]["reason"] == "Low confidence"


def test_reconcile_seed_fallback(client):
    rows = client.get("/api/reconcile").json()
    assert len(rows) == 4
    assert rows[2]["flagStatus"] == "flagged"


def test_runs_seed_fallback(client):
    rows = client.get("/api/runs").json()
    # Seed runs (5) appear when no real/in-memory run exists.
    assert len(rows) == 5
    ids = {r["id"] for r in rows}
    assert {"h1", "h2", "h3", "h4", "h5"} <= ids
    h1 = next(r for r in rows if r["id"] == "h1")
    assert h1["counts"]["graded"] == 14


def test_settings_get_masks_secrets(client):
    s = client.get("/api/settings").json()
    assert s["marathon"] == "Pre-IELTS"
    assert "•" in s["edvibePassword"]
    assert not s["openaiApiKey"].startswith("sk-proj")


def test_settings_put_overlay_and_secret_strip(client):
    out = client.put(
        "/api/settings",
        json={"marathon": "IELTS-Advanced", "openaiApiKey": "sk-leak"},
    ).json()
    assert out["marathon"] == "IELTS-Advanced"
    # Secret must not be persisted.
    assert out["openaiApiKey"] != "sk-leak"


def test_queue_decision_and_submit(client):
    dec = client.post(
        "/api/queue/r1/decision",
        json={"decision": "edited", "score": 8, "comment": "tweaked"},
    )
    assert dec.status_code == 200
    assert dec.json()["ok"] is True

    # The decision reflects in the queue listing.
    rows = client.get("/api/queue").json()
    r1 = next(r for r in rows if r["id"] == "r1")
    assert r1["status"] == "approved"
    assert r1["edited"] is True
    assert r1["score"] == 8

    submit = client.post("/api/queue/submit")
    assert submit.status_code == 200
    assert submit.json()["submitted"] >= 1


def test_audit_seed_fallback_empty(client):
    rows = client.get("/api/audit").json()
    assert rows == []
