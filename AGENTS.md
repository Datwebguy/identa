# Rules for anyone writing code in this repository

These rules apply to every person and every coding tool working on Identa. Read them before the first change.

## 1. Authorship

- The repository owner, Datwebguy, is the only author and the only contributor.
- Every commit is authored and committed as `Datwebguy <princeabel2000@gmail.com>`. Set this as the repo-local git identity before the first commit.
- No commit may carry a co-author line, a session link, a "generated with" line, or the name of any AI model, assistant or tool. The hooks in `.githooks/` block these. Run `scripts/setup-git.sh` once after cloning.
- Never bypass the hooks (no `--no-verify`).

## 2. Hackathon rules (neatHack, 10 to 12 October 2026)

- All code is written during the hackathon window. Nothing written before it goes in.
- Every commit is dated inside the window.
- The project must use neatlogs, Entire and cfo.ai, and keep evidence of all three. See `docs/SUBMISSION.md`.

## 3. Data

- Real data only. No mock endpoints, no sample companies, no invented numbers, no hard-coded responses.
- Company domains come from the team's own input file. Each one is a real company the team intends to onboard.
- Every Crustdata response and every GitHub result used as evidence is saved with a timestamp under `evidence/`.
- Any number in the README, the video or the submission comes from a saved run. If it was not measured, it is not written.

## 4. Secrets

- Keys are read from environment variables only: `CRUSTDATA_API_KEY`, `GITHUB_TOKEN`, `NEATLOGS_API_KEY`, and `LITELLM_API_KEY` if used.
- No key is ever committed, logged, printed, pasted into an agent session or written into a trace.
- The GitHub token is fine-grained, with access only to the vendor-register repository.
- Entire checkpoints in a public repo are public. Do not put secrets in a session that Entire records.

## 5. Behaviour the code must keep

- Write the intent before any external call.
- Never retry an external write from the model. Retries come only from the workflow layer, after the reconciler returns NotApplied.
- Unknown always goes to the human queue. The agent never guesses.
- GitHub file writes run one at a time, never in parallel (GitHub documents that concurrent writes conflict).
- Call `neatlogs.flush()` before every injected crash, and `flush()` then `shutdown()` at normal exit.

## 6. Before every commit

- Lint, typecheck and `pytest` pass.
- The README status table matches what actually works.
- No key, token or `.env` file is staged.

## 7. What not to say

Do not claim anything not shown in a saved run. Do not say "guaranteed", "never fails" or "production ready". Say what was measured, with the number and the run it came from, and say what does not work yet.
