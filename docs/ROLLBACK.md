# Rollback plan

What to do if something goes wrong on launch day. Every step below uses only tools and settings that exist in this project.

## The results page (Vercel)

- Each push is deployed to production by hand with the Vercel tool (push-triggered deploys have been unreliable). Every deployment stays in Vercel, so the previous one can be made live again.
- To go back: in the Vercel dashboard, project `identa`, Deployments, choose the last good deployment and use **Promote to Production** (or ask for `request_rollback` through the Vercel tool).
- Last two good deployments at the time of writing: `dpl_5WuNuYLy4WFCx5yjJV2KcnCPfLDc` (race results, commit `0c768b6`) and `dpl_9mE6UbkUKBt5w7H3E8Qe4xZhqM2s` (logo, commit `dfe1600`).
- Check after: `https://identa-iota.vercel.app/` returns 200 and `/data.json` returns 200.

## The code (GitHub)

- `main` only moves forward. To undo a change, add a commit that reverts it (`git revert <sha>`), then push. No force-push, no rewriting history.
- Authorship checks in `.githooks/` stay on for the revert as for any commit.

## The agent (Railway)

- The service is idle by design: its variables are `IDENTA_ARGS=queue list --config identa.railway.toml`, `IDENTA_EXPORT=0`, `IDENTA_FRESH_STORE=0`, and it redeploys only when `src/**`, `Dockerfile`, `scripts/railway_entry.sh`, `identa.railway.toml`, `domains.csv` or `pyproject.toml` change.
- If a run starts by accident: set `IDENTA_ARGS` back to the read-only command and redeploy. Do not stop it by pushing code, because each push can start another run.
- If a deployment is bad: in Railway, Deployments, redeploy the previous successful one.

## The register (`Datwebguy/identavendors`)

- Pull requests and branches made by tests (prefixes `crash-*`, `control-*`, `race-*`) are kept open on purpose, as evidence. Nothing is closed, deleted or changed without the owner's decision.

## The evidence

- Evidence lives in the repository (`evidence/`) and in the `evidence` branch of the register. Both are in git, so a lost container loses nothing that was pushed.
- The agent's local SQLite store (`/data/identa.sqlite`) is not a source of truth for results. Results come from `measure` on GitHub.

## Keys

- Keys are Railway variables only. If one leaks, replace it in the provider's dashboard, update the Railway variable, and redeploy.
