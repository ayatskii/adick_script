import pytest

import edvibe_bot.runner as runner_mod
from edvibe_bot.runner import run, RunConfig, RunReport
from edvibe_bot.config import Settings
from edvibe_bot.evaluator.schema import Evaluation, ExerciseType
from edvibe_bot.scraper.dashboard import Student
from edvibe_bot.scraper.progress import Lesson
from edvibe_bot.scraper.lesson import Exercise
from edvibe_bot.errors import SelectorError
from edvibe_bot.state.store import LedgerStatus


# ---- fakes -------------------------------------------------------------

class FakeStore:
    def __init__(self):
        self.run_id = "run-fake"
        self.finished = None
        self.recorded = []                 # list of LedgerEntry
        self.lesson_intents = []           # (student_id, lesson_id, run_id)
        self.lesson_completed = []         # (student_id, lesson_id, run_id, dry_run)
        self.audit_rows = []
        self._exercise_status = {}         # (s, l, e) -> status
        self._lesson_status = {}           # (s, l) -> status

    # seams used by AuditLog
    def append_audit(self, run_id, action, target_json, detail_json, ts):
        self.audit_rows.append((run_id, action, target_json, detail_json, ts))

    def create_run(self, mode, scope):
        return self.run_id

    def finish_run(self, run_id, status, counts):
        self.finished = (run_id, status, counts)

    def record_exercise(self, entry):
        self.recorded.append(entry)
        self._exercise_status[
            (entry.student_id, entry.lesson_id, entry.exercise_id)
        ] = entry.status

    def get_exercise_status(self, s, l, e):
        return self._exercise_status.get((s, l, e))

    def is_exercise_done(self, s, l, e):
        return self._exercise_status.get((s, l, e)) in ("graded", "completed")

    def is_exercise_attempted(self, s, l, e):
        return (s, l, e) in self._exercise_status

    def record_lesson_completion_intent(self, s, l, run_id):
        self.lesson_intents.append((s, l, run_id))
        self._lesson_status[(s, l)] = "in_progress"

    def record_lesson_completed(self, s, l, run_id, dry_run):
        self.lesson_completed.append((s, l, run_id, dry_run))
        self._lesson_status[(s, l)] = "completed"

    def get_lesson_status(self, s, l):
        return self._lesson_status.get((s, l))

    def is_lesson_completed(self, s, l):
        return self._lesson_status.get((s, l)) == "completed"

    def is_lesson_completion_attempted(self, s, l):
        return (s, l) in self._lesson_status


class FakePage:
    def __init__(self):
        self.shots = []
        self.url = "https://edvibe.com/marathon/1/lesson/1?pupil=1&section=0"

    def screenshot(self, path):
        self.shots.append(path)


class RecordingPoster:
    """Models the split grade flow: open_grade_modal (read max) → submit_grade /
    cancel_grade_modal. Pairs submit with the last-opened exercise so grade_calls
    still records (element_id, score, dry_run)."""

    def __init__(self, *, already_graded=None, modal_max=None):
        self.grade_calls = []       # (element_id, score, dry_run)
        self.complete_calls = []    # dry_run
        self.cancel_calls = []      # element_id
        self._already = set(already_graded or [])
        self._modal_max = modal_max or {}   # element_id -> max
        self._last_ex = None

    def is_already_graded(self, page, exercise):
        return exercise.element_id in self._already

    def open_grade_modal(self, page, exercise):
        self._last_ex = exercise
        return self._modal_max.get(exercise.element_id)

    def submit_grade(self, page, evaluation, settings):
        # dry_run never opens the modal, so every submit is a real post.
        self.grade_calls.append((self._last_ex.element_id, evaluation.score, False))

    def cancel_grade_modal(self, page):
        self.cancel_calls.append(self._last_ex.element_id if self._last_ex else None)

    def complete_lesson(self, page, dry_run):
        self.complete_calls.append(dry_run)


def _settings():
    return Settings(
        edvibe_login="u",
        edvibe_password="p",
        openai_api_key="k",
        confidence_threshold=0.6,
        pacing_seconds=0.0,
    )


def _wire(monkeypatch, *, exercises, poster,
          evaluation=None, transcribe=None, download=b"AUDIO",
          students=None, lessons=None):
    """Monkeypatch all collaborators the runner imports."""
    students = students if students is not None else [Student(id="s1", name="Al")]
    lessons = lessons if lessons is not None else [
        Lesson(id="l1", name="Lesson 1", status="awaiting")
    ]
    evaluation = evaluation or Evaluation(
        score=8, comment="Nice.", rationale="ok", confidence=0.9
    )

    page = FakePage()
    monkeypatch.setattr(runner_mod, "ensure_logged_in", lambda ctx, s: page)
    monkeypatch.setattr(runner_mod, "open_marathon", lambda p, s: None)
    monkeypatch.setattr(runner_mod, "list_students", lambda p: students)
    monkeypatch.setattr(runner_mod, "open_progress", lambda p, st, url=None: None)
    monkeypatch.setattr(runner_mod, "list_lessons", lambda p: lessons)
    monkeypatch.setattr(
        runner_mod, "awaiting_lessons",
        lambda ls: [x for x in ls if x.status == "awaiting"],
    )
    monkeypatch.setattr(runner_mod, "open_lesson", lambda p, le: None)
    monkeypatch.setattr(
        runner_mod, "gather_exercises", lambda p, url=None, lid=None: exercises
    )
    monkeypatch.setattr(runner_mod, "goto_section", lambda p, url, idx: None)

    def _dl(ctx, url):
        return download
    monkeypatch.setattr(runner_mod.audio, "download_audio", _dl)

    def _tr(blob, s):
        if transcribe is not None:
            return transcribe(blob, s)
        return "transcript text"
    monkeypatch.setattr(runner_mod.audio, "transcribe", _tr)

    monkeypatch.setattr(runner_mod.text, "evaluate", lambda req, s: evaluation)

    monkeypatch.setattr(runner_mod.poster, "is_already_graded", poster.is_already_graded)
    monkeypatch.setattr(runner_mod.poster, "open_grade_modal", poster.open_grade_modal)
    monkeypatch.setattr(runner_mod.poster, "submit_grade", poster.submit_grade)
    monkeypatch.setattr(runner_mod.poster, "cancel_grade_modal", poster.cancel_grade_modal)
    monkeypatch.setattr(runner_mod.poster, "complete_lesson", poster.complete_lesson)

    # silence the real browser launch
    monkeypatch.setattr(
        runner_mod, "_launch_context",
        lambda headed: _FakeCM(),
    )
    return page


class _FakeContext:
    pass


class _FakeCM:
    def __enter__(self):
        return _FakeContext()

    def __exit__(self, *a):
        return False


def _text_exercise(element_id="ex-1", answer="My answer is long enough."):
    return Exercise(
        section="Writing", number="1", type=ExerciseType.TEXT,
        prompt_text="Write something.", has_grade_button=True,
        audio_url=None, answer_text=answer, element_id=element_id,
    )


def _audio_exercise(element_id="ex-a", url="http://a/x.mp3"):
    return Exercise(
        section="Speaking", number="2", type=ExerciseType.AUDIO,
        prompt_text="Speak.", has_grade_button=True,
        audio_url=url, answer_text=None, element_id=element_id,
    )


def _auto_exercise():
    return Exercise(
        section="Grammar", number="9", type=ExerciseType.AUTO_CHECKED,
        prompt_text="Auto.", has_grade_button=False,
        audio_url=None, answer_text="x", element_id="ex-auto",
    )


def _statuses(recorded):
    return [(e.exercise_id, e.status) for e in recorded]


# ---- tests -------------------------------------------------------------

def test_full_auto_grades_and_completes(monkeypatch):
    store = FakeStore()
    poster = RecordingPoster()
    _wire(monkeypatch, exercises=[_text_exercise()], poster=poster)
    report = run(RunConfig(mode="full_auto"), _settings(), store)
    assert report.graded == 1
    assert poster.grade_calls == [("ex-1", 8, False)]
    assert poster.complete_calls == [False]
    assert report.completed_lessons == 1
    # in_progress claim written BEFORE the terminal graded row
    statuses = [e.status for e in store.recorded if e.exercise_id == "ex-1"]
    assert statuses[0] == LedgerStatus.IN_PROGRESS.value
    assert statuses[-1] == LedgerStatus.GRADED.value
    # audit fired for evaluate, grade, complete_lesson
    actions = [r[1] for r in store.audit_rows]
    assert "evaluate" in actions and "grade" in actions
    assert "complete_lesson" in actions


def test_already_graded_on_platform_is_skipped_not_regraded(monkeypatch):
    # Defense-in-depth for the estimate-view render lag: if the exercise turns out
    # already graded when we reach its section, skip it — never re-grade.
    store = FakeStore()
    poster = RecordingPoster(already_graded={"ex-1"})
    _wire(monkeypatch, exercises=[_text_exercise()], poster=poster)
    report = run(RunConfig(mode="full_auto"), _settings(), store)
    assert poster.grade_calls == []            # never submitted
    assert report.graded == 0
    assert report.skipped == 1
    assert report.completed_lessons == 0       # nothing graded → no completion
    assert any(
        e.exercise_id == "ex-1" and e.status == LedgerStatus.SKIPPED.value
        for e in store.recorded
    )
    skip_audits = [r for r in store.audit_rows if r[1] == "skip"]
    assert skip_audits and any("already_graded" in str(r[3]) for r in skip_audits)


def test_dry_run_submits_nothing(monkeypatch):
    store = FakeStore()
    poster = RecordingPoster()
    _wire(monkeypatch, exercises=[_text_exercise()], poster=poster)
    report = run(RunConfig(mode="dry_run"), _settings(), store)
    assert poster.grade_calls == []          # never even called the poster
    assert poster.complete_calls == []
    assert report.graded == 0
    assert report.completed_lessons == 0
    assert store.lesson_completed == []


def test_review_submits_nothing(monkeypatch):
    store = FakeStore()
    poster = RecordingPoster()
    _wire(monkeypatch, exercises=[_text_exercise()], poster=poster)
    report = run(RunConfig(mode="review"), _settings(), store)
    assert poster.grade_calls == []
    assert poster.complete_calls == []
    assert report.completed_lessons == 0


def test_low_confidence_flagged_not_graded_and_no_completion(monkeypatch):
    store = FakeStore()
    poster = RecordingPoster()
    low = Evaluation(score=5, comment="meh", rationale="ok", confidence=0.2)
    _wire(monkeypatch, exercises=[_text_exercise()], poster=poster, evaluation=low)
    report = run(RunConfig(mode="full_auto"), _settings(), store)
    assert poster.grade_calls == []
    assert report.graded == 0
    assert report.flagged == 1
    assert poster.complete_calls == []
    assert ("ex-1", LedgerStatus.FLAGGED.value) in _statuses(store.recorded)


def test_parse_failed_flagged_even_with_threshold_zero(monkeypatch):
    store = FakeStore()
    poster = RecordingPoster()
    pf = Evaluation(score=0, comment="", rationale="parse_failed", confidence=0.0)
    _wire(monkeypatch, exercises=[_text_exercise()], poster=poster, evaluation=pf)
    cfg = RunConfig(mode="full_auto", confidence_threshold=0.0)
    report = run(cfg, _settings(), store)
    assert poster.grade_calls == []
    assert report.graded == 0
    assert report.flagged == 1
    assert poster.complete_calls == []


def test_empty_answer_flagged_not_graded(monkeypatch):
    store = FakeStore()
    poster = RecordingPoster()
    _wire(
        monkeypatch,
        exercises=[_text_exercise(answer="   ")],
        poster=poster,
    )
    report = run(RunConfig(mode="full_auto"), _settings(), store)
    assert poster.grade_calls == []
    assert report.flagged == 1
    assert report.graded == 0


def test_missing_element_id_flagged_not_graded(monkeypatch):
    store = FakeStore()
    poster = RecordingPoster()
    ex = _text_exercise()
    ex.element_id = None
    _wire(monkeypatch, exercises=[ex], poster=poster)
    report = run(RunConfig(mode="full_auto"), _settings(), store)
    assert poster.grade_calls == []
    assert report.flagged == 1
    assert report.graded == 0
    assert poster.complete_calls == []
    assert any(
        e.status == LedgerStatus.FLAGGED.value and e.proposed_comment == "no_stable_id"
        for e in store.recorded
    )


def test_preexisting_in_progress_exercise_skipped_flagged_blocked(monkeypatch):
    store = FakeStore()
    poster = RecordingPoster()
    store._exercise_status[("s1", "l1", "ex-1")] = "in_progress"
    _wire(monkeypatch, exercises=[_text_exercise()], poster=poster)
    report = run(RunConfig(mode="full_auto"), _settings(), store)
    assert poster.grade_calls == []
    assert report.flagged == 1
    assert report.graded == 0
    assert poster.complete_calls == []      # blocked → no completion


def test_lesson_sentinel_in_progress_not_recompleted(monkeypatch):
    store = FakeStore()
    poster = RecordingPoster()
    store._lesson_status[("s1", "l1")] = "in_progress"
    _wire(monkeypatch, exercises=[_text_exercise()], poster=poster)
    report = run(RunConfig(mode="full_auto"), _settings(), store)
    assert poster.grade_calls == []          # lesson skipped entirely
    assert poster.complete_calls == []
    assert report.flagged == 1               # lesson flagged for human verify


def test_already_completed_lesson_skipped(monkeypatch):
    store = FakeStore()
    poster = RecordingPoster()
    store._lesson_status[("s1", "l1")] = "completed"
    _wire(monkeypatch, exercises=[_text_exercise()], poster=poster)
    report = run(RunConfig(mode="full_auto"), _settings(), store)
    assert poster.grade_calls == []
    assert poster.complete_calls == []


def test_zero_manual_exercises_lesson_not_completed(monkeypatch):
    store = FakeStore()
    poster = RecordingPoster()
    _wire(monkeypatch, exercises=[_auto_exercise()], poster=poster)
    report = run(RunConfig(mode="full_auto"), _settings(), store)
    assert poster.grade_calls == []
    assert poster.complete_calls == []       # NEVER complete a zero-manual lesson
    assert report.completed_lessons == 0


def test_flagged_exercise_blocks_completion(monkeypatch):
    store = FakeStore()
    poster = RecordingPoster()
    good = _text_exercise(element_id="ex-good")
    bad = _text_exercise(element_id="ex-bad", answer="  ")  # empty → flagged
    _wire(monkeypatch, exercises=[good, bad], poster=poster)
    report = run(RunConfig(mode="full_auto"), _settings(), store)
    assert ("ex-good", 8, False) in poster.grade_calls   # one graded
    assert report.graded == 1
    assert report.flagged == 1
    assert poster.complete_calls == []                   # blocked by flag


def test_audio_download_none_flagged(monkeypatch):
    store = FakeStore()
    poster = RecordingPoster()
    _wire(
        monkeypatch, exercises=[_audio_exercise()], poster=poster, download=None,
    )
    report = run(RunConfig(mode="full_auto"), _settings(), store)
    assert poster.grade_calls == []
    assert report.flagged == 1
    assert poster.complete_calls == []


def test_transcription_failure_flagged(monkeypatch):
    store = FakeStore()
    poster = RecordingPoster()

    def _boom(blob, s):
        raise RuntimeError("both models failed")

    _wire(
        monkeypatch, exercises=[_audio_exercise()], poster=poster,
        transcribe=_boom,
    )
    report = run(RunConfig(mode="full_auto"), _settings(), store)
    assert poster.grade_calls == []
    assert report.flagged == 1


def test_selector_error_screenshots_and_continues(monkeypatch):
    store = FakeStore()
    poster = RecordingPoster()
    lessons = [
        Lesson(id="l1", name="L1", status="awaiting"),
        Lesson(id="l2", name="L2", status="awaiting"),
    ]
    page = _wire(
        monkeypatch, exercises=[_text_exercise()], poster=poster, lessons=lessons,
    )

    calls = {"n": 0}

    def _le(p, url=None, lid=None):
        calls["n"] += 1
        if calls["n"] == 1:
            raise SelectorError("boom on first lesson")
        return [_text_exercise(element_id="ex-2")]

    monkeypatch.setattr(runner_mod, "gather_exercises", _le)
    report = run(RunConfig(mode="full_auto"), _settings(), store)
    assert report.errors == 1
    assert page.shots and "error-run-fake-s1-l1" in page.shots[0]
    # the SECOND lesson was still processed → graded
    assert ("ex-2", 8, False) in poster.grade_calls
    assert report.graded == 1


def test_screenshot_failure_is_audited_not_swallowed(monkeypatch):
    store = FakeStore()
    poster = RecordingPoster()

    class ExplodingPage(FakePage):
        def screenshot(self, path):
            raise RuntimeError("screenshot device busy")

    bad_page = ExplodingPage()
    monkeypatch.setattr(runner_mod, "ensure_logged_in", lambda ctx, s: bad_page)
    _wire(monkeypatch, exercises=[_text_exercise()], poster=poster)
    # re-point ensure_logged_in after _wire (which overrode it)
    monkeypatch.setattr(runner_mod, "ensure_logged_in", lambda ctx, s: bad_page)

    def _le(p, url=None, lid=None):
        raise SelectorError("boom")

    monkeypatch.setattr(runner_mod, "gather_exercises", _le)
    report = run(RunConfig(mode="full_auto"), _settings(), store)
    assert report.errors == 1
    # the screenshot failure was audited (not silently swallowed)
    actions = [r[1] for r in store.audit_rows]
    assert "screenshot_failed" in actions


def test_max_students_and_max_lessons_caps(monkeypatch):
    store = FakeStore()
    poster = RecordingPoster()
    students = [Student(id="s1", name="A"), Student(id="s2", name="B")]
    lessons = [
        Lesson(id="l1", name="L1", status="awaiting"),
        Lesson(id="l2", name="L2", status="awaiting"),
    ]
    _wire(
        monkeypatch, exercises=[_text_exercise()], poster=poster,
        students=students, lessons=lessons,
    )
    cfg = RunConfig(mode="dry_run", max_students=1, max_lessons=1)
    run(cfg, _settings(), store)
    # only one student × one lesson processed → one evaluate audit row
    evals = [r for r in store.audit_rows if r[1] == "evaluate"]
    assert len(evals) == 1


def test_student_filter_restricts(monkeypatch):
    store = FakeStore()
    poster = RecordingPoster()
    students = [Student(id="s1", name="A"), Student(id="s2", name="B")]
    _wire(
        monkeypatch, exercises=[_text_exercise()], poster=poster, students=students,
    )
    cfg = RunConfig(mode="dry_run", student_filter=["s2"])
    run(cfg, _settings(), store)
    evals = [r for r in store.audit_rows if r[1] == "evaluate"]
    assert len(evals) == 1


def test_student_offset_batches_the_roster(monkeypatch):
    store = FakeStore()
    poster = RecordingPoster()
    students = [Student(id=f"s{i}", name=str(i)) for i in (1, 2, 3)]
    _wire(
        monkeypatch, exercises=[_text_exercise()], poster=poster, students=students,
    )
    seen: list[str] = []
    cfg = RunConfig(mode="dry_run", student_offset=1, max_students=1)
    run(
        cfg, _settings(), store,
        on_event=lambda e: seen.append(e["student_id"])
        if e.get("event") == "student" else None,
    )
    assert seen == ["s2"]   # offset 1 skips s1; max_students 1 → only s2
