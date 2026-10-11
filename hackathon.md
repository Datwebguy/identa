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
- Tests run: `pytest` on `tests/test_keys.py`, 5 passed. Nothing else has run.

## Demo

Not available yet.

## Known limitations and next steps

Nothing is built yet. See `docs/BUILD.md` for the plan.

## Submission

Confirmed requirements: see `docs/SUBMISSION.md`. Outstanding: everything in its checklist.
