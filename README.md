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
| Crustdata identify and enrich | code written, not run against the real API |
| GitHub branch, file and pull request steps | code written, not run against the real API |
| Reconciler and three verdicts | verdict logic and GitHub checks written; verdict logic unit-tested, GitHub checks not run |
| Crash test (three crash points) | crash hook written (`IDENTA_CRASH_AFTER`), not run |
| Naive control and duplicate count | not built |
| neatlogs traces | span wrappers written, no trace sent yet |
| Entire checkpoint | not built |
| cfo.ai plan | not built |
| Demo video | not built |

## Running it

Not run end to end yet. The command is:

```
python -m identa run --config identa.toml --domains domains.csv
```

It needs `CRUSTDATA_API_KEY`, `GITHUB_TOKEN` and `NEATLOGS_API_KEY` in the environment, a `domains.csv` with one real company domain per row, and a TOML config with all of these keys (there are no defaults): `confidence_threshold`, `repo_owner`, `repo_name`, `base_branch`, `store_path`, `evidence_dir`.

To inject a crash, set `IDENTA_CRASH_AFTER` to `create_branch`, `commit_file` or `open_pr`. The next run reconciles before doing new work.

## Licence

MIT. See [LICENSE](LICENSE).
