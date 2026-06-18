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
    element_id: str | None      # composite "{lesson_id}:s{section}:{number}" — stable key
    score_max: int | None = None   # per-exercise max (e.g. 5), read live
    is_graded: bool = False     # already graded on the platform → skip
    section_index: int = 0      # URL ?section=n the exercise lives under


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


def _read_written_answer(block) -> str | None:
    """Read the student's WRITTEN answer from the contenteditable answer editor.

    The block's innerText is the task INSTRUCTIONS, not the answer — grading that
    is how the bot graded blank work. The real answer lives in
    ``selectors.ANSWER_EDITOR``. Returns None when the editor is absent or empty
    (an unanswered exercise), so the runner's empty-answer guard flags it instead
    of grading the instructions.
    """
    editor = block.locator(selectors.ANSWER_EDITOR)
    parts = [(node.inner_text() or "").strip() for node in editor.all()]
    answer = "\n".join(part for part in parts if part).strip()
    return answer or None


def _audio_src(audio_loc) -> str | None:
    """Read the audio element's currentSrc (direct media-a.edvibe.com MP3),
    falling back to src. None when there is no audio answer."""
    if audio_loc.count() == 0:
        return None
    first = audio_loc.first
    src = first.get_attribute("currentSrc") or first.get_attribute("src")
    return src or None


def wait_lesson_ready(page: Page, timeout_s: int = 45) -> bool:
    """Block until the marathon lesson player has rendered: at least one section
    rail item exists AND the "Загрузка марафона" loading text is gone. The player
    typically needs ~6-8s after navigation. Returns True when ready."""
    for _ in range(timeout_s):
        page.wait_for_timeout(1000)
        ready = page.evaluate(
            """() => {
              const sec = document.querySelectorAll('.sections-list_item').length;
              const loading = (document.body.innerText||'').includes('Загрузка марафона');
              return sec > 0 && !loading;
            }"""
        )
        if ready:
            return True
    return False


def section_headings(page: Page) -> list[str]:
    """The content-section headings in the left rail, excluding the trailing
    "Завершить урок" (complete-lesson) item. Index == URL ?section=n."""
    items = page.locator(selectors.SECTION_ITEM)
    out: list[str] = []
    for item in items.all():
        text = (item.inner_text() or "").strip()
        if "Завершить урок" in text:
            continue
        out.append(text)
    return out


def _lesson_base_url(lesson_url: str) -> str:
    """PURE: strip a trailing ?section=n / &section=n from a lesson URL."""
    return re.sub(r"[?&]section=\d+", "", lesson_url)


def goto_section(page: Page, base_lesson_url: str, index: int) -> None:
    """Switch to section `index` by CLICKING its left-rail item.

    Sections switch in-app via these clicks. Navigating by ?section=n URL does
    NOT work — the SPA canonicalises the query straight back to section 0 (and a
    fresh goto re-triggers the slow "Загрузка марафона" full reload). If the rail
    is missing (e.g. we are not on the lesson), re-open the lesson first.
    """
    items = page.locator(selectors.SECTION_ITEM)
    if items.count() == 0:
        page.goto(_lesson_base_url(base_lesson_url))
        page.wait_for_load_state("networkidle")
        wait_lesson_ready(page)
        items = page.locator(selectors.SECTION_ITEM)
    items.nth(index).click()
    page.wait_for_timeout(3000)   # in-app section content render settle
    wait_lesson_ready(page)


def gather_exercises(
    page: Page, base_lesson_url: str, lesson_id: str | None
) -> list[Exercise]:
    """Walk every section of the opened lesson and collect all exercises. The
    lesson player renders one section at a time (switched by clicking the left-rail
    items), so we visit each in turn. Run with the page already on the opened
    lesson."""
    wait_lesson_ready(page)
    headings = section_headings(page)
    all_exercises: list[Exercise] = []
    for idx, heading in enumerate(headings):
        goto_section(page, base_lesson_url, idx)
        all_exercises.extend(
            list_exercises(page, lesson_id, section=heading, section_index=idx)
        )
    return all_exercises


def list_exercises(
    page: Page, lesson_id: str | None, section: str = "", section_index: int = 0
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

        # GRADED: `.exercise-estimate-view` renders ONLY for already-graded
        # exercises, showing the awarded "N/M" score. Its presence + a parseable
        # score is the authoritative "already graded" signal.
        estimate_loc = block.locator(selectors.GRADE_ESTIMATE_VIEW)
        if estimate_loc.count() > 0:
            is_graded, score_max = parse_estimate(estimate_loc.first.inner_text())
        else:
            is_graded, score_max = False, None

        # UNGRADED (awaiting): a manual-check exercise that is not yet graded
        # shows the clickable "Оценить упражнение" trigger (confirmed live). The
        # estimate-view is absent until a score is posted. Guard with `not
        # is_graded` so a graded widget that still echoes the trigger text never
        # re-grades.
        has_grade_button = (
            block.locator(selectors.GRADE_EXERCISE_BTN).count() > 0 and not is_graded
        )
        # The grade modal caps manual scores at SCORE_MAX (5); use it as the
        # per-exercise max for ungraded exercises until the modal is opened.
        if has_grade_button and score_max is None:
            score_max = selectors.SCORE_MAX

        # Text answers: read the student's WRITTEN response from the answer editor
        # (NOT the block instructions). AUDIO answers come from the transcript, so
        # answer_text stays None there. An empty editor → None → empty-answer flag.
        answer_text = None if has_audio else _read_written_answer(block)
        has_text_answer = answer_text is not None

        ex_type = classify_exercise(has_grade_button, has_audio, has_text_answer)

        # Composite stable key. Section index is part of the key because exercise
        # numbers ("1.1") can repeat across sections of the same lesson.
        element_id = (
            f"{lesson_id}:s{section_index}:{number}"
            if (lesson_id and number)
            else None
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
                section_index=section_index,
            )
        )
    return exercises
