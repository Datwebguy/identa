#!/bin/sh
# Container entry point. IDENTA_ARGS holds the command, for example:
#   run --config identa.railway.toml --domains domains.csv
set -e
mkdir -p /data/evidence
cp -n /app/evidence/* /data/evidence/ 2>/dev/null || true   # reuse saved enrich responses

# IDENTA_FRESH_STORE=1 clears the store once per deployment. A restart of the same
# deployment (for example after an injected crash) keeps its store, so it can recover.
if [ "$IDENTA_FRESH_STORE" = "1" ] && [ "$(cat /data/.reset_for 2>/dev/null)" != "$RAILWAY_DEPLOYMENT_ID" ]; then
  rm -f /data/identa.sqlite /data/identa.crashed /data/identa.control-crashed
  echo "$RAILWAY_DEPLOYMENT_ID" > /data/.reset_for
fi

# shellcheck disable=SC2086
python -m identa $IDENTA_ARGS
# Evidence is copied off the volume only when IDENTA_EXPORT_SINCE is set to a timestamp prefix
# such as 20261012T0502. Only files from that time on are copied, and the copy does not
# record its own calls, so it cannot feed itself.
if [ -n "$IDENTA_EXPORT_SINCE" ] && [ "$IDENTA_EXPORT" != "0" ]; then
  python -m identa export-evidence --config identa.railway.toml --skip-dir /app/evidence --since "$IDENTA_EXPORT_SINCE"
fi
