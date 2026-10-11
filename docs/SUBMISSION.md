# Submission pack: neatHack

Submission opens Mon 12 Oct 2026, 7:00 PM IST. Planned close 11:55 PM IST (about 18:25 UTC). The final cutoff is announced on Discord. Winners on Fri 16 Oct 2026.

Fill every `[ ]` from real results only. Anything not built stays marked "not built".

## 1. Checklist

| Item | Done |
|---|---|
| Public repo, all commits dated 10 to 12 Oct 2026, owner the only author | [ ] |
| neatlogs: before-and-after comparison with numbers (protocol vs control) | [ ] |
| neatlogs: trace links or screenshots for the crash and recovery runs | [ ] |
| Entire: accessible checkpoint link and its ID | [ ] |
| A recorded run where the agent recovers from a failed action | [ ] |
| cfo.ai business plan (pricing, costs, revenue, runway) | [ ] |
| Demo video, 2 to 3 minutes, link works | [ ] |
| Progress posts on X tagged #neatHack | [ ] |
| Quote post of the official neatlogs post with team, project, repo and video | [ ] |
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
| Duplicate pull requests across all crash points | [ ] | [ ] |
| Time from crash to completed reconciliation | [ ] | n/a |
| Crustdata credits per onboarded company | [ ] | [ ] |
| Tokens and cost per run | [ ] | [ ] |

## 4. Project description (draft)

**One line:** Identa onboards vendors into a company's register from a list of domains, and after any crash it checks GitHub before acting again, so no vendor is added twice.

**The problem:** an agent that crashes after acting does not know whether the action happened. GitHub documents no idempotency key for creating pull requests or refs, so a blind retry can create a duplicate vendor.

**What it does:** identifies each company with Crustdata, writes the intent first, opens one pull request per vendor, and reconciles by exact branch name after any interruption. Ambiguous cases go to a human.

**Result:** [protocol duplicates] versus [control duplicates] across [n] crash runs. Traces: [links].

**Idea credit:** the intent-log and reconciler protocol is adapted from Anchor (Viraj Chogle). This is a new implementation written during the neatHack window. No code from that project is used.

## 5. Video script (2:00 to 3:00)

| Time | Scene | Show |
|---|---|---|
| 0:00 to 0:20 | The problem | A duplicate vendor pull request from the control run |
| 0:20 to 0:50 | The run | Domains in, Crustdata identify, intent written, PR opened, neatlogs trace on screen |
| 0:50 to 1:40 | The crash | Process killed mid-run, restart, reconciler verdict, GitHub showing one PR |
| 1:40 to 2:10 | The numbers | Protocol versus control from the saved runs |
| 2:10 to 2:40 | The tools | Entire checkpoint, cfo.ai plan |

Show only what was built. Never show a number that is not on a real screen.
