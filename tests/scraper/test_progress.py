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
    def __init__(self, *, text="", children=None, estimates=None, done=False):
        self._text = text
        self._children = children if children is not None else []
        # estimates: list of .exercise-estimate-view texts for this row.
        self._estimates = estimates
        # done: row shows the green "Done" tag (selectors.LESSON_DONE_MARKER).
        self._done = done
        self.click_count = 0

    @property
    def first(self):
        return self._children[0] if self._children else self

    def all(self):
        return list(self._children)

    def nth(self, i):
        return self._children[i]

    def inner_text(self):
        return self._text

    def locator(self, selector):
        if selector == selectors.GRADE_ESTIMATE_VIEW and self._estimates is not None:
            return FakeLocator(
                children=[FakeLocator(text=t) for t in self._estimates]
            )
        if selector == selectors.LESSON_OPEN_BUTTON:
            return FakeLocator(children=[self])
        if selector == selectors.LESSON_DONE_MARKER:
            return FakeLocator(children=[FakeLocator()] if self._done else [])
        return FakeLocator(children=[])

    def count(self):
        return len(self._children)

    def fill(self, value):
        pass

    def wait_for(self, state=None, timeout=None):
        pass

    def click(self, **kwargs):
        self.click_count += 1

    def evaluate(self, script, *args, **kwargs):
        # JS bridge for list_lessons (scrollIntoView) and open_lesson (el.click()).
        # A ".click()" script counts as a click on this element; scroll calls no-op.
        if isinstance(script, str) and ".click()" in script:
            self.click_count += 1
        return None


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

    def wait_for_url(self, predicate, timeout=None):
        # The fake URL is already the post-navigation lesson URL.
        return None

    def wait_for_timeout(self, ms):
        return None

    def goto(self, url):
        self.url = url

    def wait_for_load_state(self, state=None):
        return None


def test_open_progress_searches_then_clicks_progress_button():
    btn = FakeLocator()
    page = FakePage(locators={selectors.STUDENT_PROGRESS_BTN: btn})
    open_progress(
        page,
        Student(id="s1", name="Анель", email="anel@mail.ru"),
        "https://edvibe.com/cabinet/school/marathons/marathon/110326/students",
    )
    assert btn.click_count == 1
    assert page.url.endswith("/students")   # reset to a clean roster first


def test_list_lessons_marks_done_rows_complete_rest_awaiting():
    # A row with the green "Done" tag is 'complete' (no ungraded work, skip it);
    # a row without it is an 'awaiting' candidate the runner opens and grades.
    rows = FakeLocator(children=[
        FakeLocator(text="Lesson 14: Entertainment"),            # not Done
        FakeLocator(text="Lesson 13: Travel", done=True),         # Done
    ])
    page = FakePage(locators={selectors.LESSON_ROW: rows})

    lessons = list_lessons(page)
    assert lessons == [
        Lesson(id="14", name="Lesson 14: Entertainment", status="awaiting", number="14"),
        Lesson(id="13", name="Lesson 13: Travel", status="complete", number="13"),
    ]
    # awaiting_lessons drops the Done one, so only Lesson 14 is opened.
    assert awaiting_lessons(lessons) == [lessons[0]]


def test_list_lessons_scrolls_each_row_into_view_to_render_lazy_names():
    # Recent rows render their text BLANK until scrolled into view. list_lessons
    # must scroll each row in (evaluate) before reading, or it drops them (which
    # is how lessons 21-29 were being missed). LazyRow returns its name only after
    # evaluate() has been called on it.
    class LazyRow(FakeLocator):
        def __init__(self, name, done=False):
            super().__init__(done=done)
            self._real_name = name
            self._rendered = False

        def evaluate(self, *a, **k):
            self._rendered = True
            return None

        def inner_text(self):
            return self._real_name if self._rendered else ""

    rows = FakeLocator(children=[
        LazyRow("Lesson 1: A"),
        LazyRow("Lesson 2: B", done=True),
        LazyRow("Lesson 3: C"),
    ])
    page = FakePage(locators={selectors.LESSON_ROW: rows})
    lessons = list_lessons(page)
    assert sorted(l.number for l in lessons) == ["1", "2", "3"]
    # The Done row (Lesson 2) is 'complete'; the others 'awaiting'.
    assert {l.number: l.status for l in lessons} == {
        "1": "awaiting", "2": "complete", "3": "awaiting"
    }


def test_open_lesson_clicks_and_parses_url_ids():
    lesson = Lesson(id="14", name="Lesson 14: Entertainment", status="awaiting", number="14")
    # The row text includes the "Открыть урок" button label that open_lesson polls
    # for before JS-clicking it.
    row = FakeLocator(text="Lesson 14: Entertainment\nОткрыть урок")

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
