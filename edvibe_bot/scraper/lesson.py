from __future__ import annotations

import re
from dataclasses import dataclass

from playwright.sync_api import Page

from edvibe_bot import selectors
from edvibe_bot.evaluator.schema import ExerciseType

_SCORE_RE = re.compile(r"(\d+)\s*/\s*(\d+)")
_NUMBER_RE = re.compile(r"\d+(?:\.\d+)*")


@dataclass
class Exercise:
    section: str                # section heading text
    number: str                 # "1.1" / "1.2" (text inside the wrapper)
    type: ExerciseType
    prompt_text: str            # the exercise task/question text (grounds evaluation)
    has_grade_button: bool
    audio_url: str | None
    answer_text: str | None
    element_id: str | None      # composite "{lesson_id}:{number}" — stable key
    score_max: int | None = None   # per-exercise max (e.g. 5), read live
    is_graded: bool = False     # already graded on the platform → skip


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


def parse_estimate(estimate_text: str) -> tuple[bool, int | None]:
    """PURE: read the .exercise-estimate-view text.

    A graded exercise shows "Оценить упражнение: N/M" (e.g. "5/5") →
    (is_graded=True, score_max=M). An ungraded one shows the clickable
    "Оценить упражнение" with no score → (False, None — max unknown until the
    grade modal). Scores are per-exercise max, NOT a fixed /10.
    """
    match = _SCORE_RE.search(estimate_text or "")
    if match:
        return True, int(match.group(2))
    return False, None


def parse_number(block_text: str) -> str:
    """PURE: the exercise number ("1.1") is the leading numeric token."""
    match = _NUMBER_RE.search(block_text or "")
    return match.group(0) if match else ""


def _audio_src(audio_loc) -> str | None:
    """Read the audio element's currentSrc (direct media-a.edvibe.com MP3),
    falling back to src. None when there is no audio answer."""
    if audio_loc.count() == 0:
        return None
    first = audio_loc.first
    src = first.get_attribute("currentSrc") or first.get_attribute("src")
    return src or None


def list_exercises(
    page: Page, lesson_id: str | None, section: str = ""
) -> list[Exercise]:
    """Read every .exercise-wrapper on the current section page.

    Identity: there is no exercise id attribute on the live DOM. The stable key
    is the composite f"{lesson_id}:{number}", where `lesson_id` is the
    URL-derived lesson id (captured by open_lesson) and `number` is the visible
    exercise number ("1.1"). `section` is the current section heading (the
    runner iterates sections via ?section=n).
    """
    blocks = page.locator(selectors.EXERCISE_BLOCK)
    exercises: list[Exercise] = []
    for block in blocks.all():
        block_text = block.inner_text().strip()
        number = parse_number(block_text)

        audio_loc = block.locator(selectors.EXERCISE_AUDIO)
        audio_url = _audio_src(audio_loc)
        has_audio = audio_url is not None

        estimate_loc = block.locator(selectors.GRADE_ESTIMATE_VIEW)
        has_estimate = estimate_loc.count() > 0
        if has_estimate:
            is_graded, score_max = parse_estimate(estimate_loc.first.inner_text())
        else:
            is_graded, score_max = False, None

        # The grade trigger is only present/clickable while the exercise is
        # ungraded (a graded widget shows "N/M" instead of the trigger).
        has_grade_button = has_estimate and not is_graded

        # Text answers: for a non-audio manual exercise the student's written
        # response is the block text. AUDIO answers come from the transcript,
        # so answer_text stays None there.
        answer_text = None if has_audio else (block_text or None)
        has_text_answer = answer_text is not None

        ex_type = classify_exercise(has_grade_button, has_audio, has_text_answer)

        element_id = (
            f"{lesson_id}:{number}" if (lesson_id and number) else None
        )

        exercises.append(
            Exercise(
                section=section,
                number=number,
                type=ex_type,
                prompt_text=block_text,
                has_grade_button=has_grade_button,
                audio_url=audio_url,
                answer_text=answer_text,
                element_id=element_id,
                score_max=score_max,
                is_graded=is_graded,
            )
        )
    return exercises
