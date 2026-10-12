"""Crustdata identify (free) and enrich (2 credits per record). Shapes from the official docs."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

from identa import evidence
from identa.tracing import tool

BASE_URL = "https://api.crustdata.com"
API_VERSION = "2025-11-01"
MAX_IDENTIFY_BATCH = 25
# Documented limits: identify 30 per minute, enrich 15 per minute.
IDENTIFY_MIN_INTERVAL_S = 60 / 30
ENRICH_MIN_INTERVAL_S = 60 / 15


class CrustdataError(Exception):
    pass


@dataclass(frozen=True)
class Identified:
    domain: str
    company_id: int | None
    confidence: float | None
    name: str | None
    primary_domain: str | None
    # Every match that shares the top confidence_score: (company id, name, confidence).
    candidates: tuple[tuple[int, str | None, float], ...] = ()

    @property
    def tied(self) -> bool:
        return len(self.candidates) > 1


def find_saved_enrich(evidence_dir: Path, company_id: int) -> dict[str, Any] | None:
    """Look through saved evidence for a successful enrich response for this company."""
    for path in sorted(evidence_dir.glob("*-crustdata-enrich.json")):
        rec = json.loads(path.read_text(encoding="utf-8"))
        body = rec.get("body")
        if rec.get("status") != 200 or not isinstance(body, list) or not body:
            continue
        entry = body[0]
        if str(entry.get("matched_on")) != str(company_id) or not entry.get("matches"):
            continue
        data: dict[str, Any] = entry["matches"][0]["company_data"]
        return data
    return None


class Crustdata:
    def __init__(self, api_key: str, evidence_dir: Path, client: httpx.Client | None = None):
        self._client = client or httpx.Client(timeout=30)
        self._headers = {"Authorization": f"Bearer {api_key}", "x-api-version": API_VERSION}
        self._evidence_dir = evidence_dir
        self._last: dict[str, float] = {}

    def _wait(self, kind: str, interval: float) -> None:
        gap = self._last.get(kind, 0.0) + interval - time.monotonic()
        if gap > 0:
            time.sleep(gap)
        self._last[kind] = time.monotonic()

    def _post(self, kind: str, path: str, body: dict[str, Any], interval: float) -> httpx.Response:
        self._wait(kind, interval)
        resp = self._client.post(BASE_URL + path, json=body, headers=self._headers)
        try:
            payload: Any = resp.json()
        except ValueError:
            payload = resp.text
        evidence.save(self._evidence_dir, "crustdata", kind, resp.status_code, payload)
        return resp

    @tool("crustdata.identify")
    def identify(self, domains: list[str]) -> list[Identified]:
        """One result per input domain, in order. Empty matches give company_id None."""
        out: list[Identified] = []
        for i in range(0, len(domains), MAX_IDENTIFY_BATCH):
            batch = domains[i : i + MAX_IDENTIFY_BATCH]
            resp = self._post(
                "identify",
                "/company/identify",
                {"domains": batch, "exact_match": True},
                IDENTIFY_MIN_INTERVAL_S,
            )
            if resp.status_code == 404:
                out.extend(Identified(d, None, None, None, None) for d in batch)
                continue
            if resp.status_code != 200:
                raise CrustdataError(f"identify returned {resp.status_code}")
            entries = resp.json()
            if len(entries) != len(batch):
                raise CrustdataError("identify returned a different number of entries")
            for domain, entry in zip(batch, entries, strict=True):
                out.append(self._parse(domain, entry))
        return out

    @staticmethod
    def _parse(domain: str, entry: dict[str, Any]) -> Identified:
        matches = entry.get("matches") or []
        if not matches:
            return Identified(domain, None, None, None, None)
        top = matches[0]
        data = top["company_data"]
        info = data.get("basic_info") or {}
        candidates = tuple(
            (
                int(m["company_data"]["crustdata_company_id"]),
                (m["company_data"].get("basic_info") or {}).get("name"),
                float(m["confidence_score"]),
            )
            for m in matches
            if m["confidence_score"] == top["confidence_score"]
        )
        return Identified(
            domain,
            int(data["crustdata_company_id"]),
            float(top["confidence_score"]),
            info.get("name"),
            info.get("primary_domain"),
            candidates,
        )

    @tool("crustdata.enrich")
    def enrich(self, company_id: int) -> dict[str, Any]:
        """Returns matches[0].company_data for basic_info and headcount.

        A saved successful enrich response for this company is reused, so the same company
        never costs credits twice.
        """
        saved = find_saved_enrich(self._evidence_dir, company_id)
        if saved is not None:
            return saved
        resp = self._post(
            "enrich",
            "/company/enrich",
            {"crustdata_company_ids": [company_id], "fields": ["basic_info", "headcount"]},
            ENRICH_MIN_INTERVAL_S,
        )
        if resp.status_code != 200:
            raise CrustdataError(f"enrich returned {resp.status_code}")
        entries = resp.json()
        matches = entries[0].get("matches") if entries else None
        if not matches:
            raise CrustdataError(f"enrich returned no match for {company_id}")
        data: dict[str, Any] = matches[0]["company_data"]
        return data

    def credits(self) -> Any:
        resp = self._client.get(BASE_URL + "/account/credits", headers=self._headers)
        evidence.save(self._evidence_dir, "crustdata", "credits", resp.status_code, resp.json())
        if resp.status_code != 200:
            raise CrustdataError(f"credits returned {resp.status_code}")
        return resp.json()
