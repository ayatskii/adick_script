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

    @property
    def last(self):
        return self._children[-1] if self._children else self

    def scroll_into_view_if_needed(self, timeout=None):
        pass

    def nth(self, i):
        return self._children[i]

    def count(self):
        return len(self._children)

    def all(self):
        return list(self._children)

    def locator(self, selector):
        return FakeLocator()

    def get_attribute(self, name):
        return self._attrs.get(name)

    def inner_text(self):
        return self._text

    def wait_for(self, state=None, timeout=None):
        pass

    def click(self):
        self.click_count += 1


class FakeMouse:
    def __init__(self):
        self.wheels = 0

    def wheel(self, dx, dy):
        self.wheels += 1


class FakePage:
    def __init__(self, *, locators=None):
        # locators: mapping selector-string -> FakeLocator
        self._locators = locators or {}
        self.goto_calls = []
        self.click_log = []
        self.mouse = FakeMouse()
        self.url = ""

    def goto(self, url):
        self.goto_calls.append(url)
        self.url = url

    def wait_for_load_state(self, state=None):
        pass

    def wait_for_url(self, predicate, timeout=None):
        # Mirror Playwright: return if the current url already matches, else raise
        # (the production retry loop catches this and re-gotos).
        if callable(predicate) and predicate(self.url):
            return
        raise TimeoutError("url did not match")

    def wait_for_timeout(self, ms):
        pass

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

    # The curator dropdown's readonly input reports this value after a pick. Set
    # to a wrong value in a test to exercise the apply-time verification guard.
    curator_value = "Mister Adilet"

    def locator(self, selector):
        page = self

        class _Click(FakeLocator):
            def click(_self):
                page.click_log.append(("click", selector))

            def input_value(_self):
                if selector == selectors.CURATOR_DROPDOWN:
                    return page.curator_value
                return ""

        return _Click()

    def get_by_text(self, text, exact=False):
        page = self

        class _Click(FakeLocator):
            def click(_self, timeout=None):
                page.click_log.append(("get_by_text", text))

        return _Click()


class DummySettings:
    marathon_name = "Pre-IELTS"
    curator_name = "Mister Adilet"


def test_open_marathon_navigates_direct_then_filters():
    # Direct roster URL lands on a /marathon/ page (RecordingPage.goto sets url),
    # so the flaky Марафоны→Pre-IELTS click flow is skipped; the curator filter
    # opens the modal, opens the Кураторы dropdown, picks the exact curator, then
    # applies.
    page = RecordingPage()
    open_marathon(page, DummySettings())
    assert page.click_log == [
        ("goto", selectors.MARATHON_STUDENTS_URL),
        ("click", selectors.FILTER_BUTTON),
        ("click", selectors.CURATOR_DROPDOWN),
        ("get_by_text", "Mister Adilet"),
        ("click", selectors.FILTER_APPLY),
    ]


def test_open_marathon_raises_when_curator_not_selected():
    # If the dropdown pick didn't take (input value stays wrong), the filter is
    # NOT confirmed → raise instead of silently grading the whole roster.
    from edvibe_bot.errors import SelectorError

    page = RecordingPage()
    page.curator_value = ""   # selection never registered
    with pytest.raises(SelectorError):
        open_marathon(page, DummySettings())
    # crucially, Применить was never clicked
    assert ("click", selectors.FILTER_APPLY) not in page.click_log


def test_open_marathon_falls_back_to_click_flow_when_direct_bounces():
    # If the direct URL doesn't land on a marathon page, fall back to the clicks.
    class Bounced(RecordingPage):
        def goto(self, url):
            self.goto_calls.append(url)
            self.click_log.append(("goto", url))
            # direct roster bounces to login; classes goto "lands" normally
            self.url = "" if url == selectors.MARATHON_STUDENTS_URL else url

    page = Bounced()
    open_marathon(page, DummySettings())
    assert ("goto", selectors.MARATHON_STUDENTS_URL) in page.click_log
    assert ("click", selectors.MARATHONS_TAB) in page.click_log
    assert ("click", selectors.PRE_IELTS_CARD) in page.click_log


def test_list_students_builds_students_from_row_text():
    # id = 7-digit numeric text, email = the @ token, name = the rest (minus a
    # leading one-letter avatar initial).
    rows = FakeLocator(
        children=[
            FakeLocator(text="A Nurdana Ardaqqyzy 3190603 n021rd@icloud.com Прогресс ученика"),
            FakeLocator(text="B Bauyrzhan 3176679 bau@mail.ru Прогресс ученика"),
        ]
    )
    page = FakePage(locators={selectors.STUDENT_ROW: rows})
    students = list_students(page)
    assert students == [
        Student(id="3190603", name="Nurdana Ardaqqyzy", email="n021rd@icloud.com"),
        Student(id="3176679", name="Bauyrzhan", email="bau@mail.ru"),
    ]


def test_list_students_dedupes_across_scroll_passes():
    # The virtualised roster re-renders the same rows across scrolls; ids dedupe.
    rows = FakeLocator(
        children=[
            FakeLocator(text="Анель 3176678 anel@mail.ru"),
            FakeLocator(text="Анель 3176678 anel@mail.ru"),
        ]
    )
    page = FakePage(locators={selectors.STUDENT_ROW: rows})
    assert list_students(page) == [Student(id="3176678", name="Анель", email="anel@mail.ru")]


def test_list_students_skips_rows_without_id():
    rows = FakeLocator(children=[FakeLocator(text="just a header, no id")])
    page = FakePage(locators={selectors.STUDENT_ROW: rows})
    assert list_students(page) == []


def test_list_students_empty_returns_empty_list():
    page = FakePage(locators={selectors.STUDENT_ROW: FakeLocator(children=[])})
    assert list_students(page) == []
