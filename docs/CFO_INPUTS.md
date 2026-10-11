# Inputs for the cfo.ai business plan

Every measured number below comes from a saved run, with its source. Numbers marked **Decide** are business decisions for the owner to enter in cfo.ai; nothing here suggests a value for them.

All runs: 11 October 2026, the nine vendor domains in `domains.csv`, agent on Railway (project `identa`, service `agent`).

## 1. Measured costs

| Input | Value | Status | Source |
|---|---|---|---|
| Crustdata credits per onboarded company | 2 credits | Measured | Balance 5,200 before the first enrichment, 5,182 after all nine companies were enriched once: 18 credits for 9 companies. `evidence/20261011T185751598889Z-crustdata-credits.json` and `evidence/20261011T200229795852Z-crustdata-credits.json` |
| Crustdata credits for identify | 0 | Measured | Identify is free (Crustdata pricing page); the balance did not change across identify calls |
| Crustdata credits for re-runs, crash recovery and the control | 0 additional | Measured | Balance still 5,182 after all crash tests and control runs, because saved enrich responses are reused. `evidence/20261011T202527195994Z-crustdata-credits.json` |
| Model tokens and cost per run | none | Measured | No language model is called. Every decision is deterministic code |
| GitHub cost | 0 | Measured | Public repository and the standard REST API on a personal account; no paid GitHub feature is used |
| Railway cost | **Owner to supply** | From the Railway bill | Enter the figure from Railway's usage page for project `identa` |
| Vercel cost (results page) | **Owner to supply** | From the Vercel bill | Static page on the AlgoDao team |
| neatlogs cost | **Owner to supply** | From the neatlogs plan | Paid plan is free during the event; enter the post-event price if the plan should include it |

## 2. Measured time

| Input | Value | Status | Source |
|---|---|---|---|
| Time per company, end to end | 3.88 s on average | Measured | First full run: identify call at 20:00:40.87 UTC, ninth pull request opened at 20:01:15.79 UTC, 34.92 s for 9 companies. Timestamps of the saved `crustdata-identify` and `github-open_pr` files |
| Gap between consecutive pull requests | 3.39 s to 4.33 s | Measured | Same run, the nine `github-open_pr` timestamps |
| What limits that time | The agent's own enrich pacing | From the code | Crustdata documents 15 enrich requests per minute, so the agent waits 4 s between enrich calls (`src/identa/crustdata.py`). Faster onboarding would need a higher Crustdata rate limit |
| Time from crash to completed reconciliation | 2.17 s, 2.42 s, 2.59 s | Measured | Three crash tests, container restart included. Computed by `scripts/build_site.py` from saved evidence |

## 3. Reliability, for the plan's narrative

| Input | Value | Status | Source |
|---|---|---|---|
| Duplicate pull requests, protocol, 3 crash runs of 9 companies | 0 | Measured | `identa measure` records for `crash-a`, `crash-b`, `crash-c` |
| Duplicate pull requests, control, same 3 crash points | 1 | Measured | `identa measure` records for `control-a`, `control-b`, `control-c` |
| Control C repeated by accident | 4 more runs, 1 duplicate each | Measured | `evidence/20261011T205609731739Z-audit-register-pull-requests.json` |

## 4. Owner decisions (not measured, not suggested)

| Input | Value |
|---|---|
| Price per onboarded vendor, or pricing model | **Decide** |
| Monthly subscription price, if any | **Decide** |
| Number of customers, and growth | **Decide** |
| Vendors onboarded per customer per month | **Decide** |
| Crustdata plan after the event (credits and price) | **Decide**, from Crustdata's price list |
| Team cost and salaries | **Decide** |
| Starting cash, for runway | **Decide** |

## 5. What does not work yet

- The `Unknown` verdict has not occurred in a real run.
- A tie between two top matches at the same confidence is not yet sent to human review (seen for `cfo.ai` and `amazon.com`).
- Copying evidence off the Railway volume runs at about one file per second.
