"""Build web/data.json from the saved files under evidence/. Nothing is added or invented."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def build(evidence_dir: Path) -> dict[str, object]:
    files: list[dict[str, object]] = []
    measures: list[dict[str, object]] = []
    pull_requests: list[dict[str, object]] = []
    for path in sorted(evidence_dir.glob("*.json")):
        rec = json.loads(path.read_text(encoding="utf-8"))
        source, status, body = rec["source"], rec["status"], rec["body"]
        label = path.stem.split(f"-{source}-", 1)[-1]
        files.append(
            {
                "file": path.name,
                "saved_at": rec["saved_at"],
                "source": source,
                "label": label,
                "status": status,
            }
        )
        if source == "measure":
            measures.append({"saved_at": rec["saved_at"], **body})
        if source == "github" and label.endswith("open_pr") and status == 201:
            pull_requests.append(
                {
                    "saved_at": rec["saved_at"],
                    "url": body["html_url"],
                    "branch": body["head"]["ref"],
                }
            )
    return {"evidence": files, "measures": measures, "pull_requests": pull_requests}


def main() -> None:
    out = ROOT / "web" / "data.json"
    data = build(ROOT / "evidence")
    out.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)}: {len(data['evidence'])} evidence files", file=sys.stderr)  # type: ignore[arg-type]


if __name__ == "__main__":
    main()
