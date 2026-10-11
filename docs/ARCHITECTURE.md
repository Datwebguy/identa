# Architecture

## Components

```
domains.csv
    |
    v
Planner ---- Crustdata identify (free) ---- Crustdata enrich (2 credits)
    |
    v
Intent store (SQLite, one transaction per commit)
    |
    v
Executor ---- GitHub: read base ref -> create ref -> PUT file -> open PR
    |
    v
Reconciler ---- GitHub: GET git/ref/heads/<branch>, then the PR
    |
    +--> Applied     -> record outcome
    +--> NotApplied  -> executor may act again
    +--> Unknown     -> human queue
```

All external calls are wrapped in neatlogs spans: WORKFLOW for each run, AGENT for the planner, TOOL for each Crustdata and GitHub call.

## Identity

- Company identity: the Crustdata company ID from `POST /company/identify`.
- Idempotency key: `sha256(company_id, action, canonical_json(args))`. `args` includes the canonical name and domain.
- Branch: `vendor/<crustdata_company_id>-<first 8 hex of the key>`.
- File: `vendors/<crustdata_company_id>.yaml`.

The same company and intent always produce the same branch name, so the reconciler can look it up exactly.

## Phases

Order note: Crustdata identify and enrich are read-only and run before the intent is written, because the idempotency key needs the company ID and name they return. The intent is written before the first GitHub call.

1. Intend. Write the intent row (action, company ID, key, branch, planned steps, state `pending`) before any GitHub call.
2. Act. Each GitHub step is its own logged step:
   1. `GET /repos/{owner}/{repo}/git/ref/heads/main` for the base SHA.
   2. `POST /repos/{owner}/{repo}/git/refs` with `refs/heads/<branch>` and the base SHA.
   3. `PUT /repos/{owner}/{repo}/contents/vendors/<id>.yaml` on that branch. Serial only.
   4. `POST /repos/{owner}/{repo}/pulls` with `head` set to the branch and `base` set to `main`.
3. Commit. Record the outcome, the pull request URL and the memory row in one SQLite transaction.

## Reconciliation

Runs on start and after any interrupted run, for every intent not in a final state.

| GitHub answer | Verdict |
|---|---|
| ref returns 404 | NotApplied |
| ref returns 200 and an open PR exists from that branch with the expected file | Applied |
| ref returns 200 but no PR, or the file is missing | resume from the missing step, then reconcile again |
| any other status, a timeout, or content that does not match the intent | Unknown |

## Decision rules for Crustdata

- An identify entry with an empty `matches` array is Unknown.
- A top match below the configured confidence threshold is Unknown.
- The threshold lives in config, not in code.

## Store

SQLite behind a small repository interface, so it can be swapped later. Tables: `intents`, `steps`, `outcomes`, `human_queue`. Each commit phase is one transaction.

## Control

The control is the same executor with the reconciler removed and a blind retry on any error. It has no memory across runs (an in-memory store) and no stable key, so each attempt names its branch freshly, under `control/<company_id>-<random>`. A stable branch name would make GitHub reject the second creation, which would test GitHub, not the missing protocol. It runs the same crash points so the duplicate count can be compared. `measure` counts branches and pull requests per company from GitHub for either prefix.

## Hosting

The agent runs on Railway (long-lived container, volume for the SQLite store and evidence). The results page in `web/` is static and is built from `evidence/` by `scripts/build_site.py`.
