# Identa

Identa onboards vendors into a company's vendor register without ever adding the same vendor twice.

You give it a list of company domains. For each company, Identa looks it up in Crustdata, then opens one GitHub pull request that adds the vendor to the register. If the process crashes or times out partway through, Identa checks what actually happened on GitHub before it does anything again. It never assumes a retry is safe.

Built for neatHack (neatlogs x VibeFounder), 10 to 12 October 2026.

## The problem

An agent that acts on an outside system and then crashes does not know whether the action happened. If it retries, the action can happen twice. For vendor onboarding, a duplicate means two payables, two contracts and two approval chains for one company.

GitHub's REST documentation gives no idempotency key for creating a pull request or a git reference, and no documented error for a duplicate pull request. A retry cannot rely on GitHub to refuse it.

## How it works

Each company gets a stable identity: its Crustdata company ID. Each action gets an idempotency key, `sha256(company_id, action, canonical_json(args))`. The branch name is built from both, so the same company and the same intent always produce the same branch.

Identa writes its intent to a local SQLite store before it touches GitHub. After a crash, it looks up the branch by exact name:

- Applied: the branch and its pull request exist and match the intent. Identa records the outcome.
- NotApplied: the branch does not exist. Identa can safely act again.
- Unknown: the check failed or the state is ambiguous. The intent goes to a human queue. Identa never guesses.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full flow, [docs/BUILD.md](docs/BUILD.md) for the build spec, [docs/RESOURCES.md](docs/RESOURCES.md) for every link, and [hackathon.md](hackathon.md) for the build log.

## Status

Under construction for neatHack. The table below is updated only from saved runs.

| Part | Status |
|---|---|
| Idempotency key and branch naming | built, unit tests pass (`tests/test_keys.py`) |
| Crustdata identify and enrich | not built |
| GitHub branch, file and pull request steps | not built |
| Reconciler and three verdicts | not built |
| Crash test (three crash points) | not built |
| Naive control and duplicate count | not built |
| neatlogs traces | not built |
| Entire checkpoint | not built |
| cfo.ai plan | not built |
| Demo video | not built |

## Running it

Not runnable yet. This section will be filled in when the first run works.

## Licence

MIT. See [LICENSE](LICENSE).
