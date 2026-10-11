# Identa: plan to the finish

One ordered guide. Follow the steps in order. Each step says who does it, what to do, and how we know it is done.

**Who:** `YOU` means the owner (account logins, decisions, anything with a key). `ME` means the coding agent.

Dates: submission opens Mon 12 Oct 2026, 7:00 PM IST and closes about 11:55 PM IST. The final cutoff is announced on Discord, so check it there.

---

## Where we are now

| Part | State | Proof |
|---|---|---|
| Agent (identify, enrich, branch, file, pull request) | Works | 9 of 9 companies onboarded on Railway |
| Crash recovery | Works | 3 crash points, 0 duplicate pull requests |
| Control (no reconciler) | Works | 1 duplicate pull request, 3 duplicate branches |
| Results page | Live | https://identa-iota.vercel.app |
| cfo.ai inputs | Written | `docs/CFO_INPUTS.md` |
| neatlogs | SDK works, traces sent | trace links not collected yet |
| Entire | Not started | |
| cfo.ai plan | Not started | |
| Demo video | Not started | |
| Submission on X | Not started | |

Known gaps, also in `hackathon.md`: the `Unknown` verdict has not occurred in a real run, and a tie between two top matches is not sent to human review yet.

---

## Step 1. Three decisions (YOU, 5 minutes)

Reply with an answer to each.

1. **Tie rule.** When two matches share the top confidence, should the company go to human review? Recommended: yes. It affects `cfo.ai` and `amazon.com`.
2. **Entire and authorship.** Entire records which agent wrote the code, in its own refs, not in your commits. Is that acceptable? If yes, I let your push hook skip Entire's refs only. Your branches stay protected.
3. **Extras.** Do you want (a) an hourly schedule so Identa starts by itself, and (b) a short AI-written summary for each human-review case? The model would explain, never decide. (b) needs a `LITELLM_API_KEY`. Both are optional.

Done when: I have your three answers.

---

## Step 2. Entire app on GitHub (YOU, 10 minutes, start now)

Do this first because Entire can take up to an hour to sync.

1. Open https://entire.io/login and choose **Sign in with GitHub**.
2. Authorize the Entire GitHub App.
3. Install the app on `Datwebguy/identa` (Datwebguy account, that repo only).
4. Tell me "Entire app installed".

Done when: `Datwebguy/identa` appears in Entire.

---

## Step 3. Keys (no change)

The owner decided to keep the current keys. They stay in Railway as variables. The Entire work happens in a fresh session (Step 4), which starts without any keys in its history. No key is pasted into that session.

---

## Step 4. Start a fresh session (YOU)

Open a new session for this repo (`Datwebguy/identa`). It starts without any keys in its history. Do not paste any key into it.

Done when: the new session is open. In it, I read `docs/PLAN.md` and continue from Step 5.

---

## Step 5. Entire setup (ME, then you check)

1. I install the Entire command line tool and run `entire enable --agent claude-code`.
2. I commit the setup files it adds (`.entire/settings.json` and the hooks in `.claude/settings.json`).
3. I tell you what was added before pushing.

Done when: `entire status` shows Entire enabled, and the setup commit is on `main`.

---

## Step 6. The commit that matters (ME)

1. I implement the tie rule in the decision code, with unit tests. Two top matches at the same confidence become Unknown and go to the human queue.
2. Lint, type check and tests pass.
3. I commit it linked to the session. When Entire asks, the answer is yes.
4. I push, then run `entire checkpoint list`, `entire checkpoint explain HEAD` and `entire status`.

Done when: a checkpoint exists for that commit and `entire status` shows it synced.

---

## Step 7. The Entire link (ME)

1. I build the link: `https://entire.io/gh/Datwebguy/identa/commit/FULL_COMMIT_SHA`.
2. I check that it opens, and that its **Sessions** and **Changes** tabs show the work.
3. I send you the link and the checkpoint ID, and add both to `docs/SUBMISSION.md`.

Done when: the link opens and shows the session. The repo is public, so the checkpoint is public. That is why Step 3 comes first.

---

## Step 8. Re-run the demo evidence with the tie rule (ME)

1. I re-run the nine domains on Railway with the new rule.
2. I confirm `cfo.ai` and `amazon.com` go to human review, and record the count.
3. This is likely to produce the first real `Unknown` verdict, which we have not yet shown.
4. I update the results page, `README.md` and `hackathon.md` with the new numbers.

Done when: the new numbers are saved in `evidence/` and shown on the results page.

---

## Step 9. neatlogs traces (YOU, with my help)

1. Open https://app.neatlogs.com and the `identa` project.
2. Find the traces for the crash tests (around 20:04, 20:06 and 20:08 UTC on 11 Oct) and for the control runs.
3. Copy each trace link, and send them to me.
4. If you prefer, I use the neatlogs command line instead. That needs one browser approval from you.

Done when: I have links for at least one crash run, its recovery, and one control run. I add them to `docs/SUBMISSION.md`.

---

## Step 10. cfo.ai plan (YOU)

1. Open `docs/CFO_INPUTS.md`. Section 1 and 2 are measured. Section 4 are your decisions.
2. Go to https://cfo.ai/neathacks and enter the inputs yourself.
3. Fill the Railway, Vercel and neatlogs costs from their usage pages.
4. Decide price per vendor, monthly price, number of customers, Crustdata plan after the event, team cost and starting cash. I will not suggest values.
5. Send me the plan link or export.
6. Cancel the cfo.ai subscription in Settings, then Billing, once the plan is saved.

Done when: you have a plan link or export. I add it to `docs/SUBMISSION.md` and the demo script.

---

## Step 11. Optional extras (ME, only if you said yes in Step 1)

- **Schedule:** hourly run on Railway, so Identa starts on its own and reconciles unfinished work.
- **AI summary:** a short explanation for each human-review case, written by a model through LiteLLM. It never changes a decision. Token counts and cost come from the real run.

Done when: one real scheduled run is saved, and the summary appears on a real human-review case.

---

## Step 12. Final documents (ME)

1. `README.md`: the status table matches what actually works, with setup and run steps.
2. `hackathon.md`: dated build log, planned work kept apart from completed work.
3. `docs/SUBMISSION.md`: checklist and results table filled from saved runs only.
4. Demo script updated with the real numbers and links.

Done when: no number in any document lacks a saved run behind it.

---

## Step 13. Demo video (YOU)

Three minutes or less. It must cover neatlogs, Entire and cfo.ai, each with architecture, implementation, runtime, reasoning and result. The scene order is in `docs/SUBMISSION.md`, section 5.

1. Record the crash, the restart, the verdict and the control's duplicate on screen.
2. Show the neatlogs trace, the Entire checkpoint and the cfo.ai plan.
3. End with the repo link and what does not work yet.
4. Upload it somewhere public and check that the link opens.

Done when: the video link opens for someone who is not logged in.

---

## Step 14. Post and submit (YOU)

1. Post progress on X with #neatHack (building in public counts for 15% of the score). Do this before the deadline, not only at the end.
2. On Mon 12 Oct from 7:00 PM IST, use the **Submit on X** button on the official neatlogs submission post.
3. Quote it with: team MajorLabs, project Identa, the public repo link and the demo video link.
4. Publish it. A draft does not count.
5. Early entries get engagement from neatlogs and cfo.ai, so submit early.

Done when: the quote post is published and visible.

---

## Final checks (ME, before you submit)

- All commits are authored and committed by Datwebguy, all dated 10 to 12 October 2026.
- No key, token or `.env` file is in the repo.
- Lint, type check and tests pass.
- The results page matches the saved evidence.
- Every checklist item in `docs/SUBMISSION.md` is either done or marked "not built".

---

## What does not work yet (we say this openly)

- The `Unknown` verdict has not occurred in a real run (this changes after Step 8).
- Copying evidence off the Railway volume runs at about one file per second.
- The control gives each attempt a new branch name, because it has no stable key.
- Unplanned control C runs happened by mistake and are shown separately on the results page.
