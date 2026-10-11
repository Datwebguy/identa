"""Typed wrappers over neatlogs, so the rest of the code stays type-checked.

Inputs are never captured on tool spans: client methods can see headers with keys.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar, cast

import neatlogs  # type: ignore[import-untyped]

F = TypeVar("F", bound=Callable[..., Any])


def tool(name: str) -> Callable[[F], F]:
    def wrap(fn: F) -> F:
        return cast(F, neatlogs.span("TOOL", name=name, capture_input=False)(fn))

    return wrap


def span(kind: str, name: str) -> Callable[[F], F]:
    def wrap(fn: F) -> F:
        return cast(F, neatlogs.span(kind, name=name, capture_input=False)(fn))

    return wrap


def init(api_key: str) -> None:
    neatlogs.init(api_key=api_key, endpoint="https://ingest.neatlogs.com", workflow_name="identa")


def flush() -> None:
    neatlogs.flush()


def shutdown() -> None:
    """Flush, then shut down, as documented for a normal exit."""
    neatlogs.flush()
    neatlogs.shutdown()
