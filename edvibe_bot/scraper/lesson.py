from __future__ import annotations

from dataclasses import dataclass

from playwright.sync_api import Page

from edvibe_bot import selectors
from edvibe_bot.evaluator.schema import ExerciseType


@dataclass
class Exercise:
    section: str                # section heading text (from selectors.SECTION_NAV)
    number: str
    type: ExerciseType
    prompt_text: str            # the exercise task/question text (grounds evaluation)
    has_grade_button: bool
    audio_url: str | None
    answer_text: str | None
    element_id: str | None


def classify_exercise(
    has_grade_button: bool, has_audio: bool, has_text_answer: bool
) -> ExerciseType:
    """PURE: no grade button -> already auto-checked by the platform."""
    if not has_grade_button:
        return ExerciseType.AUTO_CHECKED
    if has_audio:
        return ExerciseType.AUDIO
    if has_text_answer:
        return ExerciseType.TEXT
    return ExerciseType.MANUAL_UNKNOWN


def _read_text(block, selector: str) -> str:
    # number / prompt are always present on a manual exercise block; read directly
    # (a count()-gate here diverges from the test doubles and yields empty strings).
    return block.locator(selector).inner_text().strip()


def list_exercises(page: Page) -> list[Exercise]:
    section = page.locator(selectors.SECTION_NAV).inner_text().strip()
    blocks = page.locator(selectors.EXERCISE_BLOCK)
    exercises: list[Exercise] = []
    for block in blocks.all():
        element_id = block.get_attribute(selectors.EXERCISE_ID_ATTR)
        number = _read_text(block, selectors.EXERCISE_NUMBER)
        prompt_text = _read_text(block, selectors.EXERCISE_PROMPT)

        audio_loc = block.locator(selectors.EXERCISE_AUDIO)
        has_audio = audio_loc.count() > 0
        audio_url = audio_loc.first.get_attribute("src") if has_audio else None

        answer_loc = block.locator(selectors.EXERCISE_TEXT_ANSWER)
        has_text_answer = answer_loc.count() > 0
        answer_text = answer_loc.inner_text().strip() if has_text_answer else None

        has_grade_button = block.locator(selectors.GRADE_EXERCISE_BTN).count() > 0
        ex_type = classify_exercise(has_grade_button, has_audio, has_text_answer)

        exercises.append(
            Exercise(
                section=section,
                number=number,
                type=ex_type,
                prompt_text=prompt_text,
                has_grade_button=has_grade_button,
                audio_url=audio_url,
                answer_text=answer_text,
                element_id=element_id,
            )
        )
    return exercises
