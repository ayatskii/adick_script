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
from edvibe_bot.scraper.lesson import _lesson_base_url


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


# ---- PURE: _lesson_base_url ----

def test_lesson_base_url_strips_section_param():
    assert _lesson_base_url(
        "https://edvibe.com/marathon/110326/lesson/1798271?pupil=3190603&section=4"
    ) == "https://edvibe.com/marathon/110326/lesson/1798271?pupil=3190603"


def test_lesson_base_url_noop_without_section():
    url = "https://edvibe.com/marathon/110326/lesson/1798271?pupil=3190603"
    assert _lesson_base_url(url) == url


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

    def input_value(self):
        return self._attrs.get("value", "")

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


def _block(*, text, audio_src=None, grade_button=False, graded_score=None, answer=None, inputs=None):
    """Models the confirmed live DOM:
    - grade_button=True  → an ungraded manual exercise exposing the
      "Оценить упражнение" trigger (selectors.GRADE_EXERCISE_BTN).
    - graded_score="N/M" → an already-graded exercise whose
      .exercise-estimate-view shows the awarded score.
    - neither             → an auto-checked exercise.
    - answer="..."        → the student's WRITTEN answer inside the
      ``.html-editor-inline`` contenteditable. None → editor absent;
      "" → editor present but empty (unanswered)."""
    editor_children = []
    if answer is not None:
        editor_children = [FakeLocator(text=answer)]
    nested = {
        selectors.EXERCISE_AUDIO: FakeLocator(
            children=[FakeLocator(attrs={"currentSrc": audio_src})]
            if audio_src
            else []
        ),
        selectors.ANSWER_EDITOR: FakeLocator(children=editor_children),
        selectors.GRADE_ESTIMATE_VIEW: (
            FakeLocator(children=[FakeLocator(text=f"Оценить упражнение: {graded_score}")])
            if graded_score is not None
            else FakeLocator(children=[])
        ),
        selectors.GRADE_EXERCISE_BTN: (
            FakeLocator(children=[FakeLocator(text="Оценить упражнение")])
            if grade_button
            else FakeLocator(children=[])
        ),
        "textarea": FakeLocator(children=[]),
        "input[type='text'], input:not([type])": FakeLocator(
            children=[FakeLocator(attrs={"value": v}) for v in (inputs or [])]
        ),
    }
    return FakeLocator(text=text, attrs={"__nested__": nested})


def test_list_exercises_builds_audio_exercise_with_composite_id():
    block = _block(
        text="1.1 Describe your weekend.",
        audio_src="https://media-a.edvibe.com/files/LessonExerciseAudioRecordings/x.mp3",
        grade_button=True,
    )
    page = FakePage(blocks=[block])
    exercises = list_exercises(page, lesson_id="1781437", section="Speaking")
    assert len(exercises) == 1
    ex = exercises[0]
    assert ex.element_id == "1781437:s0:1.1"  # composite: lesson id + section + number
    assert ex.section == "Speaking"
    assert ex.number == "1.1"
    assert ex.type is ExerciseType.AUDIO
    assert ex.has_grade_button is True        # ungraded grade trigger present
    assert ex.is_graded is False
    assert ex.score_max == selectors.SCORE_MAX   # defaults to modal max (5)
    assert ex.audio_url.endswith("x.mp3")
    assert ex.answer_text is None


def test_list_exercises_builds_text_exercise():
    # The block text is the INSTRUCTIONS; the answer is in the editor.
    block = _block(
        text="2 Write about your hobby.",
        audio_src=None,
        grade_button=True,
        answer="I like reading books in the evening.",
    )
    page = FakePage(blocks=[block])
    ex = list_exercises(page, lesson_id="L", section="Writing")[0]
    assert ex.type is ExerciseType.TEXT
    assert ex.answer_text == "I like reading books in the evening."
    assert ex.audio_url is None
    assert ex.element_id == "L:s0:2"


def test_list_exercises_answer_is_editor_not_instructions():
    # Regression: the bot once graded the instructions as the answer. The
    # answer must come from the editor, and the instructions must NOT leak in.
    block = _block(
        text="3 Rewrite the sentences using used to or would.",
        grade_button=True,
        answer="My uncle used to be an artist.",
    )
    page = FakePage(blocks=[block])
    ex = list_exercises(page, lesson_id="L", section="Grammar")[0]
    assert ex.answer_text == "My uncle used to be an artist."
    assert "Rewrite the sentences" not in (ex.answer_text or "")


def test_list_exercises_reads_fill_in_the_blank_inputs():
    # A fill-in answer lives in <input>.value (NOT innerText / editor). It must be
    # captured so a real answer is never mis-flagged as empty.
    block = _block(
        text="5 Complete the sentences.",
        grade_button=True,
        answer="",  # editor empty
        inputs=["used to", "would"],
    )
    page = FakePage(blocks=[block])
    ex = list_exercises(page, lesson_id="L", section="Grammar")[0]
    assert ex.answer_text == "used to\nwould"
    assert ex.type is ExerciseType.TEXT


def test_list_exercises_blank_writing_exercise_has_no_answer():
    # Editor present but EMPTY → unanswered. answer_text must be None so the
    # runner flags empty_answer instead of grading the instructions.
    block = _block(
        text="4 Write three sentences about your weekend.",
        grade_button=True,
        answer="",
    )
    page = FakePage(blocks=[block])
    ex = list_exercises(page, lesson_id="L", section="Writing")[0]
    assert ex.answer_text is None
    assert ex.has_grade_button is True   # still a manual target → runner flags empty
    assert ex.type is ExerciseType.MANUAL_UNKNOWN


def test_list_exercises_already_graded_is_skipped_by_flags():
    # Even if a graded block still echoes the trigger text, `not is_graded`
    # guards it from being re-graded.
    block = _block(
        text="3 Write a sentence.",
        audio_src=None,
        grade_button=True,
        graded_score="5/5",
    )
    page = FakePage(blocks=[block])
    ex = list_exercises(page, lesson_id="L", section="Writing")[0]
    assert ex.is_graded is True
    assert ex.score_max == 5
    assert ex.has_grade_button is False       # graded → not a manual target


def test_list_exercises_auto_checked_when_no_grade_trigger():
    block = _block(text="4 Pick the correct word.", audio_src=None)
    page = FakePage(blocks=[block])
    ex = list_exercises(page, lesson_id="L", section="Grammar")[0]
    assert ex.type is ExerciseType.AUTO_CHECKED
    assert ex.has_grade_button is False


def test_list_exercises_no_composite_id_when_number_missing():
    block = _block(text="Describe your day.", grade_button=True)
    page = FakePage(blocks=[block])
    ex = list_exercises(page, lesson_id="L", section="Speaking")[0]
    assert ex.number == ""
    assert ex.element_id is None              # → runner FLAGs as no_stable_id
