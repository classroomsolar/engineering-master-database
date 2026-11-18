#!/usr/bin/env python3
"""Deterministic Repository Security, Privacy Boundary & Governance Audit.

Scans code, static assets, configuration, and repository boundaries without mutating any files.
Outputs: 01_Engineering_Equipment_Database/website/dist/verification/security_governance_audit.json
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
WEBSITE_DIR = TOOLS_DIR.parent
DIST_DIR = WEBSITE_DIR / "dist"
REPO_ROOT = WEBSITE_DIR.parent.parent
OUT_PATH = DIST_DIR / "verification" / "security_governance_audit.json"

SECRET_PATTERNS = [
    ("Google API Key", re.compile(r"AIza[0-9A-Za-z\-_]{35}")),
    ("OpenAI / Anthropic Key", re.compile(r"\bsk-(?:proj-|ant-)?[A-Za-z0-9\-_]{24,}\b")),
    ("GitHub PAT", re.compile(r"\b(?:ghp|gho|ghu|ghs|github_pat)_[A-Za-z0-9_]{20,}\b")),
    ("AWS Access Key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("Private Key PEM", re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----")),
    ("Hardcoded Bearer Secret", re.compile(r"Authorization[\"'\s:=]+Bearer\s+[A-Za-z0-9\-_.]{20,}", re.I)),
]

UNSAFE_WEB_PATTERNS = [
    ("eval()", re.compile(r"\beval\s*\(")),
    ("new Function()", re.compile(r"\bnew\s+Function\s*\(")),
    ("document.write()", re.compile(r"\bdocument\.write\s*\(")),
    ("window.alert()", re.compile(r"\bwindow\.alert\s*\(")),
    ("window.open()", re.compile(r"\bwindow\.open\s*\(")),
    ("innerHTML sink", re.compile(r"\.innerHTML\s*=")),
]

TEXT_EXTS = {".js", ".mjs", ".ts", ".tsx", ".jsx", ".html", ".css", ".py", ".json", ".md", ".txt", ".csv", ".yml", ".yaml", ".env", ".example"}
SKIP_DIRS = {"node_modules", ".git", "__pycache__", ".playwright-cli"}


def scan_tree() -> dict:
    files_scanned = 0
    secret_hits = []
    web_sink_hits = []
    insecure_http_links = []

    for path in sorted(REPO_ROOT.rglob("*")):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        rel = path.relative_to(REPO_ROOT).as_posix()
        # Skip huge raw data chunks when scanning secrets (only equipment catalogs; check verification + code + docs + server)
        if rel.startswith("01_Engineering_Equipment_Database/website/dist/data/s") and rel.endswith(".js"):
            continue
        if rel.startswith("01_Engineering_Equipment_Database/website/dist/collections/") and path.name != "index.js":
            continue
        if path.suffix.lower() not in TEXT_EXTS and not path.name.startswith(".env"):
            continue
        if path.stat().st_size > 2_000_000:
            continue

        files_scanned += 1
        text = path.read_text(encoding="utf-8", errors="replace")

        for label, pat in SECRET_PATTERNS:
            for m in pat.finditer(text):
                # Ignore placeholder examples
                snippet = m.group(0)
                if "YOUR_" in snippet or "EXAMPLE" in snippet or "xxxx" in snippet.lower():
                    continue
                secret_hits.append({"file": rel, "pattern": label, "preview": snippet[:10] + "..."})

        # Check unsafe DOM/JS sinks strictly inside served website assets + server.js
        if rel in ("server.js", "01_Engineering_Equipment_Database/website/dist/index.html") or rel.startswith("01_Engineering_Equipment_Database/website/dist/assets/"):
            for label, pat in UNSAFE_WEB_PATTERNS:
                for m in pat.finditer(text):
                    # innerHTML in app.js only renders trusted static SVG path literals from ICONS const; still report accurately!
                    line_no = text[:m.start()].count("\n") + 1
                    web_sink_hits.append({
                        "file": rel,
                        "line": line_no,
                        "pattern": label,
                        "mitigated": label == "innerHTML sink" and "icon(" in text.splitlines()[line_no - 1],
                    })

            # Check plain http:// external links inside HTML/JS/CSS
            for m in re.finditer(r"http://[^\s\"'<>)]+", text):
                url = m.group(0)
                if "localhost" in url or "127.0.0.1" in url or "${HOST}" in url or "w3.org" in url:
                    continue
                insecure_http_links.append({"file": rel, "url": url})

    # Public vs Private Boundary Check
    dist_paths = [p.relative_to(DIST_DIR).as_posix() for p in DIST_DIR.rglob("*") if p.is_file()]
    private_leak = [p for p in dist_paths if any(k in p.lower() for k in ("marketmind", "trading", "alpaca", "portfolio", "03_", "04_"))]

    # Express server & HTML header checks
    html = (DIST_DIR / "index.html").read_text(encoding="utf-8")
    app_js = (DIST_DIR / "assets" / "app.js").read_text(encoding="utf-8") if (DIST_DIR / "assets" / "app.js").is_file() else ""
    server_js = (REPO_ROOT / "server.js").read_text(encoding="utf-8") if (REPO_ROOT / "server.js").is_file() else ""
    controls = [
        {"control": "Read-only static architecture (no write/mutation endpoints in server.js)", "status": "PASS" if ("app.post" not in server_js and "app.put" not in server_js and "app.delete" not in server_js) else "WARN"},
        {"control": "Zero leaked credentials / API secrets across repository", "status": "PASS" if not secret_hits else "FAIL", "count": len(secret_hits)},
        {"control": "Public website isolation from 03_MarketMind_Financial_Trading & 04_Google_AI_Studio_Review", "status": "PASS" if not private_leak else "FAIL", "count": len(private_leak)},
        {"control": "Referrer privacy policy (<meta name='referrer' content='no-referrer'>)", "status": "PASS" if 'name="referrer" content="no-referrer"' in html else "WARN"},
        {"control": "External tabnabbing protection (rel='noopener' / 'noopener noreferrer')", "status": "PASS" if ("noopener" in (html + app_js)) else "WARN"},
        {"control": "No plain http:// external asset URLs in website HTML/JS/CSS", "status": "PASS" if not insecure_http_links else "WARN", "count": len(insecure_http_links)},
        {"control": "Immutable .env cleanliness (no .env committed in repo root)", "status": "PASS" if not (REPO_ROOT / ".env").exists() else "WARN"},
        {"control": "No eval() / new Function() / window.alert() / window.open() in frontend", "status": "PASS" if not any(h["pattern"] != "innerHTML sink" for h in web_sink_hits) else "WARN"},
    ]

    unmitigated_sinks = [h for h in web_sink_hits if not h["mitigated"]]
    overall = "PASS" if (not secret_hits and not private_leak and all(c["status"] == "PASS" for c in controls)) else "REVIEW_NOTED"

    report = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "overallStatus": overall,
        "filesScanned": files_scanned,
        "secretFindings": secret_hits,
        "privateBoundaryLeaks": private_leak,
        "insecureHttpLinks": insecure_http_links,
        "webSinkAudit": {
            "total": len(web_sink_hits),
            "unmitigated": len(unmitigated_sinks),
            "findings": web_sink_hits,
        },
        "controls": controls,
        "repositoryDomains": {
            "publicEngineeringWebsite": "01_Engineering_Equipment_Database",
            "masterSourceAndAudits": "02_Engineering_Master_Database",
            "privateTradingExcludedFromDist": "03_MarketMind_Financial_Trading",
            "governanceReviews": "04_Google_AI_Studio_Review",
            "requirementsAndContinuation": "05_Requirements_Plans_and_Continuation",
            "verificationHarness": "06_Verification",
        },
    }

    OUT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "overallStatus": overall,
        "filesScanned": files_scanned,
        "secretFindings": len(secret_hits),
        "privateBoundaryLeaks": len(private_leak),
        "insecureHttpLinks": len(insecure_http_links),
        "unmitigatedSinks": len(unmitigated_sinks),
        "controlsPassed": f"{sum(1 for c in controls if c['status'] == 'PASS')}/{len(controls)}",
    }, indent=2))


if __name__ == "__main__":
    scan_tree()
