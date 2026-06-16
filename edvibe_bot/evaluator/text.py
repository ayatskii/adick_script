import json
import time

import openai

from edvibe_bot.audit.log import get_logger
from edvibe_bot.evaluator.prompts import build_messages
from edvibe_bot.evaluator.schema import EvalRequest, Evaluation

logger = get_logger(__name__)

_MAX_ATTEMPTS = 3
_BASE_BACKOFF_SECONDS = 1.0

_PARSE_FAILED = Evaluation(
    score=0, comment="", rationale="parse_failed", confidence=0.0
)


def _parse(content: "str | None") -> "Evaluation | None":
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
            evaluation = _parse(content)
            if evaluation is not None:
                return evaluation
            logger.warning(
                "evaluate: unparseable OpenAI response on attempt %d/%d",
                attempt + 1,
                _MAX_ATTEMPTS,
            )
        except Exception as exc:  # noqa: BLE001 - bounded retry around the I/O call
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
