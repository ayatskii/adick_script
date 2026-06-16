import pytest

from edvibe_bot.config import ConfigError, Settings, load_settings


def _write_env(tmp_path, body: str) -> str:
    env_file = tmp_path / ".env"
    env_file.write_text(body)
    return str(env_file)


def _clear_ambient(monkeypatch) -> None:
    monkeypatch.delenv("EDVIBE_LOGIN", raising=False)
    monkeypatch.delenv("EDVIBE_PASSWORD", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("MARATHON_NAME", raising=False)
    monkeypatch.delenv("CURATOR_NAME", raising=False)
    monkeypatch.delenv("CONFIDENCE_THRESHOLD", raising=False)


def test_defaults_applied(monkeypatch, tmp_path):
    _clear_ambient(monkeypatch)
    env_path = _write_env(
        tmp_path,
        "EDVIBE_LOGIN=teacher\nEDVIBE_PASSWORD=secret\nOPENAI_API_KEY=sk-test\n",
    )
    settings = load_settings(env_path)
    assert settings.edvibe_login == "teacher"
    assert settings.edvibe_password == "secret"
    assert settings.openai_api_key == "sk-test"
    assert settings.marathon_name == "Pre-IELTS"
    assert settings.curator_name == "Mister Adilet"
    assert settings.transcription_model == "gpt-4o-transcribe"
    assert settings.evaluation_model == "gpt-4o"
    assert settings.fallback_transcription_model == "whisper-1"
    assert settings.confidence_threshold == 0.6
    assert settings.pacing_seconds == 1.5
    assert settings.storage_state_path == "storage_state.json"
    assert settings.db_path == "edvibe.sqlite"
    assert settings.audit_jsonl_path == "reports/audit.jsonl"


def test_values_read_from_env(monkeypatch, tmp_path):
    _clear_ambient(monkeypatch)
    env_path = _write_env(
        tmp_path,
        "EDVIBE_LOGIN=alice\n"
        "EDVIBE_PASSWORD=pw\n"
        "OPENAI_API_KEY=sk-zzz\n"
        "MARATHON_NAME=Pre-IELTS\n"
        "CURATOR_NAME=Mister Adilet\n"
        "CONFIDENCE_THRESHOLD=0.8\n",
    )
    settings = load_settings(env_path)
    assert settings.edvibe_login == "alice"
    assert settings.openai_api_key == "sk-zzz"
    assert settings.confidence_threshold == 0.8


def test_os_environ_overlays_dotenv(monkeypatch, tmp_path):
    _clear_ambient(monkeypatch)
    env_path = _write_env(
        tmp_path,
        "EDVIBE_LOGIN=fromfile\nEDVIBE_PASSWORD=pw\nOPENAI_API_KEY=sk-file\n",
    )
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fromenv")
    settings = load_settings(env_path)
    assert settings.openai_api_key == "sk-fromenv"
    assert settings.edvibe_login == "fromfile"


@pytest.mark.parametrize("missing", ["EDVIBE_LOGIN", "EDVIBE_PASSWORD", "OPENAI_API_KEY"])
def test_missing_required_secret_raises(monkeypatch, tmp_path, missing):
    _clear_ambient(monkeypatch)
    lines = {
        "EDVIBE_LOGIN": "teacher",
        "EDVIBE_PASSWORD": "secret",
        "OPENAI_API_KEY": "sk-test",
    }
    del lines[missing]
    body = "".join(f"{k}={v}\n" for k, v in lines.items())
    env_path = _write_env(tmp_path, body)
    with pytest.raises(ConfigError):
        load_settings(env_path)


@pytest.mark.parametrize("blank", ["EDVIBE_LOGIN", "EDVIBE_PASSWORD", "OPENAI_API_KEY"])
def test_blank_required_secret_raises(monkeypatch, tmp_path, blank):
    _clear_ambient(monkeypatch)
    lines = {
        "EDVIBE_LOGIN": "teacher",
        "EDVIBE_PASSWORD": "secret",
        "OPENAI_API_KEY": "sk-test",
    }
    lines[blank] = ""
    body = "".join(f"{k}={v}\n" for k, v in lines.items())
    env_path = _write_env(tmp_path, body)
    with pytest.raises(ConfigError):
        load_settings(env_path)


@pytest.mark.parametrize("bad", ["0", "0.0", "1.5", "-0.2"])
def test_bad_confidence_threshold_raises(monkeypatch, tmp_path, bad):
    _clear_ambient(monkeypatch)
    env_path = _write_env(
        tmp_path,
        "EDVIBE_LOGIN=teacher\n"
        "EDVIBE_PASSWORD=secret\n"
        "OPENAI_API_KEY=sk-test\n"
        f"CONFIDENCE_THRESHOLD={bad}\n",
    )
    with pytest.raises(ConfigError):
        load_settings(env_path)


def test_confidence_threshold_one_is_allowed(monkeypatch, tmp_path):
    _clear_ambient(monkeypatch)
    env_path = _write_env(
        tmp_path,
        "EDVIBE_LOGIN=teacher\n"
        "EDVIBE_PASSWORD=secret\n"
        "OPENAI_API_KEY=sk-test\n"
        "CONFIDENCE_THRESHOLD=1\n",
    )
    settings = load_settings(env_path)
    assert settings.confidence_threshold == 1.0
