# Handover to the fresh session (11 Oct 2026, about 22:30 UTC)

Read this first. It replaces the older parts of `docs/PLAN.md` (that file still has IST times, which were wrong; the owner is on UTC+1).

## Who and what

- Owner: Datwebguy (`princeabel2000@gmail.com`), team MajorLabs, project Identa, neatHack 10 to 12 Oct 2026. The owner is on UTC+1.
- Identa onboards vendors into a register as one GitHub pull request each, and after a crash checks GitHub before acting again. Code: https://github.com/Datwebguy/identa. Register: https://github.com/Datwebguy/identavendors (**no hyphen**; `identa-vendors` does not exist).
- Results page (Vercel): https://identa-iota.vercel.app

## Rules that never change

- Read `AGENTS.md` first. Every commit is authored and committed as `Datwebguy <princeabel2000@gmail.com>`. Run `scripts/setup-git.sh` and set the repo-local identity before the first commit.
- Commit messages are plain. The hook blocks any message with a tool or assistant name, "generated with", or trailers such as co-author or session lines. The `Entire-Checkpoint` trailer is expected. Never use `--no-verify`. If a hook blocks a commit, fix the commit. If Entire's own data trips a hook, stop and ask the owner.
- Real data only. No mock, sample or invented numbers. Any number written anywhere comes from a saved run under `evidence/`.
- No key or token is ever written into the repo, a commit message, a log or this session. Do not ask the owner to paste a key. This session is recorded by Entire and checkpoints in a public repo are public.
- Do **not** close, delete or change any existing pull request or branch in the register without asking the owner first.
- Only fast-forward `main` (`git push origin <branch>:main`). No force-push, no merge commits, no pull requests unless asked.
- Plain, professional wording in anything a user reads.

## What is done (all on `main`)

- Agent: identify, enrich, branch, file, pull request, reconciler with verdicts Applied, NotApplied, Resume, Unknown; SQLite intent store; human queue; control run; `measure`; `export-evidence`.
- First full run on Railway: 9 of 9 companies onboarded, pull requests #1 to #9, 0 duplicates. Crustdata: 2 credits per company, balance 5,182 afterwards and unchanged since.
- Crash tests on Railway (prefixes `crash-a`, `crash-b`, `crash-c`): 9 branches and 9 pull requests each, 0 duplicates, recovery 2.17 s, 2.42 s, 2.59 s. Control (`control-a`, `-b`, `-c`): 1 duplicate pull request and 3 duplicate branches in total.
- Accidental control C runs at 20:45 to 20:53 UTC: 36 branches and 35 pull requests (#65 to #99). Recorded in `hackathon.md`, kept out of the headline numbers, labelled on the results page. Nothing was closed or changed.
- neatlogs: 23 traces with workflow `identa`, read with the neatlogs command line tool and saved in `evidence/` (ids in `docs/SUBMISSION.md`). Not available in this session: the CLI login was temporary.
- cfo.ai inputs written: `docs/CFO_INPUTS.md`. The owner enters them in cfo.ai and shares the plan.
- Railway agent is idle: variables are `IDENTA_ARGS=queue list --config identa.railway.toml`, `IDENTA_EXPORT=0`, `IDENTA_FRESH_STORE=0`; Railway only redeploys on changes to `src/**`, `Dockerfile`, `scripts/railway_entry.sh`, `identa.railway.toml`, `domains.csv`, `pyproject.toml`.

## The owner's decisions

1. Tie rule: **yes**. When another match has the same confidence as the top match, the company goes to the human queue as Unknown. Seen for `cfo.ai` and `amazon.com`.
2. Entire: **option A**, one short session for the tie-rule work. Confirm the integration name by checking the Entire docs or `entire enable --help` before enabling; do not assume. The docs list `claude-code`.
3. Hourly schedule: **yes, after the required items**. A scheduled run must make no enrich calls and open no pull requests for companies already onboarded, so it spends no credits (the store must persist, so `IDENTA_FRESH_STORE` must be 0). AI summary: only if time remains, and only to explain a human-review case, never to decide.
4. Keys stay as they are, no rotation. That is why this session must stay free of keys.

## Your tasks, in order

1. **Entire setup.** Install the CLI (`curl -fsSL https://entire.io/install.sh | bash`), confirm the agent name, run `entire enable --agent <name>`, and show the owner every file it adds (`.entire/settings.json`, hooks in `.claude/settings.json`) before pushing. Commit the setup with a plain message.
2. **The tie-rule commit** (this is the checkpoint commit, so it must be real code):
   - `Crustdata._parse` in `src/identa/crustdata.py` keeps only the top match. Record whether a second match has the same `confidence_score` as the top.
   - `decide_identity` in `src/identa/workflow.py` returns a reason such as "tie at top confidence" so the company goes to the human queue.
   - Unit tests use small literal inputs for the pure function only. Lint (`ruff check .`, `ruff format --check .`), `mypy src tests scripts/build_site.py` and `pytest` must pass.
   - Commit linked to the session (answer yes when Entire asks). Then run `entire checkpoint list`, `entire checkpoint explain HEAD`, `entire status`.
3. **Checkpoint link** for the owner: `https://entire.io/gh/Datwebguy/identa/commit/FULL_COMMIT_SHA` and the checkpoint ID. Check the link opens and that Sessions and Changes show the work. Add both to `docs/SUBMISSION.md`. The Entire GitHub app is installed on `Datwebguy/identa`; sync can take up to an hour.
4. **Re-run plan, and wait for the owner's go-ahead before running.** Tell the owner: existing pull requests #7 (cfo.ai) and #9 (Amazon) stay untouched. On Railway, with prefix `vendor` and a fresh store, the seven unambiguous companies are refused by GitHub (branch exists) and the reconciler records them Applied with no new writes. `cfo.ai` and `amazon.com` stop at the tie rule and go to the human queue as Unknown with no GitHub calls. The owner then decides each one; accepting records the existing pull request through the same reconcile path and creates no new one; rejecting only marks the local queue.
5. After approval: set the Railway variables for that run (`IDENTA_ARGS=run --config identa.railway.toml --domains domains.csv`, `IDENTA_FRESH_STORE=1`, `IDENTA_EXPORT=1`), redeploy, check logs, count with `identa measure`, then **set the variables back** to the read-only values above so later pushes do not start runs. Update `evidence/`, the results page, `README.md`, `hackathon.md`.
6. Hourly schedule on Railway (cron), then test it: balance of credits before and after must be unchanged and no new pull request may appear.
7. Update `docs/SUBMISSION.md`, the demo script (section 5) and the README status table with only what was measured. Add the cfo.ai plan link once the owner shares it.

## Tools and IDs (not secrets)

- Railway project `e77616b7-e3ed-46a4-89b2-5aefab32f4ba`, service `agent` `815de6c4-710f-424a-868a-b90ded43bd75`, environment `e1e8a4b7-6058-45a2-81d6-bbb9f2b3d901`, volume `/data`. Keys are Railway variables; never read or print them.
- Vercel team `team_GmFSWykUB2dgrQ1lSOS5uPax`, project `prj_tKvUZ62esHIDzRLCROw4ru4QSbT7`. Push-triggered deploys have been unreliable: after changing `web/`, run `python scripts/build_site.py`, commit, push, then create a production deployment for the pushed commit with the Vercel tool.
- Local checks: `python -m venv .venv && . .venv/bin/activate && pip install -e '.[dev]'`. `scripts/build_site.py` builds `web/data.json` from `evidence/`.
- This session's network blocks GitHub REST writes, so runs happen on Railway. Reads (`identa measure`) may work if `GITHUB_TOKEN` is in the environment.

## Open items for the owner

- cfo.ai plan: the owner enters the inputs and shares the link or export.
- Confirm one trace link on the results page opens (format `https://app.neatlogs.com/traces/<trace id>`).
- Demo video (three minutes or less, covering neatlogs, Entire and cfo.ai), progress posts on X with #neatHack, and the quote post on the official neatlogs submission post from 12 Oct 7:00 PM IST (13:30 UTC). The planned close is about 18:25 UTC; the final cutoff is announced on Discord.

## Known gaps to state openly

- The `Unknown` verdict has not occurred in a real run yet (the tie-rule re-run should produce it).
- The control gives each attempt a new branch name, because it has no stable key.
- Copying evidence off the Railway volume runs at about one file per second.
