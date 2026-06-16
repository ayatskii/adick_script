from enum import Enum

from pydantic import BaseModel, field_validator


class ExerciseType(str, Enum):
    AUDIO = "audio"
    TEXT = "text"
    AUTO_CHECKED = "auto_checked"
    MANUAL_UNKNOWN = "manual_unknown"


class Evaluation(BaseModel):
    score: int
    comment: str
    rationale: str
    confidence: float

    @field_validator("score")
    @classmethod
    def _clamp_score(cls, v: int) -> int:
        if v < 0:
            return 0
        if v > 10:
            return 10
        return v

    @field_validator("confidence")
    @classmethod
    def _clamp_confidence(cls, v: float) -> float:
        if v < 0.0:
            return 0.0
        if v > 1.0:
            return 1.0
        return v


class EvalRequest(BaseModel):
    exercise_type: ExerciseType
    section: str
    prompt_text: str
    student_answer: str
