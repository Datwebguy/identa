# Identa: build spec for neatHack

Hackathon: neatHack (neatlogs x TheVibeFounder), online, 10–12 Oct 2026. 48 hours. The hackathon page gives the start as Sat 10 Oct, 12:30 PM IST; the Luma event lists 12:30 AM IST. All code must be written between the start and the deadline.
Submission window: Mon 12 Oct 2026, 7:00 PM IST to about 11:55 PM IST (about 18:25 UTC). The final cutoff is announced on Discord.
Winners: Fri 16 Oct 2026.

## 1. The problem

An agent that takes a real action on an outside system and then crashes, times out or gets an error does not know whether the action happened. If it retries, the action can happen twice.

For vendor onboarding this creates duplicate vendor records. A vendor added twice means two payables, two contracts and two sets of approvals.

Verified in the GitHub REST documentation (checked 11 Oct 2026):
- Creating a pull request (`POST /repos/{owner}/{repo}/pulls`) documents no idempotency key. Creating a git reference (`POST /repos/{owner}/{repo}/git/refs`) documents none either.
- The documentation does not give an error for "a pull request already exists for this head and base". So a retry cannot rely on GitHub to refuse the duplicate.
- Getting a single reference (`GET /repos/{owner}/{repo}/git/ref/heads/<branch>`) returns 200 if the branch exists and 404 if it doesn't. That is a precise, documented existence check.

## 2. The solution

A vendor-onboarding agent. It takes a list of company domains and adds each company to a vendor register as a pull request in a GitHub repository.

Every action has a stable identity. The branch name is built from the company's Crustdata ID and a hash of the intent, so the same company and intent always produce the same name. A reconciler looks up that exact name before deciding anything. A retry therefore cannot create a second record silently.

The protocol, in three phases:
1. Intend: write the intent (action, company ID, branch name, planned steps) to a local store before touching GitHub.
2. Act: create the branch, commit the vendor file, open the pull request. Each step is logged as its own intent, so a crash between steps is recoverable.
3. Commit: record the outcome and the memory row together in one local transaction.

If the process dies between acting and committing, the reconciler checks the external system by name and returns one of three verdicts:
- Applied: the branch and pull request exist and match this intent. The local record is completed.
- NotApplied: the branch does not exist. Safe to act again.
- Unknown: the check failed or the state is ambiguous. The intent goes to a human approve or reject queue. The agent never guesses.

Idea credit: the protocol is adapted from Anchor (Viraj Chogle, CockroachDB x AWS Agentic Memory hackathon, 2026). This is a new implementation written during the neatHack window. No code from that project is used.

## 3. What the agent does, step by step

Input: a CSV of company domains supplied by the team. Each domain must be a real company the team actually intends to onboard. No invented or sample companies.

1. Identify each domain with Crustdata `POST https://api.crustdata.com/company/identify`, body `{"domains": [...], "exact_match": true}`. Identify is free. The response is a top-level array with `matches[].confidence_score` and `matches[].company_data.crustdata_company_id`.
2. Decide: a no-match input comes back as an entry with an empty `matches` array. If `matches` is empty, or the top confidence is below the threshold set in config, the domain goes to the human queue as Unknown. The threshold is a config value, not a hard-coded number.
3. Enrich approved companies with Crustdata `POST https://api.crustdata.com/company/enrich`, body `{"crustdata_company_ids": [id], "fields": ["basic_info", "headcount"]}`. Enrich costs 2 credits per record, and 2 more if technographics are requested (not requested here).
4. Plan: for each approved company, build the intent with idempotency key `sha256(company_id, action, canonical_json(args))`, where `args` includes the company's canonical name and domain.
5. Act on GitHub, in order, each step logged:
   a. Read the base branch SHA: `GET /repos/{owner}/{repo}/git/ref/heads/main`.
   b. Create the branch `vendor/<crustdata_company_id>-<first 8 hex of the key>`: `POST /repos/{owner}/{repo}/git/refs` with `ref` set to `refs/heads/<branch>` and `sha` set to the base SHA.
   c. Commit `vendors/<crustdata_company_id>.yaml` to that branch with `PUT /repos/{owner}/{repo}/contents/{path}` (body: `message`, Base64 `content`, `branch`; 201 on create). GitHub's documentation says concurrent requests to the create/update/delete file endpoints conflict and must be made serially, so the agent runs one company at a time through this step and never in parallel.
   d. Open the pull request: `POST /repos/{owner}/{repo}/pulls` with `head` set to the branch and `base` set to `main`.
6. Commit the outcome locally: the intent state, the pull request URL, and the memory row, in one transaction.
7. Reconcile on start and after any interrupted run: for each lapsed intent, `GET .../git/ref/heads/<branch>`. 404 means NotApplied. 200 means check the pull request and mark Applied if it matches. Any other result is Unknown.

## 4. Crash test and control (this is the recovery evidence)

Test points, each run as a real process killed with a real exit:
- after the branch is created, before the file is committed
- after the file is committed, before the pull request is opened
- after the pull request is opened, before the local commit

Each crash is followed by a restart and reconciliation. The check is: exactly one branch and one pull request per company, with the local record matching GitHub.

Control: the same code with the reconcile step removed and a retry on any error. Run the same crash points and count duplicate branches and pull requests.

Measure, from the runs (do not write any number before measuring it):
- duplicate pull requests, protocol versus control, across all crash points
- time from crash to completed reconciliation
- Crustdata credits used per onboarded company
- tokens and cost per run, if a model is called

neatlogs notes: "Ending a process does not guarantee that its final batch was sent. A flush waits for buffered logs and spans to be handed to the exporter." Call `neatlogs.flush()` before each injected crash, or the crash runs will be missing from the traces.

## 5. The three required tools

neatlogs (tracing)
- Install: `pip install -U neatlogs`. Python 3.10 to 3.13 (from the PyPI metadata, version 1.4.26).
- Account: sign up at https://app.neatlogs.com in a browser (a coding agent cannot do this step), create the project, then copy the **Project API key** from Settings, then API keys. Do not use the HTTP ingest key that starts with `nlw_`: the SDK returns 401 with it.
- Start: `neatlogs.init(api_key=os.environ["NEATLOGS_API_KEY"], workflow_name="identa")`. If a model is called through LiteLLM (OpenAI-compatible), wrap the client with `neatlogs.wrap(OpenAI(...))` so model calls, tokens and cost are traced.
- Span kinds used: WORKFLOW for each run, AGENT for the planner, TOOL for each Crustdata and GitHub call. Span kinds are documented as WORKFLOW, AGENT, CHAIN, MCP_TOOL, LLM and TOOL.
- Shutdown: `neatlogs.flush()` then `neatlogs.shutdown()` at script exit, as documented.
- Local check before any backend use: `python -m neatlogs doctor --local --json`. It makes no backend request. Then `python -m neatlogs doctor --probe`: it sends a test trace and reads it back; `TRACE_VISIBLE` and `TRACE_FINALIZED` must both show PASS.
- Reading traces back for the before-and-after numbers: the CLI is a separate package, `npm install --global neatlogs-cli@0.2.0` (Node.js 22 or 24). `neatlogs profile set work --host 'https://app.neatlogs.com'`, `neatlogs profile use work`, `neatlogs auth login --device` (the owner approves the link in a browser), then `neatlogs traces list --limit 5` and `neatlogs traces get '<trace-id>' --json`. Service-account tokens need an org admin; use the device login.
- Integration guidance: the setup guide's coding-agent prompt at https://neatlogs.com/hackathon/neatlogs-setup-guide.html, the docs index https://docs.neatlogs.com/llms.txt and the skills at https://github.com/neatlogs/skills.
- Free paid-plan access during the event (from the organisers' setup email).

Entire (checkpoints and code history)
- Follow the organisers' guide: https://hack.entire.io/neathacks-2026/
- Connect the repo: sign in to Entire with GitHub and install the Entire GitHub App on the account that owns `Datwebguy/identa`. The repo only appears after that, and sync can take up to an hour.
- Install the CLI (macOS: `brew install --cask entireio/tap/entire`; other platforms in the Entire quickstart), then in the repo run `entire enable --agent <name>`. The guide's example uses `codex`; use the integration name of the coding agent that writes the code.
- Make a commit linked to the agent session (answer yes when asked to link the commit to session context), then `entire checkpoint list`, `entire checkpoint explain HEAD`, and `entire status` to confirm the checkpoint synced.
- Submission needs an accessible checkpoint link and its ID. The link format from the guide is `https://entire.io/gh/OWNER/REPO/commit/FULL_COMMIT_SHA`. In Entire, open repository, branch, commit, checkpoint, and show Sessions (the request and decisions) and Changes (the implementation).
- Checkpoints in a public repo are public. Do not put secrets in a session.
- Separate prize: "Best Use of Entire", for the most creative use of Checkpoints, Graph or Brain.
- Optional: entire-graph (`entire plugin install graph`, then `entire graph init-agents --repo .`, which adds a block to `AGENTS.md` and `CLAUDE.md`; review it before committing) and entire-brain. Trails is behind a feature flag and needs an access request. Use these only if they help the build.

cfo.ai (business plan)
- Sign up through https://cfo.ai/neathacks. A card is required. Cancel the subscription in Settings, then Billing, straight away. The organisers provide the credits.
- The cfo.ai documentation I could read does not describe the business-plan inputs. Confirm what the plan asks for after signing up. Do not model pricing from numbers that were not measured in the runs.
- Inputs from measured data: Crustdata credits per onboarded company, tokens and cost per run, and GitHub and hosting costs.

## 6. Credits and limits

Crustdata (5,000 credits, promo code NEATLOGS-OCT2026, claimed on the account):
- Identify: free. Enrich: 2 credits per record. Search: 0.03 per result (not used).
- At 2 credits per enrichment, 5,000 credits cover up to 2,500 enrichments before any other use. Check the balance with `GET https://api.crustdata.com/account/credits` (same two headers). Requests without `x-api-version: 2025-11-01` return 400.
- Rate limits: identify 30 requests per minute, enrich 15 per minute, per the Crustdata rate-limit page. Keep requests steady, not bursty.

GitHub:
- Personal rate limit: 5,000 requests per hour for an authenticated token (GitHub docs). The secondary limits are not verified here; keep requests spaced.
- Use a fine-grained token with access only to the vendor-register repository. Store it in the environment, never in the repository.

LiteLLM ($20 per team, shared; seven Nova and Claude models through one OpenAI-compatible API; the team leader claims the key at https://neatlogs.com/hackathon/models; requests stop at the limit): optional. The core decisions are deterministic. Use a model only to write the summary for a human reviewing an Unknown case.

AWS ($25 per team; EC2, Lambda, IAM roles and load balancers in us-east-1; Bedrock is not included): not needed for this build. The access link is in the owner's email and stays private.

## 7. Stack

Python 3.11 (within neatlogs' 3.10 to 3.13).
Standard HTTP client (httpx or requests). SQLite for the intent and memory store, with a single transaction per commit. Keep the store behind a small repository interface.
Tests: pytest. Lint and typecheck before every commit.

## 8. Repository and rules (neatHack)

- A new public repository, created by the owner during the window. Commits dated 10–12 Oct 2026. No code from before the window.
- The owner is the only author and contributor. Local git identity is set in the repo, and the hooks from the previous repository are copied in, so no AI or tool name, and no co-author trailer, can be committed.
- Every project must use neatlogs, Entire and cfo.ai. Keep evidence of all three.
- Submission: a public quote post of the official neatlogs submission post on X, using the "Submit on X" button when it appears, with team, name, project, public repository and demo link. Opening the draft alone does not submit. Entries after the confirmed cutoff are not judged. neatlogs and cfo.ai engage with the first 50 quote posts, so submit early.
- Supporting evidence goes in the repository. Judges must be able to verify that commits were made during the hackathon.
- Building in public: post progress on X tagged #neatHack during the window (15% of the score).
- Build log: keep `hackathon.md` at the repo root, as the official neatHack build-log skill asks (https://neatlogs.com/hackathon/skill). Dated entries, planned work kept apart from completed work, only tests that actually ran.
- Demo video: three minutes or less. It must explicitly cover neatlogs, Entire and cfo.ai: the architecture, implementation, runtime, reasoning and result for each tool. Show the crash, the reconciliation, the verdict, and the control's duplicate pull requests, with the neatlogs trace on screen.
- Conduct: plagiarism means removal. The idea credit to Anchor stays in the README and the submission, and no code from it is used.

## 9. Data

Only real data:
- The company domains are supplied by the team. Each one must be a real company the team intends to onboard.
- Crustdata answers are real API responses. Save them, with timestamps, to `evidence/`.
- The vendor register is a real repository the team owns.
- No mock endpoints. No sample companies. No invented metrics. Any number in the submission comes from a saved run.

## 10. Test plan

Unit: the key derivation (same inputs give the same key; different inputs give different keys), the verdict logic (the three verdicts from each reconcile input), and the decision threshold.

Integration (real APIs, a test repository): create one vendor end to end; re-run it and confirm it does nothing.

Chaos: the three crash points in section 4, each followed by restart and reconciliation. Pass only if there is exactly one branch and one pull request per company.

Control: the same crash points on the naive version. Record the duplicate count.

## 11. Cut order if time runs short

Cut in this order: the human approve page (use a command-line prompt instead), then the cfo.ai plan's detail, then the LiteLLM summary, then entire-graph. Do not cut the crash test, the control, the neatlogs traces, or the Entire checkpoint. Those are the judged evidence.

## 12. Verified facts and sources (checked 11 Oct 2026)

| Fact | Source |
|---|---|
| neatHack requirements and judging weights | https://neatlogs.com/hackathon (fetched) and the organisers' email, 10 Oct 2026 |
| GitHub: pull request creation has no documented idempotency key or duplicate error | https://docs.github.com/en/rest/pulls/pulls (fetched) |
| GitHub: get a reference returns 200 if it exists and 404 if not | https://docs.github.com/en/rest/git/refs (fetched) |
| GitHub: personal rate limit 5,000 requests per hour | https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api (fetched) |
| Crustdata: identify is free, enrich 2 credits per record (+2 for technographics), search 0.03 per result | https://docs.crustdata.com/general/pricing.md (fetched) |
| Crustdata: rate limits (identify 30, enrich 15 per minute) | https://docs.crustdata.com/general/rate-limits.md (fetched) |
| Crustdata: identify request and response shape, enrich request and response shape | https://docs.crustdata.com/company-docs/identify/introduction.md and https://docs.crustdata.com/company-docs/enrichment/reference.md (fetched) |
| GitHub: create/update file endpoint, 201/200, serial-write warning | https://docs.github.com/en/rest/repos/contents (re-fetched 11 Oct 2026) |
| Crustdata: required headers, credits endpoint, empty `matches` for no match | https://docs.crustdata.com/general/introduction.md, /general/credits.md, identify introduction (re-fetched 11 Oct 2026) |
| neatlogs: install, Python version range, init arguments, flush and shutdown guidance | PyPI metadata (version 1.4.26) and https://docs.neatlogs.com/sdk/lifecycle (fetched) |
| neatlogs: a process ending does not guarantee the final batch was sent | https://docs.neatlogs.com/sdk/lifecycle (fetched) |
| Entire: connect, install, enable, first checkpoint, `entire status`, link format, Best Use of Entire prize | https://hack.entire.io/neathacks-2026/ (re-fetched 11 Oct 2026) |
| neatlogs: Project API key vs `nlw_` key, `doctor --probe`, CLI readback, coding-agent prompt | https://neatlogs.com/hackathon/neatlogs-setup-guide.html (fetched 11 Oct 2026) |
| neatHack: video three minutes or less covering all three tools, Submit on X, evidence list, LiteLLM and AWS terms | https://neatlogs.com/hackathon FAQ (re-fetched 11 Oct 2026) |
| neatHack: `hackathon.md` build log | https://neatlogs.com/hackathon/skill (fetched 11 Oct 2026) |
| Team, credits and setup links | organisers' email "Your neatHack team is ready — setup guide & credits", 10 Oct 2026 |

Not verified, and to be checked during the build:
- The exact Crustdata company ID stability across calls (the identify response supplies it; test it).
- Whether GitHub applies secondary rate limits to this pattern.
- The cfo.ai business-plan requirements.
- The exact Entire integration name for the coding agent used.
- The neatlogs span helper names used in code (confirm against the installed package with `help()` before writing code that depends on them).
