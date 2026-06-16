from __future__ import annotations

from dataclasses import dataclass

from playwright.sync_api import Page

from edvibe_bot import selectors
from edvibe_bot.config import Settings
from edvibe_bot.errors import SelectorError


@dataclass
class Student:
    id: str
    name: str


def _wait_click(page: Page, selector: str, timeout: int = 30000) -> None:
    """Click the first match, waiting for the SPA to render it first.

    `.first` dodges strict-mode duplicates (e.g. two "Фильтр" buttons); the
    explicit visible-wait avoids racing the Vue SPA's async paint after a goto.
    """
    loc = page.locator(selector).first
    loc.wait_for(state="visible", timeout=timeout)
    loc.click()


def open_marathon(page: Page, settings: Settings) -> None:
    """classes -> Марафоны -> Pre-IELTS, then a BEST-EFFORT curator filter.

    The curator-filter selectors (CURATOR_OPTION) are unconfirmed (Phase 0
    R0.3); if the filter flow fails we fall back to processing ALL marathon
    students rather than aborting the run.
    """
    page.goto(selectors.NAV_CLASSES)
    page.wait_for_load_state("networkidle")
    _wait_click(page, selectors.MARATHONS_TAB)
    _wait_click(page, selectors.PRE_IELTS_CARD)
    page.wait_for_load_state("networkidle")
    try:
        _wait_click(page, selectors.FILTER_BUTTON, timeout=8000)
        _wait_click(page, selectors.CURATOR_OPTION, timeout=8000)
        _wait_click(page, selectors.FILTER_APPLY, timeout=8000)
        page.wait_for_load_state("networkidle")
    except Exception:
        pass  # curator filter unavailable/unconfirmed -> process all students


def list_students(page: Page) -> list[Student]:
    """Read each student card. There is no id attribute on the live DOM — the
    student id is the numeric text shown in the row; the name is the rest of
    the visible text (first non-numeric line)."""
    rows = page.locator(selectors.STUDENT_ROW)
    students: list[Student] = []
    for row in rows.all():
        text = row.inner_text().strip()
        match = selectors.STUDENT_ID_RE.search(text)
        if not match:
            raise SelectorError(
                f"student row has no numeric id in text {text!r}"
            )
        student_id = match.group(0)
        # name = the row text with the id removed, first non-empty line.
        name = _student_name(text, student_id)
        students.append(Student(id=student_id, name=name))
    return students


def _student_name(text: str, student_id: str) -> str:
    """PURE: extract the display name from the student row text."""
    for line in text.splitlines():
        cleaned = line.replace(student_id, "").strip()
        if cleaned:
            return cleaned
    return text.replace(student_id, "").strip()
