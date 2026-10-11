"""Count branches and pull requests per company straight from GitHub."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from typing import Any

from identa import evidence
from identa.config import Config
from identa.github import GitHub


@dataclass(frozen=True)
class Summary:
    prefix: str
    companies: int
    branches: int
    pull_requests: int
    duplicate_branches: int
    duplicate_pull_requests: int
    per_company: dict[str, dict[str, int]]


def _company(ref_name: str, prefix: str) -> str | None:
    """'<prefix>/<company_id>-<suffix>' gives company_id."""
    head = f"{prefix}/"
    if not ref_name.startswith(head):
        return None
    return ref_name[len(head) :].split("-", 1)[0] or None


def summarize(branch_names: list[str], pr_heads: list[str], prefix: str) -> Summary:
    b: Counter[str] = Counter()
    p: Counter[str] = Counter()
    for name in branch_names:
        if (c := _company(name, prefix)) is not None:
            b[c] += 1
    for name in pr_heads:
        if (c := _company(name, prefix)) is not None:
            p[c] += 1
    ids = sorted(set(b) | set(p))
    return Summary(
        prefix=prefix,
        companies=len(ids),
        branches=sum(b.values()),
        pull_requests=sum(p.values()),
        duplicate_branches=sum(max(0, n - 1) for n in b.values()),
        duplicate_pull_requests=sum(max(0, n - 1) for n in p.values()),
        per_company={c: {"branches": b[c], "pull_requests": p[c]} for c in ids},
    )


def measure(gh: GitHub, cfg: Config, prefix: str) -> Summary:
    refs = gh.matching_refs(f"{prefix}/")
    prs = gh.list_all_prs()
    if refs.status != 200 or prs.status != 200:
        raise RuntimeError(f"GitHub returned {refs.status} for refs and {prs.status} for pulls")
    names = [str(r["ref"]).removeprefix("refs/heads/") for r in refs.body]
    heads = [str((p.get("head") or {}).get("ref", "")) for p in prs.body]
    summary = summarize(names, heads, prefix)
    record: dict[str, Any] = asdict(summary)
    evidence.save(cfg.evidence_dir, "measure", prefix, 200, record)
    return summary
