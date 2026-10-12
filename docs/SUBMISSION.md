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
| cfo.ai business plan (pricing, costs, revenue, runway) | [x] https://cfo.ai/s/yH49V0HAB1YFq5fX (owner to confirm it opens logged out) |
| Demo video, three minutes or less, covering neatlogs, Entire and cfo.ai (architecture, implementation, runtime, reasoning, result for each); link works | [ ] |
| `hackathon.md` build log up to date | [ ] |
| README has setup and run instructions | [ ] |
| Progress posts on X tagged #neatHack | [ ] |
| Quote post of the official neatlogs submission post (Submit on X button), with team, name, project, public repo and demo link, published (a draft does not count) | [ ] |
| cfo.ai subscription cancelled after the plan is made (after screenshots of the four pages are saved) | [ ] |

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


### cfo.ai plan

Public share link: https://cfo.ai/s/yH49V0HAB1YFq5fX (plan "Identa Business Plan", with Pricing, Costs, Revenue and Runway pages, months 1 to 12). Built in cfo.ai by the owner from the inputs in `docs/CFO_INPUTS.md`, in one message that gave measured costs and the owner's pricing decisions, with no number added by cfo.ai.

Results shown by the plan (calculated by cfo.ai from the inputs, checked by hand): $114 per customer per month, $36 Crustdata cost per customer, 68.42% gross margin before hosting; year one: revenue $19,152, 10,080 vendors, 20,160 credits, Crustdata cost $6,048, hosting $60, surplus after listed costs $13,044; closing cash $16,044 from $3,000 starting cash; about 10.92 hours of vendor processing at the measured 3.9 seconds per vendor. Cash does not reach zero within the 12 months, so the plan claims no exhaustion date. Measured costs (2 credits, $0.30 per credit, no AI or GitHub cost, 3.9 s) come from real runs; the price, customer numbers, hosting, team cost and starting cash are the owner's decisions, not measurements.

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

The rules require the video to cover neatlogs, Entire and cfo.ai explicitly: the architecture, implementation, runtime, reasoning and result for each tool. Every number below comes from a saved run. Items in [brackets] are filled after those steps are done; if one is not done, that scene says so plainly instead.

Record in this order. Keep the results page (https://identa-iota.vercel.app) and the register's pull request list open in two browser tabs.

| Time | Scene | What is on screen | What to say |
|---|---|---|---|
| 0:00 to 0:15 | The problem | The control run's duplicate: two pull requests for the same company in `identavendors` (control C, pull requests #55 and #56) | An agent that crashes after acting does not know whether the action happened. A blind retry made a second pull request for the same vendor. |
| 0:15 to 0:40 | The agent | `domains.csv` with the nine domains, then the first full run's trace: identify, enrich, branch, file, pull request. Pull requests #1 to #9 | Nine real vendors in, nine pull requests out. 2 Crustdata credits per company, 3.9 seconds per company, no model called. |
| 0:40 to 1:15 | Crash and recovery | The results page chart and the three crash cards. Then the register: 9 branches and 9 pull requests for each crash prefix | Killed after the branch, after the file, and after the pull request. Each restart read the branch on GitHub first. 0 duplicates in all three. Control: 1 duplicate pull request and 3 extra branches. Recovery took 2.2 to 2.6 seconds, restart included. |
| 1:15 to 1:50 | neatlogs | The crash A killed trace (5 spans, ends at `create_ref`) next to its restart trace (47 spans, starts with `get_ref`, `get_file`, `list_prs`). Then the control's second run, which starts with `identify` | Architecture: one workflow span per run, a tool span per Crustdata and GitHub call, inputs never recorded. Runtime: the trace proves the order. Result: the restart reads before it writes; the control never reads. 0 tokens, 0 cost. |
| 1:50 to 2:20 | Entire | [The checkpoint link, its Sessions tab (request and decisions) and Changes tab for the tie-rule commit] | Architecture: Entire hooks capture the session and link it to the commit. Implementation: one short session for the tie rule, a tie at the top confidence now goes to a human. Reasoning: the Sessions tab shows the decisions. Result: [what the re-run did with `cfo.ai` and `amazon.com`]. |
| 2:20 to 2:45 | cfo.ai | [The saved plan: pricing, costs, revenue, runway] | Inputs from the runs: 2 credits per vendor, no model cost, no GitHub cost, 3.9 s per vendor. Price, customers and monthly price are the owner's decisions. [What the plan shows.] |
| 2:45 to 3:00 | Close | The results page and the repo link | Built with a coding agent, directed and reviewed by the owner. What does not work yet: the Unknown verdict [had not occurred before the tie-rule run], the control uses a fresh branch name per attempt, and copying evidence off the server is slow. |

Show only what was built. Never show a number that is not on a real screen. Four accidental control C runs happened at 9:45 to 9:53 PM (UTC+1); they are labelled on the results page and are not in the headline numbers.
