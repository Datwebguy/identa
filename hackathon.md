# neatHack build log

Kept as the official neatHack build-log skill asks (https://neatlogs.com/hackathon/skill). Planned work and completed work are kept apart. Only tests that actually ran are recorded.

## Project

Identa: an agent that onboards vendors into a company's vendor register from a list of domains, and after any crash checks GitHub before acting again, so no vendor is added twice.

## Team

MajorLabs. Datwebguy.

## Stack

Python 3.11, Crustdata (identify, enrich), the GitHub REST API, SQLite, neatlogs, Entire, cfo.ai. Railway runs the agent; Vercel serves the results page and the read-only company check.

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
- Crash tests (Railway, 11 Oct 2026, 9 companies each, fresh store, crash exits the process with code 137 once, Railway restarts it, the restart reconciles first):
  - A, crash after the branch is created: 1 recovered, 8 onboarded; 9 branches, 9 pull requests, 0 duplicates.
  - B, crash after the file is committed: 1 recovered, 8 onboarded; 9 branches, 9 pull requests, 0 duplicates.
  - C, crash after the pull request is opened: 1 recovered, 8 onboarded; 9 branches, 9 pull requests, 0 duplicates.
- Control (same executor, no reconciler, no memory, blind retry, a fresh branch name per attempt, up to 3 attempts per company; the retry limit was not reached because each run crashes once): A: 10 branches, 9 pull requests; B: 10 branches, 9 pull requests; C: 10 branches, 10 pull requests. Duplicates: 1 pull request and 3 branches across the three points.
- Crustdata balance after all crash tests and control runs: 5182, unchanged, because saved enrich responses were reused.
- Time from the saved crash-step record to the reconciler's last check finishing, from evidence timestamps (includes the container restart): A 2.17 s, B 2.42 s, C 2.59 s.
- Limits of these tests: the crash fires at the first company only, so each test is one crash among nine companies. The control gives each attempt a new branch name, because it has no stable key; with a stable name GitHub would reject the second branch. The `Unknown` verdict has not occurred in a real run.
- Done: results page deployed to Vercel (project `identa`, linked to this repo, production branch `main`): https://identa-iota.vercel.app . The agent runs on Railway (project `identa`, service `agent`, volume at `/data`).
- Done: results page redesigned (light and dark themes with a toggle, glass panels, protocol versus control chart, per crash point cards, reconciliations, vendor register). Every number on it is computed from `evidence/` by `scripts/build_site.py`, including the reconciliation times (crash or re-run is detected from the saved records).
- Found in the evidence: a push to `main` at about 20:02 UTC made Railway redeploy with the `vendor` prefix and a fresh store before the crash tests. GitHub refused all 9 branch creations (422, already exists), the reconciler found branch, file and pull request for each and recorded Applied, with no new vendor writes. The `vendor` count stayed at 9 branches and 9 pull requests.
- Mistake, recorded as found (about 02:15 to 02:23 IST on 12 Oct, 20:45 to 20:53 UTC on 11 Oct): every push to `main` redeployed the Railway agent, which was still configured for control C, so four pushes started four unplanned control C runs. What they created in `Datwebguy/identavendors`: 36 branches under `control-c/` and 35 pull requests, #65 to #99. One of the 36 branches has no pull request (`control-c/6034577-45a40c52`), because that run was stopped before opening it. Two runs were stopped part-way by the next deploy. Each of the four opened a second pull request for the first company, so `control-c` holds 45 pull requests in total (10 from the planned run, 35 unplanned). None of these was closed, deleted or changed. They are kept out of the headline numbers, which come from the measurement saved right after each planned run, and the results page lists them separately. Fix: the agent's variables are now a read-only command, and Railway redeploys only when agent code changes (watch paths). Source: `evidence/20261011T205609731739Z-audit-register-pull-requests.json`.
- Found in the neatlogs project (screenshot from the owner, 11 Oct, 10:41 PM local time = 21:41 UTC): 11,258 traces, all ingested within the same minute, so something was still sending traces long after the planned runs. Likely cause: the evidence export after each run makes thousands of small GitHub calls, and the container started at 20:53 UTC was still working through them. Fix: export is skipped when `IDENTA_EXPORT=0` (set on Railway), and the `measure`, `export-evidence` and `queue` commands no longer send traces. Not yet confirmed from the traces themselves.
- Correction: the owner's local time is UTC+1 (West Africa), not IST. Times given earlier in IST were wrong for finding traces; use UTC or UTC+1.
- Done: neatlogs traces read with the neatlogs command line tool (device login with the protected-file fallback, because the server has no keychain). 23 traces carry workflow `identa`: each crash test has a short trace for the killed process and a longer one for the restart, and the span order matches the evidence (restart reads the branch first). Saved in `evidence/`; ids are in the README.
- Done: cfo.ai business plan built by the owner in one message (measured costs plus the owner's pricing decisions); share link https://cfo.ai/s/yH49V0HAB1YFq5fX. Figures re-checked by hand: $114 per customer per month, $36 Crustdata, 68.42% margin, year one revenue $19,152, surplus $13,044, closing cash $16,044. Crustdata credit price $0.30 confirmed from the owner's billing page (balance $1,554.60 for 5,182 credits).
- Entire, in order: (1) a session started before Entire's hooks existed never recorded, so its tie-rule commit had no checkpoint; (2) attaching that session created checkpoint `01M4Q4K1B9YEFGAWS11NTY4X2B`, but it is stored as a custom ref and this environment's git proxy refuses to push custom refs (HTTP 403), so it never reached GitHub; (3) the CLI was installed by the environment's setup script (v0.9.0, checksum verified), branch storage was set in the tracked `.entire/settings.json`, and a third session recorded from its start. Result: commit `c480cd0e850fefd116118c5ecd8b0307f8ce86da` with `Entire-Checkpoint: d0ace3cc5007`, checkpoint data on `entire/checkpoints/v1`. The link https://entire.io/gh/Datwebguy/identa/commit/c480cd0e850fefd116118c5ecd8b0307f8ce86da returned 404 to an unauthenticated fetch right after the push; the owner is checking it signed in. The tie-rule commit `2dd58e6` and the tied-candidates commit `f49158f` have no checkpoint.
- Entire dashboard: the repository first showed a 404 and then a 500 error. Cause: the Entire GitHub app was installed (all repositories) but the repository had not been mirrored in Entire. After the owner mirrored only `Datwebguy/identa` (European Union region; Entire had pre-selected 10 repositories and the owner cleared the others), the session appears under Sessions: "Record Crustdata Credits per Run", 1 checkpoint, 3 file changes (+32 / −3), 4.8K tokens, commit `c480cd0`. The session page shows the full request and decisions.
- Fixed: the first commit of `entire/checkpoints/v1` was authored by an assistant identity (made by Entire's CLI before the repo identity was set). The branch was rewritten so both commits are authored and committed by Datwebguy, with identical files, messages and dates; the force-push was limited to that one branch with a lease. Verified from a separate clone: 46 commits across `main` and that branch, all Datwebguy.
- (older note) Found while checking: the first commit of `entire/checkpoints/v1` ("Initialize metadata ref", `0e794ce`) is authored by `Claude <noreply@anthropic.com>`, made by Entire's CLI before the repo identity was set in that container. `main` has only Datwebguy commits. Decision pending with the owner.
- Re-run with the tie rule (Railway, 12 Oct 2026, 05:02 UTC, fresh store, prefix `vendor`): onboarded 0, queued for human review 2, recovered 7, failed 0. Crustdata credits spent: 0 (balance 5182 before and after), the first measurement from the new per-run credit record. Checked on GitHub afterwards: 99 pull requests in total (unchanged), the nine `vendor` pull requests are still #1 to #9, nothing was closed, deleted or changed. The two held companies are `cfo.ai` and `amazon.com` (each had two matches at confidence 1.0).
- Found and stopped: the evidence copy off the volume recorded each of its own GitHub calls as new evidence and then tried to copy those too. The evidence branch grew from about 2,000 to 5,225 files, and it is also what flooded neatlogs with small traces earlier. Stopped by setting `IDENTA_EXPORT=0`. Fix: the copy no longer records its own calls, it copies only files from a given start time (`--since`), and it only runs when `IDENTA_EXPORT_SINCE` is set.
- Results page wording: the owner pointed out developer wording on the page. Rewritten in plain words (protocol and control became "with Identa" and "without the check"; reconcile, verdict names, hashes, branch names, spans, company IDs and the call-by-call evidence table were removed or replaced). The repository docs keep the technical terms.
- Logo: a mark with no letters, two overlapping rings (two attempts) around one glowing shape (the single vendor record). Files in `web/`: `logo.svg`, `favicon.svg`, `favicon-32.png`, `apple-touch-icon.png`, `logo-512.png`, and `og.png` (the link-preview card used when the page is shared). Used as the page logo, the favicon and the README header.
- Not done yet: Entire link check, demo video, submission post, cancelling the cfo.ai subscription. (neatlogs trace links and the cfo.ai plan are done.), Entire, cfo.ai, demo video.
- Tests run: `pytest` on `tests/`, 36 passed (pure functions only: keys, verdicts, store, parsers, identity decision). No real API call has been made. Nothing else has run.

- 12 Oct, 05:41 to 05:45 UTC: race test, added after studying another team's public project (Anchor) that measures "many agents, one action". New command `identa race`. Eight copies of the program, each with its own memory and GitHub connection, started together on `github.com`. With Identa (`race-a`): 1 branch, 1 pull request, 0 duplicates; GitHub accepted 1 branch request and refused 7. Without the check (`race-b`): 8 branches, 8 pull requests, 7 duplicates. The seven losing Identa copies ended as `failed` (their file writes were refused with one 409 and six 422); nothing resumes them later because their memory is in-process. Two Railway builds started together (push and variable change); the older one was removed before it ran, so one race ran per prefix. The 8 extra pull requests in `race-b` and the 1 in `race-a` were left open. No unit test covers `identa race`: it needs a live GitHub; the real runs are the evidence.

- 12 Oct: Entire is switched off in the repo (`.entire/settings.json`, `enabled: false`) by the owner's decision, so later work is not recorded as Entire sessions. The checkpoint `d0ace3cc5007` for the tie-rule commit is unchanged. The attribution checks in `.githooks/` stay on.

- 12 Oct, pre-launch checks: scanned the working tree and every git ref for keys (none found; the local `.env` is git-ignored and was never committed). Found and fixed a sideways scroll on narrow phones (the three crash-test cards and the header pill pushed the page to 353 px at 320 px wide); now exactly as wide as the screen at 320, 360, 412, 768 and 1280 px. Under a throttled phone profile (4x slower CPU, slow network) the page loaded in 4.0 s and showed its data in 4.3 s; the page is 36 KB and its data 23 KB, so most of that is network delay (not retested after this change). Added a 404 page, a short privacy page, security headers (`nosniff`, no framing, referrer policy), a contact link (GitHub issues) and a rollback plan (now in the README under Hosting). Not applicable because the project has none of them: sign-up, payment, password reset, email, user database, visitor-triggered routes. No spending cap is possible on the Crustdata key; the balance is 5,182 credits and a run costs 2 credits per new company.

- 12 Oct: added a read-only company check to the results page (`api/identify.js`) after looking at another team's public page (FirstRun doc-audit) that lets visitors run its tool. It calls Crustdata identify (free) and applies the same rule as the agent (threshold 0.9, tie goes to a person). It writes nothing to GitHub and saves nothing. Limits are best-effort in memory: 5 checks per minute per address and 20 per minute in total per server instance. Four small node tests cover the rule (`node --test tests/identify.test.js`, 4 passed). It needs `CRUSTDATA_API_KEY` set in Vercel; until then the page says the live check is not switched on. Added a "Run it yourself" command to the page. Not yet verified against live Crustdata data.

- 12 Oct: page changes after studying two more public projects (FirstRun doc-audit and TruthOps). Added a "Skip to the results" link, a short "who it is for" line, a one-line limits banner near the top with a full "What does not work yet" section, a "See the saved records" link on every headline tile, and a table of the exact evidence file behind each measurement (9 files, all checked to exist). Checked at 320, 360 and 1280 px: no sideways scroll, no script errors. TruthOps's page, as far as its text could be read, is driven by recorded fixtures; Identa's numbers come from saved live runs.

- 12 Oct, 06:12 UTC: tested the live company check after the key was set in Vercel. `github.com` returned accept (company 632750, confidence 1); `amazon.com` returned hold with the same two tied candidates the agent found; a malformed domain returned 400. Records: `evidence/*-vercel-check-*.json`. Correction to the entry above: the per-address limit did not work. Eight quick requests all returned 200 (intended limit 5 per minute), because each request can run on a different server instance. The page now says the limit is not enforced. The check is free (identify costs no credits) but shares the 30-per-minute lookup limit with the agent.

- 12 Oct, 06:22 UTC: signed in to neatlogs with write access (owner approved a device code) and created one custom detection in project `identa`: "Killed process" (status = ERROR on spans named `identa`, the root span a stopped process leaves). It has 0 hits so far: it scores new traces only, and my four attempts to backfill the older traces were rejected (`INVALID_ARGUMENTS`, request body shape unknown). The other two planned detections, "GitHub write refused" and "Recovery run", were not created, because I could not find the field names for matching a refused write or a recovery. Record: `evidence/*-neatlogs-detection-created.json`.

- 12 Oct: removed the "What does not work yet" section and the banner from the results page: the owner objected to its developer wording and to listing weaknesses on the front page. The same limits stay in the README and this log.

- 12 Oct: read every visible word of the live results page, privacy page and 404 page for developer wording. Removed the "Run it yourself" block (it is in the README), changed "open an issue" to "contact us on GitHub", reworded the privacy page in plain terms, and fixed "1 branches" in the records table. Found and fixed a sideways scroll on phones when the records table was opened (764 px wide at a 360 px screen); now exact at 320, 360, 412 and 1280 px, open or closed. The page still has the section "A mistake of ours, shown openly" about the accidental repeats; it is the one remaining place that lists a failure.

- 12 Oct: a visitor tried `joinopenstock.xyz` in the company check and got "Hold for a person: no match". Checked directly with Crustdata identify (free), with and without exact match: both returned an empty match list, so the answer was correct. The check now explains each reason in plain words.

- 12 Oct: moved the evidence for each tool and the idea credit out of the README into this log, because the README is public and should read as a product page. Removed every Markdown file except `README.md` and `hackathon.md` (the hackathon asks for both): the working notes, plan, build spec, handover, resource list, submission draft, architecture note, rollback plan, `AGENTS.md`, `CHANGELOG.md` and `SECURITY.md`. What a reader needs from them is now in the README: how it works, results, evidence for each tool (trace ids, Entire checkpoint, cfo.ai plan) and hosting. The files stay in git history.

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

## Credit

The approach of writing down what you are about to do, and checking before you retry, is adapted from Anchor by Viraj Chogle. No code from it is used.

## Demo

Results page: https://identa-iota.vercel.app. The demo video link will be added here when it is published.

## Known limitations and next steps

- The human review queue is a command line queue, not a web page.
- In the race test, 7 of 8 copies stopped without finishing because GitHub refused their writes. Their memory lives inside each process, so nothing resumes them later.
- The comparison without the check gives every attempt a new branch name, because it has no stable key. That is why it duplicates.
- Only one commit, the tie-rule work, has an Entire checkpoint.
- The company check on the results page has a per-address limit in its code, but a saved test showed it does not stop quick repeated requests (each request can run on a different server instance), so it is not enforced. The lookup is free but shares Crustdata's 30-per-minute identify limit with the agent.
- Four accidental repeats of one comparison test are listed separately on the results page and are not counted in any headline number.
- No language model is used, so there are no AI summaries of held cases. An hourly schedule is not built.

## Submission

Team MajorLabs, project Identa. Public repository: https://github.com/Datwebguy/identa. Evidence for each tool is listed above under "Evidence for each tool".
