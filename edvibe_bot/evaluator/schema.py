from enum import Enum

from pydantic import BaseModel, field_validator, model_validator

# Default per-exercise max when the live max is unknown. Edvibe scores are
# per-exercise (e.g. /5), NOT a fixed /10 — always thread the real score_max.
DEFAULT_SCORE_MAX = 10


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
    # The per-exercise maximum this score is on. Clamping uses [0, score_max].
    score_max: int = DEFAULT_SCORE_MAX

    @model_validator(mode="after")
    def _clamp_score_to_max(self) -> "Evaluation":
        upper = self.score_max if self.score_max and self.score_max > 0 else DEFAULT_SCORE_MAX
        if self.score < 0:
            object.__setattr__(self, "score", 0)
        elif self.score > upper:
            object.__setattr__(self, "score", upper)
        return self

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
    # Per-exercise max (e.g. 5). Drives the rubric "score out of N" + the clamp.
    score_max: int = DEFAULT_SCORE_MAX
