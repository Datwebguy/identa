"""Save raw API responses with a timestamp. Never receives headers, so no key can land here."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def save(evidence_dir: Path, source: str, label: str, status: int, body: Any) -> Path:
    stamp = datetime.now(UTC)
    safe = "".join(c if c.isalnum() or c in "-_." else "_" for c in label)
    path = evidence_dir / f"{stamp.strftime('%Y%m%dT%H%M%S%fZ')}-{source}-{safe}.json"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    record = {"saved_at": stamp.isoformat(), "source": source, "status": status, "body": body}
    path.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    return path
