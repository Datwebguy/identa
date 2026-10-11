# Submission pack: neatHack

Submission opens Mon 12 Oct 2026, 7:00 PM IST. Planned close 11:55 PM IST (about 18:25 UTC). The final cutoff is announced on Discord. Winners on Fri 16 Oct 2026.

Fill every `[ ]` from real results only. Anything not built stays marked "not built".

## 1. Checklist

| Item | Done |
|---|---|
| Public repo, all commits dated 10 to 12 Oct 2026, owner the only author | [ ] |
| neatlogs: before-and-after comparison with numbers (protocol vs control) | [ ] |
| neatlogs: trace links or screenshots for the crash and recovery runs | [x] (ids in section 3, shown on the results page) |
| Entire: accessible checkpoint link and its ID; `entire status` shows it synced | [ ] |
| A recorded run where the agent recovers from a failed action | [ ] |
| cfo.ai business plan (pricing, costs, revenue, runway) | [ ] |
| Demo video, three minutes or less, covering neatlogs, Entire and cfo.ai (architecture, implementation, runtime, reasoning, result for each); link works | [ ] |
| `hackathon.md` build log up to date | [ ] |
| README has setup and run instructions | [ ] |
| Progress posts on X tagged #neatHack | [ ] |
| Quote post of the official neatlogs submission post (Submit on X button), with team, name, project, public repo and demo link, published (a draft does not count) | [ ] |
| cfo.ai subscription cancelled after the plan is made | [ ] |

Team name: MajorLabs. Project name: Identa.

## 2. Evidence to capture, and when

| When | Capture |
|---|---|
| First end-to-end run | neatlogs trace link, the pull request URL, saved Crustdata responses |
| Each crash point (three) | trace of the crash, trace of the restart, the reconciler verdict, GitHub state after |
| Control runs | trace links, count of duplicate branches and pull requests |
| After the main feature commit | `entire checkpoint list`, `entire checkpoint explain HEAD`, the checkpoint link |
| End | Crustdata credits used (from `GET /account/credits`), tokens and cost per run if a model was called |

Entire checkpoint link format: `https://entire.io/gh/OWNER/REPO/commit/FULL_COMMIT_SHA`.

## 3. Results (fill from runs only)

| Measure | Protocol | Control |
|---|---|---|
| Duplicate pull requests across all crash points | 0 | 1 |
| Time from crash to completed reconciliation | 2.17 s, 2.42 s, 2.59 s (points A, B, C) | n/a |
| Crustdata credits per onboarded company | 2 (18 credits for 9 companies, each enriched once) | 0 additional (saved enrich responses reused) |
| Tokens and cost per run | not applicable: no model was called | not applicable |


### neatlogs traces (project `identa`, workflow `identa`)

Read with the neatlogs command line tool after a device login, saved in `evidence/*-neatlogs-*.json`. Times are UTC, 11 Oct 2026. All report 0 tokens and 0 model cost, because no model is called. The link format is `https://app.neatlogs.com/traces/<trace id>`; the trace id is the proof, and the owner confirmed in the dashboard that traces open at that address.

| Started (UTC) | What | Duration | Spans | Trace id |
|---|---|---|---|---|
| 19:05:56 | First local try, GitHub write blocked | 2.7 s | 8 | `d2498e0a4eb745e7cb31827358f81e88` |
| 20:00:37 | First full run, nine companies | 38.0 s | 47 | `11b6f1d52ad7bf3a53d9e4909fe439e2` |
| 20:03:36 | Accidental re-run, nine refused writes | 12.8 s | 56 | `986064631bf42d5169150915593a7006` |
| 20:04:49 | Protocol crash A, killed process | 1.8 s | 5 | `6102da4c4ecaca50730b67067321f123` |
| 20:04:52 | Protocol crash A, restart (reconciles, resumes) | 26.7 s | 47 | `c826fcf2d513f2b260ad52b4e91fbb1c` |
| 20:06:25 | Protocol crash B, killed process | 3.1 s | 6 | `0c783fd14551662a4d33e74a204f4f55` |
| 20:06:30 | Protocol crash B, restart (reconciles, resumes) | 25.7 s | 46 | `f877205cdaf8f229059fe6ca7d79bbd8` |
| 20:08:06 | Protocol crash C, killed process | 3.9 s | 7 | `de0ed8d916549c09aac676d9ddb12968` |
| 20:08:12 | Protocol crash C, restart (reconciles, finds the open pull request, writes nothing for it) | 24.8 s | 45 | `5913c3580f0269d35155a989dfda6c25` |
| 20:10:55 | Control A, killed process | 2.0 s | 5 | `7d53f9fd951666d9242e47a66f26a6fb` |
| 20:10:59 | Control A, second run (no reconcile) | 26.1 s | 47 | `79ad1399b4689610ddaf174f2a02cdb3` |
| 20:12:25 | Control B, killed process | 2.5 s | 6 | `b8bbf49172344635a3a1b908479c3b91` |
| 20:12:29 | Control B, second run (no reconcile) | 31.4 s | 47 | `79517cfa956569fa88992a83d79a19e6` |
| 20:14:17 | Control C, killed process | 3.6 s | 7 | `4b0db813b9d2ea82b7e003d91f8fefd9` |
| 20:14:22 | Control C, second run (no reconcile) | 26.6 s | 47 | `0ee56ee354d6a8a2c647cc3963db59ac` |

What the spans show (from `evidence/*-neatlogs-spans-*.json`): the crash A restart (47 spans) starts with `get_ref`, `get_file`, `list_prs`, then `put_file` and `open_pr` for the interrupted company before moving on. The crash C restart (45 spans) starts with the same three reads and then writes nothing for that company. Control A's second run (47 spans) starts with `identify` and creates a new branch, with no reads of the old one.

Eight further traces, from 20:45 to 20:53 UTC, belong to the unplanned control C runs and are not used.

## 4. Project description (draft)

**One line:** Identa onboards vendors into a company's register from a list of domains, and after any crash it checks GitHub before acting again, so no vendor is added twice.

**The problem:** an agent that crashes after acting does not know whether the action happened. GitHub documents no idempotency key for creating pull requests or refs, so a blind retry can create a duplicate vendor.

**What it does:** identifies each company with Crustdata, writes the intent first, opens one pull request per vendor, and reconciles by exact branch name after any interruption. Ambiguous cases go to a human.

**Result:** 0 duplicate pull requests for the protocol versus 1 for the control, across 3 crash runs of 9 companies each (the control also left 3 extra branches). Source: saved `identa measure` records in `evidence/`. Control C was also run four more times by accident (redeploys triggered by pushes); each run that reached its crash opened one more duplicate, recorded separately in `evidence/*-audit-register-pull-requests.json`. Traces: see section 3 and the results page.

**Idea credit:** the intent-log and reconciler protocol is adapted from Anchor (Viraj Chogle). This is a new implementation written during the neatHack window. No code from that project is used.

## 5. Video script (three minutes or less)

The rules require the video to cover neatlogs, Entire and cfo.ai explicitly: the architecture, implementation, runtime, reasoning and result for each tool.

| Time | Scene | Show |
|---|---|---|
| 0:00 to 0:15 | The problem | A duplicate vendor pull request from the control run |
| 0:15 to 0:45 | The agent | Domains in, Crustdata identify, intent written, PR opened |
| 0:45 to 1:25 | The crash and recovery | Process killed mid-run, restart, reconciler verdict, GitHub showing one PR |
| 1:25 to 1:55 | neatlogs | Where spans sit in the code, the crash and recovery traces, the before-and-after numbers read back from the traces |
| 1:55 to 2:25 | Entire | How Entire is enabled, the checkpoint for the reconciler change, its Sessions (request and decisions) and Changes |
| 2:25 to 2:50 | cfo.ai | The plan's pricing, costs, revenue and runway, with inputs taken from the measured runs |
| 2:50 to 3:00 | Close | Repo link and what does not work yet |

Show only what was built. Never show a number that is not on a real screen.
