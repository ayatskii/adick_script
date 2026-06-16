from contextlib import contextmanager
from dataclasses import dataclass
from typing import Callable, Optional

from playwright.sync_api import sync_playwright

from edvibe_bot import selectors  # noqa: F401  (kept for parity with sibling modules)
from edvibe_bot.errors import SelectorError
from edvibe_bot.config import Settings
from edvibe_bot.audit.log import AuditLog, get_logger
from edvibe_bot.state.store import Store, LedgerEntry, LedgerStatus
from edvibe_bot.evaluator.schema import EvalRequest, ExerciseType
from edvibe_bot.auth.login import ensure_logged_in
from edvibe_bot.scraper.dashboard import open_marathon, list_students, Student
from edvibe_bot.scraper.progress import (
    open_progress,
    list_lessons,
    awaiting_lessons,
    open_lesson,
)
from edvibe_bot.scraper.lesson import list_exercises, Exercise
from edvibe_bot.evaluator import audio, text
from edvibe_bot.grader import poster

log = get_logger("edvibe_bot.runner")

_MANUAL_TYPES = {
    ExerciseType.AUDIO,
    ExerciseType.TEXT,
    ExerciseType.MANUAL_UNKNOWN,
}


@dataclass
class RunConfig:
    mode: str
    student_filter: "list[str] | None" = None
    max_students: "int | None" = None
    max_lessons: "int | None" = None
    headed: bool = False
    confidence_threshold: float = 0.6


@dataclass
class RunReport:
    run_id: str
    graded: int
    skipped: int
    flagged: int
    errors: int
    completed_lessons: int


EventCallback = Callable[[dict], None]


# Edvibe blocks the default headless automation fingerprint at login (the form
# fills but never authenticates). Disabling the AutomationControlled blink flag
# + a realistic user-agent is required for login to succeed headless.
_STEALTH_ARGS = ["--disable-blink-features=AutomationControlled"]
_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


@contextmanager
def _launch_context(headed: bool):
    """Yield a (playwright_cm, browser_context). Patched out in unit tests."""
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=not headed, args=_STEALTH_ARGS)
        context = browser.new_context(user_agent=_UA)
        try:
            yield context
        finally:
            context.close()
            browser.close()


def _emit(on_event: "Optional[EventCallback]", payload: dict) -> None:
    if on_event is not None:
        on_event(payload)


def _entry(
    *,
    student,
    lesson,
    exercise_id,
    ex,
    run_id,
    status,
    score=None,
    comment=None,
    confidence=None,
    submitted=False,
    dry_run=False,
) -> LedgerEntry:
    return LedgerEntry(
        student_id=student.id,
        lesson_id=lesson.id,
        exercise_id=exercise_id,
        student_name=student.name,
        lesson_name=lesson.name,
        exercise_no=ex.number,
        type=ex.type.value,
        proposed_score=score,
        proposed_comment=comment,
        confidence=confidence,
        submitted=submitted,
        dry_run=dry_run,
        run_id=run_id,
        status=status,
    )


def run(
    config: RunConfig,
    settings: Settings,
    store: Store,
    on_event: "Optional[EventCallback]" = None,
) -> RunReport:
    audit = AuditLog(store, settings.audit_jsonl_path)
    scope = {
        "student_filter": config.student_filter,
        "max_students": config.max_students,
        "max_lessons": config.max_lessons,
    }
    run_id = store.create_run(config.mode, scope)

    # ONLY full_auto submits; both dry_run and review never touch the platform.
    submit_allowed = config.mode == "full_auto"
    dry_run = config.mode != "full_auto"

    graded = skipped = flagged = errors = completed_lessons = 0

    with _launch_context(config.headed) as context:
        page = ensure_logged_in(context, settings)
        open_marathon(page, settings)

        students = list_students(page)
        if config.student_filter is not None:
            wanted = set(config.student_filter)
            students = [s for s in students if s.id in wanted]
        if config.max_students is not None:
            students = students[: config.max_students]

        for student in students:
            _emit(on_event, {"event": "student", "student_id": student.id})
            open_progress(page, student)
            lessons = awaiting_lessons(list_lessons(page))
            if config.max_lessons is not None:
                lessons = lessons[: config.max_lessons]

            for lesson in lessons:
                target = {
                    "student_id": student.id,
                    "lesson_id": lesson.id,
                }
                if store.is_lesson_completed(student.id, lesson.id):
                    skipped += 1
                    _emit(on_event, {"event": "lesson_skip", **target})
                    continue
                if store.get_lesson_status(student.id, lesson.id) in (
                    "in_progress",
                    "error",
                ):
                    flagged += 1
                    audit.record(
                        run_id,
                        "flag_lesson",
                        target,
                        {"reason": "sentinel_in_progress_or_error"},
                    )
                    _emit(on_event, {"event": "lesson_flag", **target})
                    continue

                try:
                    open_lesson(page, lesson)
                    # lesson_id derived from the lesson URL after navigation
                    # (open_lesson parsed it); falls back to the row id.
                    lesson_id = lesson.lesson_url_id or lesson.id
                    exercises = list_exercises(page, lesson_id)
                    manual = [
                        e
                        for e in exercises
                        if e.has_grade_button
                        and not e.is_graded
                        and e.type in _MANUAL_TYPES
                    ]
                    manual_count = len(manual)
                    graded_this_run = 0
                    blocked = False

                    for ex in manual:
                        ex_target = {
                            "student_id": student.id,
                            "lesson_id": lesson.id,
                            "exercise_no": ex.number,
                        }

                        # Independent guard: no stable id → never grade on a guess.
                        if not ex.element_id:
                            store.record_exercise(
                                _entry(
                                    student=student,
                                    lesson=lesson,
                                    exercise_id=f"__noid__{ex.number}",
                                    ex=ex,
                                    run_id=run_id,
                                    status=LedgerStatus.FLAGGED.value,
                                    comment="no_stable_id",
                                    submitted=False,
                                    dry_run=dry_run,
                                )
                            )
                            blocked = True
                            flagged += 1
                            audit.record(
                                run_id, "flag", ex_target, {"reason": "no_stable_id"}
                            )
                            continue

                        exercise_id = ex.element_id

                        if store.is_exercise_done(
                            student.id, lesson.id, exercise_id
                        ):
                            graded_this_run += 1
                            continue

                        if (
                            store.get_exercise_status(
                                student.id, lesson.id, exercise_id
                            )
                            == "in_progress"
                        ):
                            store.record_exercise(
                                _entry(
                                    student=student,
                                    lesson=lesson,
                                    exercise_id=exercise_id,
                                    ex=ex,
                                    run_id=run_id,
                                    status=LedgerStatus.FLAGGED.value,
                                    comment="prior_in_progress",
                                    submitted=False,
                                    dry_run=dry_run,
                                )
                            )
                            blocked = True
                            flagged += 1
                            audit.record(
                                run_id,
                                "flag",
                                ex_target,
                                {"reason": "prior_in_progress"},
                            )
                            continue

                        # ---- gather the answer (fail-safe on any failure) ----
                        answer = None
                        fail_reason = None
                        try:
                            if ex.type == ExerciseType.AUDIO:
                                blob = audio.download_audio(context, ex.audio_url)
                                if blob is None:
                                    fail_reason = "audio_download_failed"
                                else:
                                    answer = audio.transcribe(blob, settings)
                            else:
                                answer = ex.answer_text
                        except Exception:  # noqa: BLE001 - fail-safe to FLAG
                            fail_reason = "gather_failed"

                        if fail_reason is None and (
                            answer is None or not answer.strip()
                        ):
                            fail_reason = "empty_answer"

                        if fail_reason is not None:
                            store.record_exercise(
                                _entry(
                                    student=student,
                                    lesson=lesson,
                                    exercise_id=exercise_id,
                                    ex=ex,
                                    run_id=run_id,
                                    status=LedgerStatus.FLAGGED.value,
                                    comment=fail_reason,
                                    submitted=False,
                                    dry_run=dry_run,
                                )
                            )
                            blocked = True
                            flagged += 1
                            audit.record(
                                run_id, "flag", ex_target, {"reason": fail_reason}
                            )
                            continue

                        # ---- evaluate ----
                        eval_req_kwargs = {
                            "exercise_type": ex.type,
                            "section": ex.section,
                            "prompt_text": ex.prompt_text,
                            "student_answer": answer,
                        }
                        if ex.score_max is not None:
                            eval_req_kwargs["score_max"] = ex.score_max
                        evaluation = text.evaluate(
                            EvalRequest(**eval_req_kwargs),
                            settings,
                        )
                        audit.record(
                            run_id,
                            "evaluate",
                            ex_target,
                            {
                                "dry_run": dry_run,
                                "score": evaluation.score,
                                "confidence": evaluation.confidence,
                                "rationale": evaluation.rationale,
                            },
                        )

                        # Threshold-INDEPENDENT parse/zero-confidence guard.
                        if (
                            evaluation.rationale == "parse_failed"
                            or evaluation.confidence <= 0
                        ):
                            store.record_exercise(
                                _entry(
                                    student=student,
                                    lesson=lesson,
                                    exercise_id=exercise_id,
                                    ex=ex,
                                    run_id=run_id,
                                    status=LedgerStatus.FLAGGED.value,
                                    score=evaluation.score,
                                    comment=evaluation.comment,
                                    confidence=evaluation.confidence,
                                    submitted=False,
                                    dry_run=dry_run,
                                )
                            )
                            blocked = True
                            flagged += 1
                            audit.record(
                                run_id, "flag", ex_target, {"reason": "parse_failed"}
                            )
                            continue

                        # Not allowed to submit, or below confidence threshold.
                        if (not submit_allowed) or (
                            evaluation.confidence < config.confidence_threshold
                        ):
                            low_conf = (
                                evaluation.confidence < config.confidence_threshold
                            )
                            status = (
                                LedgerStatus.FLAGGED.value
                                if low_conf
                                else LedgerStatus.SKIPPED.value
                            )
                            store.record_exercise(
                                _entry(
                                    student=student,
                                    lesson=lesson,
                                    exercise_id=exercise_id,
                                    ex=ex,
                                    run_id=run_id,
                                    status=status,
                                    score=evaluation.score,
                                    comment=evaluation.comment,
                                    confidence=evaluation.confidence,
                                    submitted=False,
                                    dry_run=dry_run,
                                )
                            )
                            audit.record(
                                run_id,
                                "flag" if low_conf else "skip",
                                ex_target,
                                {
                                    "dry_run": dry_run,
                                    "low_confidence": low_conf,
                                    "confidence": evaluation.confidence,
                                },
                            )
                            if low_conf:
                                blocked = True
                                flagged += 1
                            else:
                                skipped += 1
                            continue

                        # ---- DURABILITY: claim in_progress BEFORE the click ----
                        store.record_exercise(
                            _entry(
                                student=student,
                                lesson=lesson,
                                exercise_id=exercise_id,
                                ex=ex,
                                run_id=run_id,
                                status=LedgerStatus.IN_PROGRESS.value,
                                score=evaluation.score,
                                comment=evaluation.comment,
                                confidence=evaluation.confidence,
                                submitted=False,
                                dry_run=dry_run,
                            )
                        )
                        poster.grade_exercise(
                            page, ex, evaluation, settings, dry_run=dry_run
                        )
                        store.record_exercise(
                            _entry(
                                student=student,
                                lesson=lesson,
                                exercise_id=exercise_id,
                                ex=ex,
                                run_id=run_id,
                                status=LedgerStatus.GRADED.value,
                                score=evaluation.score,
                                comment=evaluation.comment,
                                confidence=evaluation.confidence,
                                submitted=True,
                                dry_run=dry_run,
                            )
                        )
                        graded += 1
                        graded_this_run += 1
                        audit.record(
                            run_id,
                            "grade",
                            ex_target,
                            {"dry_run": dry_run, "score": evaluation.score},
                        )
                        _emit(on_event, {"event": "graded", **ex_target})

                    # ---- COMPLETION GATE ----
                    if (
                        submit_allowed
                        and manual_count > 0
                        and not blocked
                        and graded_this_run >= 1
                        and store.get_lesson_status(student.id, lesson.id)
                        not in ("in_progress", "error")
                    ):
                        store.record_lesson_completion_intent(
                            student.id, lesson.id, run_id
                        )
                        poster.complete_lesson(page, dry_run=dry_run)
                        store.record_lesson_completed(
                            student.id, lesson.id, run_id, dry_run
                        )
                        completed_lessons += 1
                        audit.record(
                            run_id,
                            "complete_lesson",
                            target,
                            {"dry_run": dry_run},
                        )
                        _emit(on_event, {"event": "lesson_complete", **target})

                except Exception:  # noqa: BLE001 - per-lesson boundary (covers SelectorError)
                    try:
                        page.screenshot(
                            path=f"reports/error-{run_id}-{student.id}-{lesson.id}.png"
                        )
                    except Exception as shot_err:  # noqa: BLE001
                        log.error("screenshot failed: %s", shot_err)
                        audit.record(
                            run_id,
                            "screenshot_failed",
                            target,
                            {"error": str(shot_err)},
                        )
                    store.record_exercise(
                        LedgerEntry(
                            student_id=student.id,
                            lesson_id=lesson.id,
                            exercise_id="__lesson__",
                            student_name=student.name,
                            lesson_name=lesson.name,
                            exercise_no="",
                            type="",
                            proposed_score=None,
                            proposed_comment=None,
                            confidence=None,
                            submitted=False,
                            dry_run=dry_run,
                            run_id=run_id,
                            status=LedgerStatus.ERROR.value,
                        )
                    )
                    errors += 1
                    audit.record(run_id, "lesson_error", target, {})
                    continue

    counts = {
        "graded": graded,
        "skipped": skipped,
        "flagged": flagged,
        "errors": errors,
        "completed_lessons": completed_lessons,
    }
    store.finish_run(run_id, "done", counts)
    return RunReport(
        run_id=run_id,
        graded=graded,
        skipped=skipped,
        flagged=flagged,
        errors=errors,
        completed_lessons=completed_lessons,
    )
