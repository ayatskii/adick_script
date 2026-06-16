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


def open_marathon(page: Page, settings: Settings) -> None:
    """classes -> Марафоны -> Pre-IELTS -> filter -> curator -> apply."""
    page.goto(selectors.NAV_CLASSES)
    page.locator(selectors.MARATHONS_TAB).click()
    page.locator(selectors.PRE_IELTS_CARD).click()
    page.locator(selectors.FILTER_BUTTON).click()
    page.locator(selectors.CURATOR_OPTION).click()
    page.locator(selectors.FILTER_APPLY).click()


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
