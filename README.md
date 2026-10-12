<img src="web/logo.svg" alt="Identa logo" width="72" height="72">

# Identa

Identa onboards vendors into a company's vendor register without ever adding the same vendor twice.

You give it a list of company domains. For each company, Identa looks it up in Crustdata, then opens one GitHub pull request that adds the vendor to the register. If the process crashes or stops partway through, Identa checks what actually happened on GitHub before it does anything again. It never assumes a retry is safe.

Built for neatHack (neatlogs x VibeFounder), 10 to 12 October 2026. Team MajorLabs.

- Results page, built only from the saved runs in `evidence/`: https://identa-iota.vercel.app
- Build log: [hackathon.md](hackathon.md)

## The problem

An agent that acts on an outside system and then crashes does not know whether the action happened. If it retries, the action can happen twice. For vendor onboarding, a duplicate means two payables, two contracts and two approval chains for one company.

GitHub's REST documentation gives no idempotency key for creating a pull request or a git reference, and no documented error for a duplicate pull request. A retry cannot rely on GitHub to refuse it.

## How it works

Each company has a stable identity: its Crustdata company ID. Each action has an idempotency key, `sha256(company_id, action, canonical_json(args))`. The branch is named `vendor/<company_id>-<first 8 hex of the key>` and the file is `vendors/<company_id>.yaml`, so the same company and the same intent always produce the same names.

```
domains.csv -> Crustdata identify (free) -> Crustdata enrich (2 credits)
            -> intent store (SQLite) -> GitHub: create branch -> add file -> open pull request
            -> reconciler: Applied | NotApplied | Resume | Unknown
```

1. **Write the intent first.** The intent is saved to a local SQLite store before the first GitHub call. Each GitHub step is logged and runs one at a time.
2. **Check before acting again.** After any interruption the reconciler reads the branch, the file and the pull request on GitHub and decides:
   - Applied: everything exists and matches. Record the outcome and write nothing.
   - NotApplied: the branch does not exist. It is safe to act again.
   - Resume: the branch exists but the file or pull request is missing. Continue from the missing step.
   - Unknown: the check failed or the state is ambiguous. The company goes to a human queue. Identa never guesses.
3. **Identity rule.** A company is accepted only when its top Crustdata match is at or above the configured confidence threshold (0.9) and no other match shares that score. A tie, a low score or no match is held for a person.
4. **The control.** The same executor with the reconciler removed and a blind retry on any error. Each of its attempts names its own branch, because it has no stable key. It is run at the same crash points so duplicates can be counted.

All Crustdata and GitHub calls are traced in neatlogs (one workflow, `identa`). No language model is called, so every run reports 0 tokens and 0 model cost.

## Results

Every number comes from a saved run under `evidence/` and was read from GitHub after the run. Register: https://github.com/Datwebguy/identavendors

| Test | With Identa | Without the check |
|---|---|---|
| Three crash tests (process stopped once, at three different points), 9 companies each | 0 duplicate pull requests, 0 duplicate branches | 1 duplicate pull request, 3 duplicate branches |
| Eight copies started at the same moment on one company (`github.com`) | 1 branch, 1 pull request, 0 duplicates (GitHub refused 7 of 8 branch requests) | 8 branches, 8 pull requests, 7 duplicates |
| Time from the stop to a finished reconciliation | 2.17 s, 2.42 s, 2.59 s | not applicable |
| Crustdata credits for re-runs and crash recovery | 0 | 0 |

Other measured facts:

- First full run: 9 of 9 companies onboarded, pull requests #1 to #9, 34.92 s for the nine (3.88 s per company).
- Crustdata cost: 2 credits per new company (18 credits for 9), at $0.30 per credit, so $0.60 per company. Identify is free.
- Tie rule: `cfo.ai` (cfo.ai or Runway) and `amazon.com` (Amazon or Amazon Web Services) each had two matches at confidence 1.0, so both were held for a person. The first `Unknown` verdict came from this run.
- Race test, with Identa: one copy finished and seven stopped, because GitHub refused their writes. They opened nothing. Their memory lives inside each process, so nothing resumes them later.

## Evidence for each tool

**neatlogs** (project `identa`, workflow `identa`). 23 traces were read with the neatlogs command line tool and saved in `evidence/`. Link format: `https://app.neatlogs.com/traces/<trace id>`.

| Started (UTC, 11 Oct) | What | Duration | Spans | Trace id |
|---|---|---|---|---|
| 19:05:56 | First local try, GitHub write blocked | 2.7 s | 8 | `d2498e0a4eb745e7cb31827358f81e88` |
| 20:00:37 | First full run, nine companies | 38.0 s | 47 | `11b6f1d52ad7bf3a53d9e4909fe439e2` |
| 20:04:49 | Crash test A, stopped process | 1.8 s | 5 | `6102da4c4ecaca50730b67067321f123` |
| 20:04:52 | Crash test A, restart (reconciles, resumes) | 26.7 s | 47 | `c826fcf2d513f2b260ad52b4e91fbb1c` |
| 20:06:25 | Crash test B, stopped process | 3.1 s | 6 | `0c783fd14551662a4d33e74a204f4f55` |
| 20:06:30 | Crash test B, restart | 25.7 s | 46 | `f877205cdaf8f229059fe6ca7d79bbd8` |
| 20:08:06 | Crash test C, stopped process | 3.9 s | 7 | `de0ed8d916549c09aac676d9ddb12968` |
| 20:08:12 | Crash test C, restart (finds the open pull request) | 24.8 s | 45 | `5913c3580f0269d35155a989dfda6c25` |
| 20:10:55 | Control A, stopped process | 2.0 s | 5 | `7d53f9fd951666d9242e47a66f26a6fb` |
| 20:10:59 | Control A, second run (no check) | 26.1 s | 47 | `79ad1399b4689610ddaf174f2a02cdb3` |
| 20:12:25 | Control B, stopped process | 2.5 s | 6 | `b8bbf49172344635a3a1b908479c3b91` |
| 20:12:29 | Control B, second run | 31.4 s | 47 | `79517cfa956569fa88992a83d79a19e6` |
| 20:14:17 | Control C, stopped process | 3.6 s | 7 | `4b0db813b9d2ea82b7e003d91f8fefd9` |
| 20:14:22 | Control C, second run | 26.6 s | 47 | `0ee56ee354d6a8a2c647cc3963db59ac` |

A custom detection, "Killed process" (status = ERROR on spans named `identa`), was created in the project on 12 Oct. It has no hits yet, because it scores new traces only. Record: `evidence/*-neatlogs-detection-created.json`.

**Entire.** Commit `c480cd0e850fefd116118c5ecd8b0307f8ce86da` (the Crustdata credit record per run) carries checkpoint `d0ace3cc5007` on the `entire/checkpoints/v1` branch. Public session page: https://entire.io/gh/Datwebguy/identa/session/c3f1c6e4-5def-5acf-9d48-a704769e7e61

**cfo.ai.** Business plan with Pricing, Costs, Revenue and Runway pages: https://cfo.ai/s/yH49V0HAB1YFq5fX
- Measured inputs: 2 credits and $0.30 per credit ($0.60 per company), no model cost, no GitHub cost, 3.88 s per company.
- Founder decisions (not measurements): $99 per customer per month including 50 vendors, $1.50 per extra vendor, 3 customers in month 1 growing by 2 a month to 25 in month 12, 60 vendors per customer per month, $5 a month hosting, no team cost in year one, $3,000 starting cash.
- Plan result: $114 per customer per month, $36 Crustdata cost per customer, 68.42% gross margin before hosting; year one $19,152 revenue, $6,108 listed costs, $13,044 surplus; closing cash $16,044.

## Status

| Part | Status |
|---|---|
| Idempotency key and branch naming | works: unit tests pass; the same key was reproduced across separate runs |
| Crustdata identify and enrich | works: 9 of 9 domains, run on Railway |
| GitHub branch, file and pull request steps | works: 9 branches and 9 pull requests in the register |
| Reconciler and verdicts | Applied, NotApplied, Resume and Unknown all seen in real runs |
| Crash tests | works: three crash points, 0 duplicates each |
| Control | works: same crash points, 1 duplicate pull request and 3 duplicate branches in total |
| Race test | works: 1 pull request with Identa, 8 without |
| Human queue | works as a command line queue (no web page) |
| Results page | live at https://identa-iota.vercel.app, with a read-only company check |
| Not built | hourly schedule, AI summaries of held cases, a web page for the human queue |

## Running it

```
python -m identa run --config identa.toml --domains domains.csv
```

It needs `CRUSTDATA_API_KEY`, `GITHUB_TOKEN` and `NEATLOGS_API_KEY` in the environment, a `domains.csv` with one company domain per row, and a TOML config with all of these keys (there are no defaults): `confidence_threshold`, `repo_owner`, `repo_name`, `base_branch`, `store_path`, `evidence_dir`, `commit_author_name`, `commit_author_email`, `branch_prefix`. Keys are never written to the repository.

Other commands:

```
python -m identa run --control --max-attempts N --config identa.toml --domains domains.csv
python -m identa race --domain DOMAIN --agents N [--control] --config identa.toml
python -m identa measure [--prefix PREFIX] --config identa.toml
python -m identa queue list|accept|reject [id] [--company-id ID] --config identa.toml
```

`measure` counts branches and pull requests per company on GitHub and saves the count under `evidence/`. To inject a crash, set `IDENTA_CRASH_AFTER` to `create_branch`, `commit_file` or `open_pr`; the next run reconciles before doing new work.

Checks before every commit: `ruff check .`, `ruff format --check .`, `mypy src tests scripts/build_site.py`, `pytest`.

## Hosting

- The agent runs on Railway as a container (`Dockerfile`, `railway.json`, `scripts/railway_entry.sh`) with a volume at `/data` for the store and evidence. The command it runs comes from the `IDENTA_ARGS` variable.
- The results page in `web/` is static, built from `evidence/` by `scripts/build_site.py`, and served by Vercel. A small function, `api/identify.js`, powers the read-only company check: it looks one domain up in Crustdata and writes nothing.
- Rollback: Vercel keeps every deployment, so a previous one can be promoted from the dashboard. `main` only moves forward; changes are undone with a new commit.

## Credit

The approach of writing down what you are about to do, and checking before you retry, is adapted from Anchor by Viraj Chogle. No code from it is used.

## Licence

MIT. See [LICENSE](LICENSE).
