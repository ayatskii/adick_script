class SelectorError(Exception):
    """Raised when an expected edvibe.com element/selector is not found."""


class EvaluatorUnavailable(Exception):
    """Raised when the LLM evaluator cannot run at all — e.g. the OpenAI key has
    exhausted its quota (HTTP 429 ``insufficient_quota``) or is invalid.

    This is non-recoverable WITHIN a run: every subsequent evaluation would fail
    the same way. The runner aborts the run loudly with this error instead of
    silently flagging the entire roster as a vague ``parse_failed`` — which is
    exactly what hid an exhausted-quota account behind ~1800 review flags."""
