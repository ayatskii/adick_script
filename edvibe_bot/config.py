"""Configuration: env-backed Settings + loader for the Edvibe grader bot."""

from __future__ import annotations

import os

from dotenv import dotenv_values
from pydantic import BaseModel, ValidationError, field_validator


class ConfigError(Exception):
    """Raised when configuration is missing or invalid."""


# NOTE: the 0-10 score scale is intentionally fixed in the Evaluation clamp
# validator (evaluator/schema.py), NOT configurable here (spec §4.1 "score scale").
class Settings(BaseModel):
    edvibe_login: str
    edvibe_password: str
    openai_api_key: str
    marathon_name: str = "Pre-IELTS"
    curator_name: str = "Mister Adilet"
    transcription_model: str = "gpt-4o-transcribe"
    evaluation_model: str = "gpt-4o"
    fallback_transcription_model: str = "whisper-1"
    confidence_threshold: float = 0.6
    pacing_seconds: float = 1.5
    storage_state_path: str = "storage_state.json"
    db_path: str = "edvibe.sqlite"
    audit_jsonl_path: str = "reports/audit.jsonl"

    @field_validator("confidence_threshold")
    @classmethod
    def _validate_confidence_threshold(cls, value: float) -> float:
        if not (0 < value <= 1):
            raise ConfigError(
                f"confidence_threshold must satisfy 0 < value <= 1, got {value!r}"
            )
        return value


# Maps env var names -> Settings field names. Only these keys are read from the
# environment; everything else falls back to the Settings field defaults.
_ENV_KEYS: dict[str, str] = {
    "EDVIBE_LOGIN": "edvibe_login",
    "EDVIBE_PASSWORD": "edvibe_password",
    "OPENAI_API_KEY": "openai_api_key",
    "MARATHON_NAME": "marathon_name",
    "CURATOR_NAME": "curator_name",
    "TRANSCRIPTION_MODEL": "transcription_model",
    "EVALUATION_MODEL": "evaluation_model",
    "FALLBACK_TRANSCRIPTION_MODEL": "fallback_transcription_model",
    "CONFIDENCE_THRESHOLD": "confidence_threshold",
    "PACING_SECONDS": "pacing_seconds",
    "STORAGE_STATE_PATH": "storage_state_path",
    "DB_PATH": "db_path",
    "AUDIT_JSONL_PATH": "audit_jsonl_path",
}

_REQUIRED_ENV_KEYS = ("EDVIBE_LOGIN", "EDVIBE_PASSWORD", "OPENAI_API_KEY")


def load_settings(env_path: str = ".env") -> Settings:
    """Read settings from ``env_path`` (.env), overlaid by ``os.environ``.

    Raises ``ConfigError`` if a required secret is missing or blank, or if any
    value fails validation.
    """
    # dotenv_values does not mutate the process environment; os.environ overlays it.
    file_values = dotenv_values(env_path)
    merged: dict[str, str] = {}
    for env_key in _ENV_KEYS:
        value = os.environ.get(env_key, file_values.get(env_key))
        if value is not None:
            merged[env_key] = value

    for required in _REQUIRED_ENV_KEYS:
        value = merged.get(required)
        if value is None or value.strip() == "":
            raise ConfigError(f"Missing required secret: {required}")

    field_kwargs = {_ENV_KEYS[k]: v for k, v in merged.items()}

    try:
        return Settings(**field_kwargs)
    except ConfigError:
        raise
    except ValidationError as exc:
        raise ConfigError(str(exc)) from exc
