"""Step 1 of the monthly check: deterministic data collection (no model, no Anthropic key).

Writes to .agent-out/:
  snapshot.json   current facts (versions, advisories, page fingerprints)  -> becomes the next state
  previous.json   state of the last run (from the last bot issue, else .agent/state/baseline.json)
  changes.json    differences computed by this script
  untrusted.json  external texts (release notes, advisory summaries, page excerpts) - DATA ONLY

Usage: python .agent/collect.py [--no-previous-issue]
"""
from __future__ import annotations

import hashlib
import html.parser
import json
import re
import sys
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

from common import (AGENT_DIR, BOT_LOGIN, ROOT, STATE_RE, FetchError, decode_state, http, http_json,
                    load_sources, write_json)

SOURCES = load_sources()
LIMITS = SOURCES["limits"]
TIMEOUT = LIMITS["http_timeout_seconds"]
MAX_BYTES = LIMITS["http_max_bytes"]
untrusted: list[dict] = []


def get(url: str, **kw):
    return http_json(url, timeout=TIMEOUT, max_bytes=MAX_BYTES, **kw)


_SAFE = re.compile(r"[A-Za-z0-9._\-+/:#?=&%]{1,200}")


def safe(value: object, limit: int = 80) -> object:
    """Foreign short values (tags, hrefs, versions) enter the trusted facts only in a narrow alphabet."""
    if value is None or isinstance(value, bool):
        return value
    text = str(value)
    return text if len(text) <= limit and _SAFE.fullmatch(text) else "(verworfen: unerwartetes Format)"


def add_untrusted(source: str, kind: str, text: str, limit: int) -> None:
    text = (text or "").strip()
    if text:
        untrusted.append({"source": source, "kind": kind, "text": text[:limit], "truncated": len(text) > limit})


# --- packages ---------------------------------------------------------------------------------------------

def project_packages() -> dict[str, str]:
    """PackageReference Include/Version from the fork's own project files on the checked-out main."""
    found: dict[str, set[str]] = {}
    for rel in SOURCES["fork"]["projects"]:
        tree = ET.parse(ROOT / rel)
        for ref in tree.iter("PackageReference"):
            name, version = ref.get("Include"), ref.get("Version")
            if name and version:
                found.setdefault(name, set()).add(version)
    return {name: ",".join(sorted(v)) for name, v in sorted(found.items())}


def nuget_registration_entry(package: str, version: str | None) -> dict | None:
    """Catalog entry of one version (or of the newest listed version when version is None)."""
    index = get(f"https://api.nuget.org/v3/registration5-gz-semver2/{package.lower()}/index.json")
    entries = []
    for page in index.get("items", []):
        items = page.get("items")
        if items is None:
            items = get(page["@id"]).get("items", [])
        entries.extend(item["catalogEntry"] for item in items)
    if version is not None:
        return next((e for e in entries if e.get("version", "").lower() == version.lower()), None)
    listed = [e for e in entries if e.get("listed", True)]
    return listed[-1] if listed else None


def nuget_latest_stable(package: str) -> str | None:
    versions = get(f"https://api.nuget.org/v3-flatcontainer/{package.lower()}/index.json").get("versions", [])
    stable = [v for v in versions if "-" not in v]
    return safe(stable[-1]) if stable else None


def osv_ids(package: str, version: str) -> tuple[list[str], dict[str, str]]:
    result = get("https://api.osv.dev/v1/query", method="POST",
                 body={"package": {"name": package, "ecosystem": "NuGet"}, "version": version})
    vulns = result.get("vulns", []) if isinstance(result, dict) else []
    summaries = {safe(v["id"]): (v.get("summary") or v.get("details") or "") for v in vulns}
    return sorted(summaries), summaries


def ghsa_ids(package: str, version: str) -> tuple[list[str], dict[str, str]]:
    query = urllib.parse.urlencode({"ecosystem": "nuget", "affects": f"{package}@{version}", "per_page": 100})
    advisories = get(f"https://api.github.com/advisories?{query}", github=True)
    summaries = {safe(a["ghsa_id"]): f'{a.get("severity", "?")}: {a.get("summary", "")}' for a in advisories}
    return sorted(summaries), summaries


def collect_packages() -> dict:
    out = {}
    for package, versions in project_packages().items():
        entry: dict = {"used": versions}
        try:
            entry["latest_stable"] = nuget_latest_stable(package)
        except FetchError as e:
            entry["latest_stable_error"] = str(e)
        osv_all, ghsa_all = set(), set()
        for version in versions.split(","):
            if not re.fullmatch(r"[0-9][0-9A-Za-z.\-+]*", version):
                continue  # ranges/wildcards are reported as they are, not queried
            try:
                ids, summaries = osv_ids(package, version)
                osv_all.update(ids)
                for vid in ids:
                    add_untrusted(f"osv:{vid}", "advisory", summaries[vid], LIMITS["advisory_text_chars"])
            except FetchError as e:
                entry["osv_error"] = str(e)
            try:
                ids, summaries = ghsa_ids(package, version)
                ghsa_all.update(ids)
                for gid in ids:
                    add_untrusted(f"ghsa:{gid}", "advisory", summaries[gid], LIMITS["advisory_text_chars"])
            except FetchError as e:
                entry["ghsa_error"] = str(e)
        entry["osv"] = sorted(osv_all)
        entry["ghsa"] = sorted(ghsa_all)
        out[package] = entry
    return out


def collect_upstream() -> dict:
    up = SOURCES["upstream"]
    out: dict = {"nuget": {}}
    try:
        repo = get(f"https://api.github.com/repos/{up['repo']}", github=True)
        out["archived"] = bool(repo.get("archived"))
        out["pushed_at"] = safe(repo.get("pushed_at"))
        latest = get(f"https://api.github.com/repos/{up['repo']}/releases?per_page=1", github=True)
        out["latest_release"] = safe(latest[0]["tag_name"]) if latest else None
        advisories = get(f"https://api.github.com/repos/{up['repo']}/security-advisories?per_page=100", github=True)
        out["security_advisories"] = sorted(safe(a["ghsa_id"]) for a in advisories)
    except FetchError as e:
        out["repo_error"] = str(e)
    for package in up["nuget"]:
        info: dict = {}
        try:
            entry = nuget_registration_entry(package, None)
            if entry is None:
                info["status"] = "no listed version"
            else:
                info["latest_listed"] = safe(entry.get("version"))
                deprecation = entry.get("deprecation")
                info["deprecated"] = bool(deprecation)
                if deprecation:
                    info["deprecation_reasons"] = sorted(safe(r) for r in deprecation.get("reasons", []))
                    add_untrusted(f"nuget-deprecation:{package}", "deprecation_message",
                                  deprecation.get("message", ""), LIMITS["advisory_text_chars"])
        except FetchError as e:
            info["status"] = "removed" if str(e) == "HTTP 404" else f"error: {e}"
        out["nuget"][package] = info
    return out


# --- standards --------------------------------------------------------------------------------------------

def collect_releases() -> dict:
    out = {}
    for src in SOURCES["standards"]["github_releases"]:
        entry: dict = {"repo": src["repo"], "report_only": src["report_only"]}
        try:
            releases = get(f"https://api.github.com/repos/{src['repo']}/releases?per_page=5", github=True)
            releases = [r for r in releases if not r.get("draft")]
            if releases:
                top = releases[0]
                entry.update(latest_tag=safe(top["tag_name"]), published_at=safe(top.get("published_at")),
                             prerelease=bool(top.get("prerelease", False)))
                entry["_notes"] = {safe(r["tag_name"]): (r.get("name") or "") + "\n" + (r.get("body") or "")
                                   for r in releases}
            else:
                entry["latest_tag"] = None
        except FetchError as e:
            entry["error"] = str(e)
        out[src["key"]] = entry
    return out


class _Text(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.links: list[tuple[str, str]] = []
        self._skip = 0
        self._href: str | None = None
        self._link_text: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript", "svg"):
            self._skip += 1
        elif tag == "a":
            self._href = dict(attrs).get("href")
            self._link_text = []

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript", "svg") and self._skip:
            self._skip -= 1
        elif tag == "a" and self._href is not None:
            self.links.append((self._href, " ".join("".join(self._link_text).split())))
            self._href = None

    def handle_data(self, data):
        if not self._skip:
            self.parts.append(data)
            if self._href is not None:
                self._link_text.append(data)


VERSION_RE = re.compile(r"(?:ZUGFeRD|Factur-X)[\s\-]*(?:Version\s*|v)?(\d+\.\d+(?:\.\d+)?)", re.IGNORECASE)


def collect_pages() -> dict:
    out = {}
    for src in SOURCES["standards"]["web_pages"]:
        entry: dict = {"url": src["url"]}
        try:
            raw = http(src["url"], timeout=TIMEOUT, max_bytes=MAX_BYTES).decode("utf-8", errors="replace")
            parser = _Text()
            parser.feed(raw)
            text = " ".join(" ".join(parser.parts).split())
            if src["mode"] == "versions":
                entry["versions"] = sorted({m.group(0).split()[0] + " " + m.group(1) for m in VERSION_RE.finditer(text)},
                                           key=str.lower)
                entry["text_sha256"] = hashlib.sha256(text.encode("utf-8")).hexdigest()
                entry["_text"] = text
            else:
                pattern = re.compile(src["link_filter"], re.IGNORECASE)
                news = {safe(href, 200) for href, label in parser.links if href and pattern.search(href + " " + label)}
                entry["links"] = sorted(news)
                entry["_labels"] = {safe(href, 200): label for href, label in parser.links if safe(href, 200) in news}
        except FetchError as e:
            entry["error"] = str(e)
        out[src["key"]] = entry
    return out


# --- own source: XML hardening facts (static, deterministic) ------------------------------------------------

def collect_xml_hardening() -> dict:
    facts = {}
    for rel in SOURCES["fork"]["xml_readers"]:
        code = (ROOT / rel).read_text(encoding="utf-8-sig")
        facts[rel] = {
            "new_XmlDocument": len(re.findall(r"new\s+XmlDocument\s*\(", code)),
            "DtdProcessing_Prohibit": len(re.findall(r"DtdProcessing\.Prohibit", code)),
            "XmlResolver_null": len(re.findall(r"XmlResolver\s*=\s*null", code)),
            "ReadToEnd": len(re.findall(r"\.ReadToEnd\s*\(", code)),
        }
    return facts


# --- previous state ---------------------------------------------------------------------------------------

def previous_state(use_issue: bool) -> tuple[dict, str]:
    if use_issue:
        repo = SOURCES["fork"]["repo"]
        query = urllib.parse.urlencode({"labels": "monatspruefung", "state": "all", "creator": BOT_LOGIN,
                                        "sort": "created", "direction": "desc", "per_page": 20})
        try:
            for issue in get(f"https://api.github.com/repos/{repo}/issues?{query}", github=True):
                user = issue.get("user") or {}
                # Only issues written by the workflow itself carry trusted state; anyone else's text is ignored.
                if user.get("login") != BOT_LOGIN or user.get("type") != "Bot":
                    continue
                match = STATE_RE.search(issue.get("body") or "")
                if match:
                    return decode_state(match.group(1)), f"issue #{issue['number']}"
        except FetchError as e:
            print(f"Vorheriger Stand aus Issues nicht lesbar ({e}), nehme Baseline.", file=sys.stderr)
    return json.loads((AGENT_DIR / "state" / "baseline.json").read_text(encoding="utf-8")), "baseline.json"


# --- diff -------------------------------------------------------------------------------------------------

def public(d: object) -> object:
    """Drops keys starting with '_' (raw texts) - those never enter the state."""
    if isinstance(d, dict):
        return {k: public(v) for k, v in d.items() if not k.startswith("_")}
    return d


def diff(prev: object, cur: object, path: str = "") -> list[str]:
    if isinstance(prev, dict) and isinstance(cur, dict):
        changes = []
        for key in sorted(set(prev) | set(cur)):
            sub = f"{path}.{key}" if path else key
            if key not in prev:
                changes.append(f"neu: {sub} = {cur[key]!r}")
            elif key not in cur:
                changes.append(f"entfallen: {sub} (war {prev[key]!r})")
            else:
                changes.extend(diff(prev[key], cur[key], sub))
        return changes
    if prev != cur:
        return [f"geändert: {path}: {prev!r} -> {cur!r}"]
    return []


def main() -> int:
    raw = {
        "collected_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "packages": collect_packages(),
        "upstream": collect_upstream(),
        "releases": collect_releases(),
        "pages": collect_pages(),
        "xml_hardening": collect_xml_hardening(),
    }
    snapshot = public(raw)
    prev, prev_source = previous_state("--no-previous-issue" not in sys.argv)
    changes = diff({k: v for k, v in prev.items() if k != "collected_at"},
                   {k: v for k, v in snapshot.items() if k != "collected_at"})

    # External texts only where something changed - unchanged sources cost no tokens.
    prev_releases = prev.get("releases", {})
    for key, entry in raw["releases"].items():
        old_tag = prev_releases.get(key, {}).get("latest_tag")
        if entry.get("latest_tag") == old_tag:
            continue
        for tag, notes in entry.get("_notes", {}).items():  # newest first, up to the known tag
            if tag == old_tag:
                break
            add_untrusted(f"release:{key}:{tag}", "release_notes", notes, LIMITS["release_notes_chars"])
    prev_pages = prev.get("pages", {})
    for key, entry in raw["pages"].items():
        if "_text" in entry and entry.get("text_sha256") != prev_pages.get(key, {}).get("text_sha256"):
            add_untrusted(f"page:{key}", "web_page_excerpt", entry["_text"], LIMITS["web_excerpt_chars"])
        if "_labels" in entry:
            old = set(prev_pages.get(key, {}).get("links", []))
            for href, label in entry["_labels"].items():
                if href not in old:
                    add_untrusted(f"page:{key}:link", "news_link_title", f"{label} ({href})", 300)

    budget = LIMITS["untrusted_total_chars"]
    kept = []
    for item in untrusted:
        if budget - len(item["text"]) < 0:
            item = {**item, "text": item["text"][:max(budget, 0)], "truncated": True}
        budget -= len(item["text"])
        if item["text"]:
            kept.append(item)

    write_json("snapshot.json", snapshot)
    write_json("previous.json", {"source": prev_source, "state": prev})
    write_json("changes.json", changes)
    write_json("untrusted.json", kept)
    errors = [c for c in diff({}, snapshot) if "error" in c or "removed" in c]
    print(f"Gesammelt: {len(changes)} Änderungen gegenüber {prev_source}, {len(kept)} externe Texte, "
          f"{len(errors)} Quellen mit Fehlern.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
