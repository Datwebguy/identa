"""Asks GitHub what actually happened for one intent, by exact branch name."""

from __future__ import annotations

import base64
import binascii
import json
from typing import Any

import httpx

from identa.github import GitHub, Reply
from identa.keys import vendor_file_path
from identa.store import Intent
from identa.vendor import render_vendor_file
from identa.verdict import Decision, FileState, PrState, decide

FILE_OK = (200, 201)


def classify_file(reply: Reply, expected: str) -> FileState:
    if reply.status == 404:
        return FileState.MISSING
    if reply.status != 200 or not isinstance(reply.body, dict):
        return FileState.ERROR
    try:
        actual = base64.b64decode(reply.body.get("content", "")).decode("utf-8")
    except (binascii.Error, UnicodeDecodeError):
        return FileState.MISMATCH
    return FileState.MATCHES if actual == expected else FileState.MISMATCH


def classify_prs(reply: Reply, branch: str, base: str) -> tuple[PrState, str | None]:
    """Returns the state and, if exactly one matching open PR exists, its URL."""
    if reply.status != 200 or not isinstance(reply.body, list):
        return PrState.ERROR, None
    mine: list[dict[str, Any]] = [
        p for p in reply.body if (p.get("head") or {}).get("ref") == branch
    ]
    if not mine:
        return PrState.NONE, None
    if len(mine) == 1 and mine[0].get("state") == "open":
        if (mine[0].get("base") or {}).get("ref") == base:
            return PrState.OPEN_MATCHES, str(mine[0]["html_url"])
    return PrState.MISMATCH, None


def reconcile(gh: GitHub, intent: Intent, base: str) -> tuple[Decision, str | None]:
    """Returns the decision and the pull request URL when the verdict is Applied."""
    try:
        ref = gh.get_ref(intent.branch)
        if ref.status != 200:
            return decide(ref.status, FileState.ERROR, PrState.ERROR), None
        args = json.loads(intent.args_json)
        expected = render_vendor_file(intent.company_id, args["name"], args["domain"])
        file_state = classify_file(
            gh.get_file(vendor_file_path(intent.company_id), intent.branch), expected
        )
        pr_state, url = classify_prs(gh.list_prs(intent.branch), intent.branch, base)
    except (httpx.HTTPError, ValueError, KeyError):
        return decide(None, FileState.ERROR, PrState.ERROR), None
    return decide(200, file_state, pr_state), url
