"""Build web/data.json from the saved files under evidence/. Nothing is added or invented."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
WRITES = ("create_ref", "put_file", "open_pr")
NOT_VENDOR = ("refs/heads/main", "refs/heads/evidence")


def _load(evidence_dir: Path) -> list[tuple[str, str, int, Any, str]]:
    out = []
    for path in sorted(evidence_dir.glob("*.json")):
        rec = json.loads(path.read_text(encoding="utf-8"))
        label = path.stem.split(f"-{rec['source']}-", 1)[-1]
        out.append((rec["saved_at"], rec["source"], rec["status"], rec["body"], label))
    return out


def _is_export(rec: tuple[str, str, int, Any, str]) -> bool:
    body = rec[3]
    return (
        rec[4] == "put_file"
        and isinstance(body, dict)
        and str((body.get("content") or {}).get("path", "")).startswith("evidence/")
    )


def reconciliations(recs: list[tuple[str, str, int, Any, str]]) -> list[dict[str, object]]:
    """After an interruption the agent reads the intent's own branch (the executor never does),
    so the first such read marks a reconciliation. If the write just before it succeeded, the
    process was killed after that write (a crash); if it was refused, this was a re-run of work
    already done. Reconciliation ends with the pull request check that follows."""
    gh = [r for r in recs if r[1] == "github" and not _is_export(r)]
    seen: set[str] = set()
    out: list[dict[str, object]] = []
    for i, (_at, _, status, body, label) in enumerate(gh):
        if label != "get_ref" or status != 200 or not isinstance(body, dict):
            continue
        ref = str(body.get("ref", ""))
        if ref in NOT_VENDOR or ref in seen or "/" not in ref.removeprefix("refs/heads/"):
            continue
        seen.add(ref)
        prev = next((g for g in reversed(gh[:i]) if g[4] in WRITES), None)
        done = next((g for g in gh[i + 1 :] if g[4] == "list_prs"), None)
        if prev is None or done is None:
            continue
        secs = (datetime.fromisoformat(done[0]) - datetime.fromisoformat(prev[0])).total_seconds()
        branch = ref.removeprefix("refs/heads/")
        out.append(
            {
                "prefix": branch.split("/", 1)[0],
                "branch": branch,
                "kind": "crash" if prev[2] in (200, 201) else "re-run",
                "after": prev[4],
                "after_status": prev[2],
                "seconds": round(secs, 2),
            }
        )
    return out


def _company(pr: dict[str, Any]) -> str:
    return str(pr["branch"]).split("/", 1)[1].split("-", 1)[0]


def control_runs(
    recs: list[tuple[str, str, int, Any, str]], planned_measured_at: str | None, prefix: str
) -> list[dict[str, object]]:
    """Group a prefix's pull requests from the latest register audit into runs. Every run walks
    the companies in input order, so a new run starts when the first company appears again
    after others, or after a gap of more than a minute. A run is planned if it finished before
    the planned measurement of that prefix was saved."""
    audits = [r for r in recs if r[1] == "audit" and r[4] == "register-pull-requests"]
    if not audits:
        return []
    prs = sorted(
        (p for p in audits[-1][3]["pull_requests"] if str(p["branch"]).startswith(prefix + "/")),
        key=lambda p: str(p["created_at"]),
    )
    runs: list[list[dict[str, Any]]] = []
    for pr in prs:
        at = datetime.fromisoformat(str(pr["created_at"]).replace("Z", "+00:00"))
        if runs:
            cur = runs[-1]
            last = datetime.fromisoformat(str(cur[-1]["created_at"]).replace("Z", "+00:00"))
            seen = {_company(c) for c in cur}
            restarted = _company(pr) == _company(cur[0]) and len(seen) > 1
            if (at - last).total_seconds() <= 60 and not restarted:
                cur.append(pr)
                continue
        runs.append([pr])
    out: list[dict[str, object]] = []
    for run in runs:
        companies = {_company(p) for p in run}
        end = str(run[-1]["created_at"]).replace("Z", "+00:00")
        out.append(
            {
                "started": str(run[0]["created_at"]),
                "first_pr": run[0]["number"],
                "last_pr": run[-1]["number"],
                "pull_requests": len(run),
                "companies": len(companies),
                "duplicate_pull_requests": len(run) - len(companies),
                "planned": bool(planned_measured_at and end < planned_measured_at),
            }
        )
    return out


def build(evidence_dir: Path) -> dict[str, object]:
    recs = _load(evidence_dir)
    by_call: dict[tuple[str, str, int], int] = {}
    latest_measure: dict[str, dict[str, object]] = {}
    pull_requests: list[dict[str, object]] = []
    for at, source, status, body, label in recs:
        by_call[(source, label, status)] = by_call.get((source, label, status), 0) + 1
        if source == "measure" and body["prefix"] not in latest_measure:
            # The first measurement after each planned run is the one that describes it.
            m = {k: v for k, v in body.items() if k != "per_company"}
            latest_measure[body["prefix"]] = {"saved_at": at, **m}
        if source == "github" and label == "open_pr" and status == 201:
            branch = body["head"]["ref"]
            if branch.startswith("vendor/"):
                pull_requests.append(
                    {
                        "saved_at": at,
                        "url": body["html_url"],
                        "branch": branch,
                        "number": body["number"],
                        "title": body["title"],
                    }
                )
    return {
        "evidence_total": len(recs),
        "last_saved_at": recs[-1][0] if recs else None,
        "evidence_by_call": [
            {"source": k[0], "call": k[1], "status": k[2], "count": n}
            for k, n in sorted(by_call.items())
        ],
        "measures": sorted(latest_measure.values(), key=lambda m: str(m["prefix"])),
        "reconciliations": reconciliations(recs),
        "pull_requests": sorted(pull_requests, key=lambda p: int(str(p["number"]))),
        "control_c_runs": control_runs(
            recs, str(latest_measure.get("control-c", {}).get("saved_at") or ""), "control-c"
        ),
    }


def main() -> None:
    out = ROOT / "web" / "data.json"
    data = build(ROOT / "evidence")
    out.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(
        f"wrote {out.relative_to(ROOT)}: {data['evidence_total']} evidence files", file=sys.stderr
    )


if __name__ == "__main__":
    main()
