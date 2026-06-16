import pytest

from edvibe_bot import selectors
from edvibe_bot.scraper.dashboard import Student, open_marathon, list_students


class FakeLocator:
    """Mirrors the subset of the Playwright sync Locator API the scraper uses."""

    def __init__(self, *, attrs=None, text="", children=None):
        self._attrs = attrs or {}
        self._text = text
        self._children = children if children is not None else []
        self.click_count = 0

    @property
    def first(self):  # PROPERTY, not a method (mirrors Playwright)
        return self._children[0] if self._children else self

    def nth(self, i):
        return self._children[i]

    def count(self):
        return len(self._children)

    def all(self):
        return list(self._children)

    def locator(self, selector):
        # A child row resolves nested selectors to a single locator.
        if selector == selectors.STUDENT_NAME:
            return FakeLocator(text=self._text)
        return FakeLocator()

    def get_attribute(self, name):
        return self._attrs.get(name)

    def inner_text(self):
        return self._text

    def click(self):
        self.click_count += 1


class FakePage:
    def __init__(self, *, locators=None):
        # locators: mapping selector-string -> FakeLocator
        self._locators = locators or {}
        self.goto_calls = []
        self.click_log = []

    def goto(self, url):
        self.goto_calls.append(url)

    def locator(self, selector):
        loc = self._locators.get(selector)
        if loc is None:
            loc = FakeLocator()
            self._locators[selector] = loc
        return loc


class RecordingPage(FakePage):
    """Records the ordered sequence of (kind, target) actions for open_marathon."""

    def goto(self, url):
        super().goto(url)
        self.click_log.append(("goto", url))

    def locator(self, selector):
        page = self

        class _Click(FakeLocator):
            def click(_self):
                page.click_log.append(("click", selector))

        return _Click()


class DummySettings:
    marathon_name = "Pre-IELTS"
    curator_name = "Mister Adilet"


def test_open_marathon_runs_the_six_steps_in_order():
    page = RecordingPage()
    open_marathon(page, DummySettings())
    assert page.click_log == [
        ("goto", selectors.NAV_CLASSES),
        ("click", selectors.MARATHONS_TAB),
        ("click", selectors.PRE_IELTS_CARD),
        ("click", selectors.FILTER_BUTTON),
        ("click", selectors.CURATOR_OPTION),
        ("click", selectors.FILTER_APPLY),
    ]


def test_list_students_builds_students_from_rows():
    rows = FakeLocator(
        children=[
            FakeLocator(attrs={selectors.STUDENT_ID_ATTR: "s1"}, text="Анель"),
            FakeLocator(attrs={selectors.STUDENT_ID_ATTR: "s2"}, text="Bauyrzhan"),
        ]
    )
    page = FakePage(locators={selectors.STUDENT_ROW: rows})
    students = list_students(page)
    assert students == [Student(id="s1", name="Анель"), Student(id="s2", name="Bauyrzhan")]


def test_list_students_empty_returns_empty_list():
    page = FakePage(locators={selectors.STUDENT_ROW: FakeLocator(children=[])})
    assert list_students(page) == []
