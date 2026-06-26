"""The runner must ABORT loudly when the evaluator is unavailable (OpenAI quota
exhausted / bad key) instead of grinding through the roster flagging every
exercise as a vague parse_failed. Drives runner.run with the browser + scraper +
evaluator faked out, so no network/Playwright/OpenAI is touched."""
from __future__ import annotations

import contextlib
import sqlite3

import edvibe_bot.runner as runner
from edvibe_bot.config import Settings
from edvibe_bot.errors import EvaluatorUnavailable
from edvibe_bot.runner import RunConfig, run
from edvibe_bot.scraper.dashboard import Student
from edvibe_bot.scraper.progress import Lesson
from edvibe_bot.scraper.lesson import Exercise
from edvibe_bot.evaluator.schema import ExerciseType
from edvibe_bot.state.store import Store, LedgerEntry, LedgerStatus, LESSON_SENTINEL


class _FakePage:
    url = "https://edvibe.com/cabinet/school/marathons/marathon/110326/lesson/9?pupil=s1"

    def screenshot(self, *a, **k):  # pragma: no cover - error path not hit here
        pass


def _settings() -> Settings:
    return Settings(edvibe_login="x", edvibe_password="y", openai_api_key="sk-test")


def _run_status(db: str, run_id: str) -> str:
    con = sqlite3.connect(db)
    try:
        row = con.execute("SELECT status FROM runs WHERE id=?", (run_id,)).fetchone()
        return row[0] if row else ""
    finally:
        con.close()


def _answered_text_exercise() -> Exercise:
    return Exercise(
        section="Writing",
        number="1.1",
        type=ExerciseType.TEXT,
        prompt_text="Describe your weekend.",
        has_grade_button=True,
        audio_url=None,
        answer_text="I went to the park and played football with my friends.",
        element_id="9:s0:1.1",
        score_max=5,
        is_graded=False,
        section_index=0,
    )


def _patch_pipeline(monkeypatch, *, evaluate):
    """Fake every browser/scraper boundary so run() reaches the evaluate call."""
    page = _FakePage()

    @contextlib.contextmanager
    def _ctx(headed, storage_state_path=None):
        yield object()  # browser context (only used for AUDIO downloads)

    monkeypatch.setattr(runner, "_launch_context", _ctx)
    monkeypatch.setattr(runner, "ensure_logged_in", lambda ctx, settings: page)
    monkeypatch.setattr(runner, "open_marathon", lambda page, settings: None)
    monkeypatch.setattr(
        runner, "list_students", lambda page: [Student(id="s1", name="Alice", email="a@e.com")]
    )
    monkeypatch.setattr(runner, "open_progress", lambda page, student, url: None)
    monkeypatch.setattr(
        runner, "list_lessons",
        lambda page: [Lesson(id="9", name="Lesson 9: X", status="awaiting", number="9")],
    )
    monkeypatch.setattr(runner, "awaiting_lessons", lambda lessons: lessons)
    monkeypatch.setattr(runner, "open_lesson", lambda page, lesson: None)
    monkeypatch.setattr(
        runner, "gather_exercises",
        lambda page, base, lid: [_answered_text_exercise()],
    )
    monkeypatch.setattr(runner, "goto_section", lambda page, base, idx: None)
    monkeypatch.setattr(runner.poster, "is_already_graded", lambda page, ex: False)
    monkeypatch.setattr(runner.poster, "open_grade_modal", lambda page, ex: 5)
    monkeypatch.setattr(runner.poster, "cancel_grade_modal", lambda page: None)
    monkeypatch.setattr(runner.poster, "submit_grade", lambda *a, **k: None)
    monkeypatch.setattr(runner.poster, "complete_lesson", lambda *a, **k: None)
    monkeypatch.setattr(runner.text, "evaluate", evaluate)
    return page


def _blank_text_exercise(number="1.2", element_id="9:s0:1.2") -> Exercise:
    """A manual-check exercise the student left blank (answer_text empty)."""
    return Exercise(
        section="Writing", number=number, type=ExerciseType.TEXT,
        prompt_text="Describe your weekend.", has_grade_button=True,
        audio_url=None, answer_text=None, element_id=element_id,
        score_max=5, is_graded=False, section_index=0,
    )


def test_run_aborts_on_evaluator_unavailable(tmp_path, monkeypatch):
    db = str(tmp_path / "t.sqlite")
    store = Store(db)
    store.init_schema()

    def _boom(req, settings):
        raise EvaluatorUnavailable("OpenAI evaluation unavailable — quota exhausted.")

    _patch_pipeline(monkeypatch, evaluate=_boom)

    events: list[dict] = []
    config = RunConfig(mode="full_auto", confidence_threshold=0.6)
    report = run(config, _settings(), store, on_event=events.append)

    # The run STOPS at the first failed evaluation — nothing graded, no avalanche
    # of parse_failed flags.
    assert report.graded == 0
    assert report.flagged == 0

    # A prominent, fatal run-level error is emitted (not a buried per-lesson log).
    fatal = [e for e in events if e.get("event") == "run_error" and e.get("fatal")]
    assert len(fatal) == 1
    assert "quota" in fatal[0]["message"].lower()

    # The run is finalized as 'error' in the store, not left running or "done".
    assert _run_status(db, report.run_id) == "error"


def test_run_completes_normally_when_evaluator_ok(tmp_path, monkeypatch):
    """Sanity: with a working evaluator the same pipeline grades and finishes."""
    from edvibe_bot.evaluator.schema import Evaluation

    db = str(tmp_path / "ok.sqlite")
    store = Store(db)
    store.init_schema()

    def _ok(req, settings):
        return Evaluation(score=4, comment="Nice.", rationale="ok", confidence=0.9, score_max=5)

    _patch_pipeline(monkeypatch, evaluate=_ok)

    events: list[dict] = []
    report = run(RunConfig(mode="full_auto", confidence_threshold=0.6), _settings(), store, events.append)

    assert report.graded == 1
    assert not [e for e in events if e.get("event") == "run_error"]
    assert _run_status(db, report.run_id) == "done"


def _seed_lesson_sentinel(store: Store, status: str) -> None:
    """Pre-write a __lesson__ sentinel row for student s1 / lesson 9."""
    store.record_exercise(
        LedgerEntry(
            student_id="s1", lesson_id="9", exercise_id=LESSON_SENTINEL,
            student_name="", lesson_name="", exercise_no="", type="",
            proposed_score=None, proposed_comment=None, confidence=None,
            submitted=False, dry_run=False, run_id="old", status=status,
        )
    )


def _ok_eval(req, settings):
    from edvibe_bot.evaluator.schema import Evaluation
    return Evaluation(score=4, comment="Nice.", rationale="ok", confidence=0.9, score_max=5)


def test_error_sentinel_lesson_is_retried_not_skipped(tmp_path, monkeypatch):
    # A lesson left in 'error' by a prior (e.g. quota-broken / nav-timeout) run must
    # be RE-ATTEMPTED so its answered work gets graded — not flagged-and-skipped.
    db = str(tmp_path / "err.sqlite")
    store = Store(db)
    store.init_schema()
    _seed_lesson_sentinel(store, LedgerStatus.ERROR.value)

    _patch_pipeline(monkeypatch, evaluate=_ok_eval)
    events: list[dict] = []
    report = run(RunConfig(mode="full_auto", confidence_threshold=0.6), _settings(), store, events.append)

    assert report.graded == 1                                     # retried + graded
    assert not [e for e in events if e.get("event") == "lesson_flag"]  # not skipped


def test_in_progress_sentinel_lesson_is_still_skipped(tmp_path, monkeypatch):
    # An INTERRUPTED completion (mid 'Завершить урок') stays unsafe to retry — flag it.
    db = str(tmp_path / "inprog.sqlite")
    store = Store(db)
    store.init_schema()
    _seed_lesson_sentinel(store, LedgerStatus.IN_PROGRESS.value)

    _patch_pipeline(monkeypatch, evaluate=_ok_eval)
    events: list[dict] = []
    report = run(RunConfig(mode="full_auto", confidence_threshold=0.6), _settings(), store, events.append)

    assert report.graded == 0
    assert [e for e in events if e.get("event") == "lesson_flag"]


def test_lesson_completes_when_answered_tasks_graded_despite_blanks(tmp_path, monkeypatch):
    # A lesson with one answered (graded) task + one BLANK (unanswered) task must
    # still be completed: the blank is not ungraded manual-check work.
    db = str(tmp_path / "complete.sqlite")
    store = Store(db)
    store.init_schema()
    _patch_pipeline(monkeypatch, evaluate=_ok_eval)
    monkeypatch.setattr(
        runner, "gather_exercises",
        lambda page, base, lid: [_answered_text_exercise(), _blank_text_exercise()],
    )
    events: list[dict] = []
    report = run(RunConfig(mode="full_auto", confidence_threshold=0.6), _settings(), store, events.append)

    assert report.graded == 1            # the answered task
    assert report.flagged == 1           # the blank (empty_answer) task
    assert report.completed_lessons == 1  # finished despite the blank
    assert [e for e in events if e.get("event") == "lesson_complete"]


def test_lesson_not_completed_when_a_real_answer_is_ungraded(tmp_path, monkeypatch):
    # A real answer the bot couldn't confidently grade (low confidence) is genuine
    # ungraded manual-check work — it MUST still block completion for human review.
    db = str(tmp_path / "block.sqlite")
    store = Store(db)
    store.init_schema()

    def _eval_by_answer(req, settings):
        from edvibe_bot.evaluator.schema import Evaluation
        conf = 0.9 if "park" in (req.student_answer or "") else 0.3   # low for the 2nd
        return Evaluation(score=4, comment="x", rationale="ok", confidence=conf, score_max=5)

    other = Exercise(
        section="Writing", number="1.3", type=ExerciseType.TEXT,
        prompt_text="Describe your hobby.", has_grade_button=True, audio_url=None,
        answer_text="I really enjoy reading books in the evening.", element_id="9:s0:1.3",
        score_max=5, is_graded=False, section_index=0,
    )
    _patch_pipeline(monkeypatch, evaluate=_eval_by_answer)
    monkeypatch.setattr(
        runner, "gather_exercises",
        lambda page, base, lid: [_answered_text_exercise(), other],
    )
    events: list[dict] = []
    report = run(RunConfig(mode="full_auto", confidence_threshold=0.6), _settings(), store, events.append)

    assert report.graded == 1             # the 'park' answer
    assert report.flagged == 1            # the low-confidence answer
    assert report.completed_lessons == 0  # blocked: a real answer is still ungraded


def test_ai_full_control_grades_low_confidence_without_review(tmp_path, monkeypatch):
    # With --no-human-review the AI grades EVERY answered exercise regardless of
    # confidence — nothing is flagged for review — and the lesson completes.
    db = str(tmp_path / "ai.sqlite")
    store = Store(db)
    store.init_schema()

    def _low(req, settings):
        from edvibe_bot.evaluator.schema import Evaluation
        return Evaluation(score=3, comment="ok", rationale="r", confidence=0.2, score_max=5)

    _patch_pipeline(monkeypatch, evaluate=_low)
    report = run(
        RunConfig(mode="full_auto", confidence_threshold=0.6, ai_full_control=True),
        _settings(), store, lambda e: None,
    )
    assert report.graded == 1             # graded despite confidence 0.2 < 0.6
    assert report.flagged == 0            # nothing held back for review
    assert report.completed_lessons == 1
