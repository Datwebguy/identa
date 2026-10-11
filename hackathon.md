# neatHack build log

Kept as the official neatHack build-log skill asks (https://neatlogs.com/hackathon/skill). Planned work and completed work are kept apart. Only tests that actually ran are recorded.

## Project

Identa: an agent that onboards vendors into a company's vendor register from a list of domains, and after any crash checks GitHub before acting again, so no vendor is added twice.

## Team

MajorLabs. Datwebguy.

## Stack

Planned: Python 3.11, Crustdata (identify, enrich), GitHub REST API, SQLite, neatlogs, Entire, cfo.ai. Update this line with what is actually used.

## Build log

### 11 Oct 2026
- Done: repository created; project docs, rules, architecture, build spec, resources and submission pack written; git hooks added so only the owner can author commits.
- Planned next: neatlogs first trace, Entire enabled on the repo, Crustdata identify call, intent store.
- Done: project skeleton (pyproject, ruff, mypy, pytest) and the idempotency key, branch and file naming (`src/identa/keys.py`).
- Done: verdict logic (`src/identa/verdict.py`) as a pure function of GitHub's answers.
- Done: SQLite intent store (`src/identa/store.py`): intents, steps, outcomes, human queue; outcome commit in one transaction.
- Done (written, not yet run against the real APIs): Crustdata client, GitHub client, reconciler, neatlogs span wrappers.
- Done (written, not run against real APIs): executor, workflow with recovery, command line, crash hook.
- Done: neatlogs `doctor --local` and `doctor --probe` run with the project key: all checks passed (synthetic trace). Crustdata credits endpoint called once: 200 OK, saved in `evidence/`.
- Done (written, not run against real APIs): control, `measure`, human queue commands.
- Done: static results page `web/` generated from `evidence/` by `scripts/build_site.py`; `vercel.json` serves `web/`.
- Done: Dockerfile and `railway.json` for the agent; injected crash now happens once (marker file) so a restart recovers instead of looping. Nothing deployed.
- Done: `domains.csv` (the nine vendor domains supplied by the owner, unchanged) and `identa.toml` (repo `Datwebguy/identavendors`, base `main`).
- Decision: `confidence_threshold = 0.9`, chosen by the owner. Domains below it go to the human queue.
- Done: an enrich response saved in `evidence/` is reused, so the same company is never enriched twice.
- Run (first real attempt, `github.com` only): Crustdata identify matched with confidence 1.0 and enrich succeeded (both saved in `evidence/`). The GitHub branch creation was refused with 403 "Write access to this GitHub API path is not permitted through this proxy", twice (the first attempt, then the workflow layer's one retry after the reconciler returned NotApplied). No branch or pull request was created. The intent stays pending in the local store. The Claude Code cloud session's proxy blocks GitHub REST writes, so GitHub steps cannot run from there.
- Run (Railway, 11 Oct 2026, fresh store, all 9 domains): 9 onboarded, 0 queued for human review, 0 failed. `identa measure` read from GitHub afterwards: 9 companies, 9 branches, 9 pull requests, 0 duplicate branches, 0 duplicate pull requests (saved in `evidence/`). All 9 top matches had confidence 1.0, so none went to the human queue.
- Observation: for `cfo.ai` and `amazon.com` Crustdata returned two matches each, both at confidence 1.0 (the other matches were Runway and Amazon Web Services). The agent took the top-ranked match. The current rule only compares the top match to the threshold, so a tie at the top is not treated as ambiguous. To be decided.
- Crustdata credits: balance 5200 before, 5182 after, so 18 credits for 9 enrichments (2 each), each company enriched once.
- Same key check: the first local attempt for `github.com` (blocked at branch creation) and the Railway run produced the same branch name `vendor/632750-be14eff4`.
- Done: configurable branch prefix (`branch_prefix`, overridable with `IDENTA_BRANCH_PREFIX`) so each crash test and the control use their own branch namespace in the same register, because the nine companies already have branches under `vendor/`. Nothing in the register is deleted.
- Not done yet: crash tests, control, Railway crash test, neatlogs trace links, Entire, cfo.ai.
- Tests run: `pytest` on `tests/`, 36 passed (pure functions only: keys, verdicts, store, parsers, identity decision). No real API call has been made. Nothing else has run.

## Demo

Not available yet.

## Known limitations and next steps

Nothing is built yet. See `docs/BUILD.md` for the plan.

## Submission

Confirmed requirements: see `docs/SUBMISSION.md`. Outstanding: everything in its checklist.
