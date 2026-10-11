"""Settings. Secrets come from the environment only; everything else from a TOML file."""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path


class ConfigError(Exception):
    pass


@dataclass(frozen=True)
class Config:
    confidence_threshold: float
    repo_owner: str
    repo_name: str
    base_branch: str
    store_path: Path
    evidence_dir: Path
    commit_author_name: str
    commit_author_email: str
    branch_prefix: str


def load_config(path: str | Path) -> Config:
    """Every key is required. There are no defaults, so no value is silently invented."""
    try:
        raw = tomllib.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfigError(f"config file not found: {path}") from exc
    keys = (
        "confidence_threshold",
        "repo_owner",
        "repo_name",
        "base_branch",
        "store_path",
        "evidence_dir",
    )
    missing = [k for k in keys if k not in raw]
    if missing:
        raise ConfigError(f"missing config keys: {', '.join(missing)}")
    return Config(
        confidence_threshold=float(raw["confidence_threshold"]),
        repo_owner=str(raw["repo_owner"]),
        repo_name=str(raw["repo_name"]),
        base_branch=str(raw["base_branch"]),
        store_path=Path(raw["store_path"]),
        evidence_dir=Path(raw["evidence_dir"]),
        commit_author_name=str(raw["commit_author_name"]),
        commit_author_email=str(raw["commit_author_email"]),
        # IDENTA_BRANCH_PREFIX lets a test run use its own branch namespace in the same repo.
        branch_prefix=os.environ.get("IDENTA_BRANCH_PREFIX") or str(raw["branch_prefix"]),
    )


def require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise ConfigError(f"environment variable {name} is not set")
    return value
