"""Copy evidence files to a branch of the register repository, one at a time.

Used where the evidence directory is on a volume (for example a container platform), so the
files can be fetched with git and committed into this repository's evidence folder.
"""

from __future__ import annotations

from pathlib import Path

from identa.github import GitHub

EVIDENCE_BRANCH = "evidence"


def export_evidence(gh: GitHub, evidence_dir: Path, skip_dir: Path | None, base: str) -> int:
    """Returns the number of files written. Files already in skip_dir are not exported."""
    if gh.get_ref(EVIDENCE_BRANCH).status == 404:
        sha = gh.get_ref(base).body["object"]["sha"]
        if gh.create_ref(EVIDENCE_BRANCH, sha).status != 201:
            raise RuntimeError("could not create the evidence branch")
    written = 0
    for path in sorted(evidence_dir.glob("*.json")):
        if skip_dir is not None and (skip_dir / path.name).exists():
            continue
        target = f"evidence/{path.name}"
        if gh.get_file(target, EVIDENCE_BRANCH).status == 200:
            continue
        reply = gh.put_file(
            target, EVIDENCE_BRANCH, f"Add evidence {path.name}", path.read_text("utf-8")
        )
        if reply.status not in (200, 201):
            raise RuntimeError(f"export of {path.name} returned {reply.status}")
        written += 1
    return written
