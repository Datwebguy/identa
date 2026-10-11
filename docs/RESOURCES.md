# Resources

Every link the build needs, from the organisers' emails and the official pages. Checked 11 Oct 2026. Private links (the AWS access link, the LiteLLM key, login links) stay in the owner's email and are not listed here.

## neatHack

| What | Link |
|---|---|
| Hackathon guide (rules, judging, evidence, FAQ) | https://neatlogs.com/hackathon |
| Luma event | https://luma.com/s5blr882 |
| Discord (official communication, final cutoff, help) | https://neatlogs.com/discord |
| Team check-in | https://neatlogs.com/hackathon/check-in |
| Build-log skill (`hackathon.md`) | https://neatlogs.com/hackathon/skill |
| LiteLLM key claim (team leader) | https://neatlogs.com/hackathon/models |
| neatlogs announcement post on X | https://x.com/neatlogs/status/2106021295221768387 |

Key facts: one track; teams of 1 to 4; all code written during the event; every project uses neatlogs, Entire and cfo.ai; submission is a quote post of the official neatlogs submission post on X, Mon 12 Oct 7:00 to 11:55 PM IST (planned close; final cutoff on Discord); demo video three minutes or less, covering all three tools; winners Fri 16 Oct. Team: MajorLabs.

Judging: the agent 30%, use of neatlogs, Entire and cfo.ai 25%, demo video 20%, building in public 15%, usefulness and originality 10%.

## neatlogs

| What | Link |
|---|---|
| App (sign up, project, API keys, traces) | https://app.neatlogs.com |
| Setup guide (first trace, coding-agent prompt, CLI, troubleshooting) | https://neatlogs.com/hackathon/neatlogs-setup-guide.html |
| Docs | https://docs.neatlogs.com |
| Docs index for agents | https://docs.neatlogs.com/llms.txt |
| Agent skills | https://docs.neatlogs.com/integrations/skills and https://github.com/neatlogs/skills |
| SDK lifecycle (flush, shutdown) | https://docs.neatlogs.com/sdk/lifecycle |
| SDK Doctor | https://docs.neatlogs.com/sdk/doctor |
| CLI setup and configuration | https://docs.neatlogs.com/cli and https://docs.neatlogs.com/cli/configuration |
| Public API | https://docs.neatlogs.com/api-reference |
| Python package | https://pypi.org/project/neatlogs/ |

Use the Project API key (Settings, then API keys), not the `nlw_` HTTP ingest key. Paid plans are free during the event.

## Entire

| What | Link |
|---|---|
| neatHack guide (connect, first checkpoint, Trails, Graph, Brain, submission) | https://hack.entire.io/neathacks-2026/ |
| Docs | https://docs.entire.io |
| App and checkpoint links | https://entire.io (checkpoint link: `https://entire.io/gh/OWNER/REPO/commit/FULL_COMMIT_SHA`) |
| entire-brain source | https://github.com/entireio/entire-brain |

Separate prize: Best Use of Entire (Checkpoints, Graph or Brain).

## cfo.ai

| What | Link |
|---|---|
| neatHack signup (free paid plan; card required; cancel in Settings, then Billing straight away) | https://cfo.ai/neathacks |

The organisers provide the cfo.ai credits. The plan must cover pricing, costs, revenue and runway.

## Crustdata

| What | Link |
|---|---|
| App (promo code NEATLOGS-OCT2026, 5,000 credits, already claimed) | https://app.crustdata.com |
| API documentation | https://www.crustdata.com/api-documentation |
| Docs introduction (headers, versions) | https://docs.crustdata.com/general/introduction.md |
| Pricing (credits per endpoint) | https://docs.crustdata.com/general/pricing.md |
| Credits balance endpoint | https://docs.crustdata.com/general/credits.md |
| Rate limits | https://docs.crustdata.com/general/rate-limits.md |
| Company identify | https://docs.crustdata.com/company-docs/identify/introduction.md |
| Company enrich | https://docs.crustdata.com/company-docs/enrichment/reference.md |

Base URL `https://api.crustdata.com`. Headers: `Authorization: Bearer <key>` and `x-api-version: 2025-11-01`.

## GitHub REST API

| What | Link |
|---|---|
| Git references (get, create) | https://docs.github.com/en/rest/git/refs |
| Repository contents (create or update a file) | https://docs.github.com/en/rest/repos/contents |
| Pull requests | https://docs.github.com/en/rest/pulls/pulls |
| Rate limits | https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api |
| Fine-grained tokens | https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens |

## Models and compute (optional)

- LiteLLM: one shared $20 budget per team, seven Nova and Claude models, OpenAI-compatible API. Claim at https://neatlogs.com/hackathon/models.
- AWS: one $25 allowance per team, EC2, Lambda, IAM roles and load balancers in us-east-1. Bedrock is not included. Not needed for this build.

## Idea credit

The intent-log and reconciler protocol is adapted from Anchor by Viraj Chogle: https://devpost.com/software/anchor-os25c6 and https://github.com/virajchogle. No code from it is used.
