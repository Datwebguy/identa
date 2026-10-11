"""Command line: python -m identa run --config identa.toml --domains domains.csv"""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from dataclasses import asdict
from pathlib import Path

from identa import tracing
from identa.config import Config, load_config, require_env
from identa.control import CONTROL_PREFIX, run_control
from identa.crustdata import Crustdata
from identa.export import export_evidence
from identa.github import GitHub
from identa.measure import measure
from identa.store import PENDING, Store
from identa.workflow import crash_hook_from_env, crash_marker, main_exit, onboard, run


def read_domains(path: Path) -> list[str]:
    """One domain per row, first column. A header row named 'domain' is skipped."""
    with path.open(newline="", encoding="utf-8") as f:
        rows = [r[0].strip() for r in csv.reader(f) if r and r[0].strip()]
    return [d for d in rows if d.lower() != "domain"]


def _github(cfg: Config) -> GitHub:
    return GitHub(
        require_env("GITHUB_TOKEN"),
        cfg.repo_owner,
        cfg.repo_name,
        cfg.evidence_dir,
        (cfg.commit_author_name, cfg.commit_author_email),
    )


def _measure(cfg: Config, control: bool) -> None:
    summary = measure(_github(cfg), cfg, CONTROL_PREFIX if control else "vendor")
    print(json.dumps(asdict(summary), indent=2))


def _queue(cfg: Config, action: str, item: int | None) -> None:
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
        _accept(cfg, store, row)
    finally:
        store.close()


def _accept(cfg: Config, store: Store, row: sqlite3.Row) -> None:
    """A human accepts. A held intent goes back to pending so the next run reconciles it
    again. A held domain is onboarded with the company id Crustdata returned."""
    if row["key"]:
        store.set_state(row["key"], PENDING)
        store.resolve_queue_item(row["id"], "accepted")
        return
    tracing.init(require_env("NEATLOGS_API_KEY"))
    try:
        crust = Crustdata(require_env("CRUSTDATA_API_KEY"), cfg.evidence_dir)
        found = crust.identify([row["domain"]])[0]
        if found.company_id is None:
            raise SystemExit("Crustdata returned no company for this domain; cannot accept")
        outcome = onboard(
            found, cfg, store, crust, _github(cfg), crash_hook_from_env(crash_marker(cfg))
        )
        store.resolve_queue_item(row["id"], "accepted")
        print(outcome)
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
    m.add_argument("--control", action="store_true", help="count the control's branches")
    e = sub.add_parser("export-evidence", help="copy evidence files to the evidence branch")
    e.add_argument("--config", required=True, type=Path)
    e.add_argument("--skip-dir", type=Path, help="files already present here are not exported")
    q = sub.add_parser("queue", help="the human queue")
    q.add_argument("--config", required=True, type=Path)
    q.add_argument("action", choices=["list", "accept", "reject"])
    q.add_argument("item", nargs="?", type=int)
    args = parser.parse_args()

    cfg = load_config(args.config)
    if args.cmd == "measure":
        _measure(cfg, args.control)
        return
    if args.cmd == "export-evidence":
        count = export_evidence(_github(cfg), cfg.evidence_dir, args.skip_dir, cfg.base_branch)
        print({"exported": count})
        return
    if args.cmd == "queue":
        _queue(cfg, args.action, args.item)
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
