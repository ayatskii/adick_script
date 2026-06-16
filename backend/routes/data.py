"""Read-mostly data endpoints: students, queue, flagged, reconcile, audit,
settings. Each falls back to verbatim seed data when the store is empty."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from .. import config as backend_config
from ..schemas import OkResponse, QueueDecisionRequest, SubmitResponse
from ..seed_data import (
    SEED_AUDIT,
    SEED_FLAGGED,
    SEED_RECONCILE,
    SEED_REVIEW_ITEMS,
    SEED_SETTINGS,
    SEED_STUDENTS,
)
from ..store_read import StoreReader

router = APIRouter(prefix="/api", tags=["data"])

# In-memory overlay for settings PUT + queue decisions/submit (v1 records
# intent; real platform submit needs a browser — a documented non-goal).
_settings_overlay: dict[str, Any] = {}
_queue_decisions: dict[str, dict] = {}


def _reader() -> StoreReader:
    return StoreReader(backend_config.db_path())


@router.get("/students")
async def list_students() -> list[dict]:
    rows = _reader().students()
    return rows if rows else SEED_STUDENTS


@router.get("/queue")
async def list_queue() -> list[dict]:
    rows = _reader().queue_items()
    items = rows if rows else [dict(i) for i in SEED_REVIEW_ITEMS]
    # Apply any recorded decisions.
    for item in items:
        d = _queue_decisions.get(item["id"])
        if d is not None:
            item["status"] = (
                "approved" if d["decision"] in ("approved", "edited") else "rejected"
            )
            item["edited"] = d["decision"] == "edited"
            if d.get("score") is not None:
                item["score"] = d["score"]
            if d.get("comment") is not None:
                item["comment"] = d["comment"]
    return items


@router.post("/queue/{item_id}/decision", response_model=OkResponse)
async def decide_queue(item_id: str, req: QueueDecisionRequest) -> OkResponse:
    _queue_decisions[item_id] = {
        "decision": req.decision,
        "score": req.score,
        "comment": req.comment,
    }
    return OkResponse(ok=True)


@router.post("/queue/submit", response_model=SubmitResponse)
async def submit_queue() -> SubmitResponse:
    # v1: records submission intent for items with a non-rejected decision.
    submitted = sum(
        1 for d in _queue_decisions.values() if d["decision"] != "rejected"
    )
    return SubmitResponse(submitted=submitted)


@router.get("/flagged")
async def list_flagged() -> list[dict]:
    rows = _reader().flagged_items()
    return rows if rows else SEED_FLAGGED


@router.get("/reconcile")
async def list_reconcile() -> list[dict]:
    rows = _reader().reconcile_rows()
    return rows if rows else SEED_RECONCILE


@router.get("/audit")
async def list_audit() -> list[dict]:
    rows = _reader().all_audit()
    return rows if rows else SEED_AUDIT


@router.get("/settings")
async def get_settings() -> dict:
    settings = dict(SEED_SETTINGS)
    # Reflect any real (non-secret) config values where available.
    real = backend_config.try_load_settings()
    if real is not None:
        settings.update(
            {
                "transcriptionModel": real.transcription_model,
                "evaluationModel": real.evaluation_model,
                "confidenceThreshold": real.confidence_threshold,
                "marathon": real.marathon_name,
                "curator": real.curator_name,
                # Credentials remain masked.
                "edvibeLogin": real.edvibe_login,
                "edvibePassword": "••••••••",
                "openaiApiKey": "sk-••••••••" if real.openai_api_key else "",
            }
        )
    settings.update(_settings_overlay)
    return settings


@router.put("/settings")
async def put_settings(patch: dict) -> dict:
    # Never persist secrets; mask any credential-ish keys that come in.
    for secret_key in ("edvibePassword", "openaiApiKey"):
        patch.pop(secret_key, None)
    _settings_overlay.update(patch)
    return await get_settings()
