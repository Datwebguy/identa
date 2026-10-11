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
- Tests run: `pytest` on `tests/`, 36 passed (pure functions only: keys, verdicts, store, parsers, identity decision). No real API call has been made. Nothing else has run.

## Demo

Not available yet.

## Known limitations and next steps

Nothing is built yet. See `docs/BUILD.md` for the plan.

## Submission

Confirmed requirements: see `docs/SUBMISSION.md`. Outstanding: everything in its checklist.
