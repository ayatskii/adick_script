"""normalize_runner_event maps the runner's REAL raw events into the normalized
RunEvent shapes the frontend renders (progress + per-exercise outcomes)."""

from __future__ import annotations

from backend.jobs import normalize_runner_event


def test_progress_event_is_student_based():
    ev = normalize_runner_event(
        {"event": "progress", "students_total": 209, "students_done": 12}
    )
    assert ev["type"] == "progress"
    assert ev["data"]["students_done"] == 12
    assert ev["data"]["students"] == 209
    assert ev["data"]["current"] == 12 and ev["data"]["total"] == 209


def test_exercise_graded_maps_to_graded_with_score():
    ev = normalize_runner_event(
        {
            "event": "exercise", "status": "graded", "student_name": "Nurdana",
            "lesson_name": "Lesson 18", "exercise_no": "1.1", "type": "audio",
            "score": 4, "score_max": 5, "confidence": 0.9, "comment": "Good.",
        }
    )
    assert ev["type"] == "graded"
    assert ev["data"]["student_name"] == "Nurdana"
    assert ev["data"]["score"] == 4 and ev["data"]["score_max"] == 5
    assert "1.1" in ev["message"]


def test_exercise_flagged_maps_to_flagged():
    ev = normalize_runner_event(
        {"event": "exercise", "status": "flagged", "exercise_no": "1.2",
         "reason": "empty_answer"}
    )
    assert ev["type"] == "flagged"
    assert "empty_answer" in ev["message"]


def test_exercise_skipped_is_a_proposal():
    ev = normalize_runner_event(
        {"event": "exercise", "status": "skipped", "exercise_no": "1.3",
         "score": 5, "score_max": 5}
    )
    assert ev["type"] == "skipped"
    assert "review" in ev["message"].lower()


def test_student_event_uses_name():
    ev = normalize_runner_event(
        {"event": "student", "student_id": "3190603", "student_name": "Nurdana"}
    )
    assert ev["type"] == "student"
    assert "Nurdana" in ev["message"]
