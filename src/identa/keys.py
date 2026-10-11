"""Stable identity for a company and an action.

The same company and the same intent always give the same key, branch and file path,
so the reconciler can look an action up by exact name.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

ACTION_ONBOARD = "onboard_vendor"


def canonical_json(value: Any) -> str:
    """Sorted keys, no whitespace, non-ASCII kept as is."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def idempotency_key(company_id: int | str, action: str, args: dict[str, Any]) -> str:
    """sha256 over the company id, the action and the canonical JSON of the args, as hex."""
    material = canonical_json({"company_id": str(company_id), "action": action, "args": args})
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def branch_name(prefix: str, company_id: int | str, key: str) -> str:
    return f"{prefix}/{company_id}-{key[:8]}"


def vendor_file_path(company_id: int | str) -> str:
    return f"vendors/{company_id}.yaml"
