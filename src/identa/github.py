"""GitHub REST calls for one vendor-register repository.

No call here retries. Writes are serialised with a lock because GitHub documents that
concurrent create/update/delete file requests conflict.
"""

from __future__ import annotations

import base64
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx

from identa import evidence
from identa.tracing import tool

API = "https://api.github.com"
API_VERSION = "2022-11-28"


@dataclass(frozen=True)
class Reply:
    status: int
    body: Any


class GitHub:
    def __init__(
        self,
        token: str,
        owner: str,
        repo: str,
        evidence_dir: Path,
        author: tuple[str, str],
        client: httpx.Client | None = None,
        record: bool = True,
    ) -> None:
        self._client = client or httpx.Client(timeout=30)
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": API_VERSION,
        }
        self._author = {"name": author[0], "email": author[1]}
        self.owner = owner
        self.repo = repo
        self._evidence_dir = evidence_dir
        self._record = record
        self._write_lock = threading.Lock()

    def _url(self, path: str) -> str:
        return f"{API}/repos/{self.owner}/{self.repo}{path}"

    def _call(self, label: str, method: str, path: str, **kw: Any) -> Reply:
        resp = self._client.request(method, self._url(path), headers=self._headers, **kw)
        try:
            body: Any = resp.json()
        except ValueError:
            body = resp.text
        if self._record:
            evidence.save(self._evidence_dir, "github", label, resp.status_code, body)
        return Reply(resp.status_code, body)

    def _write(self, label: str, method: str, path: str, **kw: Any) -> Reply:
        with self._write_lock:
            return self._call(label, method, path, **kw)

    @tool("github.get_ref")
    def get_ref(self, branch: str) -> Reply:
        return self._call("get_ref", "GET", f"/git/ref/heads/{quote(branch, safe='/')}")

    @tool("github.create_ref")
    def create_ref(self, branch: str, sha: str) -> Reply:
        return self._write(
            "create_ref", "POST", "/git/refs", json={"ref": f"refs/heads/{branch}", "sha": sha}
        )

    @tool("github.put_file")
    def put_file(self, path: str, branch: str, message: str, content: str) -> Reply:
        encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")
        return self._write(
            "put_file",
            "PUT",
            f"/contents/{quote(path, safe='/')}",
            json={
                "message": message,
                "content": encoded,
                "branch": branch,
                "author": self._author,
                "committer": self._author,
            },
        )

    @tool("github.get_file")
    def get_file(self, path: str, branch: str) -> Reply:
        return self._call(
            "get_file", "GET", f"/contents/{quote(path, safe='/')}", params={"ref": branch}
        )

    @tool("github.open_pr")
    def open_pr(self, branch: str, base: str, title: str, body: str) -> Reply:
        return self._write(
            "open_pr",
            "POST",
            "/pulls",
            json={"title": title, "head": branch, "base": base, "body": body},
        )

    @tool("github.list_prs")
    def list_prs(self, branch: str) -> Reply:
        return self._call(
            "list_prs",
            "GET",
            "/pulls",
            params={"head": f"{self.owner}:{branch}", "state": "all", "per_page": 100},
        )

    @tool("github.matching_refs")
    def matching_refs(self, prefix: str) -> Reply:
        """Branches whose name starts with prefix. Paginated: returns every page, merged."""
        refs: list[Any] = []
        page = 1
        while True:
            reply = self._call(
                "matching_refs",
                "GET",
                f"/git/matching-refs/heads/{prefix}",
                params={"per_page": 100, "page": page},
            )
            if reply.status != 200 or not isinstance(reply.body, list):
                return reply
            refs.extend(reply.body)
            if len(reply.body) < 100:
                return Reply(200, refs)
            page += 1

    @tool("github.list_all_prs")
    def list_all_prs(self) -> Reply:
        """Every pull request in the repository, any state, merged across pages."""
        prs: list[Any] = []
        page = 1
        while True:
            reply = self._call(
                "list_all_prs",
                "GET",
                "/pulls",
                params={"state": "all", "per_page": 100, "page": page},
            )
            if reply.status != 200 or not isinstance(reply.body, list):
                return reply
            prs.extend(reply.body)
            if len(reply.body) < 100:
                return Reply(200, prs)
            page += 1
