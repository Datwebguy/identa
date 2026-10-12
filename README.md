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
| Idempotency key and branch naming | works: unit tests pass; the same key was reproduced across two separate runs for `github.com` |
| Crustdata identify and enrich | works: 9 of 9 domains identified and enriched (run on Railway, 11 Oct 2026) |
| GitHub branch, file and pull request steps | works: 9 branches and 9 pull requests created in `Datwebguy/identavendors` |
| Reconciler and three verdicts | NotApplied, Resume, Applied and Unknown all observed in real runs (Unknown: the two tied matches in the 12 Oct re-run, held for a human) |
| Crash test (three crash points) | works: run on Railway at all three points; 9 companies, 9 branches, 9 pull requests, 0 duplicates each |
| Naive control and duplicate count | works: run at the same three points; 1 duplicate pull request and 3 duplicate branches in total |
| neatlogs traces | Doctor probe passed; the Railway run sent traces (trace links not yet collected) |
| Entire checkpoint | built: commit `c480cd0`, checkpoint `d0ace3cc5007` on `entire/checkpoints/v1`; public session page: https://entire.io/gh/Datwebguy/identa/session/c3f1c6e4-5def-5acf-9d48-a704769e7e61 |
| cfo.ai plan | built: https://cfo.ai/s/yH49V0HAB1YFq5fX (measured costs from the runs; pricing is the owner's decisions) |
| Results page (`web/`, on Vercel) | deployed: https://identa-iota.vercel.app , built from saved evidence |
| Demo video | not built |

## Results

Live results page, built only from the saved files in `evidence/`: https://identa-iota.vercel.app

## Running it

Not run end to end yet. The command is:

```
python -m identa run --config identa.toml --domains domains.csv
```

It needs `CRUSTDATA_API_KEY`, `GITHUB_TOKEN` and `NEATLOGS_API_KEY` in the environment, a `domains.csv` with one real company domain per row, and a TOML config with all of these keys (there are no defaults): `confidence_threshold`, `repo_owner`, `repo_name`, `base_branch`, `store_path`, `evidence_dir`.

Other commands:

```
python -m identa run --control --max-attempts N --config identa.toml --domains domains.csv
python -m identa measure [--prefix PREFIX] --config identa.toml
python -m identa queue list|accept|reject [id] --config identa.toml
```

The control has no memory and no stable key, so each attempt names its branch freshly, under the configured branch prefix. `measure` counts branches and pull requests per company on GitHub and saves the count under `evidence/`.

To inject a crash, set `IDENTA_CRASH_AFTER` to `create_branch`, `commit_file` or `open_pr`. The next run reconciles before doing new work.

## Railway

The agent runs on Railway as a long-lived container (`Dockerfile`, `railway.json`, `scripts/railway_entry.sh`), with a volume at `/data` for the store and evidence. The command it runs comes from the `IDENTA_ARGS` variable. Keys are Railway variables, never in the repo.

- Why Railway: this development session's network blocks GitHub REST writes, so the GitHub steps cannot run from here.
- An injected crash exits with code 137 and writes a marker file beside the store, so it happens once. Railway's restart policy restarts the process, which reconciles before doing new work.
- Evidence is written to `/data/evidence`. After a successful run the agent copies new files, one at a time, to the `evidence` branch of `identavendors`. They are then fetched with git and committed into this repo's `evidence/` folder before the results page is rebuilt.

## Licence

MIT. See [LICENSE](LICENSE).
