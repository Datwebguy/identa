"""Build web/data.json from the saved files under evidence/. Nothing is added or invented."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def build(evidence_dir: Path) -> dict[str, object]:
    by_call: dict[tuple[str, str, int], int] = {}
    latest_measure: dict[str, dict[str, object]] = {}
    pull_requests: list[dict[str, object]] = []
    total = 0
    for path in sorted(evidence_dir.glob("*.json")):
        rec = json.loads(path.read_text(encoding="utf-8"))
        source, status, body = rec["source"], rec["status"], rec["body"]
        label = path.stem.split(f"-{source}-", 1)[-1]
        total += 1
        by_call[(source, label, status)] = by_call.get((source, label, status), 0) + 1
        if source == "measure":
            latest_measure[body["prefix"]] = {"saved_at": rec["saved_at"], **body}
        if source == "github" and label.endswith("open_pr") and status == 201:
            branch = body["head"]["ref"]
            if branch.startswith("vendor/"):
                pull_requests.append(
                    {"saved_at": rec["saved_at"], "url": body["html_url"], "branch": branch}
                )
    calls = [
        {"source": k[0], "call": k[1], "status": k[2], "count": n}
        for k, n in sorted(by_call.items())
    ]
    for m in latest_measure.values():
        m.pop("per_company", None)
    return {
        "evidence_total": total,
        "evidence_by_call": calls,
        "measures": sorted(latest_measure.values(), key=lambda m: str(m["prefix"])),
        "pull_requests": sorted(pull_requests, key=lambda p: str(p["saved_at"])),
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
