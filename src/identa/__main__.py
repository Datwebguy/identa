"""Command line: python -m identa run --config identa.toml --domains domains.csv"""

from __future__ import annotations

import argparse
import csv
from dataclasses import asdict
from pathlib import Path

from identa import tracing
from identa.config import load_config, require_env
from identa.crustdata import Crustdata
from identa.github import GitHub
from identa.store import Store
from identa.workflow import main_exit, run


def read_domains(path: Path) -> list[str]:
    """One domain per row, first column. A header row named 'domain' is skipped."""
    with path.open(newline="", encoding="utf-8") as f:
        rows = [r[0].strip() for r in csv.reader(f) if r and r[0].strip()]
    return [d for d in rows if d.lower() != "domain"]


def main() -> None:
    parser = argparse.ArgumentParser(prog="identa")
    sub = parser.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="onboard the domains in a CSV, reconciling first")
    r.add_argument("--config", required=True, type=Path)
    r.add_argument("--domains", required=True, type=Path)
    args = parser.parse_args()

    cfg = load_config(args.config)
    tracing.init(require_env("NEATLOGS_API_KEY"))
    store = Store(cfg.store_path)
    crust = Crustdata(require_env("CRUSTDATA_API_KEY"), cfg.evidence_dir)
    gh = GitHub(require_env("GITHUB_TOKEN"), cfg.repo_owner, cfg.repo_name, cfg.evidence_dir)
    try:
        report = run(read_domains(args.domains), cfg, store, crust, gh)
        print(asdict(report))
    finally:
        store.close()
        main_exit()


if __name__ == "__main__":
    main()
