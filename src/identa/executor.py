"""Runs the GitHub steps for one intent. Each step is logged as started before the call.

The executor never retries. Retrying is the workflow layer's job, after the reconciler.
"""

from __future__ import annotations

import json
from collections.abc import Callable

from identa.github import GitHub, Reply
from identa.keys import vendor_file_path
from identa.store import Intent, Store
from identa.vendor import pr_title, render_vendor_file
from identa.verdict import Step

ORDER = (Step.CREATE_BRANCH, Step.COMMIT_FILE, Step.OPEN_PR)
CrashHook = Callable[[str], None]


class StepError(Exception):
    pass


def _expect(reply: Reply, step: Step, ok: tuple[int, ...]) -> Reply:
    if reply.status not in ok:
        raise StepError(f"{step} returned {reply.status}")
    return reply


def execute(
    store: Store,
    gh: GitHub,
    intent: Intent,
    base: str,
    start: Step = Step.CREATE_BRANCH,
    crash_hook: CrashHook | None = None,
) -> str:
    """Run the steps from `start`. Commits the outcome locally and returns the PR URL."""
    args = json.loads(intent.args_json)
    pr_url = ""
    for step in ORDER[ORDER.index(start) :]:
        store.log_step(intent.key, step, "started")
        if step is Step.CREATE_BRANCH:
            sha = _expect(gh.get_ref(base), step, (200,)).body["object"]["sha"]
            _expect(gh.create_ref(intent.branch, sha), step, (201,))
        elif step is Step.COMMIT_FILE:
            content = render_vendor_file(intent.company_id, args["name"], args["domain"])
            _expect(
                gh.put_file(
                    vendor_file_path(intent.company_id),
                    intent.branch,
                    f"Add vendor file for {args['domain']}",
                    content,
                ),
                step,
                (200, 201),
            )
        else:
            reply = _expect(
                gh.open_pr(
                    intent.branch,
                    base,
                    pr_title(args["name"], args["domain"]),
                    f"Crustdata company id {intent.company_id}.\nIntent key {intent.key}.",
                ),
                step,
                (201,),
            )
            pr_url = str(reply.body["html_url"])
        store.log_step(intent.key, step, "done")
        if crash_hook:
            crash_hook(step)
    store.commit_outcome(intent.key, pr_url, intent.memory_json)
    return pr_url
