import pytest

from edvibe_bot import selectors
from edvibe_bot.evaluator.schema import ExerciseType
from edvibe_bot.scraper.lesson import Exercise, classify_exercise, list_exercises


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


# ---- Reader doubles ----

class FakeLocator:
    def __init__(self, *, text="", attrs=None, children=None, src=None):
        self._text = text
        self._attrs = attrs or {}
        self._children = children if children is not None else []
        self._src = src

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
        if name == "src":
            return self._src
        return self._attrs.get(name)

    def locator(self, selector):
        return self._children_for(selector)

    # Maps a nested selector to a configured child locator.
    def _children_for(self, selector):
        mapping = self._attrs.get("__nested__", {})
        return mapping.get(selector, FakeLocator(children=[]))


class FakePage:
    def __init__(self, *, blocks, section):
        self._blocks = blocks
        self._section = section

    def locator(self, selector):
        if selector == selectors.EXERCISE_BLOCK:
            return FakeLocator(children=self._blocks)
        if selector == selectors.SECTION_NAV:
            return FakeLocator(text=self._section)
        return FakeLocator(children=[])


def _block(*, ex_id, number, prompt, audio_src=None, answer=None, has_grade):
    nested = {
        selectors.EXERCISE_NUMBER: FakeLocator(text=number),
        selectors.EXERCISE_PROMPT: FakeLocator(text=prompt),
        selectors.EXERCISE_AUDIO: FakeLocator(
            children=[FakeLocator(src=audio_src)] if audio_src else []
        ),
        selectors.EXERCISE_TEXT_ANSWER: (
            FakeLocator(text=answer, children=[FakeLocator()])
            if answer is not None
            else FakeLocator(children=[])
        ),
        selectors.GRADE_EXERCISE_BTN: (
            FakeLocator(children=[FakeLocator()]) if has_grade else FakeLocator(children=[])
        ),
    }
    return FakeLocator(attrs={selectors.EXERCISE_ID_ATTR: ex_id, "__nested__": nested})


def test_list_exercises_builds_audio_exercise_with_stable_id():
    block = _block(
        ex_id="ex-101",
        number="1",
        prompt="Describe your weekend.",
        audio_src="https://cdn.edvibe.com/a.mp3",
        answer=None,
        has_grade=True,
    )
    page = FakePage(blocks=[block], section="Speaking")
    exercises = list_exercises(page)
    assert len(exercises) == 1
    ex = exercises[0]
    assert ex.element_id == "ex-101"          # populated from EXERCISE_ID_ATTR
    assert ex.section == "Speaking"           # from SECTION_NAV, not prompt-derived
    assert ex.number == "1"
    assert ex.prompt_text == "Describe your weekend."
    assert ex.type is ExerciseType.AUDIO
    assert ex.has_grade_button is True
    assert ex.audio_url == "https://cdn.edvibe.com/a.mp3"
    assert ex.answer_text is None


def test_list_exercises_builds_text_exercise():
    block = _block(
        ex_id="ex-202",
        number="2",
        prompt="Write about your hobby.",
        audio_src=None,
        answer="I like reading.",
        has_grade=True,
    )
    page = FakePage(blocks=[block], section="Writing")
    ex = list_exercises(page)[0]
    assert ex.type is ExerciseType.TEXT
    assert ex.answer_text == "I like reading."
    assert ex.audio_url is None
    assert ex.element_id == "ex-202"


def test_list_exercises_auto_checked_when_no_grade_button():
    block = _block(
        ex_id="ex-303",
        number="3",
        prompt="Pick the correct word.",
        audio_src=None,
        answer="done",
        has_grade=False,
    )
    page = FakePage(blocks=[block], section="Grammar")
    ex = list_exercises(page)[0]
    assert ex.type is ExerciseType.AUTO_CHECKED
    assert ex.has_grade_button is False
