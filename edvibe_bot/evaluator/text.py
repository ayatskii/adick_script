import json
import re
import time

import openai

from edvibe_bot.audit.log import get_logger
from edvibe_bot.errors import EvaluatorUnavailable
from edvibe_bot.evaluator.prompts import build_messages
from edvibe_bot.evaluator.schema import EvalRequest, Evaluation

logger = get_logger(__name__)

# Word tokens = runs of >=2 letters (unicode; covers Latin + Cyrillic).
_WORD_RE = re.compile(r"[^\W\d_]{2,}", re.UNICODE)
# Whisper's well-known outputs for silence/near-silence — these are NOT answers.
_SILENCE_HALLUCINATIONS = {
    "you", "thank you", "thanks", "thanks for watching", "thank you for watching",
    "bye", "okay", "ok", "hmm", "mm", "uh", "um", "the", "yeah",
}


def is_blank_answer(text: "str | None") -> bool:
    """PURE: True when a student answer (typed text or audio transcript) carries
    no gradeable content — empty/whitespace/punctuation-only, a single word, or a
    known Whisper silence hallucination. Such answers must be FLAGGED for review,
    never scored (a silent recording was scoring 0 instead of flagging)."""
    if not text or not text.strip():
        return True
    normalized = " ".join(text.lower().split()).strip(" .,!?-…")
    if normalized in _SILENCE_HALLUCINATIONS:
        return True
    return len(_WORD_RE.findall(text)) < 2

_MAX_ATTEMPTS = 3
_BASE_BACKOFF_SECONDS = 1.0

_PARSE_FAILED = Evaluation(
    score=0, comment="", rationale="parse_failed", confidence=0.0
)

# OpenAI error codes that will NEVER recover within a run — retrying them per
# exercise across the whole roster only buries the real cause under flags.
_FATAL_OPENAI_CODES = {
    "insufficient_quota",   # 429: billing/quota exhausted (the actual show-stopper)
    "invalid_api_key",      # 401: misconfigured key
    "account_deactivated",
}


def _is_fatal_openai_error(exc: Exception) -> bool:
    """True when ``exc`` from the OpenAI call is non-recoverable for the run
    (exhausted quota / bad key), as opposed to a transient hiccup worth retrying.

    Detection is defensive: prefer the SDK's structured ``code``/``type`` and the
    auth/permission exception classes, then fall back to the message text (the
    quota 429 reads "You exceeded your current quota")."""
    auth_types = tuple(
        getattr(openai, name)
        for name in ("AuthenticationError", "PermissionDeniedError")
        if hasattr(openai, name)
    )
    if auth_types and isinstance(exc, auth_types):
        return True
    code = getattr(exc, "code", None) or getattr(exc, "type", None)
    if isinstance(code, str) and code in _FATAL_OPENAI_CODES:
        return True
    msg = str(exc).lower()
    return (
        "insufficient_quota" in msg
        or "exceeded your current quota" in msg
        or "invalid_api_key" in msg
    )


def _parse(content: "str | None", score_max: int) -> "Evaluation | None":
    if not content:
        return None
    try:
        data = json.loads(content)
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(data, dict):
        return None
    try:
        return Evaluation(
            score=int(data["score"]),
            comment=str(data["comment"]),
            rationale=str(data["rationale"]),
            confidence=float(data["confidence"]),
            score_max=score_max,
        )
    except (KeyError, TypeError, ValueError):
        return None


def evaluate(req: "EvalRequest", settings: "Settings") -> "Evaluation":
    messages = build_messages(req)
    client = openai.OpenAI(api_key=settings.openai_api_key)

    last_error: "Exception | None" = None
    for attempt in range(_MAX_ATTEMPTS):
        try:
            response = client.chat.completions.create(
                model=settings.evaluation_model,
                messages=messages,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content
            evaluation = _parse(content, req.score_max)
            if evaluation is not None:
                return evaluation
            logger.warning(
                "evaluate: unparseable OpenAI response on attempt %d/%d",
                attempt + 1,
                _MAX_ATTEMPTS,
            )
        except Exception as exc:  # noqa: BLE001 - bounded retry around the I/O call
            if _is_fatal_openai_error(exc):
                # Quota exhausted / bad key: no retry, no parse_failed avalanche —
                # abort the run so the cause is unmissable.
                raise EvaluatorUnavailable(
                    "OpenAI evaluation unavailable — the API key cannot grade "
                    f"(non-recoverable error: {exc}). Check the OpenAI plan/billing "
                    "for this key. No grades were submitted."
                ) from exc
            last_error = exc
            logger.warning(
                "evaluate: OpenAI call failed on attempt %d/%d: %s",
                attempt + 1,
                _MAX_ATTEMPTS,
                exc,
            )

        if attempt < _MAX_ATTEMPTS - 1:
            time.sleep(_BASE_BACKOFF_SECONDS * (2**attempt))

    logger.error(
        "evaluate: giving up after %d attempts; flagging as parse_failed (last_error=%s)",
        _MAX_ATTEMPTS,
        last_error,
    )
    return _PARSE_FAILED
