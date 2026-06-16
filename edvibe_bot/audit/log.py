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
