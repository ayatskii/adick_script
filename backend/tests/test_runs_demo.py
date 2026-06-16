"""A full demo run driven through the WebSocket stream."""

from __future__ import annotations


def test_demo_run_streams_to_completion(client):
    # Start a demo run.
    resp = client.post("/api/runs", json={"mode": "demo", "scope": {"all": True}})
    assert resp.status_code == 200
    run_id = resp.json()["run_id"]
    assert resp.json()["status"] == "running"

    # The run should be listed.
    runs = client.get("/api/runs").json()
    assert any(r["id"] == run_id for r in runs)

    # Connect to the WS stream and collect events until run_complete.
    types: list[str] = []
    saw_complete = False
    with client.websocket_connect(f"/api/runs/{run_id}/stream") as ws:
        for _ in range(500):  # safety bound
            ev = ws.receive_json()
            types.append(ev["type"])
            assert "ts" in ev
            if ev["type"] == "run_complete":
                saw_complete = True
                assert "counts" in ev["data"]
                break

    assert saw_complete, f"never saw run_complete; got {types}"
    # Realistic sequence: a run start, students, exercises, mixed outcomes.
    assert types[0] == "run_started"
    assert "student" in types
    assert "exercise" in types
    assert "graded" in types
    assert "flagged" in types
    assert "skipped" in types
    assert "progress" in types
    assert "log" in types
    assert "lesson_complete" in types

    # After completion the run detail reports a finished run.
    detail = client.get(f"/api/runs/{run_id}").json()
    assert detail["run"]["id"] == run_id
    assert detail["run"]["counts"]["graded"] >= 1


def test_demo_run_can_be_stopped(client):
    resp = client.post("/api/runs", json={"mode": "demo", "scope": {"all": True}})
    run_id = resp.json()["run_id"]

    stop = client.post(f"/api/runs/{run_id}/stop")
    assert stop.status_code == 200
    assert stop.json()["ok"] is True

    # Stream still terminates cleanly with run_complete.
    with client.websocket_connect(f"/api/runs/{run_id}/stream") as ws:
        saw_complete = False
        for _ in range(500):
            ev = ws.receive_json()
            if ev["type"] == "run_complete":
                saw_complete = True
                break
    assert saw_complete


def test_stop_unknown_run(client):
    resp = client.post("/api/runs/nope/stop")
    assert resp.status_code == 200
    assert resp.json()["ok"] is False
