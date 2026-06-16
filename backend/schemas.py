"""Pydantic request/response models for the backend API.

Mirrors the contract's data shapes and the frontend's web/src/types.ts where
possible. JSON field names match the frontend (camelCase preserved verbatim in
the seed/data dicts; these models are mostly for request bodies + typed
responses where the shape is stable).
"""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

# ------------------------------------------------------------------
# Runs
# ------------------------------------------------------------------

RunMode = Literal["demo", "dry_run", "full_auto", "review", "dryrun", "full"]


class RunScope(BaseModel):
    all: bool = True
    students: Optional[list[str]] = None


class StartRunRequest(BaseModel):
    mode: RunMode = "demo"
    scope: RunScope = Field(default_factory=RunScope)
    max_students: Optional[int] = None
    max_lessons: Optional[int] = None
    headed: bool = False
    confidence_threshold: float = 0.6


class StartRunResponse(BaseModel):
    run_id: str
    status: str


class RunCounts(BaseModel):
    graded: int = 0
    skipped: int = 0
    flagged: int = 0
    errors: int = 0
    completed_lessons: int = 0


class Run(BaseModel):
    id: str
    mode: str
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    status: str
    duration: Optional[str] = None
    counts: RunCounts = Field(default_factory=RunCounts)


class RunDetail(BaseModel):
    run: Run
    timeline: list[dict[str, Any]]
    audit: list[dict[str, Any]]


class StopResponse(BaseModel):
    ok: bool = True
    note: str


# ------------------------------------------------------------------
# Review queue
# ------------------------------------------------------------------


class QueueDecisionRequest(BaseModel):
    decision: Literal["approved", "rejected", "edited"]
    score: Optional[int] = None
    comment: Optional[str] = None


class OkResponse(BaseModel):
    ok: bool = True


class SubmitResponse(BaseModel):
    submitted: int


# ------------------------------------------------------------------
# Health
# ------------------------------------------------------------------


class HealthResponse(BaseModel):
    ok: bool = True
    phase0_done: bool
    openai_key_set: bool


# ------------------------------------------------------------------
# RunEvent (normalized WS payload). The runtime payloads are plain dicts
# (built in jobs.py); this model documents the shape and is used for typing.
# ------------------------------------------------------------------


class RunEvent(BaseModel):
    type: str
    ts: str
    message: Optional[str] = None
    data: Optional[dict[str, Any]] = None
