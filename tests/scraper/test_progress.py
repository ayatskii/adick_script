# tests/scraper/test_progress.py
import pytest

from edvibe_bot import selectors
from edvibe_bot.scraper.dashboard import Student
from edvibe_bot.scraper.progress import (
    Lesson,
    open_progress,
    list_lessons,
    awaiting_lessons,
    open_lesson,
)


# ---- PURE: awaiting_lessons ----

def test_awaiting_lessons_keeps_only_awaiting():
    lessons = [
        Lesson(id="l1", name="Lesson 1", status="awaiting"),
        Lesson(id="l2", name="Lesson 2", status="complete"),
        Lesson(id="l3", name="Lesson 3", status="awaiting"),
        Lesson(id="l4", name="Lesson 4", status="other"),
    ]
    assert awaiting_lessons(lessons) == [lessons[0], lessons[2]]


def test_awaiting_lessons_empty_when_none_awaiting():
    lessons = [Lesson(id="l1", name="Lesson 1", status="complete")]
    assert awaiting_lessons(lessons) == []


def test_awaiting_lessons_empty_input():
    assert awaiting_lessons([]) == []


# ---- Reader doubles ----

class FakeLocator:
    def __init__(self, *, text="", children=None, attrs=None, present_selectors=None):
        self._text = text
        self._children = children if children is not None else []
        self._attrs = attrs or {}
        self._present = set(present_selectors or [])
        self.click_count = 0

    @property
    def first(self):
        return self._children[0] if self._children else self

    def all(self):
        return list(self._children)

    def get_attribute(self, name):
        return self._attrs.get(name)

    def inner_text(self):
        return self._text

    def locator(self, selector):
        if selector == selectors.LESSON_NAME:
            return FakeLocator(text=self._text)
        if selector in self._present:
            return FakeLocator(children=[FakeLocator()])  # count() > 0
        return FakeLocator(children=[])  # absent -> count() == 0

    def count(self):
        return len(self._children)

    def click(self):
        self.click_count += 1


class FakePage:
    def __init__(self, *, locators=None):
        self._locators = locators or {}
        self.clicked = []

    def locator(self, selector):
        loc = self._locators.get(selector)
        if loc is None:
            loc = FakeLocator()
            self._locators[selector] = loc
        return loc


def test_open_progress_clicks_progress_button():
    btn = FakeLocator()
    page = FakePage(locators={selectors.STUDENT_PROGRESS_BTN: btn})
    open_progress(page, Student(id="s1", name="Анель"))
    assert btn.click_count == 1


def test_list_lessons_reads_id_name_and_status():
    awaiting_row = FakeLocator(
        text="Lesson 14",
        attrs={selectors.LESSON_ID_ATTR: "l14"},
        present_selectors=[selectors.LESSON_STATUS_AWAITING],
    )
    complete_row = FakeLocator(
        text="Lesson 13",
        attrs={selectors.LESSON_ID_ATTR: "l13"},
        present_selectors=[],  # no awaiting marker
    )
    rows = FakeLocator(children=[awaiting_row, complete_row])
    page = FakePage(locators={selectors.LESSON_ROW: rows})

    lessons = list_lessons(page)
    assert lessons == [
        Lesson(id="l14", name="Lesson 14", status="awaiting"),
        Lesson(id="l13", name="Lesson 13", status="complete"),
    ]


def test_open_lesson_clicks_open_button_inside_matched_row():
    lesson = Lesson(id="l14", name="Lesson 14", status="awaiting")
    composed = f"{selectors.LESSON_ROW}[{selectors.LESSON_ID_ATTR}='{lesson.id}']"
    open_btn = FakeLocator()

    class RowLocator(FakeLocator):
        def locator(self, selector):
            assert selector == selectors.LESSON_OPEN_BUTTON
            return open_btn

    page = FakePage(locators={composed: RowLocator()})
    open_lesson(page, lesson)
    assert open_btn.click_count == 1
