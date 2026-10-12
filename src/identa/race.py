"""Several independent agents onboard the same company at the same moment.

Each agent has its own memory (an in-memory store) and its own GitHub client, as separate
processes would. The protocol agents derive one key, so they name one branch. The control
agents each name a fresh branch, as the control does for every attempt.
"""

from __future__ import annotations

import threading
import uuid
from collections import Counter
from collections.abc import Callable
from typing import Any

import httpx

from identa import evidence
from identa.config import Config
from identa.crustdata import Identified
from identa.executor import StepError, execute
from identa.github import GitHub
from identa.keys import ACTION_ONBOARD
from identa.store import Store
from identa.verdict import Step
from identa.workflow import onboard_with


def _protocol_agent(found: Identified, data: dict[str, Any], cfg: Config, gh: GitHub) -> str:
    store = Store(":memory:")
    try:
        # onboard_with reconciles after a refused step, then resumes or stops.
        return onboard_with(found, data, cfg, store, gh, None)
    finally:
        store.close()


def _control_agent(found: Identified, data: dict[str, Any], cfg: Config, gh: GitHub) -> str:
    assert found.company_id is not None
    info = data.get("basic_info") or {}
    args = {"name": info.get("name"), "domain": info.get("primary_domain")}
    store = Store(":memory:")
    try:
        attempt = uuid.uuid4().hex
        branch = f"{cfg.branch_prefix}/{found.company_id}-{attempt[:8]}"
        import json

        store.write_intent(
            attempt, str(found.company_id), ACTION_ONBOARD, json.dumps(args), "{}", branch
        )
        intent = store.get_intent(attempt)
        assert intent is not None
        try:
            execute(store, gh, intent, cfg.base_branch, Step.CREATE_BRANCH, None)
            return "onboarded"
        except (StepError, httpx.HTTPError):
            return "failed"
    finally:
        store.close()


def race(
    found: Identified,
    data: dict[str, Any],
    cfg: Config,
    make_github: Callable[[], GitHub],
    agents: int,
    control: bool,
) -> dict[str, Any]:
    """Start the agents together and return how each one ended."""
    gate = threading.Barrier(agents)
    outcomes: list[str] = [""] * agents
    fn = _control_agent if control else _protocol_agent

    def work(i: int) -> None:
        gh = make_github()
        gate.wait()
        try:
            outcomes[i] = fn(found, data, cfg, gh)
        except Exception as exc:  # recorded, never hidden
            outcomes[i] = f"error: {type(exc).__name__}"

    threads = [threading.Thread(target=work, args=(i,)) for i in range(agents)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    result: dict[str, Any] = {
        "domain": found.domain,
        "company_id": found.company_id,
        "agents": agents,
        "control": control,
        "branch_prefix": cfg.branch_prefix,
        "outcomes": dict(Counter(outcomes)),
    }
    evidence.save(cfg.evidence_dir, "race", f"{cfg.branch_prefix}", 200, result)
    return result
