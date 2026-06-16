"""Backend API configuration.

Reuses ``edvibe_bot.config.load_settings`` but tolerates a missing/blank
OPENAI key (and missing edvibe creds) so the read-only GET endpoints and the
``demo`` run mode work before any credentials are configured.
"""

from __future__ import annotations

import os
from functools import lru_cache

from edvibe_bot.config import ConfigError, Settings, load_settings

# CORS: the Vite dev server.
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# Where the bot-core SQLite store lives. Mirrors Settings.db_path default and
# may be overridden via DB_PATH (same env var the bot core honours).
DEFAULT_DB_PATH = "edvibe.sqlite"

_ENV_PATH = os.environ.get("EDVIBE_ENV_PATH", ".env")


def _safe_str(value: object) -> str:
    return value if isinstance(value, str) else ""


def db_path() -> str:
    """Resolve the SQLite path used for read-only store access.

    Order: explicit DB_PATH env -> Settings (if loadable) -> default. Never
    raises; a missing OPENAI key must not break read-only endpoints.
    """
    env_db = os.environ.get("DB_PATH")
    if env_db:
        return env_db
    settings = try_load_settings()
    if settings is not None:
        return settings.db_path
    return DEFAULT_DB_PATH


@lru_cache(maxsize=1)
def try_load_settings() -> "Settings | None":
    """Load full Settings if possible, else ``None`` (cached).

    Real run modes require this. Read-only endpoints and ``demo`` must not.
    """
    try:
        return load_settings(_ENV_PATH)
    except (ConfigError, Exception):  # noqa: BLE001 - never break GETs/boot
        return None


def openai_key_set() -> bool:
    """True iff an OpenAI key is present (env or .env), non-blank."""
    from dotenv import dotenv_values

    key = os.environ.get("OPENAI_API_KEY")
    if key is None:
        key = dotenv_values(_ENV_PATH).get("OPENAI_API_KEY")
    return bool(key and key.strip())


def reset_settings_cache() -> None:
    """Test seam: drop the cached Settings load."""
    try_load_settings.cache_clear()
