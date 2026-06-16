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
    page.locator(selectors.GRADE_EXERCISE_BTN).click()
    page.locator(selectors.SCORE_INPUT).fill(str(evaluation.score))
    page.locator(selectors.COMMENT_INPUT).fill(evaluation.comment)
    page.locator(selectors.GRADE_SAVE_BTN).click()
    time.sleep(settings.pacing_seconds)


def complete_lesson(page: Page, dry_run: bool) -> None:
    """Click "Завершить урок" to finish the lesson, unless dry_run."""
    if dry_run:
        return
    page.locator(selectors.COMPLETE_LESSON_BTN).click()
