# tests/evaluator/test_audio.py
import io

import pytest

import edvibe_bot.evaluator.audio as audio_mod
from edvibe_bot.evaluator.audio import download_audio, transcribe, _sniff_extension


# ---- fakes for the Playwright request context -------------------------------

class _FakeResponse:
    def __init__(self, ok: bool, body: bytes = b"", status: int = 200):
        self.ok = ok
        self.status = status
        self._body = body

    def body(self) -> bytes:
        return self._body


class _FakeRequest:
    """Mirrors context.request.get(url) -> response (or raising)."""

    def __init__(self, response=None, exc: Exception | None = None):
        self._response = response
        self._exc = exc
        self.calls: list[str] = []

    def get(self, url, **kwargs):
        self.calls.append(url)
        if self._exc is not None:
            raise self._exc
        return self._response


class _FakeContext:
    def __init__(self, request):
        self.request = request


# ---- fakes for the OpenAI client --------------------------------------------

class _Recorder:
    """Records each transcription call's model + raises/returns per script."""

    def __init__(self, script):
        # script: list of ("raise", Exception) or ("return", text)
        self._script = list(script)
        self.models: list[str] = []
        self.filenames: list[str] = []

    def _next(self, *, model, file, **kwargs):
        self.models.append(model)
        # the API receives an in-memory file-like with a .name attribute
        self.filenames.append(getattr(file, "name", None))
        kind, payload = self._script.pop(0)
        if kind == "raise":
            raise payload
        return payload


class _Transcriptions:
    def __init__(self, recorder):
        self._recorder = recorder

    def create(self, **kwargs):
        return self._recorder._next(**kwargs)


class _Audio:
    def __init__(self, recorder):
        self.transcriptions = _Transcriptions(recorder)


class _FakeOpenAI:
    def __init__(self, recorder):
        self.audio = _Audio(recorder)


class _FakeSettings:
    transcription_model = "gpt-4o-transcribe"
    fallback_transcription_model = "whisper-1"
    openai_api_key = "sk-test"


# ---- download_audio ---------------------------------------------------------

def test_download_audio_returns_bytes_on_success():
    req = _FakeRequest(response=_FakeResponse(ok=True, body=b"OGGDATA"))
    ctx = _FakeContext(req)
    assert download_audio(ctx, "https://edvibe.com/a.ogg") == b"OGGDATA"
    assert req.calls == ["https://edvibe.com/a.ogg"]


def test_download_audio_returns_none_on_non_200():
    req = _FakeRequest(response=_FakeResponse(ok=False, status=403, body=b""))
    ctx = _FakeContext(req)
    assert download_audio(ctx, "https://edvibe.com/a.ogg") is None


def test_download_audio_returns_none_on_exception():
    req = _FakeRequest(exc=RuntimeError("network down"))
    ctx = _FakeContext(req)
    assert download_audio(ctx, "https://edvibe.com/a.ogg") is None


def test_download_audio_returns_none_on_empty_body():
    req = _FakeRequest(response=_FakeResponse(ok=True, body=b""))
    ctx = _FakeContext(req)
    assert download_audio(ctx, "https://edvibe.com/a.ogg") is None


# ---- transcribe -------------------------------------------------------------

def _patch_client(monkeypatch, recorder):
    monkeypatch.setattr(
        audio_mod, "_make_client", lambda settings: _FakeOpenAI(recorder)
    )
    # make retries instant
    monkeypatch.setattr(audio_mod.time, "sleep", lambda *_a, **_k: None)


def test_sniff_extension_detects_real_formats():
    assert _sniff_extension(b"ID3\x04\x00\x00") == "mp3"     # edvibe recordings
    assert _sniff_extension(b"\xff\xfb\x90\x00") == "mp3"     # MPEG frame sync
    assert _sniff_extension(b"OggS\x00\x02\x00") == "ogg"
    assert _sniff_extension(b"RIFF\x00\x00\x00\x00WAVEfmt ") == "wav"
    assert _sniff_extension(b"\x1aE\xdf\xa3stuff") == "webm"
    assert _sniff_extension(b"\x00\x00\x00\x20ftypM4A ") == "m4a"
    assert _sniff_extension(b"unrecognized bytes") == "mp3"   # default to edvibe's mp3


def test_transcribe_returns_text_on_first_success(monkeypatch):
    rec = _Recorder([("return", "hello world")])
    _patch_client(monkeypatch, rec)
    out = transcribe(b"ID3\x04 mp3 body bytes", _FakeSettings())
    assert out == "hello world"
    assert rec.models == ["gpt-4o-transcribe"]
    # MP3 bytes → upload filename carries the MATCHING extension, so the strict
    # primary model (gpt-4o-transcribe) accepts it instead of rejecting .ogg.
    assert rec.filenames[0] == "audio.mp3"


def test_transcribe_unwraps_object_with_text_attr(monkeypatch):
    class _Resp:
        text = "from attr"

    rec = _Recorder([("return", _Resp())])
    _patch_client(monkeypatch, rec)
    assert transcribe(b"OGGDATA", _FakeSettings()) == "from attr"


def test_transcribe_falls_back_to_whisper_after_primary_persistent_failure(monkeypatch):
    # primary fails on every attempt, whisper-1 then succeeds
    rec = _Recorder(
        [
            ("raise", RuntimeError("boom1")),
            ("raise", RuntimeError("boom2")),
            ("raise", RuntimeError("boom3")),
            ("return", "fallback text"),
        ]
    )
    _patch_client(monkeypatch, rec)
    out = transcribe(b"OGGDATA", _FakeSettings())
    assert out == "fallback text"
    # primary tried 3x, then fell back to whisper-1
    assert rec.models[:3] == ["gpt-4o-transcribe"] * 3
    assert rec.models[3] == "whisper-1"


def test_transcribe_raises_when_both_models_fail(monkeypatch):
    rec = _Recorder([("raise", RuntimeError("x"))] * 6)
    _patch_client(monkeypatch, rec)
    with pytest.raises(Exception):
        transcribe(b"OGGDATA", _FakeSettings())
    # both models were exhausted (3 attempts each)
    assert rec.models == (["gpt-4o-transcribe"] * 3) + (["whisper-1"] * 3)
