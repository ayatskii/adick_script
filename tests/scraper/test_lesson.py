import pytest

from edvibe_bot import selectors
from edvibe_bot.evaluator.schema import ExerciseType
from edvibe_bot.scraper.lesson import (
    Exercise,
    classify_exercise,
    list_exercises,
    parse_estimate,
    parse_number,
)


# ---- PURE: classify_exercise ----

def test_classify_grade_and_audio_is_audio():
    assert classify_exercise(True, True, False) is ExerciseType.AUDIO


def test_classify_grade_and_audio_prefers_audio_over_text():
    assert classify_exercise(True, True, True) is ExerciseType.AUDIO


def test_classify_grade_and_text_is_text():
    assert classify_exercise(True, False, True) is ExerciseType.TEXT


def test_classify_no_grade_button_is_auto_checked():
    assert classify_exercise(False, True, True) is ExerciseType.AUTO_CHECKED
    assert classify_exercise(False, False, False) is ExerciseType.AUTO_CHECKED


def test_classify_grade_but_neither_is_manual_unknown():
    assert classify_exercise(True, False, False) is ExerciseType.MANUAL_UNKNOWN


# ---- PURE: parse helpers ----

def test_parse_number_reads_leading_dotted_token():
    assert parse_number("1.1 Describe your weekend.") == "1.1"
    assert parse_number("2 Write about your hobby.") == "2"
    assert parse_number("no number here") == ""


def test_parse_estimate_graded_reads_max():
    assert parse_estimate("Оценить упражнение: 5/5") == (True, 5)
    assert parse_estimate("4 / 5") == (True, 5)


def test_parse_estimate_ungraded():
    assert parse_estimate("Оценить упражнение") == (False, None)
    assert parse_estimate("") == (False, None)


# ---- Reader doubles ----

class FakeLocator:
    def __init__(self, *, text="", children=None, attrs=None):
        self._text = text
        self._attrs = attrs or {}
        self._children = children if children is not None else []

    @property
    def first(self):
        return self._children[0] if self._children else self

    def all(self):
        return list(self._children)

    def count(self):
        return len(self._children)

    def inner_text(self):
        return self._text

    def get_attribute(self, name):
        return self._attrs.get(name)

    def locator(self, selector):
        mapping = self._attrs.get("__nested__", {})
        return mapping.get(selector, FakeLocator(children=[]))


class FakePage:
    def __init__(self, *, blocks):
        self._blocks = blocks

    def locator(self, selector):
        if selector == selectors.EXERCISE_BLOCK:
            return FakeLocator(children=self._blocks)
        return FakeLocator(children=[])


def _block(*, text, audio_src=None, estimate=None):
    """estimate=None → no .exercise-estimate-view (auto-checked).
    estimate="..." → the widget text ("Оценить упражнение" / "...: 5/5")."""
    nested = {
        selectors.EXERCISE_AUDIO: FakeLocator(
            children=[FakeLocator(attrs={"currentSrc": audio_src})]
            if audio_src
            else []
        ),
        selectors.GRADE_ESTIMATE_VIEW: (
            FakeLocator(children=[FakeLocator(text=estimate)])
            if estimate is not None
            else FakeLocator(children=[])
        ),
    }
    return FakeLocator(text=text, attrs={"__nested__": nested})


def test_list_exercises_builds_audio_exercise_with_composite_id():
    block = _block(
        text="1.1 Describe your weekend.",
        audio_src="https://media-a.edvibe.com/files/LessonExerciseAudioRecordings/x.mp3",
        estimate="Оценить упражнение",
    )
    page = FakePage(blocks=[block])
    exercises = list_exercises(page, lesson_id="1781437", section="Speaking")
    assert len(exercises) == 1
    ex = exercises[0]
    assert ex.element_id == "1781437:1.1"     # composite, URL lesson id + number
    assert ex.section == "Speaking"
    assert ex.number == "1.1"
    assert ex.type is ExerciseType.AUDIO
    assert ex.has_grade_button is True        # ungraded estimate present
    assert ex.is_graded is False
    assert ex.audio_url.endswith("x.mp3")
    assert ex.answer_text is None


def test_list_exercises_builds_text_exercise():
    block = _block(
        text="2 Write about your hobby. I like reading.",
        audio_src=None,
        estimate="Оценить упражнение",
    )
    page = FakePage(blocks=[block])
    ex = list_exercises(page, lesson_id="L", section="Writing")[0]
    assert ex.type is ExerciseType.TEXT
    assert "I like reading." in ex.answer_text
    assert ex.audio_url is None
    assert ex.element_id == "L:2"


def test_list_exercises_already_graded_is_skipped_by_flags():
    block = _block(
        text="3 Write a sentence.",
        audio_src=None,
        estimate="Оценить упражнение: 5/5",
    )
    page = FakePage(blocks=[block])
    ex = list_exercises(page, lesson_id="L", section="Writing")[0]
    assert ex.is_graded is True
    assert ex.score_max == 5
    assert ex.has_grade_button is False       # graded → not a manual target


def test_list_exercises_auto_checked_when_no_estimate_widget():
    block = _block(text="4 Pick the correct word.", audio_src=None, estimate=None)
    page = FakePage(blocks=[block])
    ex = list_exercises(page, lesson_id="L", section="Grammar")[0]
    assert ex.type is ExerciseType.AUTO_CHECKED
    assert ex.has_grade_button is False


def test_list_exercises_no_composite_id_when_number_missing():
    block = _block(text="Describe your day.", estimate="Оценить упражнение")
    page = FakePage(blocks=[block])
    ex = list_exercises(page, lesson_id="L", section="Speaking")[0]
    assert ex.number == ""
    assert ex.element_id is None              # → runner FLAGs as no_stable_id
