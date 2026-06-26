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
    then name), then click their progress button.

    The whole sequence is RETRIED: the roster SPA intermittently fails to paint
    the search box or the progress modal within the wait (the dominant source of
    per-lesson nav errors). We re-goto and retry, returning only once the modal's
    lesson rows have actually rendered — a click that "succeeds" but leaves an
    unpainted modal is what otherwise stalls the next open_lesson."""
    query = student.email or student.id or student.name
    last_exc: "Exception | None" = None
    for _ in range(3):
        try:
            page.goto(roster_url)
            page.wait_for_load_state("networkidle")
            box = page.locator(selectors.STUDENT_SEARCH).first
            box.wait_for(state="visible", timeout=15000)
            box.fill(query)
            page.wait_for_timeout(1800)   # let the filter narrow the list
            page.locator(selectors.STUDENT_PROGRESS_BTN).first.click(timeout=10000)
            page.wait_for_timeout(1500)
            return
        except Exception as exc:  # noqa: BLE001 - retry transient SPA render misses
            last_exc = exc
            page.wait_for_timeout(1500)
    raise SelectorError(
        f"open_progress failed for {student.id} after retries: {last_exc}"
    )


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
    """A lesson row is an *awaiting* (still-to-grade) candidate UNLESS it shows the
    green "Done" tag (``selectors.LESSON_DONE_MARKER``).

    Validated live (2026-06-23, on the most-graded student): a "Done" row NEVER
    holds answered-ungraded work — its manual exercises are either already graded
    or unanswered (nothing to grade). Skipping Done rows therefore loses no
    gradeable work while avoiding the dominant cost of a run: opening every
    already-finished lesson. ``--all-lessons`` bypasses this for a paranoid full
    sweep (e.g. if the virtualised modal under-renders the row list)."""
    return row.locator(selectors.LESSON_DONE_MARKER).count() == 0


def _estimate_is_ungraded(estimate_text: str) -> bool:
    """PURE: the grade widget is ungraded (awaiting) when it offers the
    "Оценить упражнение" trigger and shows no "N/M" score."""
    text = estimate_text or ""
    if "Оценить упражнение" not in text:
        return False
    return re.search(r"\d+\s*/\s*\d+", text) is None


# The progress modal (`.marathon-student-progress-modal`) is a SCROLL container
# (~5 screens tall) whose lesson rows render lazily as it scrolls. Reading rows
# once captures only the first window (~20 of 29), so the recent lessons — where
# active students' ungraded homework lives — were silently never discovered. We
# scroll the modal's own scrollTop and accumulate until no new lesson appears.
# The progress modal renders all lesson-row ELEMENTS, but the rows below the fold
# (the recent lessons 21-29 — where active students' ungraded homework is) keep
# their TEXT empty until scrolled into view. Reading rows without scrolling each
# into view therefore silently drops them. Scrolling the container's scrollTop is
# unreliable for triggering the render; scrolling each row element into view is.
_ROW_INTO_VIEW_JS = "el => el.scrollIntoView({block: 'center'})"


def list_lessons(page: Page) -> list[Lesson]:
    """Collect EVERY lesson in the student's progress modal.

    Walk each row BY INDEX, scrolling it into view to force its lazy text to
    render before reading — otherwise the recent (high-numbered) lessons read
    blank and are skipped. Dedupe by lesson number; skip rows that stay blank."""
    rows = page.locator(selectors.LESSON_ROW)
    n = rows.count()
    if n == 0:
        raise SelectorError("no lesson rows found in progress modal")
    collected: "dict[str, Lesson]" = {}
    for i in range(n):
        row = rows.nth(i)
        try:
            row.evaluate(_ROW_INTO_VIEW_JS)
        except Exception:  # noqa: BLE001 - best-effort; still try to read
            pass
        name = _lesson_name((row.inner_text() or "").strip())
        if not name:
            page.wait_for_timeout(120)   # let the lazy row content paint
            name = _lesson_name((row.inner_text() or "").strip())
        if not name:
            continue
        number = _lesson_number(name)
        key = number or name
        if key in collected:
            continue
        status = "awaiting" if _row_is_awaiting(row) else "complete"
        collected[key] = Lesson(
            id=number or name, name=name, status=status, number=number
        )
    if not collected:
        raise SelectorError("no named lesson rows in progress modal")
    return list(collected.values())


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
    # Match "Lesson N:" (with the colon) so "Lesson 1" doesn't also match
    # "Lesson 10".."Lesson 19"; fall back to the full name when no number.
    matcher = f"Lesson {lesson.number}:" if lesson.number else lesson.name
    # Open via a JS click, NOT Locator.click. On the recent lessons (21+) the
    # "Открыть урок" button is visible, uncovered and pointer-enabled, yet
    # Playwright's actionability check never settles (the modal row reports as
    # never "stable") and the click times out after 20-30s. A direct el.click()
    # fires the Vue handler and navigates reliably (confirmed live). Scroll the
    # row in first so its lazily-rendered button exists.
    last_exc: "Exception | None" = None
    for _ in range(3):
        try:
            row = page.locator(selectors.LESSON_ROW).filter(has_text=matcher).first
            # The row's "Открыть урок" button renders lazily AFTER the row scrolls
            # into view, and not always within a single wait. Poll: re-scroll and
            # check the row's own text until the button appears, then JS-click it.
            rendered = False
            for _ in range(8):
                try:
                    row.evaluate("el => el.scrollIntoView({block: 'center'})")
                except Exception:  # noqa: BLE001 - best-effort scroll
                    pass
                if "Открыть урок" in (row.inner_text() or ""):
                    rendered = True
                    break
                page.wait_for_timeout(500)
            if not rendered:
                raise SelectorError(f"open button never rendered for {matcher}")
            row.locator(selectors.LESSON_OPEN_BUTTON).first.evaluate("el => el.click()")
            last_exc = None
            break
        except Exception as exc:  # noqa: BLE001 - retry a transient render/click miss
            last_exc = exc
            page.wait_for_timeout(1500)
    if last_exc is not None:
        raise last_exc
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
