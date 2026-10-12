<img src="web/logo.svg" alt="Identa logo" width="72" height="72">

# Identa

Identa onboards vendors into a company's vendor register without ever adding the same vendor twice.

You give it a list of company domains. For each company, Identa looks it up in Crustdata, then opens one GitHub pull request that adds the vendor to the register. If the process crashes or stops partway through, Identa checks what actually happened on GitHub before it does anything again. It never assumes a retry is safe.

- Results page, built only from the saved runs in `evidence/`: https://identa-iota.vercel.app

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
3. **Identity rule.** A company is accepted only when its top Crustdata match is at or above the configured confidence threshold (0.9). When two matches share the top score, Identa settles the tie from the matches themselves: it picks the only match whose primary domain is the requested domain, or else the only one whose website is exactly that domain, and records why. A tie that nothing separates, a low score or no match is held for a person. What a person decides is remembered: a company rejected in review is not held again on a later run, and an earlier choice among tied matches is applied without a new review.
4. **The control.** The same executor with the reconciler removed and a blind retry on any error. Each of its attempts names its own branch, because it has no stable key. It is run at the same crash points so duplicates can be counted.

All Crustdata and GitHub calls are traced with neatlogs. No language model is called, so every run reports 0 tokens and 0 model cost.

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
- Ties: in the 12 Oct re-run, `cfo.ai` (cfo.ai or Runway) and `amazon.com` (Amazon or Amazon Web Services) each had two matches at confidence 1.0 and were held for a person; that run produced the first `Unknown` verdict. The tie-breaker added afterwards settles both from the same saved Crustdata answers: cfo.ai, because its website is cfo.ai itself (Runway's is runway.cfo.ai), and Amazon, because its primary domain is amazon.com (AWS's is aws.com). Record: `evidence/*-identa-tie-check-on-saved-identify.json`.
- Race test, with Identa: one copy finished and seven stopped, because GitHub refused their writes. They opened nothing. Their memory lives inside each process, so nothing resumes them later.

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
| Human queue and memory | works as a command line queue (no web page); a person's accept or reject is remembered and recalled on later runs |
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

## Licence

MIT. See [LICENSE](LICENSE).
