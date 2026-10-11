"""The control: the same executor with the reconciler removed and a retry on any error.

It has no memory of earlier runs (an in-memory store, no intent lookup, no skip), and no
stable key, so each attempt names its branch freshly. Branches live under `control/` so
protocol and control results can be counted separately.
"""

from __future__ import annotations

import json
import uuid

import httpx

from identa import tracing
from identa.config import Config
from identa.crustdata import Crustdata
from identa.executor import CrashHook, StepError, execute
from identa.github import GitHub
from identa.keys import ACTION_ONBOARD
from identa.store import Store
from identa.verdict import Step
from identa.workflow import decide_identity

CONTROL_PREFIX = "control"


@tracing.span("WORKFLOW", "identa.control_run")
def run_control(
    domains: list[str],
    cfg: Config,
    crust: Crustdata,
    gh: GitHub,
    max_attempts: int,
    hook: CrashHook | None,
) -> dict[str, int]:
    memory_store = Store(":memory:")
    done = failed = 0
    for found in crust.identify(domains):
        if decide_identity(found, cfg.confidence_threshold) or found.company_id is None:
            continue  # the same acceptance rule as the protocol; the control skips the queue
        info = crust.enrich(found.company_id).get("basic_info") or {}
        args = {"name": info.get("name"), "domain": info.get("primary_domain")}
        for _ in range(max_attempts):  # retry on any error, blind
            attempt_key = uuid.uuid4().hex
            branch = f"{CONTROL_PREFIX}/{found.company_id}-{attempt_key[:8]}"
            memory_store.write_intent(
                attempt_key,
                str(found.company_id),
                ACTION_ONBOARD,
                json.dumps(args),
                "{}",
                branch,
            )
            intent = memory_store.get_intent(attempt_key)
            assert intent is not None
            try:
                execute(memory_store, gh, intent, cfg.base_branch, Step.CREATE_BRANCH, hook)
                done += 1
                break
            except (StepError, httpx.HTTPError):
                continue
        else:
            failed += 1
    return {"onboarded": done, "failed": failed}
