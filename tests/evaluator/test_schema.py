import pytest
from pydantic import ValidationError

from edvibe_bot.evaluator.schema import (
    Evaluation,
    EvalRequest,
    ExerciseType,
)


def test_exercise_type_values():
    assert ExerciseType.AUDIO.value == "audio"
    assert ExerciseType.TEXT.value == "text"
    assert ExerciseType.AUTO_CHECKED.value == "auto_checked"
    assert ExerciseType.MANUAL_UNKNOWN.value == "manual_unknown"


def test_score_clamped_high():
    assert Evaluation(score=15, comment="c", rationale="r", confidence=0.5).score == 10


def test_score_clamped_low():
    assert Evaluation(score=-3, comment="c", rationale="r", confidence=0.5).score == 0


def test_score_within_range_unchanged():
    assert Evaluation(score=7, comment="c", rationale="r", confidence=0.5).score == 7


def test_confidence_clamped_high():
    assert Evaluation(score=5, comment="c", rationale="r", confidence=2.0).confidence == 1.0


def test_confidence_clamped_low():
    assert Evaluation(score=5, comment="c", rationale="r", confidence=-1.0).confidence == 0.0


def test_confidence_within_range_unchanged():
    assert Evaluation(score=5, comment="c", rationale="r", confidence=0.6).confidence == 0.6


def test_eval_request_carries_prompt_and_answer():
    req = EvalRequest(
        exercise_type=ExerciseType.TEXT,
        section="Writing",
        prompt_text="Describe your weekend.",
        student_answer="I went to the park.",
    )
    assert req.exercise_type is ExerciseType.TEXT
    assert req.section == "Writing"
    assert req.prompt_text == "Describe your weekend."
    assert req.student_answer == "I went to the park."


def test_eval_request_accepts_audio_type():
    req = EvalRequest(
        exercise_type=ExerciseType.AUDIO,
        section="Speaking",
        prompt_text="Read the passage aloud.",
        student_answer="transcript text",
    )
    assert req.exercise_type is ExerciseType.AUDIO
