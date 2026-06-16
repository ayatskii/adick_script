"""Shared fixtures: a TestClient pointed at a throwaway DB path so tests never
touch the real edvibe.sqlite, and a fresh RunManager per test."""

from __future__ import annotations

import importlib

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def empty_db(tmp_path, monkeypatch):
    """Point the backend at a non-existent DB so seed fallback kicks in."""
    db = tmp_path / "does-not-exist.sqlite"
    monkeypatch.setenv("DB_PATH", str(db))
    # Drop the cached Settings load so config picks up the env override.
    from backend import config as backend_config

    backend_config.reset_settings_cache()
    return str(db)


@pytest.fixture()
def client(empty_db):
    # Reload jobs to get a fresh RunManager singleton per test, so run state
    # doesn't leak across tests.
    from backend import jobs as jobs_module

    importlib.reload(jobs_module)
    from backend.routes import runs as runs_module
    from backend.routes import data as data_module

    importlib.reload(runs_module)
    importlib.reload(data_module)
    from backend import app as app_module

    importlib.reload(app_module)

    with TestClient(app_module.app) as c:
        yield c
