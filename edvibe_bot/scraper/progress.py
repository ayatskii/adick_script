# edvibe_bot/scraper/progress.py
from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse

from playwright.sync_api import Page

from edvibe_bot import selectors
from edvibe_bot.errors import SelectorError
from edvibe_bot.scraper.dashboard import Student

_LESSON_NUMBER_RE = re.compile(r"Lesson\s+(\d+)", re.IGNORECASE)


@dataclass
class Lesson:
    id: str                     # stable per-student key: the lesson number text
    name: str                   # first text line ("Lesson 14: Entertainment")
    status: str                 # "awaiting" | "complete" | "other"
    number: str = ""            # parsed lesson number ("14")
    lesson_url_id: str | None = None   # URL /lesson/{id} — captured on open
    pupil_id: str | None = None        # URL ?pupil= — captured on open


def open_progress(page: Page, student: Student, roster_url: str) -> None:
    """Open THIS student's progress modal.

    The roster shows ~200 students, each with its own "Прогресс ученика" button,
    so a bare first-match click would open the wrong student. Reset to a clean
    roster page (clears scroll position and transient overlays left by the
    previous student's lessons — a stray .tir-modal otherwise intercepts the
    click), filter to this student (search is unique by email; fall back to id,
    then name), then click their progress button."""
    page.goto(roster_url)
    page.wait_for_load_state("networkidle")
    query = student.email or student.id or student.name
    box = page.locator(selectors.STUDENT_SEARCH).first
    box.wait_for(state="visible", timeout=15000)
    box.fill(query)
    page.wait_for_timeout(1800)   # let the filter narrow the list
    page.locator(selectors.STUDENT_PROGRESS_BTN).first.click(timeout=10000)
    page.wait_for_timeout(1500)


def _lesson_name(row_text: str) -> str:
    """PURE: lesson name = first non-empty text line of the row."""
    for line in row_text.splitlines():
        if line.strip():
            return line.strip()
    return row_text.strip()


def _lesson_number(name: str) -> str:
    """PURE: parse "14" out of "Lesson 14: Entertainment"."""
    match = _LESSON_NUMBER_RE.search(name)
    return match.group(1) if match else ""


def _row_is_awaiting(row) -> bool:
    """The progress-modal lesson row exposes NO reliable awaiting marker (Phase 0:
    the `.status` div is empty and `.exercise-estimate-view` only exists inside the
    OPENED lesson, not the modal row). So we cannot pre-filter here — treat every
    lesson as a candidate. The runner opens each one and skips exercises already
    graded on the platform via ``Exercise.is_graded`` (which uses
    :func:`_estimate_is_ungraded` against the live lesson view). The lessons-tab
    awaiting-count badge is a possible future optimisation to skip globally-0
    lessons and avoid opening every lesson."""
    return True


def _estimate_is_ungraded(estimate_text: str) -> bool:
    """PURE: the grade widget is ungraded (awaiting) when it offers the
    "Оценить упражнение" trigger and shows no "N/M" score."""
    text = estimate_text or ""
    if "Оценить упражнение" not in text:
        return False
    return re.search(r"\d+\s*/\s*\d+", text) is None


def list_lessons(page: Page) -> list[Lesson]:
    rows = page.locator(selectors.LESSON_ROW)
    lessons: list[Lesson] = []
    for row in rows.all():
        name = _lesson_name(row.inner_text().strip())
        if not name:
            raise SelectorError("lesson row has no visible text/name")
        number = _lesson_number(name)
        status = "awaiting" if _row_is_awaiting(row) else "complete"
        lessons.append(
            Lesson(id=number or name, name=name, status=status, number=number)
        )
    return lessons


def awaiting_lessons(lessons: list[Lesson]) -> list[Lesson]:
    """PURE filter: only lessons whose status is exactly 'awaiting'."""
    return [lesson for lesson in lessons if lesson.status == "awaiting"]


def parse_lesson_url(url: str) -> tuple[str | None, str | None]:
    """PURE: extract (lesson_url_id, pupil_id) from a lesson URL like
    /marathon/110326/lesson/1781437?pupil=3176678&section=0."""
    match = selectors.LESSON_URL_RE.search(url)
    lesson_url_id = match.group(1) if match else None
    pupil_values = parse_qs(urlparse(url).query).get(selectors.PUPIL_QS, [])
    pupil_id = pupil_values[0] if pupil_values else None
    return lesson_url_id, pupil_id


def open_lesson(page: Page, lesson: Lesson) -> None:
    """Click this lesson's "Открыть урок"; navigation lands on
    /marathon/{m}/lesson/{lessonId}?pupil={pupilId}. Parse the lessonId and
    pupilId from the URL — these are the stable ids used for the per-exercise
    composite key."""
    row = page.locator(selectors.LESSON_ROW).filter(
        has_text=f"Lesson {lesson.number}" if lesson.number else lesson.name
    )
    row.locator(selectors.LESSON_OPEN_BUTTON).first.click()
    # The lesson opens via an async SPA transition; the URL only becomes
    # /marathon/{m}/lesson/{id}?pupil={p} a moment after the click. Wait for it
    # before parsing, otherwise we read the stale students-page URL.
    try:
        page.wait_for_url(lambda url: "/lesson/" in url, timeout=30000)
    except Exception:  # noqa: BLE001 - fall through to best-effort parse
        pass
    lesson_url_id, pupil_id = parse_lesson_url(page.url)
    lesson.lesson_url_id = lesson_url_id
    lesson.pupil_id = pupil_id
