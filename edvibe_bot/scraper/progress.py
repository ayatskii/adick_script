# edvibe_bot/scraper/progress.py
from __future__ import annotations

from dataclasses import dataclass

from playwright.sync_api import Page

from edvibe_bot import selectors
from edvibe_bot.errors import SelectorError
from edvibe_bot.scraper.dashboard import Student


@dataclass
class Lesson:
    id: str
    name: str
    status: str  # "awaiting" | "complete" | "other"


def open_progress(page: Page, student: Student) -> None:
    page.locator(selectors.STUDENT_PROGRESS_BTN).click()


def list_lessons(page: Page) -> list[Lesson]:
    rows = page.locator(selectors.LESSON_ROW)
    lessons: list[Lesson] = []
    for row in rows.all():
        lesson_id = row.get_attribute(selectors.LESSON_ID_ATTR)
        if not lesson_id:
            raise SelectorError(
                f"lesson row missing id attribute {selectors.LESSON_ID_ATTR!r}"
            )
        name = row.locator(selectors.LESSON_NAME).inner_text().strip()
        is_awaiting = row.locator(selectors.LESSON_STATUS_AWAITING).count() > 0
        status = "awaiting" if is_awaiting else "complete"
        lessons.append(Lesson(id=lesson_id, name=name, status=status))
    return lessons


def awaiting_lessons(lessons: list[Lesson]) -> list[Lesson]:
    """PURE filter: only lessons whose status is exactly 'awaiting'."""
    return [lesson for lesson in lessons if lesson.status == "awaiting"]


def open_lesson(page: Page, lesson: Lesson) -> None:
    row = page.locator(
        f"{selectors.LESSON_ROW}[{selectors.LESSON_ID_ATTR}='{lesson.id}']"
    )
    row.locator(selectors.LESSON_OPEN_BUTTON).click()
