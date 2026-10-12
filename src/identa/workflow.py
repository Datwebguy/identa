"""The workflow layer: decide, intend, act, and recover through the reconciler."""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx

from identa import evidence, tracing
from identa.config import Config
from identa.crustdata import Crustdata, Identified, credits_spent
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
    if found.tied:
        return "tie at top confidence"
    return None


def _host(value: str | None) -> str | None:
    """The bare host of a domain or website address, without 'www.'."""
    if not value:
        return None
    host = urlparse(value if "://" in value else "//" + value).hostname or ""
    host = host.lower().rstrip(".")
    return host[4:] if host.startswith("www.") else host or None


def break_tie(found: Identified) -> tuple[Identified, str] | None:
    """Settle a tie from the evidence in the matches themselves.

    First: the only tied match whose primary domain is the requested domain. Then: the only
    one whose website is exactly the requested domain. Anything else stays a tie for a person.
    """
    if not found.tied or len(found.candidate_sites) != len(found.candidates):
        return None
    want = _host(found.domain)
    rules = (
        ([_host(primary) for _, primary, _ in found.candidate_sites], "its primary domain is {d}"),
        ([_host(site) for _, _, site in found.candidate_sites], "its website is {d} itself"),
    )
    for hosts, why in rules:
        hits = [i for i, host in enumerate(hosts) if host == want]
        if len(hits) == 1:
            cid, name, score = found.candidates[hits[0]]
            primary = found.candidate_sites[hits[0]][1]
            chosen = Identified(found.domain, cid, score, name, primary, ((cid, name, score),))
            return chosen, why.format(d=want)
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
    return onboard_with(found, crust.enrich(found.company_id), cfg, store, gh, hook)


def onboard_with(
    found: Identified,
    data: dict[str, Any],
    cfg: Config,
    store: Store,
    gh: GitHub,
    hook: CrashHook | None,
) -> str:
    """The same as onboard, with the enrich response already in hand."""
    assert found.company_id is not None
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
        branch_name(cfg.branch_prefix, found.company_id, key),
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
    balance_before = crust.balance()

    for pending in store.unfinished():  # reconcile anything left over before new work
        if recover(store, gh, cfg, pending, hook):
            report.recovered += 1

    for found in crust.identify(domains):
        settled = break_tie(found)
        if settled is not None:
            chosen, why = settled
            print(f"tie settled for {found.domain}: {chosen.name} ({chosen.company_id}), {why}")
            evidence.save(
                cfg.evidence_dir,
                "identa",
                "tie-settled",
                0,
                {
                    "domain": found.domain,
                    "chosen": chosen.company_id,
                    "why": why,
                    "candidates": json.loads(_detail(found))["candidates"],
                },
            )
            found = chosen
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

    balance_after = crust.balance()
    spent = credits_spent(balance_before, balance_after)
    print(f"crustdata credits spent: {spent:g} ({balance_before:g} -> {balance_after:g})")
    evidence.save(
        cfg.evidence_dir,
        "identa",
        "credits-spent",
        0,
        {"before": balance_before, "after": balance_after, "spent": spent},
    )
    return report


def _detail(found: Identified) -> str:
    d: dict[str, Any] = {
        "confidence": found.confidence,
        "company_id": found.company_id,
        "name": found.name,
    }
    if found.tied:
        d["candidates"] = [
            {"company_id": cid, "name": name, "confidence": score}
            for cid, name, score in found.candidates
        ]
    return json.dumps(d)


def choose_candidate(found: Identified, company_id: int) -> Identified:
    """The tied candidate a human picked. Raises ValueError if it is not one of them."""
    for cid, name, score in found.candidates:
        if cid == company_id:
            return Identified(found.domain, cid, score, name, None, found.candidates)
    raise ValueError(f"company {company_id} is not a candidate for {found.domain}")


def main_exit() -> None:
    tracing.shutdown()
    sys.stdout.flush()
