import time

from playwright.sync_api import Page

from edvibe_bot import selectors
from edvibe_bot.config import Settings
from edvibe_bot.evaluator.schema import Evaluation
from edvibe_bot.scraper.lesson import Exercise


def grade_exercise(
    page: Page,
    exercise: Exercise,
    evaluation: Evaluation,
    settings: Settings,
    dry_run: bool,
) -> None:
    """Open the grade modal, enter score + comment, save.

    Independent second safety check: when dry_run is True we touch the
    platform NOT AT ALL. The runner is responsible for never passing
    dry_run=False outside full_auto, but this guard stands on its own.
    """
    if dry_run:
        return

    # Scope the grade trigger to THIS exercise's block (a section can hold
    # several ungraded exercises; a bare page-wide locator would be ambiguous).
    block = page.locator(selectors.EXERCISE_BLOCK).filter(
        has_text=ex_number_text(exercise.number)
    ).first if exercise.number else page.locator(selectors.EXERCISE_BLOCK).first
    block.locator(selectors.GRADE_EXERCISE_BTN).first.click()

    # Wait for the Vue grade modal ("Поставить оценку") to render.
    modal = page.locator(selectors.GRADE_MODAL)
    modal.wait_for(state="visible", timeout=15000)

    modal.locator(selectors.SCORE_INPUT_REL).fill(str(evaluation.score))

    # The comment field is hidden behind a toggle; flip it on, then fill.
    if evaluation.comment:
        toggle = modal.locator(selectors.COMMENT_TOGGLE_REL)
        textarea = modal.locator(selectors.COMMENT_INPUT_REL)
        if textarea.count() == 0:
            toggle.first.click()
            textarea.first.wait_for(state="visible", timeout=5000)
        textarea.first.fill(evaluation.comment)

    modal.locator(selectors.GRADE_SAVE_BTN_REL).first.click()
    time.sleep(settings.pacing_seconds)


def ex_number_text(number: str) -> str:
    """PURE: the leading exercise-number token used to disambiguate blocks."""
    return number.strip()


def complete_lesson(page: Page, dry_run: bool) -> None:
    """Click "Завершить урок" to finish the lesson, unless dry_run."""
    if dry_run:
        return
    page.locator(selectors.COMPLETE_LESSON_BTN).click()
