# Security

## Reporting

Report a security problem privately to the repository owner through GitHub. Do not open a public issue for it.

## Secrets

- All keys come from environment variables: `CRUSTDATA_API_KEY`, `GITHUB_TOKEN`, `NEATLOGS_API_KEY`, and `LITELLM_API_KEY` if used.
- `.env` files are ignored by git and never committed.
- The GitHub token is fine-grained and limited to the vendor-register repository.
- Keys are never logged, printed or written into neatlogs traces or Entire checkpoints.

## Data

- Crustdata responses saved under `evidence/` contain company data only, never keys.
- Only real companies the team intends to onboard are processed.
