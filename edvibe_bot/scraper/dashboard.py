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
    rows = page.locator(selectors.STUDENT_ROW)
    students: list[Student] = []
    for row in rows.all():
        student_id = row.get_attribute(selectors.STUDENT_ID_ATTR)
        if not student_id:
            raise SelectorError(
                f"student row missing id attribute {selectors.STUDENT_ID_ATTR!r}"
            )
        name = row.locator(selectors.STUDENT_NAME).inner_text().strip()
        students.append(Student(id=student_id, name=name))
    return students
