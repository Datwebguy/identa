"""Command line: python -m identa run --config identa.toml --domains domains.csv"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sqlite3
from dataclasses import asdict
from pathlib import Path

from identa import tracing
from identa.config import Config, load_config, require_env
from identa.control import run_control
from identa.crustdata import Crustdata
from identa.export import export_evidence
from identa.github import GitHub
from identa.measure import measure
from identa.race import race
from identa.store import PENDING, Store
from identa.workflow import (
    choose_candidate,
    crash_hook_from_env,
    crash_marker,
    decide_identity,
    main_exit,
    onboard,
    run,
)


def read_domains(path: Path) -> list[str]:
    """One domain per row, first column. A header row named 'domain' is skipped."""
    with path.open(newline="", encoding="utf-8") as f:
        rows = [r[0].strip() for r in csv.reader(f) if r and r[0].strip()]
    return [d for d in rows if d.lower() != "domain"]


def _github(cfg: Config, record: bool = True) -> GitHub:
    return GitHub(
        require_env("GITHUB_TOKEN"),
        cfg.repo_owner,
        cfg.repo_name,
        cfg.evidence_dir,
        (cfg.commit_author_name, cfg.commit_author_email),
        record=record,
    )


def _measure(cfg: Config, prefix: str | None) -> None:
    chosen = prefix or cfg.branch_prefix
    summary = measure(_github(cfg), cfg, chosen)
    print(json.dumps(asdict(summary), indent=2))


def _queue(cfg: Config, action: str, item: int | None, company_id: int | None = None) -> None:
    store = Store(cfg.store_path)
    try:
        if action == "list":
            for entry in store.human_queue():
                print(
                    entry["id"],
                    entry["domain"] or entry["key"],
                    entry["reason"],
                    entry["detail_json"],
                )
            return
        if item is None:
            raise SystemExit("an item id is required")
        row = store.get_queue_item(item)
        if row is None or row["status"] != "pending":
            raise SystemExit(f"no pending queue item {item}")
        if action == "reject":
            store.resolve_queue_item(item, "rejected")
            if row["key"]:
                store.set_state(row["key"], "rejected")
            return
        _accept(cfg, store, row, company_id)
    finally:
        store.close()


def _accept(cfg: Config, store: Store, row: sqlite3.Row, company_id: int | None = None) -> None:
    """A human accepts. A held intent goes back to pending so the next run reconciles it
    again. A held domain is onboarded with the company id Crustdata returned, or with the
    tied candidate chosen by company_id."""
    if row["key"]:
        if company_id is not None:
            raise SystemExit("--company-id applies only to a held domain, not a held intent")
        store.set_state(row["key"], PENDING)
        store.resolve_queue_item(row["id"], "accepted")
        return
    tracing.init(require_env("NEATLOGS_API_KEY"))
    try:
        crust = Crustdata(require_env("CRUSTDATA_API_KEY"), cfg.evidence_dir)
        found = crust.identify([row["domain"]])[0]
        if found.company_id is None:
            raise SystemExit("Crustdata returned no company for this domain; cannot accept")
        if company_id is not None:
            try:
                found = choose_candidate(found, company_id)
            except ValueError as exc:
                raise SystemExit(str(exc)) from exc
        outcome = onboard(
            found, cfg, store, crust, _github(cfg), crash_hook_from_env(crash_marker(cfg))
        )
        store.resolve_queue_item(row["id"], "accepted")
        print(outcome)
    finally:
        main_exit()


def _race(cfg: Config, domain: str, agents: int, control: bool) -> None:
    if agents < 2:
        raise SystemExit("--agents must be at least 2")
    tracing.init(require_env("NEATLOGS_API_KEY"))
    try:
        crust = Crustdata(require_env("CRUSTDATA_API_KEY"), cfg.evidence_dir)
        found = crust.identify([domain])[0]
        reason = decide_identity(found, cfg.confidence_threshold)
        if reason is not None or found.company_id is None:
            raise SystemExit(f"{domain} is held for a human ({reason}); choose another")
        data = crust.enrich(found.company_id)  # one call, reused from the saved response
        print(race(found, data, cfg, lambda: _github(cfg), agents, control))
    finally:
        main_exit()


def main() -> None:
    parser = argparse.ArgumentParser(prog="identa")
    sub = parser.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="onboard the domains in a CSV, reconciling first")
    r.add_argument("--config", required=True, type=Path)
    r.add_argument("--domains", required=True, type=Path)
    r.add_argument("--control", action="store_true", help="run the naive control instead")
    r.add_argument("--max-attempts", type=int, help="control only: blind retries per company")
    m = sub.add_parser("measure", help="count branches and pull requests per company on GitHub")
    m.add_argument("--config", required=True, type=Path)
    m.add_argument("--prefix", help="count this branch prefix instead of the configured one")
    e = sub.add_parser("export-evidence", help="copy evidence files to the evidence branch")
    e.add_argument("--config", required=True, type=Path)
    e.add_argument("--skip-dir", type=Path, help="files already present here are not exported")
    e.add_argument(
        "--since", required=True, help="only export files named at or after this timestamp"
    )
    rc = sub.add_parser("race", help="several agents onboard one company at the same moment")
    rc.add_argument("--config", required=True, type=Path)
    rc.add_argument("--domain", required=True)
    rc.add_argument("--agents", required=True, type=int)
    rc.add_argument("--control", action="store_true", help="agents without the reconciler")
    q = sub.add_parser("queue", help="the human queue")
    q.add_argument("--config", required=True, type=Path)
    q.add_argument("action", choices=["list", "accept", "reject"])
    q.add_argument("item", nargs="?", type=int)
    q.add_argument("--company-id", type=int, help="accept: onboard this tied candidate")
    args = parser.parse_args()

    cfg = load_config(args.config)
    if args.cmd in ("measure", "export-evidence", "queue"):
        # Only agent runs are traced. Without a key the SDK sends nothing, so bookkeeping
        # commands (thousands of small calls when copying evidence) cannot flood the project.
        os.environ.pop("NEATLOGS_API_KEY", None)
    if args.cmd == "measure":
        _measure(cfg, args.prefix)
        return
    if args.cmd == "export-evidence":
        count = export_evidence(
            _github(cfg, record=False), cfg.evidence_dir, args.skip_dir, cfg.base_branch, args.since
        )
        print({"exported": count})
        return
    if args.cmd == "queue":
        _queue(cfg, args.action, args.item, args.company_id)
        return
    if args.cmd == "race":
        _race(cfg, args.domain, args.agents, args.control)
        return
    tracing.init(require_env("NEATLOGS_API_KEY"))
    store = Store(cfg.store_path)
    crust = Crustdata(require_env("CRUSTDATA_API_KEY"), cfg.evidence_dir)
    gh = _github(cfg)
    try:
        if args.control:
            if not args.max_attempts:
                parser.error("--control needs --max-attempts")
            result = run_control(
                read_domains(args.domains),
                cfg,
                crust,
                gh,
                args.max_attempts,
                crash_hook_from_env(crash_marker(cfg)),
            )
            print(result)
            return
        report = run(read_domains(args.domains), cfg, store, crust, gh)
        print(asdict(report))
    finally:
        store.close()
        main_exit()


if __name__ == "__main__":
    main()
