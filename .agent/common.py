"""Shared helpers of the monthly check agent (standard library only).

Security model, see docs/AGENT.md: everything fetched from outside is data, never instruction.
This module never prints tokens, request headers or response bodies of failed requests.
"""
from __future__ import annotations

import base64
import gzip
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AGENT_DIR = ROOT / ".agent"
OUT_DIR = Path(os.environ.get("AGENT_OUT", ROOT / ".agent-out"))
STATE_MARKER = "monatspruefung-state:v1"
STATE_RE = re.compile(r"<!-- " + re.escape(STATE_MARKER) + r" ([A-Za-z0-9+/=]+) -->")
BOT_LOGIN = "github-actions[bot]"
USER_AGENT = "zugferd-csharp-maintained-monthly-check"


def load_sources() -> dict:
    return json.loads((AGENT_DIR / "sources.json").read_text(encoding="utf-8"))


class FetchError(Exception):
    """Expected fetch failure. The message holds only a short class (e.g. 'HTTP 404'), never response content."""


def http(url: str, *, method: str = "GET", body: dict | None = None, github: bool = False,
         timeout: float = 30, max_bytes: int = 5_000_000) -> bytes:
    headers = {"User-Agent": USER_AGENT, "Accept-Encoding": "gzip"}
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if github:
        headers["Accept"] = "application/vnd.github+json"
        headers["X-GitHub-Api-Version"] = "2022-11-28"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    if github and url.startswith("https://api.github.com/"):
        token = os.environ.get("GH_TOKEN", "")
        if token:
            # Unredirected: a redirect to another host must never carry the token.
            request.add_unredirected_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read(max_bytes + 1)
            if len(raw) > max_bytes:
                raise FetchError("response too large")
            if response.headers.get("Content-Encoding", "").lower() == "gzip" or raw[:2] == b"\x1f\x8b":
                raw = gzip.decompress(raw)
            return raw
    except urllib.error.HTTPError as e:
        raise FetchError(f"HTTP {e.code}") from None
    except urllib.error.URLError as e:
        raise FetchError(f"network: {type(e.reason).__name__}") from None
    except TimeoutError:
        raise FetchError("timeout") from None


def http_json(url: str, **kwargs) -> object:
    return json.loads(http(url, **kwargs).decode("utf-8"))


def encode_state(state: dict) -> str:
    raw = json.dumps(state, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return base64.b64encode(gzip.compress(raw, mtime=0)).decode("ascii")


def decode_state(blob: str) -> dict:
    return json.loads(gzip.decompress(base64.b64decode(blob, validate=True)).decode("utf-8"))


def write_json(name: str, data: object) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / name).write_text(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")


def read_json(name: str) -> object:
    return json.loads((OUT_DIR / name).read_text(encoding="utf-8"))
