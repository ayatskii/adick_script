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
    def __init__(self, *, text="", children=None, estimates=None):
        self._text = text
        self._children = children if children is not None else []
        # estimates: list of .exercise-estimate-view texts for this row.
        self._estimates = estimates
        self.click_count = 0

    @property
    def first(self):
        return self._children[0] if self._children else self

    def all(self):
        return list(self._children)

    def inner_text(self):
        return self._text

    def locator(self, selector):
        if selector == selectors.GRADE_ESTIMATE_VIEW and self._estimates is not None:
            return FakeLocator(
                children=[FakeLocator(text=t) for t in self._estimates]
            )
        if selector == selectors.LESSON_OPEN_BUTTON:
            return FakeLocator(children=[self])
        return FakeLocator(children=[])

    def count(self):
        return len(self._children)

    def click(self):
        self.click_count += 1


class FakePage:
    def __init__(self, *, locators=None, url=""):
        self._locators = locators or {}
        self.url = url
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


def test_list_lessons_reads_all_lessons_as_awaiting_candidates():
    # The progress modal exposes no reliable per-lesson awaiting marker, so every
    # lesson is returned as an "awaiting" candidate; the runner opens each and
    # skips exercises already graded on the platform (Exercise.is_graded).
    rows = FakeLocator(children=[
        FakeLocator(text="Lesson 14: Entertainment"),
        FakeLocator(text="Lesson 13: Travel"),
    ])
    page = FakePage(locators={selectors.LESSON_ROW: rows})

    lessons = list_lessons(page)
    assert lessons == [
        Lesson(id="14", name="Lesson 14: Entertainment", status="awaiting", number="14"),
        Lesson(id="13", name="Lesson 13: Travel", status="awaiting", number="13"),
    ]


def test_open_lesson_clicks_and_parses_url_ids():
    lesson = Lesson(id="14", name="Lesson 14: Entertainment", status="awaiting", number="14")
    row = FakeLocator(text="Lesson 14: Entertainment")

    class FilteringRows(FakeLocator):
        def filter(self, has_text=None):
            return row

    page = FakePage(
        locators={selectors.LESSON_ROW: FilteringRows()},
        url="https://edvibe.com/marathon/110326/lesson/1781437?pupil=3176678&section=0",
    )
    open_lesson(page, lesson)
    assert row.click_count == 1
    assert lesson.lesson_url_id == "1781437"
    assert lesson.pupil_id == "3176678"


def test_parse_lesson_url_pure():
    from edvibe_bot.scraper.progress import parse_lesson_url
    lid, pid = parse_lesson_url(
        "https://edvibe.com/marathon/110326/lesson/1781437?pupil=3176678&section=2"
    )
    assert lid == "1781437"
    assert pid == "3176678"
    assert parse_lesson_url("https://edvibe.com/cabinet/school/classes") == (None, None)
