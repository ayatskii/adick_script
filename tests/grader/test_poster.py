import edvibe_bot.grader.poster as poster_mod
from edvibe_bot.grader.poster import grade_exercise, complete_lesson
from edvibe_bot.evaluator.schema import Evaluation, ExerciseType
from edvibe_bot.scraper.lesson import Exercise
from edvibe_bot import selectors


class FakeLocator:
    def __init__(self, selector, page):
        self._selector = selector
        self._page = page

    def click(self):
        self._page.actions.append(("click", self._selector))

    def fill(self, value):
        self._page.actions.append(("fill", self._selector, value))


class FakePage:
    def __init__(self):
        self.actions = []

    def locator(self, selector):
        return FakeLocator(selector, self)


def _settings():
    from edvibe_bot.config import Settings
    return Settings(
        edvibe_login="u",
        edvibe_password="p",
        openai_api_key="k",
        pacing_seconds=0.0,
    )


def _exercise():
    return Exercise(
        section="Writing",
        number="3",
        type=ExerciseType.TEXT,
        prompt_text="Describe your day.",
        has_grade_button=True,
        audio_url=None,
        answer_text="I woke up early.",
        element_id="ex-3",
    )


def _evaluation():
    return Evaluation(score=7, comment="Good effort.", rationale="ok", confidence=0.9)


def test_grade_exercise_dry_run_touches_nothing(monkeypatch):
    monkeypatch.setattr(poster_mod.time, "sleep", lambda s: None)
    page = FakePage()
    grade_exercise(page, _exercise(), _evaluation(), _settings(), dry_run=True)
    assert page.actions == []


def test_grade_exercise_full_run_exact_sequence(monkeypatch):
    slept = []
    monkeypatch.setattr(poster_mod.time, "sleep", lambda s: slept.append(s))
    page = FakePage()
    grade_exercise(page, _exercise(), _evaluation(), _settings(), dry_run=False)
    assert page.actions == [
        ("click", selectors.GRADE_EXERCISE_BTN),
        ("fill", selectors.SCORE_INPUT, "7"),
        ("fill", selectors.COMMENT_INPUT, "Good effort."),
        ("click", selectors.GRADE_SAVE_BTN),
    ]
    assert slept == [0.0]


def test_complete_lesson_dry_run_touches_nothing(monkeypatch):
    page = FakePage()
    complete_lesson(page, dry_run=True)
    assert page.actions == []


def test_complete_lesson_full_run_clicks_complete(monkeypatch):
    page = FakePage()
    complete_lesson(page, dry_run=False)
    assert page.actions == [("click", selectors.COMPLETE_LESSON_BTN)]
