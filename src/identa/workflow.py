"""The workflow layer: decide, intend, act, and recover through the reconciler."""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

from identa import tracing
from identa.config import Config
from identa.crustdata import Crustdata, Identified
from identa.executor import CrashHook, StepError, execute
from identa.github import GitHub
from identa.keys import ACTION_ONBOARD, branch_name, idempotency_key
from identa.reconciler import reconcile
from identa.store import NEEDS_HUMAN, Intent, Store
from identa.verdict import Step, Verdict


def crash_marker(cfg: Config, control: bool = False) -> Path:
    return cfg.store_path.with_suffix(".control-crashed" if control else ".crashed")


CRASH_ENV = "IDENTA_CRASH_AFTER"  # one of: create_branch, commit_file, open_pr


def crash_hook_from_env(marker: Path) -> CrashHook | None:
    """Crash once at the step named in IDENTA_CRASH_AFTER.

    The marker file records that the crash happened, so a supervisor that restarts the
    process (for example a container platform) does not crash it again at the same point.
    """
    point = os.environ.get(CRASH_ENV)
    if not point:
        return None

    def hook(step: str) -> None:
        if step == point and not marker.exists():
            marker.write_text(step, encoding="utf-8")
            tracing.flush()  # required before every injected crash
            os._exit(137)

    return hook


@dataclass
class Report:
    onboarded: int = 0
    queued_for_human: int = 0
    skipped_existing: int = 0
    recovered: int = 0
    failed: int = 0


def decide_identity(found: Identified, threshold: float) -> str | None:
    """None means accept. Otherwise the reason it goes to the human queue (Unknown)."""
    if found.company_id is None:
        return "no match"
    if found.confidence is None or found.confidence < threshold:
        return "confidence below threshold"
    return None


def recover(store: Store, gh: GitHub, cfg: Config, intent: Intent, hook: CrashHook | None) -> bool:
    """Reconcile one intent. Returns True if it ended up completed."""
    decision, url = reconcile(gh, intent, cfg.base_branch)
    start: Step | None = None
    if decision.verdict is Verdict.APPLIED and url:
        store.commit_outcome(intent.key, url, intent.memory_json)
        return True
    if decision.verdict is Verdict.NOT_APPLIED:
        start = Step.CREATE_BRANCH  # safe to act again: the branch does not exist
    elif decision.verdict is Verdict.RESUME:
        start = decision.resume_from
    if start is None:
        store.set_state(intent.key, NEEDS_HUMAN)
        store.enqueue_human(
            intent.key, None, decision.reason, json.dumps({"branch": intent.branch})
        )
        return False
    try:
        execute(store, gh, intent, cfg.base_branch, start, hook)
    except (StepError, httpx.HTTPError):
        return False  # stays pending; the next start reconciles it again
    return True


def onboard(
    found: Identified,
    cfg: Config,
    store: Store,
    crust: Crustdata,
    gh: GitHub,
    hook: CrashHook | None,
) -> str:
    """One accepted company. Returns onboarded, recovered, failed, skipped or queued."""
    assert found.company_id is not None
    if store.find_by_company(str(found.company_id), ACTION_ONBOARD):
        return "skipped"  # already intended or done: nothing to do
    data = crust.enrich(found.company_id)
    info = data.get("basic_info") or {}
    name, domain = info.get("name"), info.get("primary_domain")
    if not name or not domain:
        store.enqueue_human(None, found.domain, "enrich lacks name or domain", _detail(found))
        return "queued"
    args = {"name": name, "domain": domain}
    key = idempotency_key(found.company_id, ACTION_ONBOARD, args)
    memory = {"headcount": data.get("headcount"), "name": name, "domain": domain}
    store.write_intent(  # the intent is on disk before the first GitHub call
        key,
        str(found.company_id),
        ACTION_ONBOARD,
        json.dumps(args, sort_keys=True),
        json.dumps(memory, sort_keys=True),
        branch_name(found.company_id, key),
    )
    intent = store.get_intent(key)
    assert intent is not None
    try:
        execute(store, gh, intent, cfg.base_branch, Step.CREATE_BRANCH, hook)
        return "onboarded"
    except (StepError, httpx.HTTPError):
        return "recovered" if recover(store, gh, cfg, intent, hook) else "failed"


@tracing.span("WORKFLOW", "identa.run")
def run(
    domains: list[str],
    cfg: Config,
    store: Store,
    crust: Crustdata,
    gh: GitHub,
) -> Report:
    report = Report()
    hook = crash_hook_from_env(crash_marker(cfg))

    for pending in store.unfinished():  # reconcile anything left over before new work
        if recover(store, gh, cfg, pending, hook):
            report.recovered += 1

    for found in crust.identify(domains):
        reason = decide_identity(found, cfg.confidence_threshold)
        if reason is not None or found.company_id is None:
            store.enqueue_human(None, found.domain, reason or "no match", _detail(found))
            report.queued_for_human += 1
            continue
        outcome = onboard(found, cfg, store, crust, gh, hook)
        if outcome == "queued":
            report.queued_for_human += 1
        elif outcome == "skipped":
            report.skipped_existing += 1
        else:
            report.onboarded += outcome == "onboarded"
            report.recovered += outcome == "recovered"
            report.failed += outcome == "failed"
    return report


def _detail(found: Identified) -> str:
    d: dict[str, Any] = {
        "confidence": found.confidence,
        "company_id": found.company_id,
        "name": found.name,
    }
    return json.dumps(d)


def main_exit() -> None:
    tracing.shutdown()
    sys.stdout.flush()
