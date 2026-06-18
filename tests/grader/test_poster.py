import edvibe_bot.grader.poster as poster_mod
from edvibe_bot.grader.poster import (
    parse_modal_max,
    is_already_graded,
    open_grade_modal,
    submit_grade,
    cancel_grade_modal,
    complete_lesson,
)
from edvibe_bot.evaluator.schema import Evaluation, ExerciseType
from edvibe_bot.scraper.lesson import Exercise
from edvibe_bot import selectors


class FakeLocator:
    """Registry-backed: every .locator(sel) resolves through the page so actions
    record against the innermost selector. filter()/first/nth are pass-throughs."""

    def __init__(self, page, selector):
        self._page = page
        self._sel = selector

    def filter(self, **kwargs):
        return self

    @property
    def first(self):
        return self

    def nth(self, i):
        return self

    def locator(self, selector):
        return self._page.locator(selector)

    def count(self):
        return self._page.counts.get(self._sel, 1)

    def inner_text(self):
        return self._page.texts.get(self._sel, "")

    def wait_for(self, **kwargs):
        self._page.actions.append(("wait_for", self._sel))

    def click(self):
        self._page.actions.append(("click", self._sel))

    def fill(self, value):
        self._page.actions.append(("fill", self._sel, value))


class FakeKeyboard:
    def __init__(self, page):
        self._page = page

    def press(self, key):
        self._page.actions.append(("press", key))


class FakePage:
    def __init__(self, *, texts=None, counts=None):
        self.actions = []
        self.texts = texts or {}
        self.counts = counts or {}
        self.keyboard = FakeKeyboard(self)

    def locator(self, selector):
        return FakeLocator(self, selector)


def _settings():
    from edvibe_bot.config import Settings
    return Settings(
        edvibe_login="u", edvibe_password="p", openai_api_key="k", pacing_seconds=0.0,
    )


def _exercise(number="3"):
    return Exercise(
        section="Writing", number=number, type=ExerciseType.TEXT,
        prompt_text="Describe your day.", has_grade_button=True,
        audio_url=None, answer_text="I woke up early.", element_id="ex-3",
    )


def _evaluation(score=4, comment="Good effort."):
    return Evaluation(score=score, comment=comment, rationale="ok", confidence=0.9, score_max=6)


# ---- PURE: parse_modal_max ----

def test_parse_modal_max_reads_per_exercise_max():
    assert parse_modal_max(
        "Поставить оценку. Максимальное количество баллов: 6. Добавить комментарий"
    ) == 6
    assert parse_modal_max("Максимальное количество баллов: 5.") == 5


def test_parse_modal_max_none_when_absent():
    assert parse_modal_max("no max stated here") is None
    assert parse_modal_max("") is None


# ---- is_already_graded ----

def test_is_already_graded_true_when_estimate_shows_score():
    page = FakePage(
        texts={selectors.GRADE_ESTIMATE_VIEW: "Оценить упражнение: 3/6 Комментарий: x"},
        counts={selectors.GRADE_ESTIMATE_VIEW: 1},
    )
    assert is_already_graded(page, _exercise()) is True


def test_is_already_graded_false_when_no_estimate_view():
    page = FakePage(counts={selectors.GRADE_ESTIMATE_VIEW: 0})
    assert is_already_graded(page, _exercise()) is False


def test_is_already_graded_false_when_estimate_has_no_score():
    page = FakePage(
        texts={selectors.GRADE_ESTIMATE_VIEW: "Оценить упражнение"},
        counts={selectors.GRADE_ESTIMATE_VIEW: 1},
    )
    assert is_already_graded(page, _exercise()) is False


# ---- open_grade_modal ----

def test_open_grade_modal_clicks_trigger_and_returns_max():
    page = FakePage(
        texts={selectors.GRADE_MODAL: "Максимальное количество баллов: 6."},
    )
    mx = open_grade_modal(page, _exercise())
    assert mx == 6
    assert ("click", selectors.GRADE_EXERCISE_BTN) in page.actions
    assert ("wait_for", selectors.GRADE_MODAL) in page.actions


# ---- submit_grade ----

def test_submit_grade_fills_score_toggles_comment_and_submits(monkeypatch):
    monkeypatch.setattr(poster_mod.time, "sleep", lambda s: None)
    page = FakePage(counts={selectors.COMMENT_INPUT_REL: 0})  # textarea hidden first
    submit_grade(page, _evaluation(score=4, comment="Nice work."), _settings())
    assert page.actions == [
        ("fill", selectors.SCORE_INPUT_REL, "4"),
        ("click", selectors.COMMENT_TOGGLE_REL),
        ("wait_for", selectors.COMMENT_INPUT_REL),
        ("fill", selectors.COMMENT_INPUT_REL, "Nice work."),
        ("click", selectors.GRADE_SAVE_BTN_REL),
    ]


def test_submit_grade_without_comment_skips_toggle(monkeypatch):
    monkeypatch.setattr(poster_mod.time, "sleep", lambda s: None)
    page = FakePage()
    submit_grade(page, _evaluation(score=5, comment=""), _settings())
    assert page.actions == [
        ("fill", selectors.SCORE_INPUT_REL, "5"),
        ("click", selectors.GRADE_SAVE_BTN_REL),
    ]


# ---- cancel_grade_modal ----

def test_cancel_grade_modal_clicks_cancel():
    page = FakePage(counts={selectors.GRADE_CANCEL_BTN_REL: 1})
    cancel_grade_modal(page)
    assert ("click", selectors.GRADE_CANCEL_BTN_REL) in page.actions


def test_cancel_grade_modal_escape_fallback():
    page = FakePage(counts={selectors.GRADE_CANCEL_BTN_REL: 0})
    cancel_grade_modal(page)
    assert ("press", "Escape") in page.actions


# ---- complete_lesson ----

def test_complete_lesson_dry_run_touches_nothing():
    page = FakePage()
    complete_lesson(page, dry_run=True)
    assert page.actions == []


def test_complete_lesson_full_run_clicks_complete():
    page = FakePage()
    complete_lesson(page, dry_run=False)
    assert page.actions == [("click", selectors.COMPLETE_LESSON_BTN)]
