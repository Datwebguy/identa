# Inputs for the cfo.ai business plan

Every measured number below comes from a saved run, with its source. Numbers marked **Decide** are business decisions for the owner to enter in cfo.ai; nothing here suggests a value for them.

All runs: 11 October 2026, the nine vendor domains in `domains.csv`, agent on Railway (project `identa`, service `agent`).

## 1. Measured costs

| Input | Value | Status | Source |
|---|---|---|---|
| Crustdata cost per credit | $0.30 | Measured | Crustdata billing page (screenshot, 12 Oct): balance $1,554.60 for 5,182 credits, which is $0.30 per credit at list price. The page also lists company enrich at $0.60 to $1.20 per record (2 to 4 credits). Volume packages are cheaper: $500 buys $600 of usage, $2,000 buys $3,000 |
| Crustdata cost per onboarded company | $0.60 | Measured | 18 credits for 9 companies = $5.40, from the balance change ($1,560.00 to $1,554.60) |
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

## 4. Owner's pricing and growth decisions (chosen by the owner, not measured)

| Input | Decision |
|---|---|
| Monthly subscription | $99 per customer per month, including 50 vendors |
| Extra vendors above 50 | $1.50 each |
| Customers | 3 in month 1, then 2 more every month, 25 in month 12 |
| Vendors onboarded | 60 per customer per month |
| Hosting | $5 per month (Railway Hobby plan fee) |
| Team cost | $0 in year one |
| Starting cash | $3,000 |

Worked from the measured cost of $0.60 per vendor: each customer pays $114 per month ($99 plus 10 extra vendors at $1.50) and costs $36 in Crustdata, so $78 is left per customer. At 25 customers: revenue $2,850 per month, Crustdata $900, hosting $5, $1,945 left per month before any team cost.

## 4b. Still to supply

| Input | Value |
|---|---|
| Railway usage beyond the plan fee | **Owner to supply**, from the Railway usage page |
| Crustdata volume discount | Optional: the $500 and $2,000 packages give 17% and 33% off; the plan uses the plain $0.30 per credit |

## 5. What does not work yet

- The human queue is a command-line queue, not a web page.
- Copying evidence off the Railway volume runs at about one file per second.
- Resolved on 12 Oct 2026: a tie between two top matches now goes to the human queue (seen for `cfo.ai` and `amazon.com`), and the `Unknown` outcome has occurred in a real run.
