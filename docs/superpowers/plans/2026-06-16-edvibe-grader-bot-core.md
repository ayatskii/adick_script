# Edvibe Grader — Bot Core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Execute tasks top-to-bottom; each builds on the previous.

**Goal:** Build the Python bot core that logs into edvibe.com, finds Pre-IELTS "Awaiting" homework for Mr. Adilet's students, evaluates each manual-grade exercise with OpenAI (audio → transcribe → score; text → score), posts a 0–10 score + English comment, then completes the lesson — runnable from a CLI, with dry-run, idempotency, and audit safety rails.

**Architecture:** A Playwright (sync API) automation library split into focused modules (auth, scraper, evaluator, grader, state, audit) orchestrated by `runner.py` and exposed via `main.py`. Pure logic is unit-tested with TDD; browser-driven modules ship with real implementation code and are integration-verified via a controlled single-student dry-run (Playwright unit tests are infeasible without the live SPA). Every irreversible action is gated by run mode + an idempotency ledger, and any uncertainty defaults to NOT submitting.

**Tech Stack:** Python 3.11+, Playwright (sync API), OpenAI SDK (`openai`), pydantic v2, SQLite (stdlib `sqlite3`), pytest, python-dotenv.

**Spec:** `docs/superpowers/specs/2026-06-16-edvibe-grader-design.md` (§4 bot core, §5 safety rails, §6 data model).

---

## Conventions (read before any task)

- **Package:** all source under `edvibe_bot/`. Tests under `tests/` mirroring module paths (e.g. `tests/test_config.py`, `tests/evaluator/test_text.py`).
- **Imports:** absolute, e.g. `from edvibe_bot.config import Settings`.
- **Run a test:** `pytest tests/test_config.py::test_name -v`. Run all: `pytest -q`.
- **Env / secrets:** never hardcode. `load_settings()` reads `.env`. Secrets stay out of git (`.gitignore` already excludes `.env` and `crednetials.json`).
- **Commit style:** Conventional Commits (`feat:`, `test:`, `chore:`). Commit after each task's tests pass.
- **TDD:** for pure logic, write the failing test first, watch it fail, implement minimally, watch it pass, commit. For Playwright/OpenAI-bound code, extract pure helpers and TDD those; the I/O code ships with real implementation and a mocked-or-integration verification step (stated per task).
- **Submission gating (enforced in code):** ONLY `mode == "full_auto"` may submit. `dry_run` and `review` NEVER touch the platform — `review` records proposals to the ledger only (the approval/queue UI is web-app scope, deferred). The poster's `dry_run` guard is a second independent check: the runner passes the real flag through and never hard-codes `dry_run=False`.
- **Fail-safe rule (enforced in code):** audio fetch failure (`download_audio`→None), transcription failure, OpenAI parse failure, or `confidence < settings.confidence_threshold` → mark the exercise FLAGGED and do NOT submit. Any uncertainty defaults to NOT acting.
- **Idempotency + durability (enforced in code):** `is_exercise_done`/`is_lesson_completed` return True ONLY for terminal states (`graded`/`completed`). Before any irreversible click, write an `in_progress` ledger row; update to the terminal state AFTER the click returns. On re-run, an `in_progress` row means a prior attempt may have partially happened → skip + FLAG for human verification; never blindly retry an irreversible action.
- **Lesson completion gate (enforced in code):** complete a lesson ONLY when ≥1 manual exercise was graded this run (or every manual exercise is already terminal `graded`) AND no exercise in the lesson is `flagged`/`error`/`in_progress`. NEVER complete a lesson where zero manual exercises were detected.
- **Error boundary (enforced in code):** selector/navigation failures raise `edvibe_bot.errors.SelectorError`. The runner catches failures PER LESSON, screenshots to `reports/` (and if the screenshot itself fails, it logs/audits that — never a silent bare-except), records the lesson `error`, and CONTINUES to the next lesson/student — one failure never aborts the run, and a lesson is never left half-graded. The per-lesson handler does ONLY: screenshot → record lesson error → errors+=1 → audit → continue (no stray statements).
- **Independent FLAG guards (threshold-independent, enforced in code):** FLAG (never submit) when `evaluation.rationale == "parse_failed"` OR `evaluation.confidence <= 0` OR the gathered answer is empty/whitespace OR the exercise has no stable id (`element_id` missing). These are checked SEPARATELY from `confidence < threshold` so a misconfigured threshold can never submit them.
- **Confidence threshold (single source of truth):** validated to `0 < t <= 1` in BOTH `Settings` (field validator) and `build_run_config` (reject → SystemExit). `RunConfig.confidence_threshold` DEFAULTS from `settings.confidence_threshold`; CLI `--confidence` overrides. The runner reads `config.confidence_threshold`.
- **Dry-run passthrough (enforced in code):** the runner computes `dry_run = not submit_allowed` and passes it to `poster.grade_exercise`/`complete_lesson` — it NEVER hard-codes `dry_run=False`, so the poster guard stays an independent second check.
- **Lesson sentinel durability:** on re-run, if the lesson sentinel status is `in_progress` or `error`, do NOT re-complete — FLAG the lesson for human verification and skip (mirrors the per-exercise in_progress handling).
- **Section references:** refer to tasks by name. The ONLY numbered phase is "Phase 0 — Live exploration"; the end-to-end check is "Final integration & self-review". Do NOT invent "Phase 1/2/5/7".

## Interface contract (single source of truth — every task MUST match these signatures exactly)

```python
# ---- edvibe_bot/config.py ----
from pydantic import BaseModel

class ConfigError(Exception): ...

class Settings(BaseModel):
    edvibe_login: str
    edvibe_password: str
    openai_api_key: str
    marathon_name: str = "Pre-IELTS"
    curator_name: str = "Mister Adilet"
    transcription_model: str = "gpt-4o-transcribe"
    evaluation_model: str = "gpt-4o"
    fallback_transcription_model: str = "whisper-1"
    confidence_threshold: float = 0.6   # field validator requires 0 < value <= 1 (rejects 0/negative)
    pacing_seconds: float = 1.5
    storage_state_path: str = "storage_state.json"
    db_path: str = "edvibe.sqlite"
    audit_jsonl_path: str = "reports/audit.jsonl"

def load_settings(env_path: str = ".env") -> Settings: ...   # raises ConfigError if a required secret is missing

# ---- edvibe_bot/evaluator/schema.py ----
from enum import Enum
from pydantic import BaseModel

class ExerciseType(str, Enum):
    AUDIO = "audio"
    TEXT = "text"
    AUTO_CHECKED = "auto_checked"
    MANUAL_UNKNOWN = "manual_unknown"

class Evaluation(BaseModel):
    score: int          # validator clamps to [0, 10]
    comment: str
    rationale: str
    confidence: float   # validator clamps to [0.0, 1.0]

class EvalRequest(BaseModel):
    exercise_type: ExerciseType
    section: str
    prompt_text: str
    student_answer: str   # transcript (audio) or written text

# ---- edvibe_bot/state/store.py ----
from enum import Enum
from dataclasses import dataclass

class LedgerStatus(str, Enum):
    IN_PROGRESS = "in_progress"   # claim written BEFORE an irreversible click
    GRADED = "graded"
    SKIPPED = "skipped"
    FLAGGED = "flagged"
    ERROR = "error"
    COMPLETED = "completed"

@dataclass
class LedgerEntry:
    student_id: str
    lesson_id: str
    exercise_id: str
    student_name: str
    lesson_name: str
    exercise_no: str
    type: str            # ExerciseType value
    proposed_score: "int | None"
    proposed_comment: "str | None"
    confidence: "float | None"
    submitted: bool
    dry_run: bool
    run_id: str
    status: str          # LedgerStatus value

class Store:
    def __init__(self, db_path: str) -> None: ...
    def init_schema(self) -> None: ...   # creates runs, ledger, audit (queue/settings deferred to web-app plan)
    def create_run(self, mode: str, scope: dict) -> str: ...        # returns run_id (uuid4 hex)
    def finish_run(self, run_id: str, status: str, counts: dict) -> None: ...
    def append_audit(self, run_id: str, action: str, target_json: str, detail_json: str, ts: str) -> None: ...  # PUBLIC seam used by AuditLog
    # ledger keyed by (student_id, lesson_id, exercise_id); record_exercise UPSERTs in place; submitted_at stamped iff submitted=True.
    def record_exercise(self, entry: LedgerEntry) -> None: ...
    def get_exercise_status(self, student_id: str, lesson_id: str, exercise_id: str) -> "str | None": ...
    def is_exercise_done(self, student_id: str, lesson_id: str, exercise_id: str) -> bool: ...      # True ONLY if status in {graded, completed}
    def is_exercise_attempted(self, student_id: str, lesson_id: str, exercise_id: str) -> bool: ... # any row exists (incl. in_progress)
    # lesson completion is tracked by a sentinel ledger row (exercise_id == "__lesson__")
    def record_lesson_completion_intent(self, student_id: str, lesson_id: str, run_id: str) -> None: ...  # status=in_progress, BEFORE click
    def record_lesson_completed(self, student_id: str, lesson_id: str, run_id: str, dry_run: bool) -> None: ...  # status=completed, AFTER click
    def get_lesson_status(self, student_id: str, lesson_id: str) -> "str | None": ...
    def is_lesson_completed(self, student_id: str, lesson_id: str) -> bool: ...      # True ONLY if status == completed
    def is_lesson_completion_attempted(self, student_id: str, lesson_id: str) -> bool: ...  # any sentinel row (incl. in_progress)

# ---- edvibe_bot/audit/log.py ----
import logging
def get_logger(name: str) -> logging.Logger: ...
class AuditLog:
    def __init__(self, store: "Store", jsonl_path: str) -> None: ...
    def record(self, run_id: str, action: str, target: dict, detail: dict) -> None: ...  # writes via store.append_audit(...) + a JSONL line; ts via datetime.now(timezone.utc).isoformat()

# ---- edvibe_bot/errors.py ----
class SelectorError(Exception): ...   # raised when an expected edvibe.com element is not found

# ---- edvibe_bot/selectors.py ----
# Named constants only — CREATED by the "Bootstrap selectors + errors" task with best-guess
# defaults, then values CONFIRMED/updated in Phase 0. Other modules REFERENCE selectors.X;
# they never redefine or append to this file.

# ---- edvibe_bot/auth/login.py ----
from playwright.sync_api import BrowserContext, Page
def ensure_logged_in(context: BrowserContext, settings: "Settings") -> Page: ...  # restore storage_state, else login()
def login(page: Page, settings: "Settings") -> None: ...
def is_session_valid(page: Page) -> bool: ...

# ---- edvibe_bot/scraper/dashboard.py ----
from dataclasses import dataclass
@dataclass
class Student:
    id: str
    name: str
def open_marathon(page: "Page", settings: "Settings") -> None: ...   # classes -> Марафоны -> Pre-IELTS -> filter curator
def list_students(page: "Page") -> "list[Student]": ...

# ---- edvibe_bot/scraper/progress.py ----
from dataclasses import dataclass
@dataclass
class Lesson:
    id: str
    name: str
    status: str          # "awaiting" | "complete" | "other"
def open_progress(page: "Page", student: "Student") -> None: ...
def list_lessons(page: "Page") -> "list[Lesson]": ...
def awaiting_lessons(lessons: "list[Lesson]") -> "list[Lesson]": ...   # PURE filter (TDD this)
def open_lesson(page: "Page", lesson: "Lesson") -> None: ...

# ---- edvibe_bot/scraper/lesson.py ----
from dataclasses import dataclass
@dataclass
class Exercise:
    section: str                # section heading text (from selectors.SECTION_NAV), NOT prompt-derived
    number: str
    type: "ExerciseType"
    prompt_text: str            # the exercise task/question text (grounds evaluation)
    has_grade_button: bool
    audio_url: "str | None"
    answer_text: "str | None"
    element_id: "str | None"
def list_exercises(page: "Page") -> "list[Exercise]": ...
def classify_exercise(has_grade_button: bool, has_audio: bool, has_text_answer: bool) -> "ExerciseType": ...  # PURE (TDD this)

# ---- edvibe_bot/evaluator/audio.py ----
from playwright.sync_api import BrowserContext
def download_audio(context: BrowserContext, audio_url: str) -> "bytes | None": ...   # returns None on ANY failure (never raises)
def transcribe(audio_bytes: bytes, settings: "Settings") -> str: ...   # primary=settings.transcription_model with bounded retry/backoff; on persistent failure falls back to settings.fallback_transcription_model ("whisper-1"); raises only if BOTH fail (runner wraps + FLAGS)

# ---- edvibe_bot/evaluator/prompts.py ----
RUBRIC_AUDIO: str
RUBRIC_TEXT: str
def build_messages(req: "EvalRequest") -> "list[dict]": ...   # OpenAI chat messages enforcing JSON {score,comment,rationale,confidence}

# ---- edvibe_bot/evaluator/text.py ----
def evaluate(req: "EvalRequest", settings: "Settings") -> "Evaluation": ...  # OpenAI structured output with bounded retry/backoff; clamps score to [0,10]; on persistent error/parse failure returns Evaluation(score=0, comment="", rationale="parse_failed", confidence=0.0) so the runner FLAGS it

# ---- edvibe_bot/grader/poster.py ----
def grade_exercise(page: "Page", exercise: "Exercise", evaluation: "Evaluation", settings: "Settings", dry_run: bool) -> None: ...
def complete_lesson(page: "Page", dry_run: bool) -> None: ...   # clicks "Завершить урок" unless dry_run

# ---- edvibe_bot/runner.py ----
from dataclasses import dataclass
from typing import Callable, Optional

@dataclass
class RunConfig:
    mode: str                       # "dry_run" | "full_auto" | "review" — ONLY "full_auto" submits; "dry_run"/"review" never touch the platform
    student_filter: "list[str] | None" = None
    max_students: "int | None" = None
    max_lessons: "int | None" = None
    headed: bool = False
    confidence_threshold: float = 0.6

@dataclass
class RunReport:
    run_id: str
    graded: int
    skipped: int
    flagged: int
    errors: int
    completed_lessons: int

EventCallback = Callable[[dict], None]
# run() constructs AuditLog(store, settings.audit_jsonl_path) and calls .record(...) at every
# evaluation / submit / complete (dry_run flag inside detail). Submission requires mode=="full_auto".
# Irreversible actions use the in_progress->terminal durability pattern. Per-lesson try/except
# SelectorError -> screenshot + record error + continue. Completion obeys the completion gate.
def run(config: "RunConfig", settings: "Settings", store: "Store", on_event: "Optional[EventCallback]" = None) -> "RunReport": ...
```

## Tasks

### Task: Scaffold the `edvibe_bot` package, deps, and env template

**Files:**
- Create: `edvibe_bot/__init__.py`, `edvibe_bot/auth/__init__.py`, `edvibe_bot/scraper/__init__.py`, `edvibe_bot/evaluator/__init__.py`, `edvibe_bot/grader/__init__.py`, `edvibe_bot/state/__init__.py`, `edvibe_bot/audit/__init__.py`
- Create: `requirements.txt`, `reports/.gitkeep`, `.env.example`
- Test: none (pure file scaffolding; verified by import + install steps below)

- [ ] **Step 1: Create the package + subpackage `__init__.py` files.** Each is an empty file marking the directory as a Python package.

```bash
mkdir -p edvibe_bot/auth edvibe_bot/scraper edvibe_bot/evaluator \
         edvibe_bot/grader edvibe_bot/state edvibe_bot/audit reports
touch edvibe_bot/__init__.py \
      edvibe_bot/auth/__init__.py \
      edvibe_bot/scraper/__init__.py \
      edvibe_bot/evaluator/__init__.py \
      edvibe_bot/grader/__init__.py \
      edvibe_bot/state/__init__.py \
      edvibe_bot/audit/__init__.py
```

- [ ] **Step 2: Write `requirements.txt`.** Runtime + test deps only; no score/threshold env vars belong here.

```
playwright
openai
pydantic>=2
python-dotenv
pytest
```

- [ ] **Step 3: Write `reports/.gitkeep`.** Keeps the screenshot/audit output directory tracked even though `reports/` is gitignored. Empty file:

```bash
touch reports/.gitkeep
```

- [ ] **Step 4: Write `.env.example`.** ONLY the three real secrets — no score variables, no thresholds (those live in `Settings` defaults, not env).

```
EDVIBE_LOGIN=
EDVIBE_PASSWORD=
OPENAI_API_KEY=
```

- [ ] **Step 5: Install dependencies + the Chromium browser.** Run: `pip install -r requirements.txt && playwright install chromium`  Expected: pip resolves playwright, openai, pydantic>=2, python-dotenv, pytest; `playwright install chromium` downloads the Chromium build with no error.

- [ ] **Step 6: Verify the package imports.** Run: `python -c "import edvibe_bot, edvibe_bot.auth, edvibe_bot.scraper, edvibe_bot.evaluator, edvibe_bot.grader, edvibe_bot.state, edvibe_bot.audit; print('ok')"`  Expected: prints `ok` with no ImportError.

- [ ] **Step 7: Confirm gitignore behavior (informational).** Run: `git check-ignore -v .env reports/.gitkeep .env.example || true`  Expected: `.env` is ignored (by the `.env` rule) and `reports/.gitkeep` is ignored (by the `reports/` rule), while `.env.example` is NOT ignored (re-included via the `!.env.example` negation). Because `reports/.gitkeep` is ignored, it must be force-added in the commit below. NOTE: `.gitignore` already exists — do not recreate it.

- [ ] **Step 8: Commit.** Force-add the ignored keep file so the output dir stays tracked.

```bash
git add edvibe_bot/__init__.py edvibe_bot/auth/__init__.py edvibe_bot/scraper/__init__.py \
        edvibe_bot/evaluator/__init__.py edvibe_bot/grader/__init__.py \
        edvibe_bot/state/__init__.py edvibe_bot/audit/__init__.py \
        requirements.txt .env.example && \
git add -f reports/.gitkeep && \
git commit -m "chore: scaffold edvibe_bot package, deps, and env template"
```

---

### Task: Config — `Settings`, `ConfigError`, `load_settings` (TDD)

**Files:**
- Create: `edvibe_bot/config.py`
- Test: `tests/test_config.py`

- [ ] **Step 1: Write the failing tests.** Cover: defaults applied; values read from a temp `.env`; missing required secret → `ConfigError`; blank required secret → `ConfigError`; `confidence_threshold` of `0` or `1.5` → `ConfigError`; `0.6` accepted. The missing/blank tests must `delenv` the three secrets so a populated ambient environment cannot mask the failure.

```python
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
```

- [ ] **Step 2: Run the tests, watch them fail.** Run: `pytest tests/test_config.py -q`  Expected: collection error / `ModuleNotFoundError: edvibe_bot.config` (module not yet created).

- [ ] **Step 3: Implement `edvibe_bot/config.py`.** `Settings` has EXACTLY the contract fields (no `score_min`/`score_max`; the 0–10 scale is fixed in the `Evaluation` clamp validator, not here). The field validator on `confidence_threshold` raises `ConfigError` for anything outside `0 < value <= 1`. `load_settings` loads `.env` via python-dotenv, overlays `os.environ` for the known keys, treats missing OR blank required secrets as `ConfigError`, and converts pydantic `ValidationError` into `ConfigError`.

```python
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
```

- [ ] **Step 4: Run the tests, watch them pass.** Run: `pytest tests/test_config.py -q`  Expected: all tests pass.

- [ ] **Step 5: Commit.**

```bash
git add edvibe_bot/config.py tests/test_config.py && \
git commit -m "feat: add Settings config with confidence-threshold validation and loader"
```

---

### Task: Bootstrap selectors + errors modules (single source of truth)

> Creates `edvibe_bot/selectors.py` (best-guess defaults; Phase 0 confirms the VALUES) and `edvibe_bot/errors.py`. Every browser module REFERENCES these constants — no other task may redefine, append to, or recreate `selectors.py`.

**Files:**
- Create: `edvibe_bot/selectors.py`
- Create: `edvibe_bot/errors.py`
- Test: `tests/test_selectors.py`

- [ ] **Step 1: Write the failing test.**
```python
# tests/test_selectors.py
from edvibe_bot import selectors
from edvibe_bot.errors import SelectorError

REQUIRED = [
    "LOGIN_URL", "AUTHED_URL", "LOGIN_EMAIL", "LOGIN_PASSWORD", "LOGIN_SUBMIT",
    "NAV_CLASSES", "MARATHONS_TAB", "PRE_IELTS_CARD", "FILTER_BUTTON", "CURATOR_OPTION", "FILTER_APPLY",
    "STUDENT_ROW", "STUDENT_ID_ATTR", "STUDENT_NAME", "STUDENT_PROGRESS_BTN",
    "LESSON_ROW", "LESSON_ID_ATTR", "LESSON_NAME", "LESSON_STATUS_AWAITING", "LESSON_OPEN_BUTTON",
    "SECTION_NAV", "EXERCISE_BLOCK", "EXERCISE_ID_ATTR", "EXERCISE_NUMBER", "EXERCISE_PROMPT",
    "EXERCISE_AUDIO", "EXERCISE_TEXT_ANSWER", "GRADE_EXERCISE_BTN",
    "SCORE_INPUT", "COMMENT_INPUT", "GRADE_SAVE_BTN", "COMPLETE_LESSON_BTN",
]

def test_all_required_selectors_present():
    for name in REQUIRED:
        value = getattr(selectors, name)
        assert isinstance(value, str) and value

def test_selector_error_is_exception():
    assert issubclass(SelectorError, Exception)
```
- [ ] **Step 2: Run it to verify it fails.** Run: `pytest tests/test_selectors.py -v`  Expected: FAIL (ModuleNotFoundError / AttributeError).
- [ ] **Step 3: Write `edvibe_bot/errors.py`.**
```python
class SelectorError(Exception):
    """Raised when an expected edvibe.com element/selector is not found."""
```
- [ ] **Step 4: Write `edvibe_bot/selectors.py`** (best-guess defaults; `# CONFIRM` marks values Phase 0 must verify).
```python
# edvibe_bot/selectors.py — SINGLE SOURCE OF TRUTH for edvibe.com selectors.
# Values are best-guess defaults, CONFIRMED/updated in Phase 0. Do NOT redefine elsewhere.

# URLs
LOGIN_URL = "https://edvibe.com/login"                      # CONFIRM
AUTHED_URL = "https://edvibe.com/cabinet/school/classes"    # CONFIRM

# Login
LOGIN_EMAIL = "input[type=email]"                           # CONFIRM
LOGIN_PASSWORD = "input[type=password]"                     # CONFIRM
LOGIN_SUBMIT = "button[type=submit]"                        # CONFIRM

# Marathon dashboard + curator filter
NAV_CLASSES = "https://edvibe.com/cabinet/school/classes"   # CONFIRM (classes landing; open_marathon goto target)
MARATHONS_TAB = "text=Марафоны"
PRE_IELTS_CARD = "text=Pre-IELTS"
FILTER_BUTTON = "text=Фильтр"
CURATOR_OPTION = "text=Mister Adilet"
FILTER_APPLY = "text=Применить"

# Students
STUDENT_ROW = "[data-testid=student-row]"                   # CONFIRM
STUDENT_ID_ATTR = "data-student-id"                         # CONFIRM
STUDENT_NAME = "[data-testid=student-name]"                 # CONFIRM
STUDENT_PROGRESS_BTN = "text=Прогресс ученика"

# Progress modal — lessons
LESSON_ROW = "[data-testid=lesson-row]"                     # CONFIRM
LESSON_ID_ATTR = "data-lesson-id"                           # CONFIRM
LESSON_NAME = "[data-testid=lesson-name]"                   # CONFIRM
LESSON_STATUS_AWAITING = ".status--awaiting"                # CONFIRM
LESSON_OPEN_BUTTON = "text=Открыть урок"

# Lesson view — sections + exercises
SECTION_NAV = "[data-testid=section]"                       # CONFIRM
EXERCISE_BLOCK = "[data-testid=exercise]"                   # CONFIRM
EXERCISE_ID_ATTR = "data-exercise-id"                       # CONFIRM (stable per-exercise id -> ledger key)
EXERCISE_NUMBER = "[data-testid=exercise-number]"           # CONFIRM
EXERCISE_PROMPT = "[data-testid=exercise-prompt]"           # CONFIRM
EXERCISE_AUDIO = "audio"                                    # CONFIRM
EXERCISE_TEXT_ANSWER = "[data-testid=text-answer]"          # CONFIRM
GRADE_EXERCISE_BTN = "text=Оценить упражнение"

# Grade modal
SCORE_INPUT = "input[type=number]"                          # CONFIRM
COMMENT_INPUT = "textarea"                                  # CONFIRM
GRADE_SAVE_BTN = "text=Продолжить"

# Lesson completion
COMPLETE_LESSON_BTN = "text=Завершить урок"
```
- [ ] **Step 5: Run the test to verify it passes.** Run: `pytest tests/test_selectors.py -v`  Expected: PASS.
- [ ] **Step 6: Commit.** `git add edvibe_bot/selectors.py edvibe_bot/errors.py tests/test_selectors.py && git commit -m "feat: bootstrap selectors + errors modules"`


---

I have everything I need. Here are the tasks for my assigned modules.

### Task: State store — runs/ledger/audit schema + run lifecycle

**Files:**
- Create: `edvibe_bot/state/__init__.py`
- Create: `edvibe_bot/state/store.py`
- Test: `tests/state/__init__.py`
- Test: `tests/state/test_store_schema.py`

- [ ] **Step 1: Write the failing schema + run-lifecycle test.** Create `tests/state/__init__.py` (empty) and `tests/state/test_store_schema.py`:

  ```python
  import sqlite3

  from edvibe_bot.state.store import Store


  def _store(tmp_path):
      s = Store(str(tmp_path / "t.sqlite"))
      s.init_schema()
      return s


  def test_init_schema_creates_runs_ledger_audit(tmp_path):
      db = str(tmp_path / "t.sqlite")
      s = Store(db)
      s.init_schema()
      con = sqlite3.connect(db)
      names = {
          row[0]
          for row in con.execute(
              "SELECT name FROM sqlite_master WHERE type='table'"
          ).fetchall()
      }
      con.close()
      assert {"runs", "ledger", "audit"}.issubset(names)
      # queue + settings are DEFERRED to the web-app plan
      assert "queue" not in names
      assert "settings" not in names


  def test_init_schema_is_idempotent(tmp_path):
      s = _store(tmp_path)
      s.init_schema()  # second call must not raise


  def test_create_run_returns_uuid4_hex(tmp_path):
      s = _store(tmp_path)
      run_id = s.create_run("dry_run", {"students": ["x"]})
      assert isinstance(run_id, str)
      assert len(run_id) == 32
      int(run_id, 16)  # hex


  def test_create_run_persists_row(tmp_path):
      db = str(tmp_path / "t.sqlite")
      s = Store(db)
      s.init_schema()
      run_id = s.create_run("full_auto", {"max": 1})
      con = sqlite3.connect(db)
      row = con.execute(
          "SELECT mode, scope_json, status, finished_at FROM runs WHERE id=?",
          (run_id,),
      ).fetchone()
      con.close()
      assert row[0] == "full_auto"
      assert '"max": 1' in row[1]
      assert row[2] == "running"
      assert row[3] is None


  def test_finish_run_updates_status_and_counts(tmp_path):
      db = str(tmp_path / "t.sqlite")
      s = Store(db)
      s.init_schema()
      run_id = s.create_run("dry_run", {})
      s.finish_run(run_id, "done", {"graded": 2, "flagged": 1})
      con = sqlite3.connect(db)
      row = con.execute(
          "SELECT status, counts_json, finished_at FROM runs WHERE id=?",
          (run_id,),
      ).fetchone()
      con.close()
      assert row[0] == "done"
      assert '"graded": 2' in row[1]
      assert row[2] is not None


  def test_append_audit_inserts_row(tmp_path):
      db = str(tmp_path / "t.sqlite")
      s = Store(db)
      s.init_schema()
      run_id = s.create_run("dry_run", {})
      s.append_audit(run_id, "evaluate", '{"ex": "1"}', '{"score": 7}', "2026-06-16T00:00:00+00:00")
      con = sqlite3.connect(db)
      row = con.execute(
          "SELECT run_id, action, target_json, detail_json, ts FROM audit"
      ).fetchone()
      con.close()
      assert row == (run_id, "evaluate", '{"ex": "1"}', '{"score": 7}', "2026-06-16T00:00:00+00:00")
  ```

- [ ] **Step 2: Run the test (expect failure).** Run: `pytest tests/state/test_store_schema.py -q`  Expected: collection/import error or failures — `edvibe_bot.state.store` does not exist yet.

- [ ] **Step 3: Implement `Store` schema + run lifecycle + audit seam.** Create `edvibe_bot/state/__init__.py` (empty) and `edvibe_bot/state/store.py`:

  ```python
  import sqlite3
  import uuid
  from dataclasses import dataclass
  from datetime import datetime, timezone
  from enum import Enum


  class LedgerStatus(str, Enum):
      IN_PROGRESS = "in_progress"   # claim written BEFORE an irreversible click
      GRADED = "graded"
      SKIPPED = "skipped"
      FLAGGED = "flagged"
      ERROR = "error"
      COMPLETED = "completed"


  # Sentinel exercise_id used for the per-lesson completion ledger row.
  LESSON_SENTINEL = "__lesson__"


  @dataclass
  class LedgerEntry:
      student_id: str
      lesson_id: str
      exercise_id: str
      student_name: str
      lesson_name: str
      exercise_no: str
      type: str            # ExerciseType value
      proposed_score: "int | None"
      proposed_comment: "str | None"
      confidence: "float | None"
      submitted: bool
      dry_run: bool
      run_id: str
      status: str          # LedgerStatus value


  def _utc_now_iso() -> str:
      return datetime.now(timezone.utc).isoformat()


  class Store:
      def __init__(self, db_path: str) -> None:
          self._db_path = db_path

      def _connect(self) -> sqlite3.Connection:
          con = sqlite3.connect(self._db_path)
          con.execute("PRAGMA foreign_keys = ON")
          return con

      def init_schema(self) -> None:
          # Tables: runs, ledger, audit.
          # The §6 `queue` and `settings` tables are DEFERRED to the web-app plan
          # and are intentionally NOT created here.
          con = self._connect()
          try:
              con.executescript(
                  """
                  CREATE TABLE IF NOT EXISTS runs (
                      id          TEXT PRIMARY KEY,
                      mode        TEXT NOT NULL,
                      scope_json  TEXT NOT NULL,
                      started_at  TEXT NOT NULL,
                      finished_at TEXT,
                      status      TEXT NOT NULL,
                      counts_json TEXT
                  );

                  CREATE TABLE IF NOT EXISTS ledger (
                      student_id       TEXT NOT NULL,
                      lesson_id        TEXT NOT NULL,
                      exercise_id      TEXT NOT NULL,
                      student_name     TEXT,
                      lesson_name      TEXT,
                      exercise_no      TEXT,
                      type             TEXT,
                      proposed_score   INTEGER,
                      proposed_comment TEXT,
                      confidence       REAL,
                      submitted        INTEGER NOT NULL DEFAULT 0,
                      submitted_at     TEXT,
                      dry_run          INTEGER NOT NULL DEFAULT 0,
                      run_id           TEXT NOT NULL,
                      status           TEXT NOT NULL,
                      PRIMARY KEY (student_id, lesson_id, exercise_id)
                  );

                  CREATE TABLE IF NOT EXISTS audit (
                      id          INTEGER PRIMARY KEY AUTOINCREMENT,
                      ts          TEXT NOT NULL,
                      run_id      TEXT NOT NULL,
                      actor       TEXT NOT NULL DEFAULT 'bot',
                      action      TEXT NOT NULL,
                      target_json TEXT NOT NULL,
                      detail_json TEXT NOT NULL
                  );
                  """
              )
              con.commit()
          finally:
              con.close()

      def create_run(self, mode: str, scope: dict) -> str:
          import json

          run_id = uuid.uuid4().hex
          con = self._connect()
          try:
              con.execute(
                  "INSERT INTO runs (id, mode, scope_json, started_at, finished_at, status, counts_json) "
                  "VALUES (?, ?, ?, ?, NULL, 'running', NULL)",
                  (run_id, mode, json.dumps(scope), _utc_now_iso()),
              )
              con.commit()
          finally:
              con.close()
          return run_id

      def finish_run(self, run_id: str, status: str, counts: dict) -> None:
          import json

          con = self._connect()
          try:
              con.execute(
                  "UPDATE runs SET status=?, counts_json=?, finished_at=? WHERE id=?",
                  (status, json.dumps(counts), _utc_now_iso(), run_id),
              )
              con.commit()
          finally:
              con.close()

      def append_audit(
          self, run_id: str, action: str, target_json: str, detail_json: str, ts: str
      ) -> None:
          # PUBLIC seam used by AuditLog: inserts exactly one audit row.
          con = self._connect()
          try:
              con.execute(
                  "INSERT INTO audit (ts, run_id, actor, action, target_json, detail_json) "
                  "VALUES (?, ?, 'bot', ?, ?, ?)",
                  (ts, run_id, action, target_json, detail_json),
              )
              con.commit()
          finally:
              con.close()
  ```

- [ ] **Step 4: Run the test (expect pass).** Run: `pytest tests/state/test_store_schema.py -q`  Expected: all tests pass.

- [ ] **Step 5: Commit.** Run: `git add edvibe_bot/state/__init__.py edvibe_bot/state/store.py tests/state/__init__.py tests/state/test_store_schema.py && git commit -m "feat: state store schema (runs/ledger/audit) + run lifecycle"`

---

### Task: State store — exercise ledger (UPSERT, done/attempted, submitted_at)

**Files:**
- Edit: `edvibe_bot/state/store.py`
- Test: `tests/state/test_store_exercise.py`

- [ ] **Step 1: Write the failing exercise-ledger test.** Create `tests/state/test_store_exercise.py`:

  ```python
  import sqlite3

  from edvibe_bot.state.store import LedgerEntry, Store


  def _store(tmp_path):
      s = Store(str(tmp_path / "t.sqlite"))
      s.init_schema()
      return s


  def _entry(status, *, submitted=False, score=7, run_id="r1"):
      return LedgerEntry(
          student_id="s1",
          lesson_id="l1",
          exercise_id="e1",
          student_name="Anel",
          lesson_name="Lesson 14",
          exercise_no="3",
          type="audio",
          proposed_score=score,
          proposed_comment="Good work",
          confidence=0.9,
          submitted=submitted,
          dry_run=not submitted,
          run_id=run_id,
          status=status,
      )


  def test_record_graded_is_done(tmp_path):
      s = _store(tmp_path)
      s.record_exercise(_entry("graded"))
      assert s.get_exercise_status("s1", "l1", "e1") == "graded"
      assert s.is_exercise_done("s1", "l1", "e1") is True
      assert s.is_exercise_attempted("s1", "l1", "e1") is True


  def test_record_in_progress_attempted_but_not_done(tmp_path):
      s = _store(tmp_path)
      s.record_exercise(_entry("in_progress"))
      assert s.is_exercise_attempted("s1", "l1", "e1") is True
      assert s.is_exercise_done("s1", "l1", "e1") is False


  def test_record_flagged_not_done(tmp_path):
      s = _store(tmp_path)
      s.record_exercise(_entry("flagged"))
      assert s.is_exercise_done("s1", "l1", "e1") is False
      assert s.is_exercise_attempted("s1", "l1", "e1") is True


  def test_missing_exercise_status_and_flags(tmp_path):
      s = _store(tmp_path)
      assert s.get_exercise_status("s1", "l1", "nope") is None
      assert s.is_exercise_done("s1", "l1", "nope") is False
      assert s.is_exercise_attempted("s1", "l1", "nope") is False


  def test_submitted_true_stamps_submitted_at(tmp_path):
      db = str(tmp_path / "t.sqlite")
      s = Store(db)
      s.init_schema()
      s.record_exercise(_entry("graded", submitted=True))
      con = sqlite3.connect(db)
      row = con.execute(
          "SELECT submitted, submitted_at FROM ledger WHERE exercise_id='e1'"
      ).fetchone()
      con.close()
      assert row[0] == 1
      assert row[1] is not None


  def test_submitted_false_leaves_submitted_at_null(tmp_path):
      db = str(tmp_path / "t.sqlite")
      s = Store(db)
      s.init_schema()
      s.record_exercise(_entry("flagged", submitted=False))
      con = sqlite3.connect(db)
      row = con.execute(
          "SELECT submitted, submitted_at FROM ledger WHERE exercise_id='e1'"
      ).fetchone()
      con.close()
      assert row[0] == 0
      assert row[1] is None


  def test_upsert_replaces_in_place_no_duplicate_rows(tmp_path):
      db = str(tmp_path / "t.sqlite")
      s = Store(db)
      s.init_schema()
      s.record_exercise(_entry("in_progress", submitted=False, run_id="r1"))
      s.record_exercise(_entry("graded", submitted=True, score=9, run_id="r2"))
      con = sqlite3.connect(db)
      rows = con.execute(
          "SELECT proposed_score, status, run_id, submitted FROM ledger "
          "WHERE student_id='s1' AND lesson_id='l1' AND exercise_id='e1'"
      ).fetchall()
      con.close()
      assert len(rows) == 1
      assert rows[0] == (9, "graded", "r2", 1)
  ```

- [ ] **Step 2: Run the test (expect failure).** Run: `pytest tests/state/test_store_exercise.py -q`  Expected: `AttributeError` — `record_exercise` / `get_exercise_status` / `is_exercise_done` / `is_exercise_attempted` not implemented yet.

- [ ] **Step 3: Implement the exercise-ledger methods.** Append these methods to the `Store` class in `edvibe_bot/state/store.py` (after `append_audit`):

  ```python
      # ledger keyed by (student_id, lesson_id, exercise_id); UPSERTs in place;
      # submitted_at stamped iff submitted=True (NULL otherwise).
      def record_exercise(self, entry: LedgerEntry) -> None:
          submitted_at = _utc_now_iso() if entry.submitted else None
          con = self._connect()
          try:
              con.execute(
                  """
                  INSERT INTO ledger (
                      student_id, lesson_id, exercise_id,
                      student_name, lesson_name, exercise_no, type,
                      proposed_score, proposed_comment, confidence,
                      submitted, submitted_at, dry_run, run_id, status
                  ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                  ON CONFLICT(student_id, lesson_id, exercise_id) DO UPDATE SET
                      student_name     = excluded.student_name,
                      lesson_name      = excluded.lesson_name,
                      exercise_no      = excluded.exercise_no,
                      type             = excluded.type,
                      proposed_score   = excluded.proposed_score,
                      proposed_comment = excluded.proposed_comment,
                      confidence       = excluded.confidence,
                      submitted        = excluded.submitted,
                      submitted_at     = excluded.submitted_at,
                      dry_run          = excluded.dry_run,
                      run_id           = excluded.run_id,
                      status           = excluded.status
                  """,
                  (
                      entry.student_id,
                      entry.lesson_id,
                      entry.exercise_id,
                      entry.student_name,
                      entry.lesson_name,
                      entry.exercise_no,
                      entry.type,
                      entry.proposed_score,
                      entry.proposed_comment,
                      entry.confidence,
                      1 if entry.submitted else 0,
                      submitted_at,
                      1 if entry.dry_run else 0,
                      entry.run_id,
                      entry.status,
                  ),
              )
              con.commit()
          finally:
              con.close()

      def get_exercise_status(
          self, student_id: str, lesson_id: str, exercise_id: str
      ) -> "str | None":
          con = self._connect()
          try:
              row = con.execute(
                  "SELECT status FROM ledger "
                  "WHERE student_id=? AND lesson_id=? AND exercise_id=?",
                  (student_id, lesson_id, exercise_id),
              ).fetchone()
          finally:
              con.close()
          return row[0] if row is not None else None

      def is_exercise_done(
          self, student_id: str, lesson_id: str, exercise_id: str
      ) -> bool:
          # True ONLY for terminal states.
          status = self.get_exercise_status(student_id, lesson_id, exercise_id)
          return status in {LedgerStatus.GRADED.value, LedgerStatus.COMPLETED.value}

      def is_exercise_attempted(
          self, student_id: str, lesson_id: str, exercise_id: str
      ) -> bool:
          # Any row exists (including in_progress).
          return self.get_exercise_status(student_id, lesson_id, exercise_id) is not None
  ```

- [ ] **Step 4: Run the test (expect pass).** Run: `pytest tests/state/test_store_exercise.py -q`  Expected: all tests pass.

- [ ] **Step 5: Commit.** Run: `git add edvibe_bot/state/store.py tests/state/test_store_exercise.py && git commit -m "feat: ledger UPSERT + exercise done/attempted + submitted_at stamping"`

---

### Task: State store — lesson completion sentinel (intent → completed)

**Files:**
- Edit: `edvibe_bot/state/store.py`
- Test: `tests/state/test_store_lesson.py`

- [ ] **Step 1: Write the failing lesson-sentinel test.** Create `tests/state/test_store_lesson.py`:

  ```python
  import sqlite3

  from edvibe_bot.state.store import LESSON_SENTINEL, Store


  def _store(tmp_path):
      s = Store(str(tmp_path / "t.sqlite"))
      s.init_schema()
      return s


  def test_no_sentinel_means_not_attempted_not_completed(tmp_path):
      s = _store(tmp_path)
      assert s.get_lesson_status("s1", "l1") is None
      assert s.is_lesson_completed("s1", "l1") is False
      assert s.is_lesson_completion_attempted("s1", "l1") is False


  def test_intent_writes_in_progress_sentinel(tmp_path):
      db = str(tmp_path / "t.sqlite")
      s = Store(db)
      s.init_schema()
      s.record_lesson_completion_intent("s1", "l1", "r1")
      assert s.get_lesson_status("s1", "l1") == "in_progress"
      assert s.is_lesson_completion_attempted("s1", "l1") is True
      assert s.is_lesson_completed("s1", "l1") is False
      con = sqlite3.connect(db)
      row = con.execute(
          "SELECT exercise_id, submitted, submitted_at FROM ledger "
          "WHERE student_id='s1' AND lesson_id='l1'"
      ).fetchone()
      con.close()
      assert row[0] == LESSON_SENTINEL
      assert row[1] == 0
      assert row[2] is None


  def test_intent_then_completed_transition(tmp_path):
      db = str(tmp_path / "t.sqlite")
      s = Store(db)
      s.init_schema()
      s.record_lesson_completion_intent("s1", "l1", "r1")
      s.record_lesson_completed("s1", "l1", "r1", dry_run=False)
      assert s.get_lesson_status("s1", "l1") == "completed"
      assert s.is_lesson_completed("s1", "l1") is True
      assert s.is_lesson_completion_attempted("s1", "l1") is True
      con = sqlite3.connect(db)
      rows = con.execute(
          "SELECT submitted, submitted_at, dry_run FROM ledger "
          "WHERE student_id='s1' AND lesson_id='l1'"
      ).fetchall()
      con.close()
      assert len(rows) == 1            # sentinel UPSERTed in place
      assert rows[0][0] == 1           # submitted=True for a real (non-dry) completion
      assert rows[0][1] is not None    # submitted_at stamped
      assert rows[0][2] == 0           # dry_run=False


  def test_dry_run_completion_not_submitted(tmp_path):
      db = str(tmp_path / "t.sqlite")
      s = Store(db)
      s.init_schema()
      s.record_lesson_completion_intent("s1", "l1", "r1")
      s.record_lesson_completed("s1", "l1", "r1", dry_run=True)
      assert s.is_lesson_completed("s1", "l1") is True
      con = sqlite3.connect(db)
      row = con.execute(
          "SELECT submitted, submitted_at, dry_run FROM ledger "
          "WHERE student_id='s1' AND lesson_id='l1'"
      ).fetchone()
      con.close()
      assert row[0] == 0           # dry-run never submits
      assert row[1] is None
      assert row[2] == 1


  def test_lesson_sentinel_isolated_from_exercise_rows(tmp_path):
      db = str(tmp_path / "t.sqlite")
      s = Store(db)
      s.init_schema()
      s.record_lesson_completion_intent("s1", "l1", "r1")
      # An exercise on the same lesson must not collide with the sentinel.
      assert s.is_exercise_attempted("s1", "l1", "e1") is False
      assert s.get_exercise_status("s1", "l1", LESSON_SENTINEL) == "in_progress"
  ```

- [ ] **Step 2: Run the test (expect failure).** Run: `pytest tests/state/test_store_lesson.py -q`  Expected: `AttributeError` — lesson sentinel methods not implemented yet.

- [ ] **Step 3: Implement the lesson-sentinel methods.** Append these methods to the `Store` class in `edvibe_bot/state/store.py` (after `is_exercise_attempted`):

  ```python
      # Lesson completion is tracked by a sentinel ledger row (exercise_id == LESSON_SENTINEL).
      def record_lesson_completion_intent(
          self, student_id: str, lesson_id: str, run_id: str
      ) -> None:
          # status=in_progress, written BEFORE the irreversible "Завершить урок" click.
          self.record_exercise(
              LedgerEntry(
                  student_id=student_id,
                  lesson_id=lesson_id,
                  exercise_id=LESSON_SENTINEL,
                  student_name="",
                  lesson_name="",
                  exercise_no="",
                  type="",
                  proposed_score=None,
                  proposed_comment=None,
                  confidence=None,
                  submitted=False,
                  dry_run=False,
                  run_id=run_id,
                  status=LedgerStatus.IN_PROGRESS.value,
              )
          )

      def record_lesson_completed(
          self, student_id: str, lesson_id: str, run_id: str, dry_run: bool
      ) -> None:
          # status=completed, written AFTER the click returns. A real (non-dry)
          # completion counts as submitted; dry-run never submits.
          self.record_exercise(
              LedgerEntry(
                  student_id=student_id,
                  lesson_id=lesson_id,
                  exercise_id=LESSON_SENTINEL,
                  student_name="",
                  lesson_name="",
                  exercise_no="",
                  type="",
                  proposed_score=None,
                  proposed_comment=None,
                  confidence=None,
                  submitted=not dry_run,
                  dry_run=dry_run,
                  run_id=run_id,
                  status=LedgerStatus.COMPLETED.value,
              )
          )

      def get_lesson_status(self, student_id: str, lesson_id: str) -> "str | None":
          return self.get_exercise_status(student_id, lesson_id, LESSON_SENTINEL)

      def is_lesson_completed(self, student_id: str, lesson_id: str) -> bool:
          # True ONLY when the sentinel reached the terminal completed state.
          return self.get_lesson_status(student_id, lesson_id) == LedgerStatus.COMPLETED.value

      def is_lesson_completion_attempted(self, student_id: str, lesson_id: str) -> bool:
          # Any sentinel row exists (including in_progress).
          return self.get_lesson_status(student_id, lesson_id) is not None
  ```

- [ ] **Step 4: Run the test (expect pass).** Run: `pytest tests/state/test_store_lesson.py -q`  Expected: all tests pass.

- [ ] **Step 5: Run the full store suite.** Run: `pytest tests/state/ -q`  Expected: every store test (schema, exercise, lesson) passes.

- [ ] **Step 6: Commit.** Run: `git add edvibe_bot/state/store.py tests/state/test_store_lesson.py && git commit -m "feat: lesson completion sentinel (in_progress intent -> completed)"`

---

### Task: Audit log — structured logger + dual-sink record (SQLite seam + JSONL)

**Files:**
- Create: `edvibe_bot/audit/__init__.py`
- Create: `edvibe_bot/audit/log.py`
- Test: `tests/audit/__init__.py`
- Test: `tests/audit/test_log.py`

- [ ] **Step 1: Write the failing audit-log test (fake store).** Create `tests/audit/__init__.py` (empty) and `tests/audit/test_log.py`:

  ```python
  import json
  import logging

  from edvibe_bot.audit.log import AuditLog, get_logger


  class FakeStore:
      def __init__(self):
          self.calls = []

      def append_audit(self, run_id, action, target_json, detail_json, ts):
          self.calls.append((run_id, action, target_json, detail_json, ts))


  def test_get_logger_returns_named_logger():
      log = get_logger("edvibe_bot.test")
      assert isinstance(log, logging.Logger)
      assert log.name == "edvibe_bot.test"


  def test_record_appends_one_jsonl_line_and_calls_store(tmp_path):
      store = FakeStore()
      jsonl = tmp_path / "nested" / "audit.jsonl"   # parent dir does not exist yet
      audit = AuditLog(store, str(jsonl))
      audit.record("run1", "evaluate", {"ex": "e1"}, {"score": 7, "dry_run": True})

      assert len(store.calls) == 1
      run_id, action, target_json, detail_json, ts = store.calls[0]
      assert run_id == "run1"
      assert action == "evaluate"
      assert json.loads(target_json) == {"ex": "e1"}
      assert json.loads(detail_json) == {"score": 7, "dry_run": True}
      assert ts.endswith("+00:00")  # UTC isoformat

      lines = jsonl.read_text().splitlines()
      assert len(lines) == 1
      rec = json.loads(lines[0])
      assert rec["run_id"] == "run1"
      assert rec["action"] == "evaluate"
      assert rec["target"] == {"ex": "e1"}
      assert rec["detail"] == {"score": 7, "dry_run": True}
      assert rec["ts"] == ts


  def test_record_twice_appends_second_line(tmp_path):
      store = FakeStore()
      jsonl = tmp_path / "audit.jsonl"
      audit = AuditLog(store, str(jsonl))
      audit.record("run1", "submit", {"ex": "e1"}, {"dry_run": False})
      audit.record("run1", "complete", {"lesson": "l1"}, {"dry_run": False})

      assert len(store.calls) == 2
      lines = jsonl.read_text().splitlines()
      assert len(lines) == 2
      assert json.loads(lines[0])["action"] == "submit"
      assert json.loads(lines[1])["action"] == "complete"
  ```

- [ ] **Step 2: Run the test (expect failure).** Run: `pytest tests/audit/test_log.py -q`  Expected: import error — `edvibe_bot.audit.log` does not exist yet.

- [ ] **Step 3: Implement `get_logger` + `AuditLog`.** Create `edvibe_bot/audit/__init__.py` (empty) and `edvibe_bot/audit/log.py`:

  ```python
  import json
  import logging
  import os
  from datetime import datetime, timezone


  def get_logger(name: str) -> logging.Logger:
      logger = logging.getLogger(name)
      if not logger.handlers:
          handler = logging.StreamHandler()
          handler.setFormatter(
              logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
          )
          logger.addHandler(handler)
          logger.setLevel(logging.INFO)
      return logger


  class AuditLog:
      def __init__(self, store: "Store", jsonl_path: str) -> None:
          self._store = store
          self._jsonl_path = jsonl_path

      def record(self, run_id: str, action: str, target: dict, detail: dict) -> None:
          ts = datetime.now(timezone.utc).isoformat()
          target_json = json.dumps(target)
          detail_json = json.dumps(detail)

          # PUBLIC seam: one SQLite audit row (do NOT touch Store internals).
          self._store.append_audit(run_id, action, target_json, detail_json, ts)

          # Append-only JSONL sink; create the parent dir if absent.
          parent = os.path.dirname(self._jsonl_path)
          if parent:
              os.makedirs(parent, exist_ok=True)
          line = json.dumps(
              {
                  "ts": ts,
                  "run_id": run_id,
                  "action": action,
                  "target": target,
                  "detail": detail,
              }
          )
          with open(self._jsonl_path, "a", encoding="utf-8") as fh:
              fh.write(line + "\n")
  ```

- [ ] **Step 4: Run the test (expect pass).** Run: `pytest tests/audit/test_log.py -q`  Expected: all tests pass.

- [ ] **Step 5: Commit.** Run: `git add edvibe_bot/audit/__init__.py edvibe_bot/audit/log.py tests/audit/__init__.py tests/audit/test_log.py && git commit -m "feat: audit log (structured logger + SQLite seam + append-only JSONL)"`

---

The spec confirms the evaluator design. Note the interface contract specifies the OpenAI SDK (`openai`) — this is an OpenAI-based project, not Claude/Anthropic, so the claude-api skill does not apply here. I'll write the section using the OpenAI SDK per the binding contract.

Here are the tasks for my assigned modules.

### Task: Evaluation schema (ExerciseType, Evaluation, EvalRequest)

**Files:**
- Create: `edvibe_bot/evaluator/schema.py`
- Create: `edvibe_bot/evaluator/__init__.py`
- Create: `tests/evaluator/__init__.py`
- Test: `tests/evaluator/test_schema.py`

- [ ] **Step 1: Write the failing test** for clamping and field shapes.

```python
# tests/evaluator/test_schema.py
import pytest
from pydantic import ValidationError

from edvibe_bot.evaluator.schema import (
    Evaluation,
    EvalRequest,
    ExerciseType,
)


def test_exercise_type_values():
    assert ExerciseType.AUDIO.value == "audio"
    assert ExerciseType.TEXT.value == "text"
    assert ExerciseType.AUTO_CHECKED.value == "auto_checked"
    assert ExerciseType.MANUAL_UNKNOWN.value == "manual_unknown"


def test_score_clamped_high():
    assert Evaluation(score=15, comment="c", rationale="r", confidence=0.5).score == 10


def test_score_clamped_low():
    assert Evaluation(score=-3, comment="c", rationale="r", confidence=0.5).score == 0


def test_score_within_range_unchanged():
    assert Evaluation(score=7, comment="c", rationale="r", confidence=0.5).score == 7


def test_confidence_clamped_high():
    assert Evaluation(score=5, comment="c", rationale="r", confidence=2.0).confidence == 1.0


def test_confidence_clamped_low():
    assert Evaluation(score=5, comment="c", rationale="r", confidence=-1.0).confidence == 0.0


def test_confidence_within_range_unchanged():
    assert Evaluation(score=5, comment="c", rationale="r", confidence=0.6).confidence == 0.6


def test_eval_request_carries_prompt_and_answer():
    req = EvalRequest(
        exercise_type=ExerciseType.TEXT,
        section="Writing",
        prompt_text="Describe your weekend.",
        student_answer="I went to the park.",
    )
    assert req.exercise_type is ExerciseType.TEXT
    assert req.section == "Writing"
    assert req.prompt_text == "Describe your weekend."
    assert req.student_answer == "I went to the park."


def test_eval_request_accepts_audio_type():
    req = EvalRequest(
        exercise_type=ExerciseType.AUDIO,
        section="Speaking",
        prompt_text="Read the passage aloud.",
        student_answer="transcript text",
    )
    assert req.exercise_type is ExerciseType.AUDIO
```

- [ ] **Step 2: Run the test, watch it fail.** Run: `pytest tests/evaluator/test_schema.py -q`  Expected: collection/import error or `ModuleNotFoundError: edvibe_bot.evaluator.schema`.

- [ ] **Step 3: Create the package init files** (empty).

```python
# edvibe_bot/evaluator/__init__.py
```

```python
# tests/evaluator/__init__.py
```

- [ ] **Step 4: Implement the schema** with clamping validators.

```python
# edvibe_bot/evaluator/schema.py
from enum import Enum

from pydantic import BaseModel, field_validator


class ExerciseType(str, Enum):
    AUDIO = "audio"
    TEXT = "text"
    AUTO_CHECKED = "auto_checked"
    MANUAL_UNKNOWN = "manual_unknown"


class Evaluation(BaseModel):
    score: int
    comment: str
    rationale: str
    confidence: float

    @field_validator("score")
    @classmethod
    def _clamp_score(cls, v: int) -> int:
        if v < 0:
            return 0
        if v > 10:
            return 10
        return v

    @field_validator("confidence")
    @classmethod
    def _clamp_confidence(cls, v: float) -> float:
        if v < 0.0:
            return 0.0
        if v > 1.0:
            return 1.0
        return v


class EvalRequest(BaseModel):
    exercise_type: ExerciseType
    section: str
    prompt_text: str
    student_answer: str
```

- [ ] **Step 5: Run the test, watch it pass.** Run: `pytest tests/evaluator/test_schema.py -q`  Expected: all tests pass.

- [ ] **Step 6: Commit.** Run: `git add edvibe_bot/evaluator/__init__.py edvibe_bot/evaluator/schema.py tests/evaluator/__init__.py tests/evaluator/test_schema.py && git commit -m "feat: add evaluator schema with score/confidence clamping"`

---

### Task: Pre-IELTS rubric prompts + build_messages

**Files:**
- Create: `edvibe_bot/evaluator/prompts.py`
- Test: `tests/evaluator/test_prompts.py`

- [ ] **Step 1: Write the failing test** for rubric content and message construction.

```python
# tests/evaluator/test_prompts.py
import json

from edvibe_bot.evaluator.prompts import RUBRIC_AUDIO, RUBRIC_TEXT, build_messages
from edvibe_bot.evaluator.schema import EvalRequest, ExerciseType


def test_rubrics_are_nonempty_strings():
    assert isinstance(RUBRIC_AUDIO, str) and RUBRIC_AUDIO.strip()
    assert isinstance(RUBRIC_TEXT, str) and RUBRIC_TEXT.strip()


def test_rubrics_reference_pre_ielts_level():
    assert "Pre-IELTS" in RUBRIC_AUDIO
    assert "Pre-IELTS" in RUBRIC_TEXT
    # CEFR A2-B1 target band
    assert "A2" in RUBRIC_AUDIO and "B1" in RUBRIC_AUDIO
    assert "A2" in RUBRIC_TEXT and "B1" in RUBRIC_TEXT


def _make_req(exercise_type: ExerciseType) -> EvalRequest:
    return EvalRequest(
        exercise_type=exercise_type,
        section="Speaking",
        prompt_text="PROMPT_MARKER describe your day",
        student_answer="ANSWER_MARKER I had a good day",
    )


def test_build_messages_returns_system_then_user():
    msgs = build_messages(_make_req(ExerciseType.TEXT))
    assert isinstance(msgs, list)
    assert len(msgs) == 2
    assert msgs[0]["role"] == "system"
    assert msgs[1]["role"] == "user"


def test_build_messages_embeds_prompt_and_answer_in_user():
    msgs = build_messages(_make_req(ExerciseType.TEXT))
    user_content = msgs[1]["content"]
    assert "PROMPT_MARKER describe your day" in user_content
    assert "ANSWER_MARKER I had a good day" in user_content


def test_build_messages_demands_strict_json_keys():
    msgs = build_messages(_make_req(ExerciseType.TEXT))
    blob = msgs[0]["content"] + msgs[1]["content"]
    for key in ("score", "comment", "rationale", "confidence"):
        assert key in blob
    assert "JSON" in blob


def test_build_messages_audio_uses_audio_rubric():
    msgs = build_messages(_make_req(ExerciseType.AUDIO))
    assert RUBRIC_AUDIO in msgs[0]["content"]
    assert RUBRIC_TEXT not in msgs[0]["content"]


def test_build_messages_text_uses_text_rubric():
    msgs = build_messages(_make_req(ExerciseType.TEXT))
    assert RUBRIC_TEXT in msgs[0]["content"]
    assert RUBRIC_AUDIO not in msgs[0]["content"]


def test_build_messages_manual_unknown_falls_back_to_text_rubric():
    msgs = build_messages(_make_req(ExerciseType.MANUAL_UNKNOWN))
    assert RUBRIC_TEXT in msgs[0]["content"]
```

- [ ] **Step 2: Run the test, watch it fail.** Run: `pytest tests/evaluator/test_prompts.py -q`  Expected: `ModuleNotFoundError: edvibe_bot.evaluator.prompts`.

- [ ] **Step 3: Implement the prompts module.**

```python
# edvibe_bot/evaluator/prompts.py
from edvibe_bot.evaluator.schema import EvalRequest, ExerciseType

RUBRIC_AUDIO = """\
You are grading a spoken-English homework answer in the "Pre-IELTS" marathon.
The target level is CEFR A2-B1, so calibrate expectations to an early-intermediate
learner — do not penalise minor slips that an A2-B1 speaker would naturally make.

The student answer below is a transcript of an audio recording. Judge:
- Task response: did they actually address the prompt/task?
- Pronunciation & intelligibility: could a listener follow them?
- Fluency: pace, hesitation, and connected speech for the A2-B1 band.
- Range & accuracy: vocabulary and grammar appropriate to A2-B1.

Be fair and encouraging. A blank, off-topic, or unintelligible answer scores low.
A clear, on-task A2-B1 answer scores in the upper range."""

RUBRIC_TEXT = """\
You are grading a written-English homework answer in the "Pre-IELTS" marathon.
The target level is CEFR A2-B1, so calibrate expectations to an early-intermediate
learner — do not penalise minor slips that an A2-B1 writer would naturally make.

The student answer below is written text. Judge:
- Task completion: did they actually address the prompt/task?
- Grammar accuracy: appropriate to the A2-B1 band.
- Vocabulary range: appropriate to the A2-B1 band.
- Coherence: is the answer organised and understandable?

Be fair and encouraging. A blank, off-topic, or empty answer scores low.
A clear, on-task A2-B1 answer scores in the upper range."""


def build_messages(req: "EvalRequest") -> "list[dict]":
    if req.exercise_type is ExerciseType.AUDIO:
        rubric = RUBRIC_AUDIO
    else:
        rubric = RUBRIC_TEXT

    system_content = (
        f"{rubric}\n\n"
        "Return your evaluation as a STRICT JSON object and nothing else "
        "(no markdown, no code fences, no commentary). The object MUST have "
        "exactly these keys:\n"
        '  "score": integer 0-10 (overall mark on a 0 to 10 scale),\n'
        '  "comment": string, a 1-2 sentence constructive comment IN ENGLISH '
        "addressed to the student,\n"
        '  "rationale": string, a brief internal justification (not shown to the student),\n'
        '  "confidence": number 0.0-1.0 (how confident you are in this score).\n'
        "If the answer is empty, off-topic, or you cannot assess it, give a low "
        "score and a low confidence."
    )

    user_content = (
        f"Section: {req.section}\n\n"
        f"Exercise task / prompt:\n{req.prompt_text}\n\n"
        f"Student answer:\n{req.student_answer}\n\n"
        "Evaluate the student answer against the task using the rubric above and "
        "respond with the strict JSON object."
    )

    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
    ]
```

- [ ] **Step 4: Run the test, watch it pass.** Run: `pytest tests/evaluator/test_prompts.py -q`  Expected: all tests pass.

- [ ] **Step 5: Commit.** Run: `git add edvibe_bot/evaluator/prompts.py tests/evaluator/test_prompts.py && git commit -m "feat: add Pre-IELTS rubric prompts and build_messages"`

---

### Task: Text evaluator with bounded retry/backoff and fail-safe parse_failed

**Files:**
- Create: `edvibe_bot/evaluator/text.py`
- Test: `tests/evaluator/test_text.py`

- [ ] **Step 1: Write the failing test.** The OpenAI client is created inside `evaluate` via `openai.OpenAI(...)`; we monkeypatch `openai.OpenAI` with a fake that returns a canned chat-completion (success / transient-error-then-success / persistent failure). `time.sleep` is patched so backoff is instant.

```python
# tests/evaluator/test_text.py
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
```

- [ ] **Step 2: Run the test, watch it fail.** Run: `pytest tests/evaluator/test_text.py -q`  Expected: `ModuleNotFoundError: edvibe_bot.evaluator.text`.

- [ ] **Step 3: Implement the text evaluator.** Calls OpenAI chat completions with a JSON `response_format`, bounded retry/backoff (3 attempts), parsing into a clamped `Evaluation`; on persistent error or parse failure returns the `parse_failed` Evaluation so the runner FLAGS it.

```python
# edvibe_bot/evaluator/text.py
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
```

- [ ] **Step 4: Run the test, watch it pass.** Run: `pytest tests/evaluator/test_text.py -q`  Expected: all tests pass.

- [ ] **Step 5: Run the whole evaluator suite** to confirm nothing regressed. Run: `pytest tests/evaluator -q`  Expected: all tests pass.

- [ ] **Step 6: Commit.** Run: `git add edvibe_bot/evaluator/text.py tests/evaluator/test_text.py && git commit -m "feat: add text evaluator with bounded retry and parse_failed fail-safe"`

---

I have enough context. The spec confirms `gpt-4o-transcribe` primary with `whisper-1` fallback, retry/backoff, and flag-on-failure. Writing the section now.

```markdown
### Task: Audio download + transcription (`evaluator/audio.py`)

**Files:**
- Create: `edvibe_bot/evaluator/audio.py`
- Test: `tests/evaluator/test_audio.py`
- Test (packaging): `tests/evaluator/__init__.py` (empty, if not already created by a sibling evaluator task)

This module has two functions. `download_audio` fetches the recording bytes through Playwright's request context and returns `None` on ANY failure (never raises). `transcribe` sends those bytes to OpenAI with bounded retry/backoff on the primary model, falls back to `whisper-1`, and raises only if BOTH fail — the runner wraps this call in `try/except` and FLAGS the exercise on failure. Both behaviours are unit-tested with fakes/monkeypatching; `time.sleep` is patched so retries are instant.

- [ ] **Step 1: Write the failing tests.**

```python
# tests/evaluator/test_audio.py
import io

import pytest

import edvibe_bot.evaluator.audio as audio_mod
from edvibe_bot.evaluator.audio import download_audio, transcribe


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


def test_transcribe_returns_text_on_first_success(monkeypatch):
    rec = _Recorder([("return", "hello world")])
    _patch_client(monkeypatch, rec)
    out = transcribe(b"OGGDATA", _FakeSettings())
    assert out == "hello world"
    assert rec.models == ["gpt-4o-transcribe"]
    # bytes became an in-memory file-like that carries a usable filename
    assert rec.filenames[0] and rec.filenames[0].endswith(".ogg")


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
```

- [ ] **Step 2: Run the tests (RED).** Run: `pytest tests/evaluator/test_audio.py -q`  Expected: collection/import error or failures (`edvibe_bot.evaluator.audio` does not exist yet).

- [ ] **Step 3: Create the package `__init__.py` if missing.** Only create it if a sibling evaluator task has not already.

```python
# tests/evaluator/__init__.py
```

- [ ] **Step 4: Implement `edvibe_bot/evaluator/audio.py`.**

```python
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

from edvibe_bot.audit.log import get_logger

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
```

- [ ] **Step 5: Run the tests (GREEN).** Run: `pytest tests/evaluator/test_audio.py -q`  Expected: all tests pass (download returns bytes/None correctly; transcribe succeeds first-try, falls back to whisper-1 after primary exhausts 3 attempts, and raises when both exhaust). `time.sleep` is patched, so the run is fast.

- [ ] **Step 6: Commit.** (Add `tests/evaluator/__init__.py` ONLY if you created it in Step 3.)
  Run: `git add edvibe_bot/evaluator/audio.py tests/evaluator/test_audio.py tests/evaluator/__init__.py && git commit -m "feat: audio download + OpenAI transcription with whisper-1 fallback"`
```

---

I have enough context. Here is the task section for `edvibe_bot/auth/login.py`.

### Task: Auth — login, session validity, and storage_state reuse

**Files:**
- Create: `edvibe_bot/auth/login.py`
- Create: `edvibe_bot/auth/__init__.py` (empty)
- Test: `tests/auth/test_login.py`
- Create: `tests/auth/__init__.py` (empty)

> Browser I/O module. We ship the real Playwright implementation but extract no extra pure helpers (the logic is thin); we verify the I/O sequencing with a hand-rolled fake `Page`/`Context`/`Browser` double (mirroring Playwright's sync surface: `.goto/.fill/.click/.url`, and `context.new_page()`/`context.storage_state(path=...)`). Selectors and `SelectorError` already exist (Bootstrap task) — REFERENCE only. The live re-login + storage_state round-trip is confirmed in "Final integration & self-review".

- [ ] **Step 1: Write the failing test with fake Playwright doubles.** Create `tests/auth/__init__.py` (empty) and `tests/auth/test_login.py`:

```python
import os

import pytest

from edvibe_bot import selectors
from edvibe_bot.auth import login as auth
from edvibe_bot.config import Settings


def make_settings(tmp_path, **overrides) -> Settings:
    base = dict(
        edvibe_login="teacher@example.com",
        edvibe_password="s3cret",
        openai_api_key="sk-test",
        storage_state_path=str(tmp_path / "storage_state.json"),
    )
    base.update(overrides)
    return Settings(**base)


class FakePage:
    """Mirrors the slice of playwright.sync_api.Page used by auth.login."""

    def __init__(self, land_url: str):
        # url after a goto() resolves to land_url (simulates server redirect)
        self._land_url = land_url
        self.url = ""
        self.goto_calls: list[str] = []
        self.fills: list[tuple[str, str]] = []
        self.clicks: list[str] = []
        self.waited = False

    def goto(self, url, **kwargs):
        self.goto_calls.append(url)
        self.url = self._land_url

    def fill(self, sel, value):
        self.fills.append((sel, value))

    def click(self, sel):
        self.clicks.append(sel)

    def wait_for_load_state(self, state="load", **kwargs):
        self.waited = True


class FakeContext:
    def __init__(self, page: FakePage):
        self._page = page
        self.new_page_calls = 0
        self.storage_state_calls: list[str] = []

    def new_page(self) -> FakePage:
        self.new_page_calls += 1
        return self._page

    def storage_state(self, path=None):
        self.storage_state_calls.append(path)


def test_login_fills_and_clicks_the_right_selectors(tmp_path):
    page = FakePage(land_url=selectors.AUTHED_URL)
    settings = make_settings(tmp_path)

    auth.login(page, settings)

    assert page.goto_calls == [selectors.LOGIN_URL]
    assert (selectors.LOGIN_EMAIL, settings.edvibe_login) in page.fills
    assert (selectors.LOGIN_PASSWORD, settings.edvibe_password) in page.fills
    assert page.clicks == [selectors.LOGIN_SUBMIT]
    assert page.waited is True


def test_is_session_valid_true_when_landing_authed(tmp_path):
    page = FakePage(land_url=selectors.AUTHED_URL)
    assert auth.is_session_valid(page) is True
    assert page.goto_calls == [selectors.AUTHED_URL]


def test_is_session_valid_false_when_redirected_to_login(tmp_path):
    page = FakePage(land_url=selectors.LOGIN_URL)
    assert auth.is_session_valid(page) is False


def test_ensure_logged_in_logs_in_and_saves_state_when_no_file(tmp_path):
    page = FakePage(land_url=selectors.AUTHED_URL)
    ctx = FakeContext(page)
    settings = make_settings(tmp_path)
    assert not os.path.exists(settings.storage_state_path)

    returned = auth.ensure_logged_in(ctx, settings)

    assert returned is page
    assert ctx.new_page_calls == 1
    # fresh login happened
    assert page.goto_calls[0] == selectors.LOGIN_URL
    assert page.clicks == [selectors.LOGIN_SUBMIT]
    # storage_state persisted to the configured path
    assert ctx.storage_state_calls == [settings.storage_state_path]


def test_ensure_logged_in_reuses_valid_state_without_relogin(tmp_path):
    page = FakePage(land_url=selectors.AUTHED_URL)
    ctx = FakeContext(page)
    settings = make_settings(tmp_path)
    # simulate a pre-existing storage_state file
    with open(settings.storage_state_path, "w") as fh:
        fh.write("{}")

    returned = auth.ensure_logged_in(ctx, settings)

    assert returned is page
    # only the is_session_valid probe ran; no login navigation/submit
    assert page.goto_calls == [selectors.AUTHED_URL]
    assert page.clicks == []
    # no re-save when the session was already valid
    assert ctx.storage_state_calls == []


def test_ensure_logged_in_relogs_in_when_state_is_stale(tmp_path):
    # land on LOGIN_URL first (stale session) then re-login lands AUTHED
    page = FakePage(land_url=selectors.LOGIN_URL)
    ctx = FakeContext(page)
    settings = make_settings(tmp_path)
    with open(settings.storage_state_path, "w") as fh:
        fh.write("{}")

    returned = auth.ensure_logged_in(ctx, settings)

    assert returned is page
    # probe redirected to login => stale => full login() ran (goes to LOGIN_URL)
    assert selectors.LOGIN_URL in page.goto_calls
    assert page.clicks == [selectors.LOGIN_SUBMIT]
    # state re-saved after the fresh login
    assert ctx.storage_state_calls == [settings.storage_state_path]
```

- [ ] **Step 2: Run the test — watch it fail.** Run: `pytest tests/auth/test_login.py -q`  Expected: collection/import error or failures because `edvibe_bot/auth/login.py` does not exist yet.

- [ ] **Step 3: Implement `edvibe_bot/auth/login.py`.** Create `edvibe_bot/auth/__init__.py` (empty), then write the module:

```python
import os

from playwright.sync_api import BrowserContext, Page

from edvibe_bot import selectors
from edvibe_bot.config import Settings


def login(page: Page, settings: Settings) -> None:
    """Perform a fresh username/password login on edvibe.com."""
    page.goto(selectors.LOGIN_URL)
    page.fill(selectors.LOGIN_EMAIL, settings.edvibe_login)
    page.fill(selectors.LOGIN_PASSWORD, settings.edvibe_password)
    page.click(selectors.LOGIN_SUBMIT)
    page.wait_for_load_state("networkidle")


def is_session_valid(page: Page) -> bool:
    """Probe an authed URL; the session is valid iff we are NOT bounced to login."""
    page.goto(selectors.AUTHED_URL)
    return page.url != selectors.LOGIN_URL


def ensure_logged_in(context: BrowserContext, settings: Settings) -> Page:
    """Restore a saved storage_state if it is still valid; otherwise log in fresh
    and persist storage_state to settings.storage_state_path. Returns the Page."""
    page = context.new_page()
    if os.path.exists(settings.storage_state_path) and is_session_valid(page):
        return page
    login(page, settings)
    context.storage_state(path=settings.storage_state_path)
    return page
```

- [ ] **Step 4: Run the test — watch it pass.** Run: `pytest tests/auth/test_login.py -q`  Expected: all tests pass (login selector wiring, session-validity true/false, and the three `ensure_logged_in` branches: fresh login + save, reuse valid state, re-login on stale state).

- [ ] **Step 5: Commit.** Run: `git add edvibe_bot/auth/__init__.py edvibe_bot/auth/login.py tests/auth/__init__.py tests/auth/test_login.py && git commit -m "feat: edvibe auth login with storage_state reuse and session validity check"`

---

I have enough context. Now I'll write the markdown task section for the three scraper modules, conforming exactly to the interface contract and using only the fixed selector names.

```markdown
### Task: Dashboard scraper — Student + open_marathon + list_students

**Files:**
- Create: `edvibe_bot/scraper/dashboard.py`
- Create: `tests/scraper/__init__.py`
- Test: `tests/scraper/test_dashboard.py`

REFERENCES ONLY (already created by the Bootstrap task): `from edvibe_bot import selectors`. Uses `selectors.NAV_CLASSES`, `selectors.MARATHONS_TAB`, `selectors.PRE_IELTS_CARD`, `selectors.FILTER_BUTTON`, `selectors.CURATOR_OPTION`, `selectors.FILTER_APPLY`, `selectors.STUDENT_ROW`, `selectors.STUDENT_ID_ATTR`, `selectors.STUDENT_NAME`. Never redefine selectors.

- [ ] **Step 1: Create the scraper test package marker.** Create an EMPTY file so `tests/scraper/` is importable.

```python
# tests/scraper/__init__.py
```

- [ ] **Step 2: Write failing tests for `list_students` + `open_marathon` using fake Page/Locator doubles.** These are I/O readers, but we verify them with fakes that mirror the real Playwright sync API (`.first` is a PROPERTY, `locator()` returns a locator, `.click()`/`.goto()` record calls, `get_attribute(name)` returns attr values, `inner_text()` returns text). `open_marathon` must call EXACTLY the 6 steps in order; `list_students` must read `STUDENT_ROW` and build `Student(id from STUDENT_ID_ATTR, name from STUDENT_NAME)`.

```python
# tests/scraper/test_dashboard.py
import pytest

from edvibe_bot import selectors
from edvibe_bot.scraper.dashboard import Student, open_marathon, list_students


class FakeLocator:
    """Mirrors the subset of the Playwright sync Locator API the scraper uses."""

    def __init__(self, *, attrs=None, text="", children=None):
        self._attrs = attrs or {}
        self._text = text
        self._children = children if children is not None else []
        self.click_count = 0

    @property
    def first(self):  # PROPERTY, not a method (mirrors Playwright)
        return self._children[0] if self._children else self

    def nth(self, i):
        return self._children[i]

    def count(self):
        return len(self._children)

    def all(self):
        return list(self._children)

    def locator(self, selector):
        # A child row resolves nested selectors to a single locator.
        if selector == selectors.STUDENT_NAME:
            return FakeLocator(text=self._text)
        return FakeLocator()

    def get_attribute(self, name):
        return self._attrs.get(name)

    def inner_text(self):
        return self._text

    def click(self):
        self.click_count += 1


class FakePage:
    def __init__(self, *, locators=None):
        # locators: mapping selector-string -> FakeLocator
        self._locators = locators or {}
        self.goto_calls = []
        self.click_log = []

    def goto(self, url):
        self.goto_calls.append(url)

    def locator(self, selector):
        loc = self._locators.get(selector)
        if loc is None:
            loc = FakeLocator()
            self._locators[selector] = loc
        return loc


class RecordingPage(FakePage):
    """Records the ordered sequence of (kind, target) actions for open_marathon."""

    def goto(self, url):
        super().goto(url)
        self.click_log.append(("goto", url))

    def locator(self, selector):
        page = self

        class _Click(FakeLocator):
            def click(_self):
                page.click_log.append(("click", selector))

        return _Click()


class DummySettings:
    marathon_name = "Pre-IELTS"
    curator_name = "Mister Adilet"


def test_open_marathon_runs_the_six_steps_in_order():
    page = RecordingPage()
    open_marathon(page, DummySettings())
    assert page.click_log == [
        ("goto", selectors.NAV_CLASSES),
        ("click", selectors.MARATHONS_TAB),
        ("click", selectors.PRE_IELTS_CARD),
        ("click", selectors.FILTER_BUTTON),
        ("click", selectors.CURATOR_OPTION),
        ("click", selectors.FILTER_APPLY),
    ]


def test_list_students_builds_students_from_rows():
    rows = FakeLocator(
        children=[
            FakeLocator(attrs={selectors.STUDENT_ID_ATTR: "s1"}, text="Анель"),
            FakeLocator(attrs={selectors.STUDENT_ID_ATTR: "s2"}, text="Bauyrzhan"),
        ]
    )
    page = FakePage(locators={selectors.STUDENT_ROW: rows})
    students = list_students(page)
    assert students == [Student(id="s1", name="Анель"), Student(id="s2", name="Bauyrzhan")]


def test_list_students_empty_returns_empty_list():
    page = FakePage(locators={selectors.STUDENT_ROW: FakeLocator(children=[])})
    assert list_students(page) == []
```

- [ ] **Step 3: Run the tests — watch them fail (module/functions do not exist yet).** Run: `pytest tests/scraper/test_dashboard.py -q`  Expected: collection/import error or failures (`edvibe_bot.scraper.dashboard` missing).

- [ ] **Step 4: Implement `edvibe_bot/scraper/dashboard.py`.** `open_marathon` performs EXACTLY the six steps. `list_students` iterates `STUDENT_ROW` rows, reading the stable id from the `STUDENT_ID_ATTR` attribute and the name from the nested `STUDENT_NAME` locator's text; a missing id attribute raises `SelectorError` (no row may produce a student without a stable id).

```python
# edvibe_bot/scraper/dashboard.py
from __future__ import annotations

from dataclasses import dataclass

from playwright.sync_api import Page

from edvibe_bot import selectors
from edvibe_bot.config import Settings
from edvibe_bot.errors import SelectorError


@dataclass
class Student:
    id: str
    name: str


def open_marathon(page: Page, settings: Settings) -> None:
    """classes -> Марафоны -> Pre-IELTS -> filter -> curator -> apply."""
    page.goto(selectors.NAV_CLASSES)
    page.locator(selectors.MARATHONS_TAB).click()
    page.locator(selectors.PRE_IELTS_CARD).click()
    page.locator(selectors.FILTER_BUTTON).click()
    page.locator(selectors.CURATOR_OPTION).click()
    page.locator(selectors.FILTER_APPLY).click()


def list_students(page: Page) -> list[Student]:
    rows = page.locator(selectors.STUDENT_ROW)
    students: list[Student] = []
    for row in rows.all():
        student_id = row.get_attribute(selectors.STUDENT_ID_ATTR)
        if not student_id:
            raise SelectorError(
                f"student row missing id attribute {selectors.STUDENT_ID_ATTR!r}"
            )
        name = row.locator(selectors.STUDENT_NAME).inner_text().strip()
        students.append(Student(id=student_id, name=name))
    return students
```

- [ ] **Step 5: Run the tests — watch them pass.** Run: `pytest tests/scraper/test_dashboard.py -q`  Expected: all tests pass.

- [ ] **Step 6: Commit.** Run: `git add edvibe_bot/scraper/dashboard.py tests/scraper/__init__.py tests/scraper/test_dashboard.py && git commit -m "feat: dashboard scraper (open_marathon + list_students)"`

---

### Task: Progress scraper — Lesson, list/awaiting/open lessons

**Files:**
- Create: `edvibe_bot/scraper/progress.py`
- Test: `tests/scraper/test_progress.py`

REFERENCES ONLY: `from edvibe_bot import selectors`. Uses `selectors.STUDENT_PROGRESS_BTN`, `selectors.LESSON_ROW`, `selectors.LESSON_ID_ATTR`, `selectors.LESSON_NAME`, `selectors.LESSON_STATUS_AWAITING`, `selectors.LESSON_OPEN_BUTTON`. `awaiting_lessons` is PURE (full TDD). `open_lesson` has ONE canonical implementation with no dead code.

- [ ] **Step 1: Write failing tests.** Cover the PURE `awaiting_lessons` filter (TDD), the `list_lessons` reader (status = "awaiting" when `LESSON_STATUS_AWAITING` present, else "complete"/"other"), `open_progress` (clicks `STUDENT_PROGRESS_BTN`), and `open_lesson` (locates the row by `LESSON_ROW[LESSON_ID_ATTR='<id>']`, then clicks the `LESSON_OPEN_BUTTON` inside it). The fake `Page.locator()` is keyed on the EXACT composed selector string and asserts the open button was clicked.

```python
# tests/scraper/test_progress.py
import pytest

from edvibe_bot import selectors
from edvibe_bot.scraper.dashboard import Student
from edvibe_bot.scraper.progress import (
    Lesson,
    open_progress,
    list_lessons,
    awaiting_lessons,
    open_lesson,
)


# ---- PURE: awaiting_lessons ----

def test_awaiting_lessons_keeps_only_awaiting():
    lessons = [
        Lesson(id="l1", name="Lesson 1", status="awaiting"),
        Lesson(id="l2", name="Lesson 2", status="complete"),
        Lesson(id="l3", name="Lesson 3", status="awaiting"),
        Lesson(id="l4", name="Lesson 4", status="other"),
    ]
    assert awaiting_lessons(lessons) == [lessons[0], lessons[2]]


def test_awaiting_lessons_empty_when_none_awaiting():
    lessons = [Lesson(id="l1", name="Lesson 1", status="complete")]
    assert awaiting_lessons(lessons) == []


def test_awaiting_lessons_empty_input():
    assert awaiting_lessons([]) == []


# ---- Reader doubles ----

class FakeLocator:
    def __init__(self, *, text="", children=None, attrs=None, present_selectors=None):
        self._text = text
        self._children = children if children is not None else []
        self._attrs = attrs or {}
        self._present = set(present_selectors or [])
        self.click_count = 0

    @property
    def first(self):
        return self._children[0] if self._children else self

    def all(self):
        return list(self._children)

    def get_attribute(self, name):
        return self._attrs.get(name)

    def inner_text(self):
        return self._text

    def locator(self, selector):
        if selector == selectors.LESSON_NAME:
            return FakeLocator(text=self._text)
        if selector in self._present:
            return FakeLocator(children=[FakeLocator()])  # count() > 0
        return FakeLocator(children=[])  # absent -> count() == 0

    def count(self):
        return len(self._children)

    def click(self):
        self.click_count += 1


class FakePage:
    def __init__(self, *, locators=None):
        self._locators = locators or {}
        self.clicked = []

    def locator(self, selector):
        loc = self._locators.get(selector)
        if loc is None:
            loc = FakeLocator()
            self._locators[selector] = loc
        return loc


def test_open_progress_clicks_progress_button():
    btn = FakeLocator()
    page = FakePage(locators={selectors.STUDENT_PROGRESS_BTN: btn})
    open_progress(page, Student(id="s1", name="Анель"))
    assert btn.click_count == 1


def test_list_lessons_reads_id_name_and_status():
    awaiting_row = FakeLocator(
        text="Lesson 14",
        attrs={selectors.LESSON_ID_ATTR: "l14"},
        present_selectors=[selectors.LESSON_STATUS_AWAITING],
    )
    complete_row = FakeLocator(
        text="Lesson 13",
        attrs={selectors.LESSON_ID_ATTR: "l13"},
        present_selectors=[],  # no awaiting marker
    )
    rows = FakeLocator(children=[awaiting_row, complete_row])
    page = FakePage(locators={selectors.LESSON_ROW: rows})

    lessons = list_lessons(page)
    assert lessons == [
        Lesson(id="l14", name="Lesson 14", status="awaiting"),
        Lesson(id="l13", name="Lesson 13", status="complete"),
    ]


def test_open_lesson_clicks_open_button_inside_matched_row():
    lesson = Lesson(id="l14", name="Lesson 14", status="awaiting")
    composed = f"{selectors.LESSON_ROW}[{selectors.LESSON_ID_ATTR}='{lesson.id}']"
    open_btn = FakeLocator()

    class RowLocator(FakeLocator):
        def locator(self, selector):
            assert selector == selectors.LESSON_OPEN_BUTTON
            return open_btn

    page = FakePage(locators={composed: RowLocator()})
    open_lesson(page, lesson)
    assert open_btn.click_count == 1
```

- [ ] **Step 2: Run — watch the tests fail.** Run: `pytest tests/scraper/test_progress.py -q`  Expected: import/collection error (`edvibe_bot.scraper.progress` missing).

- [ ] **Step 3: Implement `edvibe_bot/scraper/progress.py`.** `open_progress` clicks `STUDENT_PROGRESS_BTN`. `list_lessons` reads each `LESSON_ROW`: id from `LESSON_ID_ATTR` (missing → `SelectorError`), name from `LESSON_NAME`, status `"awaiting"` if `LESSON_STATUS_AWAITING` present else `"complete"`. `awaiting_lessons` is a pure filter. `open_lesson` is the single canonical implementation — locate the row by attribute, then click the open button within it (NO `get_by_role`, no placeholders).

```python
# edvibe_bot/scraper/progress.py
from __future__ import annotations

from dataclasses import dataclass

from playwright.sync_api import Page

from edvibe_bot import selectors
from edvibe_bot.errors import SelectorError
from edvibe_bot.scraper.dashboard import Student


@dataclass
class Lesson:
    id: str
    name: str
    status: str  # "awaiting" | "complete" | "other"


def open_progress(page: Page, student: Student) -> None:
    page.locator(selectors.STUDENT_PROGRESS_BTN).click()


def list_lessons(page: Page) -> list[Lesson]:
    rows = page.locator(selectors.LESSON_ROW)
    lessons: list[Lesson] = []
    for row in rows.all():
        lesson_id = row.get_attribute(selectors.LESSON_ID_ATTR)
        if not lesson_id:
            raise SelectorError(
                f"lesson row missing id attribute {selectors.LESSON_ID_ATTR!r}"
            )
        name = row.locator(selectors.LESSON_NAME).inner_text().strip()
        is_awaiting = row.locator(selectors.LESSON_STATUS_AWAITING).count() > 0
        status = "awaiting" if is_awaiting else "complete"
        lessons.append(Lesson(id=lesson_id, name=name, status=status))
    return lessons


def awaiting_lessons(lessons: list[Lesson]) -> list[Lesson]:
    """PURE filter: only lessons whose status is exactly 'awaiting'."""
    return [lesson for lesson in lessons if lesson.status == "awaiting"]


def open_lesson(page: Page, lesson: Lesson) -> None:
    row = page.locator(
        f"{selectors.LESSON_ROW}[{selectors.LESSON_ID_ATTR}='{lesson.id}']"
    )
    row.locator(selectors.LESSON_OPEN_BUTTON).click()
```

- [ ] **Step 4: Run — watch the tests pass.** Run: `pytest tests/scraper/test_progress.py -q`  Expected: all tests pass.

- [ ] **Step 5: Commit.** Run: `git add edvibe_bot/scraper/progress.py tests/scraper/test_progress.py && git commit -m "feat: progress scraper (list/awaiting/open lessons)"`

---

### Task: Lesson scraper — Exercise, classify_exercise (PURE), list_exercises

**Files:**
- Create: `edvibe_bot/scraper/lesson.py`
- Test: `tests/scraper/test_lesson.py`

REFERENCES ONLY: `from edvibe_bot import selectors`, `from edvibe_bot.evaluator.schema import ExerciseType`. Uses `selectors.EXERCISE_BLOCK`, `selectors.SECTION_NAV`, `selectors.EXERCISE_NUMBER`, `selectors.EXERCISE_ID_ATTR`, `selectors.EXERCISE_PROMPT`, `selectors.EXERCISE_AUDIO`, `selectors.EXERCISE_TEXT_ANSWER`, `selectors.GRADE_EXERCISE_BTN`. `classify_exercise` is PURE (full TDD). `list_exercises` reads `EXERCISE_AUDIO` via the `.first` PROPERTY.

- [ ] **Step 1: Write failing tests.** Full TDD for the PURE `classify_exercise` (grade+audio→AUDIO; grade+text→TEXT; no grade→AUTO_CHECKED; grade but neither→MANUAL_UNKNOWN). Then a `list_exercises` reader test using fake Page/Locator doubles that mirror the real API (`.first` is a property; `count()`/`get_attribute()`/`inner_text()`); assert `Exercise.element_id` is populated from `EXERCISE_ID_ATTR`, `section` from `SECTION_NAV`, `prompt_text` from `EXERCISE_PROMPT`, and `audio_url` from the audio locator's `.first` → `get_attribute("src")`.

```python
# tests/scraper/test_lesson.py
import pytest

from edvibe_bot import selectors
from edvibe_bot.evaluator.schema import ExerciseType
from edvibe_bot.scraper.lesson import Exercise, classify_exercise, list_exercises


# ---- PURE: classify_exercise ----

def test_classify_grade_and_audio_is_audio():
    assert classify_exercise(True, True, False) is ExerciseType.AUDIO


def test_classify_grade_and_audio_prefers_audio_over_text():
    assert classify_exercise(True, True, True) is ExerciseType.AUDIO


def test_classify_grade_and_text_is_text():
    assert classify_exercise(True, False, True) is ExerciseType.TEXT


def test_classify_no_grade_button_is_auto_checked():
    assert classify_exercise(False, True, True) is ExerciseType.AUTO_CHECKED
    assert classify_exercise(False, False, False) is ExerciseType.AUTO_CHECKED


def test_classify_grade_but_neither_is_manual_unknown():
    assert classify_exercise(True, False, False) is ExerciseType.MANUAL_UNKNOWN


# ---- Reader doubles ----

class FakeLocator:
    def __init__(self, *, text="", attrs=None, children=None, src=None):
        self._text = text
        self._attrs = attrs or {}
        self._children = children if children is not None else []
        self._src = src

    @property
    def first(self):
        return self._children[0] if self._children else self

    def all(self):
        return list(self._children)

    def count(self):
        return len(self._children)

    def inner_text(self):
        return self._text

    def get_attribute(self, name):
        if name == "src":
            return self._src
        return self._attrs.get(name)

    def locator(self, selector):
        return self._children_for(selector)

    # Maps a nested selector to a configured child locator.
    def _children_for(self, selector):
        mapping = self._attrs.get("__nested__", {})
        return mapping.get(selector, FakeLocator(children=[]))


class FakePage:
    def __init__(self, *, blocks, section):
        self._blocks = blocks
        self._section = section

    def locator(self, selector):
        if selector == selectors.EXERCISE_BLOCK:
            return FakeLocator(children=self._blocks)
        if selector == selectors.SECTION_NAV:
            return FakeLocator(text=self._section)
        return FakeLocator(children=[])


def _block(*, ex_id, number, prompt, audio_src=None, answer=None, has_grade):
    nested = {
        selectors.EXERCISE_NUMBER: FakeLocator(text=number),
        selectors.EXERCISE_PROMPT: FakeLocator(text=prompt),
        selectors.EXERCISE_AUDIO: FakeLocator(
            children=[FakeLocator(src=audio_src)] if audio_src else []
        ),
        selectors.EXERCISE_TEXT_ANSWER: (
            FakeLocator(text=answer, children=[FakeLocator()])
            if answer is not None
            else FakeLocator(children=[])
        ),
        selectors.GRADE_EXERCISE_BTN: (
            FakeLocator(children=[FakeLocator()]) if has_grade else FakeLocator(children=[])
        ),
    }
    return FakeLocator(attrs={selectors.EXERCISE_ID_ATTR: ex_id, "__nested__": nested})


def test_list_exercises_builds_audio_exercise_with_stable_id():
    block = _block(
        ex_id="ex-101",
        number="1",
        prompt="Describe your weekend.",
        audio_src="https://cdn.edvibe.com/a.mp3",
        answer=None,
        has_grade=True,
    )
    page = FakePage(blocks=[block], section="Speaking")
    exercises = list_exercises(page)
    assert len(exercises) == 1
    ex = exercises[0]
    assert ex.element_id == "ex-101"          # populated from EXERCISE_ID_ATTR
    assert ex.section == "Speaking"           # from SECTION_NAV, not prompt-derived
    assert ex.number == "1"
    assert ex.prompt_text == "Describe your weekend."
    assert ex.type is ExerciseType.AUDIO
    assert ex.has_grade_button is True
    assert ex.audio_url == "https://cdn.edvibe.com/a.mp3"
    assert ex.answer_text is None


def test_list_exercises_builds_text_exercise():
    block = _block(
        ex_id="ex-202",
        number="2",
        prompt="Write about your hobby.",
        audio_src=None,
        answer="I like reading.",
        has_grade=True,
    )
    page = FakePage(blocks=[block], section="Writing")
    ex = list_exercises(page)[0]
    assert ex.type is ExerciseType.TEXT
    assert ex.answer_text == "I like reading."
    assert ex.audio_url is None
    assert ex.element_id == "ex-202"


def test_list_exercises_auto_checked_when_no_grade_button():
    block = _block(
        ex_id="ex-303",
        number="3",
        prompt="Pick the correct word.",
        audio_src=None,
        answer="done",
        has_grade=False,
    )
    page = FakePage(blocks=[block], section="Grammar")
    ex = list_exercises(page)[0]
    assert ex.type is ExerciseType.AUTO_CHECKED
    assert ex.has_grade_button is False
```

- [ ] **Step 2: Run — watch the tests fail.** Run: `pytest tests/scraper/test_lesson.py -q`  Expected: import/collection error (`edvibe_bot.scraper.lesson` missing).

- [ ] **Step 3: Implement `edvibe_bot/scraper/lesson.py`.** Define the `Exercise` dataclass (including `prompt_text`). `classify_exercise` is the pure decision table. `list_exercises` reads the section heading once via `SECTION_NAV`, then for each `EXERCISE_BLOCK` reads number, the stable id from `EXERCISE_ID_ATTR`, prompt, audio src from `EXERCISE_AUDIO` via the `.first` PROPERTY, text answer, and grade-button presence; it classifies via `classify_exercise`. Audio url and answer text are normalized to `None` when absent.

```python
# edvibe_bot/scraper/lesson.py
from __future__ import annotations

from dataclasses import dataclass

from playwright.sync_api import Page

from edvibe_bot import selectors
from edvibe_bot.evaluator.schema import ExerciseType


@dataclass
class Exercise:
    section: str                # section heading text (from selectors.SECTION_NAV)
    number: str
    type: ExerciseType
    prompt_text: str            # the exercise task/question text (grounds evaluation)
    has_grade_button: bool
    audio_url: str | None
    answer_text: str | None
    element_id: str | None


def classify_exercise(
    has_grade_button: bool, has_audio: bool, has_text_answer: bool
) -> ExerciseType:
    """PURE: no grade button -> already auto-checked by the platform."""
    if not has_grade_button:
        return ExerciseType.AUTO_CHECKED
    if has_audio:
        return ExerciseType.AUDIO
    if has_text_answer:
        return ExerciseType.TEXT
    return ExerciseType.MANUAL_UNKNOWN


def _read_text(block, selector: str) -> str:
    # number / prompt are always present on a manual exercise block; read directly
    # (a count()-gate here diverges from the test doubles and yields empty strings).
    return block.locator(selector).inner_text().strip()


def list_exercises(page: Page) -> list[Exercise]:
    section = page.locator(selectors.SECTION_NAV).inner_text().strip()
    blocks = page.locator(selectors.EXERCISE_BLOCK)
    exercises: list[Exercise] = []
    for block in blocks.all():
        element_id = block.get_attribute(selectors.EXERCISE_ID_ATTR)
        number = _read_text(block, selectors.EXERCISE_NUMBER)
        prompt_text = _read_text(block, selectors.EXERCISE_PROMPT)

        audio_loc = block.locator(selectors.EXERCISE_AUDIO)
        has_audio = audio_loc.count() > 0
        audio_url = audio_loc.first.get_attribute("src") if has_audio else None

        answer_loc = block.locator(selectors.EXERCISE_TEXT_ANSWER)
        has_text_answer = answer_loc.count() > 0
        answer_text = answer_loc.inner_text().strip() if has_text_answer else None

        has_grade_button = block.locator(selectors.GRADE_EXERCISE_BTN).count() > 0
        ex_type = classify_exercise(has_grade_button, has_audio, has_text_answer)

        exercises.append(
            Exercise(
                section=section,
                number=number,
                type=ex_type,
                prompt_text=prompt_text,
                has_grade_button=has_grade_button,
                audio_url=audio_url,
                answer_text=answer_text,
                element_id=element_id,
            )
        )
    return exercises
```

- [ ] **Step 4: Run — watch the tests pass.** Run: `pytest tests/scraper/test_lesson.py -q`  Expected: all tests pass.

- [ ] **Step 5: Commit.** Run: `git add edvibe_bot/scraper/lesson.py tests/scraper/test_lesson.py && git commit -m "feat: lesson scraper (Exercise + classify_exercise + list_exercises)"`
```

---

I have enough context. Let me write the assigned module section for `poster.py` and `runner.py`.

```markdown
### Task: Grader poster — score/comment posting + lesson completion (dry-run gated)

**Files:**
- Create: `edvibe_bot/grader/poster.py`
- Create: `edvibe_bot/grader/__init__.py`
- Test: `tests/grader/test_poster.py`
- Create: `tests/grader/__init__.py`

- [ ] **Step 1: Write the failing test.** A `FakePage` records every action so we can assert dry-run touches NOTHING and full-run produces the exact click/fill sequence. `time.sleep` is monkeypatched so pacing never actually blocks.

    ```python
    # tests/grader/test_poster.py
    import edvibe_bot.grader.poster as poster_mod
    from edvibe_bot.grader.poster import grade_exercise, complete_lesson
    from edvibe_bot.evaluator.schema import Evaluation, ExerciseType
    from edvibe_bot.scraper.lesson import Exercise
    from edvibe_bot import selectors


    class FakeLocator:
        def __init__(self, selector, page):
            self._selector = selector
            self._page = page

        def click(self):
            self._page.actions.append(("click", self._selector))

        def fill(self, value):
            self._page.actions.append(("fill", self._selector, value))


    class FakePage:
        def __init__(self):
            self.actions = []

        def locator(self, selector):
            return FakeLocator(selector, self)


    def _settings():
        from edvibe_bot.config import Settings
        return Settings(
            edvibe_login="u",
            edvibe_password="p",
            openai_api_key="k",
            pacing_seconds=0.0,
        )


    def _exercise():
        return Exercise(
            section="Writing",
            number="3",
            type=ExerciseType.TEXT,
            prompt_text="Describe your day.",
            has_grade_button=True,
            audio_url=None,
            answer_text="I woke up early.",
            element_id="ex-3",
        )


    def _evaluation():
        return Evaluation(score=7, comment="Good effort.", rationale="ok", confidence=0.9)


    def test_grade_exercise_dry_run_touches_nothing(monkeypatch):
        monkeypatch.setattr(poster_mod.time, "sleep", lambda s: None)
        page = FakePage()
        grade_exercise(page, _exercise(), _evaluation(), _settings(), dry_run=True)
        assert page.actions == []


    def test_grade_exercise_full_run_exact_sequence(monkeypatch):
        slept = []
        monkeypatch.setattr(poster_mod.time, "sleep", lambda s: slept.append(s))
        page = FakePage()
        grade_exercise(page, _exercise(), _evaluation(), _settings(), dry_run=False)
        assert page.actions == [
            ("click", selectors.GRADE_EXERCISE_BTN),
            ("fill", selectors.SCORE_INPUT, "7"),
            ("fill", selectors.COMMENT_INPUT, "Good effort."),
            ("click", selectors.GRADE_SAVE_BTN),
        ]
        assert slept == [0.0]


    def test_complete_lesson_dry_run_touches_nothing(monkeypatch):
        page = FakePage()
        complete_lesson(page, dry_run=True)
        assert page.actions == []


    def test_complete_lesson_full_run_clicks_complete(monkeypatch):
        page = FakePage()
        complete_lesson(page, dry_run=False)
        assert page.actions == [("click", selectors.COMPLETE_LESSON_BTN)]
    ```

- [ ] **Step 2: Run the test (expect failure).** Run: `pytest tests/grader/test_poster.py -q`  Expected: collection/import error or assertion failures — `edvibe_bot/grader/poster.py` does not exist yet.

- [ ] **Step 3: Implement the poster.**

    ```python
    # edvibe_bot/grader/poster.py
    import time

    from playwright.sync_api import Page

    from edvibe_bot import selectors
    from edvibe_bot.config import Settings
    from edvibe_bot.evaluator.schema import Evaluation
    from edvibe_bot.scraper.lesson import Exercise


    def grade_exercise(
        page: Page,
        exercise: Exercise,
        evaluation: Evaluation,
        settings: Settings,
        dry_run: bool,
    ) -> None:
        """Open the grade modal, enter score + comment, save.

        Independent second safety check: when dry_run is True we touch the
        platform NOT AT ALL. The runner is responsible for never passing
        dry_run=False outside full_auto, but this guard stands on its own.
        """
        if dry_run:
            return
        page.locator(selectors.GRADE_EXERCISE_BTN).click()
        page.locator(selectors.SCORE_INPUT).fill(str(evaluation.score))
        page.locator(selectors.COMMENT_INPUT).fill(evaluation.comment)
        page.locator(selectors.GRADE_SAVE_BTN).click()
        time.sleep(settings.pacing_seconds)


    def complete_lesson(page: Page, dry_run: bool) -> None:
        """Click "Завершить урок" to finish the lesson, unless dry_run."""
        if dry_run:
            return
        page.locator(selectors.COMPLETE_LESSON_BTN).click()
    ```

- [ ] **Step 4: Run the test (expect pass).** Run: `pytest tests/grader/test_poster.py -q`  Expected: all 4 tests pass.

- [ ] **Step 5: Commit.** Run: `git add edvibe_bot/grader/__init__.py edvibe_bot/grader/poster.py tests/grader/__init__.py tests/grader/test_poster.py && git commit -m "feat: grade/complete poster gated by dry_run"`

---

### Task: Runner orchestration — run() with safety rails, durability, completion gate

**Files:**
- Create: `edvibe_bot/runner.py`
- Test: `tests/test_runner.py`

- [ ] **Step 1: Write the failing test with FAKES for every collaborator.** A recording `FakeStore` tracks ledger writes and answers the idempotency queries; auth/dashboard/progress/lesson/poster/audio/text are monkeypatched. We assert all safety invariants: dry_run/review submit nothing, low-confidence → flagged + no completion, parse_failed → flagged even with threshold 0.0, empty answer → flagged, missing element_id → flagged, pre-existing in_progress exercise → skipped+flagged+blocked, lesson sentinel in_progress → not re-completed, zero-manual lesson → not completed, flagged blocks completion, the REAL dry_run flag reaches the poster, SelectorError continues to the next lesson, a screenshot failure is audited not swallowed, and audit.record fires for evaluate+grade+complete.

    ```python
    # tests/test_runner.py
    import pytest

    import edvibe_bot.runner as runner_mod
    from edvibe_bot.runner import run, RunConfig, RunReport
    from edvibe_bot.config import Settings
    from edvibe_bot.evaluator.schema import Evaluation, ExerciseType
    from edvibe_bot.scraper.dashboard import Student
    from edvibe_bot.scraper.progress import Lesson
    from edvibe_bot.scraper.lesson import Exercise
    from edvibe_bot.errors import SelectorError
    from edvibe_bot.state.store import LedgerStatus


    # ---- fakes -------------------------------------------------------------

    class FakeStore:
        def __init__(self):
            self.run_id = "run-fake"
            self.finished = None
            self.recorded = []                 # list of LedgerEntry
            self.lesson_intents = []           # (student_id, lesson_id, run_id)
            self.lesson_completed = []         # (student_id, lesson_id, run_id, dry_run)
            self.audit_rows = []
            self._exercise_status = {}         # (s, l, e) -> status
            self._lesson_status = {}           # (s, l) -> status

        # seams used by AuditLog
        def append_audit(self, run_id, action, target_json, detail_json, ts):
            self.audit_rows.append((run_id, action, target_json, detail_json, ts))

        def create_run(self, mode, scope):
            return self.run_id

        def finish_run(self, run_id, status, counts):
            self.finished = (run_id, status, counts)

        def record_exercise(self, entry):
            self.recorded.append(entry)
            self._exercise_status[
                (entry.student_id, entry.lesson_id, entry.exercise_id)
            ] = entry.status

        def get_exercise_status(self, s, l, e):
            return self._exercise_status.get((s, l, e))

        def is_exercise_done(self, s, l, e):
            return self._exercise_status.get((s, l, e)) in ("graded", "completed")

        def is_exercise_attempted(self, s, l, e):
            return (s, l, e) in self._exercise_status

        def record_lesson_completion_intent(self, s, l, run_id):
            self.lesson_intents.append((s, l, run_id))
            self._lesson_status[(s, l)] = "in_progress"

        def record_lesson_completed(self, s, l, run_id, dry_run):
            self.lesson_completed.append((s, l, run_id, dry_run))
            self._lesson_status[(s, l)] = "completed"

        def get_lesson_status(self, s, l):
            return self._lesson_status.get((s, l))

        def is_lesson_completed(self, s, l):
            return self._lesson_status.get((s, l)) == "completed"

        def is_lesson_completion_attempted(self, s, l):
            return (s, l) in self._lesson_status


    class FakePage:
        def __init__(self):
            self.shots = []

        def screenshot(self, path):
            self.shots.append(path)


    class RecordingPoster:
        def __init__(self):
            self.grade_calls = []       # (element_id, score, dry_run)
            self.complete_calls = []    # dry_run

        def grade_exercise(self, page, exercise, evaluation, settings, dry_run):
            self.grade_calls.append((exercise.element_id, evaluation.score, dry_run))

        def complete_lesson(self, page, dry_run):
            self.complete_calls.append(dry_run)


    def _settings():
        return Settings(
            edvibe_login="u",
            edvibe_password="p",
            openai_api_key="k",
            confidence_threshold=0.6,
            pacing_seconds=0.0,
        )


    def _wire(monkeypatch, *, exercises, poster,
              evaluation=None, transcribe=None, download=b"AUDIO",
              students=None, lessons=None):
        """Monkeypatch all collaborators the runner imports."""
        students = students if students is not None else [Student(id="s1", name="Al")]
        lessons = lessons if lessons is not None else [
            Lesson(id="l1", name="Lesson 1", status="awaiting")
        ]
        evaluation = evaluation or Evaluation(
            score=8, comment="Nice.", rationale="ok", confidence=0.9
        )

        page = FakePage()
        monkeypatch.setattr(runner_mod, "ensure_logged_in", lambda ctx, s: page)
        monkeypatch.setattr(runner_mod, "open_marathon", lambda p, s: None)
        monkeypatch.setattr(runner_mod, "list_students", lambda p: students)
        monkeypatch.setattr(runner_mod, "open_progress", lambda p, st: None)
        monkeypatch.setattr(runner_mod, "list_lessons", lambda p: lessons)
        monkeypatch.setattr(
            runner_mod, "awaiting_lessons",
            lambda ls: [x for x in ls if x.status == "awaiting"],
        )
        monkeypatch.setattr(runner_mod, "open_lesson", lambda p, le: None)
        monkeypatch.setattr(runner_mod, "list_exercises", lambda p: exercises)

        def _dl(ctx, url):
            return download
        monkeypatch.setattr(runner_mod.audio, "download_audio", _dl)

        def _tr(blob, s):
            if transcribe is not None:
                return transcribe(blob, s)
            return "transcript text"
        monkeypatch.setattr(runner_mod.audio, "transcribe", _tr)

        monkeypatch.setattr(runner_mod.text, "evaluate", lambda req, s: evaluation)

        monkeypatch.setattr(runner_mod.poster, "grade_exercise", poster.grade_exercise)
        monkeypatch.setattr(runner_mod.poster, "complete_lesson", poster.complete_lesson)

        # silence the real browser launch
        monkeypatch.setattr(
            runner_mod, "_launch_context",
            lambda headed: _FakeCM(),
        )
        return page


    class _FakeContext:
        pass


    class _FakeCM:
        def __enter__(self):
            return _FakeContext()

        def __exit__(self, *a):
            return False


    def _text_exercise(element_id="ex-1", answer="My answer is long enough."):
        return Exercise(
            section="Writing", number="1", type=ExerciseType.TEXT,
            prompt_text="Write something.", has_grade_button=True,
            audio_url=None, answer_text=answer, element_id=element_id,
        )


    def _audio_exercise(element_id="ex-a", url="http://a/x.mp3"):
        return Exercise(
            section="Speaking", number="2", type=ExerciseType.AUDIO,
            prompt_text="Speak.", has_grade_button=True,
            audio_url=url, answer_text=None, element_id=element_id,
        )


    def _auto_exercise():
        return Exercise(
            section="Grammar", number="9", type=ExerciseType.AUTO_CHECKED,
            prompt_text="Auto.", has_grade_button=False,
            audio_url=None, answer_text="x", element_id="ex-auto",
        )


    def _statuses(recorded):
        return [(e.exercise_id, e.status) for e in recorded]


    # ---- tests -------------------------------------------------------------

    def test_full_auto_grades_and_completes(monkeypatch):
        store = FakeStore()
        poster = RecordingPoster()
        _wire(monkeypatch, exercises=[_text_exercise()], poster=poster)
        report = run(RunConfig(mode="full_auto"), _settings(), store)
        assert report.graded == 1
        assert poster.grade_calls == [("ex-1", 8, False)]
        assert poster.complete_calls == [False]
        assert report.completed_lessons == 1
        # in_progress claim written BEFORE the terminal graded row
        statuses = [e.status for e in store.recorded if e.exercise_id == "ex-1"]
        assert statuses[0] == LedgerStatus.IN_PROGRESS.value
        assert statuses[-1] == LedgerStatus.GRADED.value
        # audit fired for evaluate, grade, complete_lesson
        actions = [r[1] for r in store.audit_rows]
        assert "evaluate" in actions and "grade" in actions
        assert "complete_lesson" in actions


    def test_dry_run_submits_nothing(monkeypatch):
        store = FakeStore()
        poster = RecordingPoster()
        _wire(monkeypatch, exercises=[_text_exercise()], poster=poster)
        report = run(RunConfig(mode="dry_run"), _settings(), store)
        assert poster.grade_calls == []          # never even called the poster
        assert poster.complete_calls == []
        assert report.graded == 0
        assert report.completed_lessons == 0
        assert store.lesson_completed == []


    def test_review_submits_nothing(monkeypatch):
        store = FakeStore()
        poster = RecordingPoster()
        _wire(monkeypatch, exercises=[_text_exercise()], poster=poster)
        report = run(RunConfig(mode="review"), _settings(), store)
        assert poster.grade_calls == []
        assert poster.complete_calls == []
        assert report.completed_lessons == 0


    def test_low_confidence_flagged_not_graded_and_no_completion(monkeypatch):
        store = FakeStore()
        poster = RecordingPoster()
        low = Evaluation(score=5, comment="meh", rationale="ok", confidence=0.2)
        _wire(monkeypatch, exercises=[_text_exercise()], poster=poster, evaluation=low)
        report = run(RunConfig(mode="full_auto"), _settings(), store)
        assert poster.grade_calls == []
        assert report.graded == 0
        assert report.flagged == 1
        assert poster.complete_calls == []
        assert ("ex-1", LedgerStatus.FLAGGED.value) in _statuses(store.recorded)


    def test_parse_failed_flagged_even_with_threshold_zero(monkeypatch):
        store = FakeStore()
        poster = RecordingPoster()
        pf = Evaluation(score=0, comment="", rationale="parse_failed", confidence=0.0)
        _wire(monkeypatch, exercises=[_text_exercise()], poster=poster, evaluation=pf)
        cfg = RunConfig(mode="full_auto", confidence_threshold=0.0)
        report = run(cfg, _settings(), store)
        assert poster.grade_calls == []
        assert report.graded == 0
        assert report.flagged == 1
        assert poster.complete_calls == []


    def test_empty_answer_flagged_not_graded(monkeypatch):
        store = FakeStore()
        poster = RecordingPoster()
        _wire(
            monkeypatch,
            exercises=[_text_exercise(answer="   ")],
            poster=poster,
        )
        report = run(RunConfig(mode="full_auto"), _settings(), store)
        assert poster.grade_calls == []
        assert report.flagged == 1
        assert report.graded == 0


    def test_missing_element_id_flagged_not_graded(monkeypatch):
        store = FakeStore()
        poster = RecordingPoster()
        ex = _text_exercise()
        ex.element_id = None
        _wire(monkeypatch, exercises=[ex], poster=poster)
        report = run(RunConfig(mode="full_auto"), _settings(), store)
        assert poster.grade_calls == []
        assert report.flagged == 1
        assert report.graded == 0
        assert poster.complete_calls == []
        assert any(
            e.status == LedgerStatus.FLAGGED.value and e.proposed_comment == "no_stable_id"
            for e in store.recorded
        )


    def test_preexisting_in_progress_exercise_skipped_flagged_blocked(monkeypatch):
        store = FakeStore()
        poster = RecordingPoster()
        store._exercise_status[("s1", "l1", "ex-1")] = "in_progress"
        _wire(monkeypatch, exercises=[_text_exercise()], poster=poster)
        report = run(RunConfig(mode="full_auto"), _settings(), store)
        assert poster.grade_calls == []
        assert report.flagged == 1
        assert report.graded == 0
        assert poster.complete_calls == []      # blocked → no completion


    def test_lesson_sentinel_in_progress_not_recompleted(monkeypatch):
        store = FakeStore()
        poster = RecordingPoster()
        store._lesson_status[("s1", "l1")] = "in_progress"
        _wire(monkeypatch, exercises=[_text_exercise()], poster=poster)
        report = run(RunConfig(mode="full_auto"), _settings(), store)
        assert poster.grade_calls == []          # lesson skipped entirely
        assert poster.complete_calls == []
        assert report.flagged == 1               # lesson flagged for human verify


    def test_already_completed_lesson_skipped(monkeypatch):
        store = FakeStore()
        poster = RecordingPoster()
        store._lesson_status[("s1", "l1")] = "completed"
        _wire(monkeypatch, exercises=[_text_exercise()], poster=poster)
        report = run(RunConfig(mode="full_auto"), _settings(), store)
        assert poster.grade_calls == []
        assert poster.complete_calls == []


    def test_zero_manual_exercises_lesson_not_completed(monkeypatch):
        store = FakeStore()
        poster = RecordingPoster()
        _wire(monkeypatch, exercises=[_auto_exercise()], poster=poster)
        report = run(RunConfig(mode="full_auto"), _settings(), store)
        assert poster.grade_calls == []
        assert poster.complete_calls == []       # NEVER complete a zero-manual lesson
        assert report.completed_lessons == 0


    def test_flagged_exercise_blocks_completion(monkeypatch):
        store = FakeStore()
        poster = RecordingPoster()
        good = _text_exercise(element_id="ex-good")
        bad = _text_exercise(element_id="ex-bad", answer="  ")  # empty → flagged
        _wire(monkeypatch, exercises=[good, bad], poster=poster)
        report = run(RunConfig(mode="full_auto"), _settings(), store)
        assert ("ex-good", 8, False) in poster.grade_calls   # one graded
        assert report.graded == 1
        assert report.flagged == 1
        assert poster.complete_calls == []                   # blocked by flag


    def test_audio_download_none_flagged(monkeypatch):
        store = FakeStore()
        poster = RecordingPoster()
        _wire(
            monkeypatch, exercises=[_audio_exercise()], poster=poster, download=None,
        )
        report = run(RunConfig(mode="full_auto"), _settings(), store)
        assert poster.grade_calls == []
        assert report.flagged == 1
        assert poster.complete_calls == []


    def test_transcription_failure_flagged(monkeypatch):
        store = FakeStore()
        poster = RecordingPoster()

        def _boom(blob, s):
            raise RuntimeError("both models failed")

        _wire(
            monkeypatch, exercises=[_audio_exercise()], poster=poster,
            transcribe=_boom,
        )
        report = run(RunConfig(mode="full_auto"), _settings(), store)
        assert poster.grade_calls == []
        assert report.flagged == 1


    def test_selector_error_screenshots_and_continues(monkeypatch):
        store = FakeStore()
        poster = RecordingPoster()
        lessons = [
            Lesson(id="l1", name="L1", status="awaiting"),
            Lesson(id="l2", name="L2", status="awaiting"),
        ]
        page = _wire(
            monkeypatch, exercises=[_text_exercise()], poster=poster, lessons=lessons,
        )

        calls = {"n": 0}

        def _le(p):
            calls["n"] += 1
            if calls["n"] == 1:
                raise SelectorError("boom on first lesson")
            return [_text_exercise(element_id="ex-2")]

        monkeypatch.setattr(runner_mod, "list_exercises", _le)
        report = run(RunConfig(mode="full_auto"), _settings(), store)
        assert report.errors == 1
        assert page.shots and "error-run-fake-s1-l1" in page.shots[0]
        # the SECOND lesson was still processed → graded
        assert ("ex-2", 8, False) in poster.grade_calls
        assert report.graded == 1


    def test_screenshot_failure_is_audited_not_swallowed(monkeypatch):
        store = FakeStore()
        poster = RecordingPoster()

        class ExplodingPage(FakePage):
            def screenshot(self, path):
                raise RuntimeError("screenshot device busy")

        bad_page = ExplodingPage()
        monkeypatch.setattr(runner_mod, "ensure_logged_in", lambda ctx, s: bad_page)
        _wire(monkeypatch, exercises=[_text_exercise()], poster=poster)
        # re-point ensure_logged_in after _wire (which overrode it)
        monkeypatch.setattr(runner_mod, "ensure_logged_in", lambda ctx, s: bad_page)

        def _le(p):
            raise SelectorError("boom")

        monkeypatch.setattr(runner_mod, "list_exercises", _le)
        report = run(RunConfig(mode="full_auto"), _settings(), store)
        assert report.errors == 1
        # the screenshot failure was audited (not silently swallowed)
        actions = [r[1] for r in store.audit_rows]
        assert "screenshot_failed" in actions


    def test_max_students_and_max_lessons_caps(monkeypatch):
        store = FakeStore()
        poster = RecordingPoster()
        students = [Student(id="s1", name="A"), Student(id="s2", name="B")]
        lessons = [
            Lesson(id="l1", name="L1", status="awaiting"),
            Lesson(id="l2", name="L2", status="awaiting"),
        ]
        _wire(
            monkeypatch, exercises=[_text_exercise()], poster=poster,
            students=students, lessons=lessons,
        )
        cfg = RunConfig(mode="dry_run", max_students=1, max_lessons=1)
        run(cfg, _settings(), store)
        # only one student × one lesson processed → one evaluate audit row
        evals = [r for r in store.audit_rows if r[1] == "evaluate"]
        assert len(evals) == 1


    def test_student_filter_restricts(monkeypatch):
        store = FakeStore()
        poster = RecordingPoster()
        students = [Student(id="s1", name="A"), Student(id="s2", name="B")]
        _wire(
            monkeypatch, exercises=[_text_exercise()], poster=poster, students=students,
        )
        cfg = RunConfig(mode="dry_run", student_filter=["s2"])
        run(cfg, _settings(), store)
        evals = [r for r in store.audit_rows if r[1] == "evaluate"]
        assert len(evals) == 1
    ```

- [ ] **Step 2: Run the test (expect failure).** Run: `pytest tests/test_runner.py -q`  Expected: import error — `edvibe_bot/runner.py` does not exist yet.

- [ ] **Step 3: Implement the runner.** Collaborators are imported by NAME into the runner module so tests can monkeypatch `runner_mod.<name>`; `audio`, `text`, and `poster` are imported as MODULES so tests patch `runner_mod.audio.transcribe`, etc. The per-lesson `except` body does ONLY: screenshot (and audit if the screenshot itself fails) → record lesson error → errors += 1 → audit → continue. The poster always receives the REAL `dry_run` flag.

    ```python
    # edvibe_bot/runner.py
    from contextlib import contextmanager
    from dataclasses import dataclass
    from typing import Callable, Optional

    from playwright.sync_api import sync_playwright

    from edvibe_bot import selectors  # noqa: F401  (kept for parity with sibling modules)
    from edvibe_bot.errors import SelectorError
    from edvibe_bot.config import Settings
    from edvibe_bot.audit.log import AuditLog, get_logger
    from edvibe_bot.state.store import Store, LedgerEntry, LedgerStatus
    from edvibe_bot.evaluator.schema import EvalRequest, ExerciseType
    from edvibe_bot.auth.login import ensure_logged_in
    from edvibe_bot.scraper.dashboard import open_marathon, list_students, Student
    from edvibe_bot.scraper.progress import (
        open_progress,
        list_lessons,
        awaiting_lessons,
        open_lesson,
    )
    from edvibe_bot.scraper.lesson import list_exercises, Exercise
    from edvibe_bot.evaluator import audio, text
    from edvibe_bot.grader import poster

    log = get_logger("edvibe_bot.runner")

    _MANUAL_TYPES = {
        ExerciseType.AUDIO,
        ExerciseType.TEXT,
        ExerciseType.MANUAL_UNKNOWN,
    }


    @dataclass
    class RunConfig:
        mode: str
        student_filter: "list[str] | None" = None
        max_students: "int | None" = None
        max_lessons: "int | None" = None
        headed: bool = False
        confidence_threshold: float = 0.6


    @dataclass
    class RunReport:
        run_id: str
        graded: int
        skipped: int
        flagged: int
        errors: int
        completed_lessons: int


    EventCallback = Callable[[dict], None]


    @contextmanager
    def _launch_context(headed: bool):
        """Yield a (playwright_cm, browser_context). Patched out in unit tests."""
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=not headed)
            context = browser.new_context()
            try:
                yield context
            finally:
                context.close()
                browser.close()


    def _emit(on_event: "Optional[EventCallback]", payload: dict) -> None:
        if on_event is not None:
            on_event(payload)


    def _entry(
        *,
        student,
        lesson,
        exercise_id,
        ex,
        run_id,
        status,
        score=None,
        comment=None,
        confidence=None,
        submitted=False,
        dry_run=False,
    ) -> LedgerEntry:
        return LedgerEntry(
            student_id=student.id,
            lesson_id=lesson.id,
            exercise_id=exercise_id,
            student_name=student.name,
            lesson_name=lesson.name,
            exercise_no=ex.number,
            type=ex.type.value,
            proposed_score=score,
            proposed_comment=comment,
            confidence=confidence,
            submitted=submitted,
            dry_run=dry_run,
            run_id=run_id,
            status=status,
        )


    def run(
        config: RunConfig,
        settings: Settings,
        store: Store,
        on_event: "Optional[EventCallback]" = None,
    ) -> RunReport:
        audit = AuditLog(store, settings.audit_jsonl_path)
        scope = {
            "student_filter": config.student_filter,
            "max_students": config.max_students,
            "max_lessons": config.max_lessons,
        }
        run_id = store.create_run(config.mode, scope)

        # ONLY full_auto submits; both dry_run and review never touch the platform.
        submit_allowed = config.mode == "full_auto"
        dry_run = config.mode != "full_auto"

        graded = skipped = flagged = errors = completed_lessons = 0

        with _launch_context(config.headed) as context:
            page = ensure_logged_in(context, settings)
            open_marathon(page, settings)

            students = list_students(page)
            if config.student_filter is not None:
                wanted = set(config.student_filter)
                students = [s for s in students if s.id in wanted]
            if config.max_students is not None:
                students = students[: config.max_students]

            for student in students:
                _emit(on_event, {"event": "student", "student_id": student.id})
                open_progress(page, student)
                lessons = awaiting_lessons(list_lessons(page))
                if config.max_lessons is not None:
                    lessons = lessons[: config.max_lessons]

                for lesson in lessons:
                    target = {
                        "student_id": student.id,
                        "lesson_id": lesson.id,
                    }
                    if store.is_lesson_completed(student.id, lesson.id):
                        skipped += 1
                        _emit(on_event, {"event": "lesson_skip", **target})
                        continue
                    if store.get_lesson_status(student.id, lesson.id) in (
                        "in_progress",
                        "error",
                    ):
                        flagged += 1
                        audit.record(
                            run_id,
                            "flag_lesson",
                            target,
                            {"reason": "sentinel_in_progress_or_error"},
                        )
                        _emit(on_event, {"event": "lesson_flag", **target})
                        continue

                    try:
                        open_lesson(page, lesson)
                        exercises = list_exercises(page)
                        manual = [
                            e
                            for e in exercises
                            if e.has_grade_button and e.type in _MANUAL_TYPES
                        ]
                        manual_count = len(manual)
                        graded_this_run = 0
                        blocked = False

                        for ex in manual:
                            ex_target = {
                                "student_id": student.id,
                                "lesson_id": lesson.id,
                                "exercise_no": ex.number,
                            }

                            # Independent guard: no stable id → never grade on a guess.
                            if not ex.element_id:
                                store.record_exercise(
                                    _entry(
                                        student=student,
                                        lesson=lesson,
                                        exercise_id=f"__noid__{ex.number}",
                                        ex=ex,
                                        run_id=run_id,
                                        status=LedgerStatus.FLAGGED.value,
                                        comment="no_stable_id",
                                        submitted=False,
                                        dry_run=dry_run,
                                    )
                                )
                                blocked = True
                                flagged += 1
                                audit.record(
                                    run_id, "flag", ex_target, {"reason": "no_stable_id"}
                                )
                                continue

                            exercise_id = ex.element_id

                            if store.is_exercise_done(
                                student.id, lesson.id, exercise_id
                            ):
                                graded_this_run += 1
                                continue

                            if (
                                store.get_exercise_status(
                                    student.id, lesson.id, exercise_id
                                )
                                == "in_progress"
                            ):
                                store.record_exercise(
                                    _entry(
                                        student=student,
                                        lesson=lesson,
                                        exercise_id=exercise_id,
                                        ex=ex,
                                        run_id=run_id,
                                        status=LedgerStatus.FLAGGED.value,
                                        comment="prior_in_progress",
                                        submitted=False,
                                        dry_run=dry_run,
                                    )
                                )
                                blocked = True
                                flagged += 1
                                audit.record(
                                    run_id,
                                    "flag",
                                    ex_target,
                                    {"reason": "prior_in_progress"},
                                )
                                continue

                            # ---- gather the answer (fail-safe on any failure) ----
                            answer = None
                            fail_reason = None
                            try:
                                if ex.type == ExerciseType.AUDIO:
                                    blob = audio.download_audio(context, ex.audio_url)
                                    if blob is None:
                                        fail_reason = "audio_download_failed"
                                    else:
                                        answer = audio.transcribe(blob, settings)
                                else:
                                    answer = ex.answer_text
                            except Exception:  # noqa: BLE001 - fail-safe to FLAG
                                fail_reason = "gather_failed"

                            if fail_reason is None and (
                                answer is None or not answer.strip()
                            ):
                                fail_reason = "empty_answer"

                            if fail_reason is not None:
                                store.record_exercise(
                                    _entry(
                                        student=student,
                                        lesson=lesson,
                                        exercise_id=exercise_id,
                                        ex=ex,
                                        run_id=run_id,
                                        status=LedgerStatus.FLAGGED.value,
                                        comment=fail_reason,
                                        submitted=False,
                                        dry_run=dry_run,
                                    )
                                )
                                blocked = True
                                flagged += 1
                                audit.record(
                                    run_id, "flag", ex_target, {"reason": fail_reason}
                                )
                                continue

                            # ---- evaluate ----
                            evaluation = text.evaluate(
                                EvalRequest(
                                    exercise_type=ex.type,
                                    section=ex.section,
                                    prompt_text=ex.prompt_text,
                                    student_answer=answer,
                                ),
                                settings,
                            )
                            audit.record(
                                run_id,
                                "evaluate",
                                ex_target,
                                {
                                    "dry_run": dry_run,
                                    "score": evaluation.score,
                                    "confidence": evaluation.confidence,
                                    "rationale": evaluation.rationale,
                                },
                            )

                            # Threshold-INDEPENDENT parse/zero-confidence guard.
                            if (
                                evaluation.rationale == "parse_failed"
                                or evaluation.confidence <= 0
                            ):
                                store.record_exercise(
                                    _entry(
                                        student=student,
                                        lesson=lesson,
                                        exercise_id=exercise_id,
                                        ex=ex,
                                        run_id=run_id,
                                        status=LedgerStatus.FLAGGED.value,
                                        score=evaluation.score,
                                        comment=evaluation.comment,
                                        confidence=evaluation.confidence,
                                        submitted=False,
                                        dry_run=dry_run,
                                    )
                                )
                                blocked = True
                                flagged += 1
                                audit.record(
                                    run_id, "flag", ex_target, {"reason": "parse_failed"}
                                )
                                continue

                            # Not allowed to submit, or below confidence threshold.
                            if (not submit_allowed) or (
                                evaluation.confidence < config.confidence_threshold
                            ):
                                low_conf = (
                                    evaluation.confidence < config.confidence_threshold
                                )
                                status = (
                                    LedgerStatus.FLAGGED.value
                                    if low_conf
                                    else LedgerStatus.SKIPPED.value
                                )
                                store.record_exercise(
                                    _entry(
                                        student=student,
                                        lesson=lesson,
                                        exercise_id=exercise_id,
                                        ex=ex,
                                        run_id=run_id,
                                        status=status,
                                        score=evaluation.score,
                                        comment=evaluation.comment,
                                        confidence=evaluation.confidence,
                                        submitted=False,
                                        dry_run=dry_run,
                                    )
                                )
                                audit.record(
                                    run_id,
                                    "flag" if low_conf else "skip",
                                    ex_target,
                                    {
                                        "dry_run": dry_run,
                                        "low_confidence": low_conf,
                                        "confidence": evaluation.confidence,
                                    },
                                )
                                if low_conf:
                                    blocked = True
                                    flagged += 1
                                else:
                                    skipped += 1
                                continue

                            # ---- DURABILITY: claim in_progress BEFORE the click ----
                            store.record_exercise(
                                _entry(
                                    student=student,
                                    lesson=lesson,
                                    exercise_id=exercise_id,
                                    ex=ex,
                                    run_id=run_id,
                                    status=LedgerStatus.IN_PROGRESS.value,
                                    score=evaluation.score,
                                    comment=evaluation.comment,
                                    confidence=evaluation.confidence,
                                    submitted=False,
                                    dry_run=dry_run,
                                )
                            )
                            poster.grade_exercise(
                                page, ex, evaluation, settings, dry_run=dry_run
                            )
                            store.record_exercise(
                                _entry(
                                    student=student,
                                    lesson=lesson,
                                    exercise_id=exercise_id,
                                    ex=ex,
                                    run_id=run_id,
                                    status=LedgerStatus.GRADED.value,
                                    score=evaluation.score,
                                    comment=evaluation.comment,
                                    confidence=evaluation.confidence,
                                    submitted=True,
                                    dry_run=dry_run,
                                )
                            )
                            graded += 1
                            graded_this_run += 1
                            audit.record(
                                run_id,
                                "grade",
                                ex_target,
                                {"dry_run": dry_run, "score": evaluation.score},
                            )
                            _emit(on_event, {"event": "graded", **ex_target})

                        # ---- COMPLETION GATE ----
                        if (
                            submit_allowed
                            and manual_count > 0
                            and not blocked
                            and graded_this_run >= 1
                            and store.get_lesson_status(student.id, lesson.id)
                            not in ("in_progress", "error")
                        ):
                            store.record_lesson_completion_intent(
                                student.id, lesson.id, run_id
                            )
                            poster.complete_lesson(page, dry_run=dry_run)
                            store.record_lesson_completed(
                                student.id, lesson.id, run_id, dry_run
                            )
                            completed_lessons += 1
                            audit.record(
                                run_id,
                                "complete_lesson",
                                target,
                                {"dry_run": dry_run},
                            )
                            _emit(on_event, {"event": "lesson_complete", **target})

                    except Exception:  # noqa: BLE001 - per-lesson boundary (covers SelectorError)
                        try:
                            page.screenshot(
                                path=f"reports/error-{run_id}-{student.id}-{lesson.id}.png"
                            )
                        except Exception as shot_err:  # noqa: BLE001
                            log.error("screenshot failed: %s", shot_err)
                            audit.record(
                                run_id,
                                "screenshot_failed",
                                target,
                                {"error": str(shot_err)},
                            )
                        store.record_exercise(
                            LedgerEntry(
                                student_id=student.id,
                                lesson_id=lesson.id,
                                exercise_id="__lesson__",
                                student_name=student.name,
                                lesson_name=lesson.name,
                                exercise_no="",
                                type="",
                                proposed_score=None,
                                proposed_comment=None,
                                confidence=None,
                                submitted=False,
                                dry_run=dry_run,
                                run_id=run_id,
                                status=LedgerStatus.ERROR.value,
                            )
                        )
                        errors += 1
                        audit.record(run_id, "lesson_error", target, {})
                        continue

        counts = {
            "graded": graded,
            "skipped": skipped,
            "flagged": flagged,
            "errors": errors,
            "completed_lessons": completed_lessons,
        }
        store.finish_run(run_id, "done", counts)
        return RunReport(
            run_id=run_id,
            graded=graded,
            skipped=skipped,
            flagged=flagged,
            errors=errors,
            completed_lessons=completed_lessons,
        )
    ```

- [ ] **Step 4: Run the test (expect pass).** Run: `pytest tests/test_runner.py -q`  Expected: all tests pass — dry_run/review submit nothing, low-confidence/parse_failed/empty/no-id flag without grading, pre-existing in_progress skips+flags+blocks, sentinel in_progress is not re-completed, zero-manual lessons never complete, a flagged exercise blocks completion, the real dry_run flag reaches the poster, a `SelectorError` screenshots + continues to the next lesson, a failing screenshot is audited not swallowed, and audit fires for evaluate/grade/complete.

- [ ] **Step 5: Run the broader suite.** Run: `pytest -q`  Expected: the full suite is green (runner + poster integrate with the real config/schema/store/audit modules).

- [ ] **Step 6: Commit.** Run: `git add edvibe_bot/runner.py tests/test_runner.py && git commit -m "feat: runner orchestration with safety rails, durability, and completion gate"`

> **Live verification (deferred to "Final integration & self-review"):** the real `_launch_context` (Playwright `sync_playwright`) and the live collaborators are exercised only by the controlled single-student **dry-run** (`mode="dry_run"`, `headed=True`, `--max-students 1`), confirming zero submissions and a populated audit trail before any `full_auto` canary.
```

---

I have enough context. The contract fully specifies the interface I need. Let me write the `main.py` section.

### Task: CLI entrypoint — `build_run_config` (pure, TDD) + `main`

**Files:**
- Create: `edvibe_bot/main.py`
- Test: `tests/test_main.py`

- [ ] **Step 1: Write the failing test for `build_run_config` (pure helper).** This test never launches a browser or touches OpenAI/SQLite — it only exercises argparse parsing, defaults, repeatable `--student`, integer caps, the `--headed` boolean, `--mode` passthrough, `--confidence` default/override, and threshold validation (`0 < t <= 1`).

```python
import pytest

from edvibe_bot.main import build_run_config
from edvibe_bot.runner import RunConfig


def test_defaults_minimal_args():
    cfg = build_run_config(["--mode", "dry_run"])
    assert isinstance(cfg, RunConfig)
    assert cfg.mode == "dry_run"
    assert cfg.student_filter is None
    assert cfg.max_students is None
    assert cfg.max_lessons is None
    assert cfg.headed is False
    assert cfg.confidence_threshold == 0.6


def test_mode_passthrough_full_auto():
    cfg = build_run_config(["--mode", "full_auto"])
    assert cfg.mode == "full_auto"


def test_mode_passthrough_review():
    cfg = build_run_config(["--mode", "review"])
    assert cfg.mode == "review"


def test_invalid_mode_is_systemexit():
    with pytest.raises(SystemExit):
        build_run_config(["--mode", "bogus"])


def test_repeated_student_becomes_list():
    cfg = build_run_config(
        ["--mode", "dry_run", "--student", "Анель", "--student", "Bob"]
    )
    assert cfg.student_filter == ["Анель", "Bob"]


def test_single_student_is_one_element_list():
    cfg = build_run_config(["--mode", "dry_run", "--student", "Анель"])
    assert cfg.student_filter == ["Анель"]


def test_caps_parse_as_ints():
    cfg = build_run_config(
        ["--mode", "dry_run", "--max-students", "3", "--max-lessons", "1"]
    )
    assert cfg.max_students == 3
    assert isinstance(cfg.max_students, int)
    assert cfg.max_lessons == 1
    assert isinstance(cfg.max_lessons, int)


def test_non_integer_cap_is_systemexit():
    with pytest.raises(SystemExit):
        build_run_config(["--mode", "dry_run", "--max-students", "lots"])


def test_headed_flag_sets_true():
    cfg = build_run_config(["--mode", "dry_run", "--headed"])
    assert cfg.headed is True


def test_confidence_omitted_uses_passed_default():
    cfg = build_run_config(["--mode", "dry_run"], default_confidence=0.42)
    assert cfg.confidence_threshold == 0.42


def test_confidence_override_beats_default():
    cfg = build_run_config(
        ["--mode", "dry_run", "--confidence", "0.9"], default_confidence=0.42
    )
    assert cfg.confidence_threshold == 0.9


def test_confidence_zero_is_systemexit():
    with pytest.raises(SystemExit):
        build_run_config(["--mode", "dry_run", "--confidence", "0"])


def test_confidence_above_one_is_systemexit():
    with pytest.raises(SystemExit):
        build_run_config(["--mode", "dry_run", "--confidence", "1.5"])


def test_confidence_exactly_one_is_allowed():
    cfg = build_run_config(["--mode", "dry_run", "--confidence", "1.0"])
    assert cfg.confidence_threshold == 1.0


def test_default_confidence_out_of_range_is_systemexit():
    # A bad resolved default (e.g. misconfigured Settings) must also be rejected.
    with pytest.raises(SystemExit):
        build_run_config(["--mode", "dry_run"], default_confidence=0.0)
```

- [ ] **Step 2: Run the test, watch it fail.** Run: `pytest tests/test_main.py -q`  Expected: collection/import error (`ModuleNotFoundError: No module named 'edvibe_bot.main'` or `ImportError: cannot import name 'build_run_config'`) — the test fails because `main.py` does not exist yet.

- [ ] **Step 3: Implement `edvibe_bot/main.py`.** `build_run_config` is pure (argparse over an `argv` list, no I/O). `--mode` is `required` with `choices` and help text stating that only `full_auto` submits and that `dry_run`/`review` never touch the platform. `--confidence` defaults to `None` so we can tell "omitted" from "supplied" and fall back to `default_confidence`. The resolved threshold is validated `0 < t <= 1` via `parser.error(...)` so an out-of-range value (from CLI **or** a misconfigured default) raises `SystemExit`. `main()` wires `load_settings()` → `Store(...).init_schema()` → `build_run_config(sys.argv[1:], settings.confidence_threshold)` → `runner.run(...)` with an `on_event` callback that prints structured progress, and prints the final `RunReport`. `python -m edvibe_bot.main` works via the `__main__` guard.

```python
"""CLI entrypoint for the Edvibe grader bot core.

Usage:
    python -m edvibe_bot.main --mode dry_run --student "Анель" --headed
"""

from __future__ import annotations

import argparse
import json
import sys

from edvibe_bot.config import load_settings
from edvibe_bot.runner import RunConfig, run
from edvibe_bot.state.store import Store


def build_run_config(argv: list[str], default_confidence: float = 0.6) -> RunConfig:
    """Parse CLI args into a RunConfig. Pure: no browser, no network, no DB.

    - ``--mode`` is required; only ``full_auto`` submits. ``dry_run``/``review``
      never touch the platform.
    - ``--student`` is repeatable and accumulates into a list (None if absent).
    - ``--max-students`` / ``--max-lessons`` parse as ints (None if absent).
    - ``--headed`` is a boolean flag.
    - ``--confidence`` overrides ``default_confidence`` when supplied; the
      resolved threshold is validated ``0 < t <= 1`` (else argparse error ->
      SystemExit), so a CLI value *or* a misconfigured default cannot slip
      through.
    """
    parser = argparse.ArgumentParser(
        prog="edvibe_bot",
        description="Grade Pre-IELTS 'Awaiting' homework for Mr. Adilet's students.",
    )
    parser.add_argument(
        "--mode",
        required=True,
        choices=["dry_run", "full_auto", "review"],
        help=(
            "Run mode. ONLY 'full_auto' submits scores / completes lessons. "
            "'dry_run' and 'review' never touch the platform (review records "
            "proposals to the ledger only)."
        ),
    )
    parser.add_argument(
        "--student",
        action="append",
        default=None,
        metavar="NAME",
        help="Restrict to this student (repeatable). Omit for all students.",
    )
    parser.add_argument(
        "--max-students",
        type=int,
        default=None,
        metavar="N",
        help="Cap the number of students processed (blast-radius limit).",
    )
    parser.add_argument(
        "--max-lessons",
        type=int,
        default=None,
        metavar="N",
        help="Cap the number of lessons processed per student.",
    )
    parser.add_argument(
        "--headed",
        action="store_true",
        help="Run the browser headed (visible) instead of headless.",
    )
    parser.add_argument(
        "--confidence",
        type=float,
        default=None,
        metavar="T",
        help=(
            "Confidence threshold in (0, 1]; evaluations below it are flagged, "
            "never submitted. Overrides the configured default when supplied."
        ),
    )

    args = parser.parse_args(argv)

    threshold = args.confidence if args.confidence is not None else default_confidence
    if not (0 < threshold <= 1):
        parser.error(
            f"confidence threshold must satisfy 0 < t <= 1, got {threshold!r}"
        )

    return RunConfig(
        mode=args.mode,
        student_filter=args.student,
        max_students=args.max_students,
        max_lessons=args.max_lessons,
        headed=args.headed,
        confidence_threshold=threshold,
    )


def _print_event(event: dict) -> None:
    """on_event callback: emit one JSON line per run event to stdout."""
    print(json.dumps(event, ensure_ascii=False), flush=True)


def main(argv: list[str] | None = None) -> int:
    """Wire settings -> store -> config -> run; print the final report."""
    argv = sys.argv[1:] if argv is None else argv
    settings = load_settings()
    store = Store(settings.db_path)
    store.init_schema()
    config = build_run_config(argv, settings.confidence_threshold)
    report = run(config, settings, store, on_event=_print_event)
    print(
        json.dumps(
            {
                "event": "run_report",
                "run_id": report.run_id,
                "graded": report.graded,
                "skipped": report.skipped,
                "flagged": report.flagged,
                "errors": report.errors,
                "completed_lessons": report.completed_lessons,
            },
            ensure_ascii=False,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run the test, watch it pass.** Run: `pytest tests/test_main.py -q`  Expected: all tests pass (defaults, repeatable `--student` → list, int caps, `--headed`, mode passthrough, confidence default/override, and every `SystemExit` validation case — including the bad-default case).

- [ ] **Step 5: Verify the CLI help wiring without launching a run.** Run: `python -m edvibe_bot.main --help`  Expected: exits 0 and prints usage; the `--mode` help text states that only `full_auto` submits and that `dry_run`/`review` never touch the platform. (A full live `python -m edvibe_bot.main --mode dry_run --student ... --headed` invocation is exercised in "Final integration & self-review".)

- [ ] **Step 6: Commit.** Run: `git add edvibe_bot/main.py tests/test_main.py && git commit -m "feat: add CLI entrypoint with pure build_run_config and run wiring"`

---

## Phase 0 — Live exploration (read-only; HUMAN-GATED — requires a Playwright MCP)

> **This is a human-gated checkpoint, NOT an autonomous task.** It is the one task that breaks the "execute top-to-bottom" rule: an agent that reaches Phase 0 without a connected Playwright MCP and live `.env` credentials must STOP and hand off to a human rather than fabricate selectors. Every other task (Bootstrap → CLI) is fully buildable and unit-testable offline against the best-guess selectors; Phase 0 only CONFIRMS those values against the live SPA, and the "Final integration" offline gate refuses any live run while `# CONFIRM` markers remain.
>
> Read-only. CONFIRMS the selector VALUES and the audio mechanism captured as best-guess defaults by the Bootstrap task. **No grading, no "Завершить урок", no clicking grade buttons.** De-risks the unverified-selector problem and the prior accidental-grading incident.

### Task: Confirm selectors + audio strategy (read-only)

**Files:**
- Modify: `edvibe_bot/selectors.py` (update VALUES in place; do NOT add/rename constants)
- Create: `docs/superpowers/specs/phase0-exploration-notes.md`

- [ ] **Step 1:** With the Playwright MCP, log in using `.env` and walk read-only: `/cabinet/school/classes` → "Марафоны" → "Pre-IELTS" → "Фильтр" → Curator "Mister Adilet" → Apply. Screenshot each step.
- [ ] **Step 2:** Open ONE student's "Прогресс ученика" modal (read-only). Confirm the real selectors for the lessons list, the "Awaiting" marker (`LESSON_STATUS_AWAITING`), the per-row id attribute (`LESSON_ID_ATTR`), and the open-lesson control. Update those VALUES in `selectors.py`.
- [ ] **Step 3:** Open ONE awaiting lesson (read-only — do NOT grade). Confirm selectors for the section heading (`SECTION_NAV`), exercise blocks (`EXERCISE_BLOCK`), the STABLE per-exercise id attribute (`EXERCISE_ID_ATTR` — critical: this becomes the ledger key, so it must be stable across runs), the exercise prompt (`EXERCISE_PROMPT`), audio (`EXERCISE_AUDIO`), text answer (`EXERCISE_TEXT_ANSWER`), the "Оценить упражнение" button, the grade modal (`SCORE_INPUT`, `COMMENT_INPUT`, `GRADE_SAVE_BTN`), and "Завершить урок". Update `selectors.py`.
- [ ] **Step 4:** Inspect a "Голос записан" exercise. Capture the actual audio fetch request (URL pattern + any auth headers) and RECORD it in `phase0-exploration-notes.md`. State EXPLICITLY one of: (a) `download_audio`'s `context.request.get(audio_url)` path works as-is, (b) audio.py needs a specific change (describe it), or (c) audio is not fetchable → `download_audio` returns None and the runner FLAGS audio exercises. Do not leave "fetchable" as an unhandled branch.
- [ ] **Step 5:** Write `phase0-exploration-notes.md` (confirmed flow, audio decision, deviations). Commit: `git commit -am "chore: confirm edvibe selectors + audio strategy (phase 0)"`.

---

---

## Final integration & self-review

### Task: End-to-end single-student dry-run (HUMAN RUNBOOK — gated on Phase 0)

> **Human runbook, NOT an autonomous task.** Steps 2–5 require live `.env` credentials, a confirmed Phase 0, and a human reviewer between the dry-run and the canary. An agent runs only Step 1 (the offline gate) and then HANDS OFF — it must not "complete" the live steps by reading prose.

**Files:**
- Create: `tests/test_runner_dryrun.py` (offline readiness gate — asserts the build is ready; NOT a live test)

- [ ] **Step 1 — Offline readiness gate (agent-runnable).** Write `tests/test_runner_dryrun.py`:
    ```python
    import pathlib
    from edvibe_bot.main import build_run_config

    def test_build_run_config_dry_run_default():
        cfg = build_run_config(["--mode", "dry_run", "--max-students", "1"])
        assert cfg.mode == "dry_run" and cfg.max_students == 1

    def test_no_unconfirmed_selectors_remain():
        # GATE: Phase 0 must replace every best-guess value before any live run.
        # EXPECTED TO FAIL until Phase 0 lands — that is the safety gate, not a regression.
        src = pathlib.Path("edvibe_bot/selectors.py").read_text()
        assert "# CONFIRM" not in src, "Phase 0 not done: unconfirmed selectors remain"
    ```
    Run: `pytest tests/test_runner_dryrun.py::test_build_run_config_dry_run_default -q` Expected: PASS. The `test_no_unconfirmed_selectors_remain` gate is EXPECTED to FAIL until Phase 0 is complete — it blocks live runs against placeholder selectors.
- [ ] **Step 2 (human, post-Phase-0):** With confirmed selectors and `.env` populated, run: `python -m edvibe_bot.main --mode dry_run --headed --max-students 1 --max-lessons 1`. Confirm exercises were evaluated, NOTHING submitted (every ledger row `submitted=0`, `dry_run=1`), and `reports/audit.jsonl` has one line per evaluation.
- [ ] **Step 3 (human):** Inspect the SQLite `ledger`: no row has status `graded`/`completed` with `submitted=1`.
- [ ] **Step 4 (human):** Only after reviewing the dry-run report, run ONE real canary: `python -m edvibe_bot.main --mode full_auto --headed --max-students 1 --max-lessons 1` for one chosen student, and verify on edvibe.com that exactly one lesson was graded + completed.
- [ ] **Step 5:** Commit: `git commit -am "test: offline readiness gate + dry-run/canary runbook"`.

> Do not scale beyond the canary until it is confirmed correct on the platform.

---

## Deferred to the web-app plan (out of scope here)

- **Review-queue approval flow + `queue` table** (§6/§7): in this bot core, `review` mode records proposals to the ledger and submits NOTHING; the approve/edit/submit UI and `queue` table land in the web-app plan.
- **`settings` table** (§6): non-secret prefs persisted for the UI; the bot core reads config from `.env`.
- **Reconcile view** (§5): the full read-only "what is already completed on the platform" report is surfaced by the web app. ⚠️ The bot core's ledger/audit only records what THIS bot did — it CANNOT surface a leftover completed by a different actor (e.g. the prior agent's Lesson 14 / Анель). A minimal read-only platform-completion scan (list lessons where `status == "complete"` via the existing `scraper.progress.list_lessons`, cross-referenced against the ledger) is the recommended FIRST addition in the web-app plan, precisely because the motivating incident pre-dates this ledger.

---

## Known non-blocking refinements (optional polish during execution)

- **`Settings.confidence_threshold` validator** raises `ConfigError`; pydantic v2 re-wraps non-`ValueError`s, so direct `Settings(...)` surfaces `ValidationError` (only `load_settings()` converts it to `ConfigError`). Prefer raising `ValueError` in the validator if direct construction must raise `ConfigError`.
- **Pacing** (`settings.pacing_seconds`) is applied at the grade action; broader human-like pacing across navigation is tuned during the live dry-run (anti-automation), not in v1 unit scope.
- **Interpreter:** plan targets Python 3.11+ (PEP 604 `X | None` runtime annotations). Add `python_requires>=3.11` / a `python --version` check in the scaffold if the execution environment is uncertain.
- **`MANUAL_UNKNOWN`** exercises reach the gather step with no audio/text answer → caught by the empty-answer FLAG guard, so they are flagged, not graded (consistent with the fail-safe rule).
