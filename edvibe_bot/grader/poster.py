import re
import time

from playwright.sync_api import Page

from edvibe_bot import selectors
from edvibe_bot.config import Settings
from edvibe_bot.evaluator.schema import Evaluation
from edvibe_bot.scraper.lesson import Exercise

_MODAL_MAX_RE = re.compile(
    re.escape(selectors.MODAL_MAX_LABEL) + r":?\s*(\d+)"
)
_SCORE_RE = re.compile(r"(\d+)\s*/\s*(\d+)")


def _scope_block(page: Page, exercise: Exercise):
    """Locator for THIS exercise's block (a section holds several; a page-wide
    locator would be ambiguous). Disambiguated by the visible exercise number."""
    if exercise.number:
        return (
            page.locator(selectors.EXERCISE_BLOCK)
            .filter(has_text=exercise.number)
            .first
        )
    return page.locator(selectors.EXERCISE_BLOCK).first


def is_already_graded(page: Page, exercise: Exercise) -> bool:
    """Authoritative grade-time check on the fully-rendered section: True when the
    block shows a graded `.exercise-estimate-view` with an N/M score.

    Guards against the gather-time estimate-view render lag — if discovery missed
    that an exercise is already graded (its estimate-view had not rendered yet),
    this re-check on the settled single section catches it before we re-grade.
    """
    block = _scope_block(page, exercise)
    est = block.locator(selectors.GRADE_ESTIMATE_VIEW)
    if est.count() == 0:
        return False
    return _SCORE_RE.search(est.first.inner_text() or "") is not None


def parse_modal_max(modal_text: str) -> int | None:
    """PURE: read N from 'Максимальное количество баллов: N'. None if absent."""
    match = _MODAL_MAX_RE.search(modal_text or "")
    return int(match.group(1)) if match else None


def open_grade_modal(page: Page, exercise: Exercise) -> int | None:
    """Open this exercise's grade modal and return its per-exercise max score.

    The max is per-exercise (e.g. /5, /6) and only stated inside the modal, so the
    caller reads it HERE and evaluates against it. Returns None when the max can't
    be parsed (caller falls back to the discovery guess). Leaves the modal OPEN —
    follow with submit_grade or cancel_grade_modal.
    """
    _scope_block(page, exercise).locator(selectors.GRADE_EXERCISE_BTN).first.click()
    modal = page.locator(selectors.GRADE_MODAL)
    modal.wait_for(state="visible", timeout=15000)
    return parse_modal_max(modal.inner_text())


def submit_grade(page: Page, evaluation: Evaluation, settings: Settings) -> None:
    """Fill score + comment into the ALREADY-OPEN grade modal and submit it
    ("Продолжить"). The comment field is hidden behind a toggle."""
    modal = page.locator(selectors.GRADE_MODAL)
    modal.locator(selectors.SCORE_INPUT_REL).fill(str(evaluation.score))

    if evaluation.comment:
        textarea = modal.locator(selectors.COMMENT_INPUT_REL)
        if textarea.count() == 0:
            modal.locator(selectors.COMMENT_TOGGLE_REL).first.click()
            textarea.first.wait_for(state="visible", timeout=5000)
        textarea.first.fill(evaluation.comment)

    modal.locator(selectors.GRADE_SAVE_BTN_REL).first.click()
    time.sleep(settings.pacing_seconds)


def cancel_grade_modal(page: Page) -> None:
    """Close the open grade modal WITHOUT saving (Отмена; Escape as a fallback)."""
    modal = page.locator(selectors.GRADE_MODAL)
    cancel = modal.locator(selectors.GRADE_CANCEL_BTN_REL)
    if cancel.count() > 0:
        cancel.first.click()
    else:
        page.keyboard.press("Escape")


def complete_lesson(page: Page, dry_run: bool) -> None:
    """Click "Завершить урок" to finish the lesson, unless dry_run."""
    if dry_run:
        return
    page.locator(selectors.COMPLETE_LESSON_BTN).click()
