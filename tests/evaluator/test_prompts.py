import json

from edvibe_bot.evaluator.prompts import RUBRIC_AUDIO, RUBRIC_TEXT, build_messages
from edvibe_bot.evaluator.schema import EvalRequest, ExerciseType


def test_rubrics_are_nonempty_strings():
    assert isinstance(RUBRIC_AUDIO, str) and RUBRIC_AUDIO.strip()
    assert isinstance(RUBRIC_TEXT, str) and RUBRIC_TEXT.strip()


def test_rubrics_reference_pre_ielts_level():
    assert "Pre-IELTS" in RUBRIC_AUDIO
    assert "Pre-IELTS" in RUBRIC_TEXT
    # CEFR A2-B1 target band
    assert "A2" in RUBRIC_AUDIO and "B1" in RUBRIC_AUDIO
    assert "A2" in RUBRIC_TEXT and "B1" in RUBRIC_TEXT


def _make_req(exercise_type: ExerciseType) -> EvalRequest:
    return EvalRequest(
        exercise_type=exercise_type,
        section="Speaking",
        prompt_text="PROMPT_MARKER describe your day",
        student_answer="ANSWER_MARKER I had a good day",
    )


def test_build_messages_returns_system_then_user():
    msgs = build_messages(_make_req(ExerciseType.TEXT))
    assert isinstance(msgs, list)
    assert len(msgs) == 2
    assert msgs[0]["role"] == "system"
    assert msgs[1]["role"] == "user"


def test_build_messages_embeds_prompt_and_answer_in_user():
    msgs = build_messages(_make_req(ExerciseType.TEXT))
    user_content = msgs[1]["content"]
    assert "PROMPT_MARKER describe your day" in user_content
    assert "ANSWER_MARKER I had a good day" in user_content


def test_build_messages_demands_strict_json_keys():
    msgs = build_messages(_make_req(ExerciseType.TEXT))
    blob = msgs[0]["content"] + msgs[1]["content"]
    for key in ("score", "comment", "rationale", "confidence"):
        assert key in blob
    assert "JSON" in blob


def test_build_messages_audio_uses_audio_rubric():
    msgs = build_messages(_make_req(ExerciseType.AUDIO))
    assert RUBRIC_AUDIO in msgs[0]["content"]
    assert RUBRIC_TEXT not in msgs[0]["content"]


def test_build_messages_text_uses_text_rubric():
    msgs = build_messages(_make_req(ExerciseType.TEXT))
    assert RUBRIC_TEXT in msgs[0]["content"]
    assert RUBRIC_AUDIO not in msgs[0]["content"]


def test_build_messages_manual_unknown_falls_back_to_text_rubric():
    msgs = build_messages(_make_req(ExerciseType.MANUAL_UNKNOWN))
    assert RUBRIC_TEXT in msgs[0]["content"]
