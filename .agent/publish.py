"""Step 3 of the monthly check: create exactly one issue (no Anthropic key in this step).

  python .agent/publish.py            -> "Monatsprüfung YYYY-MM" with assessment, fact appendix and state
  python .agent/publish.py --failed   -> "Monatsprüfung YYYY-MM fehlgeschlagen" with the error class only

Environment: GH_TOKEN (GITHUB_TOKEN, issues: write), GITHUB_REPOSITORY, GITHUB_RUN_ID, GITHUB_SERVER_URL.
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone

from common import OUT_DIR, STATE_MARKER, FetchError, encode_state, http_json, load_sources

LABEL = "monatspruefung"
MAX_ASSESSMENT_CHARS = 30_000


def neutralize(text: str) -> str:
    """Model text is derived from foreign text: no pings, no cross-repo references, no hidden blocks."""
    text = text[:MAX_ASSESSMENT_CHARS]
    text = text.replace("<!--", "&lt;!--")  # nobody but this script writes HTML comments (state marker)
    text = re.sub(r"(?<![\w`])@(?=[A-Za-z0-9])", "@​", text)  # no @mentions
    text = re.sub(r"\b([\w.-]+/[\w.-]+)#(\d+)", r"\1&#35;\2", text)  # no backlinks into other repos
    return text


def run_url() -> str:
    server = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
    repo, run = os.environ.get("GITHUB_REPOSITORY", ""), os.environ.get("GITHUB_RUN_ID", "")
    return f"{server}/{repo}/actions/runs/{run}" if repo and run else "(lokaler Lauf)"


MODEL_SETTING = "`AGENT_MODEL` in `.github/workflows/monatspruefung.yml`"


def model_notice(models: dict) -> str:
    """Visible notice written by the script (not the model): newer model of the same line or deprecation."""
    if not models or models.get("error"):
        return ""
    lines = []
    if models.get("newer"):
        newest = models["newer"][0]
        lines.append(f"Neueres Modell der Linie `{models.get('line')}` verfügbar: `{newest['id']}` "
                     f"(veröffentlicht {newest['released']}), eingestellt ist `{models['configured']}`.")
    if models.get("lifecycle") and models["lifecycle"] != "active":
        lines.append(f"Das eingestellte Modell `{models['configured']}` ist `{models['lifecycle']}`"
                     + (f", Abschaltung geplant am {models['retires_at']}" if models.get("retires_at") else "") + ".")
    if not lines:
        return ""
    lines.append(f"Umstellen: {MODEL_SETTING} per Pull Request ändern; vorher die Migrationshinweise des neuen "
                 "Modells lesen (Parameter wie `thinking`/`effort` können sich ändern).")
    return "> [!NOTE]\n" + "\n".join(f"> {line}" for line in lines) + "\n"


def model_line(models: dict) -> str:
    if not models:
        return "Modellprüfung: nicht gelaufen"
    if models.get("error"):
        return f"Modellprüfung: fehlgeschlagen (`{models['error']}`), eingestellt `{models.get('configured')}`"
    newer = ", ".join(m["id"] for m in models.get("newer", [])) or "keins"
    return (f"Modell: `{models['configured']}` (Linie {models.get('line')}, {models.get('lifecycle')}); "
            f"neuere Modelle der Linie: {newer}")


def appendix(snapshot: dict, previous: dict, changes: list[str], models: dict | None = None) -> str:
    lines = ["", "---", "", "<details><summary>Fakten des Skripts (ohne Modell)</summary>", "",
             f"Vergleich mit: {previous['source']} (Stand {previous['state'].get('collected_at', '?')})", ""]
    lines += ["**Änderungen:**", ""] + ([f"- `{c}`" for c in changes] or ["- keine"]) + [""]
    lines += ["| Paket | genutzt | neueste stabile | OSV | GHSA |", "|---|---|---|---|---|"]
    for name, p in snapshot.get("packages", {}).items():
        lines.append(f"| {name} | {p.get('used')} | {p.get('latest_stable', p.get('latest_stable_error', '?'))} "
                     f"| {', '.join(p.get('osv', [])) or '–'} | {', '.join(p.get('ghsa', [])) or '–'} |")
    lines += ["", "| Quelle | Stand |", "|---|---|"]
    for key, r in snapshot.get("releases", {}).items():
        lines.append(f"| [{key}](https://github.com/{r['repo']}/releases) | {r.get('latest_tag', r.get('error'))} |")
    for key, p in snapshot.get("pages", {}).items():
        lines.append(f"| [{key}]({p['url']}) | {', '.join(p.get('versions', [])) or p.get('error', 'Links: ' + str(len(p.get('links', []))))} |")
    up = snapshot.get("upstream", {})
    lines += ["", f"Original: archiviert={up.get('archived')}, letztes Release {up.get('latest_release')}, "
              f"NuGet {json.dumps(up.get('nuget', {}), ensure_ascii=False)}", "", model_line(models or {}), "",
              f"Lauf: {run_url()}", "", "</details>"]
    return "\n".join(lines)


def create_issue(title: str, body: str) -> None:
    repo = os.environ.get("GITHUB_REPOSITORY") or load_sources()["fork"]["repo"]
    issue = http_json(f"https://api.github.com/repos/{repo}/issues", method="POST", github=True,
                      body={"title": title, "body": body, "labels": [LABEL]})
    print(f"Issue #{issue['number']} angelegt.")


def main() -> int:
    month = datetime.now(timezone.utc).strftime("%Y-%m")
    try:
        if "--failed" in sys.argv:
            error_file = OUT_DIR / "error.json"
            error = json.loads(error_file.read_text(encoding="utf-8")) if error_file.exists() else {}
            body = ("Der Lauf der Monatsprüfung ist fehlgeschlagen. Es wurde kein Prüfbericht erstellt.\n\n"
                    f"- Schritt: {error.get('step', 'unbekannt (siehe Lauf)')}\n"
                    f"- Fehlerklasse: `{error.get('class', 'unbekannt')}`"
                    + (f" (HTTP {error['status']})" if error.get("status") else "") + "\n"
                    f"- Lauf: {run_url()}\n\n"
                    "Typische Ursachen: Secret `ANTHROPIC_API_KEY` fehlt oder ist ungültig (`AuthenticationError`), "
                    "Guthaben/Limit erschöpft (`RateLimitError`, `PermissionDeniedError`), Quelle nicht erreichbar.")
            create_issue(f"Monatsprüfung {month} fehlgeschlagen", body)
            return 0
        snapshot = json.loads((OUT_DIR / "snapshot.json").read_text(encoding="utf-8"))
        previous = json.loads((OUT_DIR / "previous.json").read_text(encoding="utf-8"))
        changes = json.loads((OUT_DIR / "changes.json").read_text(encoding="utf-8"))
        assessment = neutralize((OUT_DIR / "assessment.md").read_text(encoding="utf-8"))
        models_file = OUT_DIR / "models.json"
        models = json.loads(models_file.read_text(encoding="utf-8")) if models_file.exists() else {}
        notice = model_notice(models)
        body = (f"{notice + chr(10) if notice else ''}{assessment}\n{appendix(snapshot, previous, changes, models)}\n\n"
                f"<!-- {STATE_MARKER} {encode_state(snapshot)} -->\n")
        create_issue(f"Monatsprüfung {month}", body)
        return 0
    except FetchError as e:
        print(f"Issue konnte nicht angelegt werden: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
