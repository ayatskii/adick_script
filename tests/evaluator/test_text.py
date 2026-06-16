import json
import types

import pytest

import edvibe_bot.evaluator.text as text_mod
from edvibe_bot.config import Settings
from edvibe_bot.evaluator.schema import EvalRequest, Evaluation, ExerciseType


def _settings() -> Settings:
    return Settings(
        edvibe_login="x",
        edvibe_password="y",
        openai_api_key="sk-test",
    )


def _req() -> EvalRequest:
    return EvalRequest(
        exercise_type=ExerciseType.TEXT,
        section="Writing",
        prompt_text="Describe your weekend.",
        student_answer="I went to the park and played football.",
    )


def _completion(content: str):
    """Mimic the openai chat.completions.create return shape."""
    message = types.SimpleNamespace(content=content)
    choice = types.SimpleNamespace(message=message)
    return types.SimpleNamespace(choices=[choice])


class _FakeCompletions:
    def __init__(self, behaviors):
        # behaviors: list of either an Exception instance (raise) or str (return content)
        self._behaviors = list(behaviors)
        self.calls = 0
        self.last_kwargs = None

    def create(self, **kwargs):
        self.last_kwargs = kwargs
        behavior = self._behaviors[self.calls]
        self.calls += 1
        if isinstance(behavior, Exception):
            raise behavior
        return _completion(behavior)


class _FakeClient:
    def __init__(self, behaviors):
        completions = _FakeCompletions(behaviors)
        self.chat = types.SimpleNamespace(completions=completions)
        self._completions = completions


def _install_fake(monkeypatch, behaviors):
    holder = {}

    def _factory(*args, **kwargs):
        client = _FakeClient(behaviors)
        holder["client"] = client
        return client

    monkeypatch.setattr(text_mod.openai, "OpenAI", _factory)
    monkeypatch.setattr(text_mod.time, "sleep", lambda *_a, **_k: None)
    return holder


def test_success_parses_and_clamps(monkeypatch):
    payload = json.dumps(
        {"score": 15, "comment": "Nice work", "rationale": "ok", "confidence": 2.0}
    )
    holder = _install_fake(monkeypatch, [payload])
    result = text_mod.evaluate(_req(), _settings())
    assert isinstance(result, Evaluation)
    assert result.score == 10           # clamped from 15
    assert result.confidence == 1.0     # clamped from 2.0
    assert result.comment == "Nice work"
    assert holder["client"]._completions.calls == 1


def test_uses_evaluation_model(monkeypatch):
    payload = json.dumps(
        {"score": 5, "comment": "ok", "rationale": "r", "confidence": 0.7}
    )
    holder = _install_fake(monkeypatch, [payload])
    settings = _settings()
    text_mod.evaluate(_req(), settings)
    assert holder["client"]._completions.last_kwargs["model"] == settings.evaluation_model


def test_transient_error_then_success_retries(monkeypatch):
    payload = json.dumps(
        {"score": 6, "comment": "good", "rationale": "r", "confidence": 0.8}
    )
    holder = _install_fake(monkeypatch, [RuntimeError("boom"), payload])
    result = text_mod.evaluate(_req(), _settings())
    assert result.score == 6
    assert result.confidence == 0.8
    assert holder["client"]._completions.calls == 2


def test_persistent_failure_returns_parse_failed(monkeypatch):
    holder = _install_fake(
        monkeypatch, [RuntimeError("a"), RuntimeError("b"), RuntimeError("c")]
    )
    result = text_mod.evaluate(_req(), _settings())
    assert result == Evaluation(
        score=0, comment="", rationale="parse_failed", confidence=0.0
    )
    assert holder["client"]._completions.calls == 3


def test_unparseable_json_returns_parse_failed(monkeypatch):
    holder = _install_fake(
        monkeypatch, ["not json at all", "still not json", "nope"]
    )
    result = text_mod.evaluate(_req(), _settings())
    assert result.rationale == "parse_failed"
    assert result.score == 0
    assert result.confidence == 0.0
