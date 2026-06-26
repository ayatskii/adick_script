"""CLI entrypoint for the Edvibe grader bot core.

Usage:
    python -m edvibe_bot.main --mode dry_run --student "Анель" --headed
"""

from __future__ import annotations

import argparse
import json
import sys

from edvibe_bot.config import load_settings
from edvibe_bot.runner import RunConfig, run
from edvibe_bot.state.store import Store


def build_run_config(argv: list[str], default_confidence: float = 0.6) -> RunConfig:
    """Parse CLI args into a RunConfig. Pure: no browser, no network, no DB.

    - ``--mode`` is required; only ``full_auto`` submits. ``dry_run``/``review``
      never touch the platform.
    - ``--student`` is repeatable and accumulates into a list (None if absent).
    - ``--max-students`` / ``--max-lessons`` parse as ints (None if absent).
    - ``--headed`` is a boolean flag.
    - ``--confidence`` overrides ``default_confidence`` when supplied; the
      resolved threshold is validated ``0 < t <= 1`` (else argparse error ->
      SystemExit), so a CLI value *or* a misconfigured default cannot slip
      through.
    """
    parser = argparse.ArgumentParser(
        prog="edvibe_bot",
        description="Grade Pre-IELTS 'Awaiting' homework for Mr. Adilet's students.",
    )
    parser.add_argument(
        "--mode",
        required=True,
        choices=["dry_run", "full_auto", "review"],
        help=(
            "Run mode. ONLY 'full_auto' submits scores / completes lessons. "
            "'dry_run' and 'review' never touch the platform (review records "
            "proposals to the ledger only)."
        ),
    )
    parser.add_argument(
        "--student",
        action="append",
        default=None,
        metavar="NAME",
        help="Restrict to this student (repeatable). Omit for all students.",
    )
    parser.add_argument(
        "--max-students",
        type=int,
        default=None,
        metavar="N",
        help="Cap the number of students processed (blast-radius limit).",
    )
    parser.add_argument(
        "--student-offset",
        type=int,
        default=0,
        metavar="N",
        help=(
            "Skip the first N students. With --max-students, processes the roster "
            "in batches (e.g. offset 0/25/50 ... with --max-students 25) across "
            "resumable runs — the practical way to cover all ~209 students."
        ),
    )
    parser.add_argument(
        "--max-lessons",
        type=int,
        default=None,
        metavar="N",
        help="Cap the number of lessons processed per student.",
    )
    parser.add_argument(
        "--headed",
        action="store_true",
        help="Run the browser headed (visible) instead of headless.",
    )
    parser.add_argument(
        "--all-lessons",
        action="store_true",
        help=(
            "Open EVERY lesson, including those the platform marks 'Done'. By "
            "default the bot skips Done lessons (they hold no ungraded work) for a "
            "large speed-up; pass this for a paranoid full sweep."
        ),
    )
    parser.add_argument(
        "--no-human-review",
        action="store_true",
        help=(
            "Let the AI grade EVERY answered exercise regardless of confidence — "
            "nothing is held back for human review (the confidence threshold is "
            "ignored). Unanswered exercises are still skipped (nothing to grade)."
        ),
    )
    parser.add_argument(
        "--confidence",
        type=float,
        default=None,
        metavar="T",
        help=(
            "Confidence threshold in (0, 1]; evaluations below it are flagged, "
            "never submitted. Overrides the configured default when supplied."
        ),
    )

    args = parser.parse_args(argv)

    threshold = args.confidence if args.confidence is not None else default_confidence
    if not (0 < threshold <= 1):
        parser.error(
            f"confidence threshold must satisfy 0 < t <= 1, got {threshold!r}"
        )

    return RunConfig(
        mode=args.mode,
        student_filter=args.student,
        student_offset=args.student_offset,
        max_students=args.max_students,
        max_lessons=args.max_lessons,
        headed=args.headed,
        confidence_threshold=threshold,
        all_lessons=args.all_lessons,
        ai_full_control=args.no_human_review,
    )


def _print_event(event: dict) -> None:
    """on_event callback: emit one JSON line per run event to stdout."""
    print(json.dumps(event, ensure_ascii=False), flush=True)


def main(argv: list[str] | None = None) -> int:
    """Wire settings -> store -> config -> run; print the final report."""
    argv = sys.argv[1:] if argv is None else argv
    # Allow --help / -h to print usage without requiring secrets to be present.
    if "--help" in argv or "-h" in argv:
        build_run_config(argv)  # argparse handles --help and calls sys.exit(0)
    settings = load_settings()
    store = Store(settings.db_path)
    store.init_schema()
    config = build_run_config(argv, settings.confidence_threshold)
    report = run(config, settings, store, on_event=_print_event)
    print(
        json.dumps(
            {
                "event": "run_report",
                "run_id": report.run_id,
                "graded": report.graded,
                "skipped": report.skipped,
                "flagged": report.flagged,
                "errors": report.errors,
                "completed_lessons": report.completed_lessons,
            },
            ensure_ascii=False,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
