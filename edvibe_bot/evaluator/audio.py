# edvibe_bot/evaluator/audio.py
"""Audio download (Playwright request context) + OpenAI transcription.

download_audio NEVER raises — it returns None on any failure so the runner
FLAGS the exercise. transcribe uses bounded retry/backoff on the primary
model, falls back to whisper-1, and raises only if BOTH models are exhausted
(the runner wraps it in try/except and FLAGS on failure).
"""

from __future__ import annotations

import io
import time

from playwright.sync_api import BrowserContext

try:  # the audit module is a sibling; tolerate it not being present yet
    from edvibe_bot.audit.log import get_logger
except Exception:  # pragma: no cover - fallback mirrors get_logger(name) contract
    import logging

    def get_logger(name: str) -> "logging.Logger":
        return logging.getLogger(name)

_log = get_logger(__name__)

# bounded retry/backoff per model
_MAX_ATTEMPTS = 3
_BASE_BACKOFF_SECONDS = 1.0


def download_audio(context: BrowserContext, audio_url: str) -> "bytes | None":
    """Fetch audio bytes via Playwright's request context.

    Returns None on ANY failure (non-200, empty body, or exception).
    NEVER raises — uncertainty defaults to NOT acting.
    """
    try:
        response = context.request.get(audio_url)
    except Exception as exc:  # network/timeout/teardown — degrade to flagging
        _log.warning("download_audio request failed for %s: %s", audio_url, exc)
        return None

    try:
        if not getattr(response, "ok", False):
            _log.warning(
                "download_audio non-OK status %s for %s",
                getattr(response, "status", "?"),
                audio_url,
            )
            return None
        data = response.body()
    except Exception as exc:
        _log.warning("download_audio body read failed for %s: %s", audio_url, exc)
        return None

    if not data:
        _log.warning("download_audio got empty body for %s", audio_url)
        return None
    return data


def _make_client(settings: "Settings"):
    """Construct an OpenAI client. Isolated so tests can monkeypatch it."""
    from openai import OpenAI

    return OpenAI(api_key=settings.openai_api_key)


def _audio_file(audio_bytes: bytes) -> io.BytesIO:
    """Wrap raw bytes in an in-memory file-like with a .name.

    The OpenAI SDK uses the filename extension to infer the audio format,
    so the BytesIO MUST carry a .name attribute.
    """
    buf = io.BytesIO(audio_bytes)
    buf.name = "audio.ogg"
    return buf


def _transcribe_once(client, model: str, audio_bytes: bytes) -> str:
    """Single transcription call. Returns the transcript text."""
    result = client.audio.transcriptions.create(
        model=model,
        file=_audio_file(audio_bytes),
    )
    # SDK may return an object with .text or (in fakes) a plain string
    text = getattr(result, "text", result)
    return str(text)


def _transcribe_with_model(client, model: str, audio_bytes: bytes) -> str:
    """Bounded retry/backoff for one model. Raises if all attempts fail."""
    last_exc: "Exception | None" = None
    for attempt in range(_MAX_ATTEMPTS):
        try:
            return _transcribe_once(client, model, audio_bytes)
        except Exception as exc:
            last_exc = exc
            _log.warning(
                "transcribe attempt %d/%d failed for model %s: %s",
                attempt + 1,
                _MAX_ATTEMPTS,
                model,
                exc,
            )
            if attempt + 1 < _MAX_ATTEMPTS:
                time.sleep(_BASE_BACKOFF_SECONDS * (2 ** attempt))
    assert last_exc is not None
    raise last_exc


def transcribe(audio_bytes: bytes, settings: "Settings") -> str:
    """Transcribe audio with the primary model, falling back to whisper-1.

    Raises only if BOTH the primary and fallback models are exhausted; the
    runner catches that and FLAGS the exercise.
    """
    client = _make_client(settings)
    try:
        return _transcribe_with_model(
            client, settings.transcription_model, audio_bytes
        )
    except Exception as primary_exc:
        _log.warning(
            "primary transcription model %s failed; falling back to %s",
            settings.transcription_model,
            settings.fallback_transcription_model,
        )
        try:
            return _transcribe_with_model(
                client, settings.fallback_transcription_model, audio_bytes
            )
        except Exception as fallback_exc:
            raise RuntimeError(
                "transcription failed on both "
                f"{settings.transcription_model} ({primary_exc}) and "
                f"{settings.fallback_transcription_model} ({fallback_exc})"
            ) from fallback_exc
