#!/usr/bin/env python3
"""Packages clean website dist fallback ZIP and complete GitHub-ready repository ZIP."""
from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
WEBSITE_DIR = TOOLS_DIR.parent
EED_DIR = WEBSITE_DIR.parent
REPO_ROOT = EED_DIR.parent
DIST_DIR = WEBSITE_DIR / "dist"
EXPORTS_DIR = REPO_ROOT / "exports"

SKIP_DIST_FILES = {"Inventory.csv", "README.txt", "Verification_Report.txt"}


def iter_clean_dist_files() -> list[Path]:
    out = []
    for p in sorted(DIST_DIR.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(DIST_DIR)
        if rel.parts[0] == "spreadsheets" or p.suffix.lower() == ".xlsx":
            continue
        if p.name in SKIP_DIST_FILES:
            continue
        out.append(p)
    return out


def build_zips() -> dict:
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    dist_files = iter_clean_dist_files()
    tool_files = [p for p in sorted(TOOLS_DIR.glob("*.py")) if p.is_file()]

    # 1. Website dist + tools ZIP (matches lib/zip_dist_fallback.mjs expectations)
    web_zip_path = EXPORTS_DIR / "engineering-equipment-database-website.zip"
    with zipfile.ZipFile(web_zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for p in dist_files:
            zf.write(p, f"dist/{p.relative_to(DIST_DIR).as_posix()}")
        for p in tool_files:
            zf.write(p, f"tools/{p.name}")

    # 2. Complete standalone GitHub-ready repository ZIP
    gh_zip_path = EXPORTS_DIR / "engineering-equipment-database-github.zip"
    gh_root_files = [
        REPO_ROOT / "package.json",
        REPO_ROOT / "server.js",
        REPO_ROOT / ".gitignore",
        REPO_ROOT / ".env.example",
        REPO_ROOT / "README.md",
    ]
    gh_extra_dirs = [
        REPO_ROOT / "lib",
        REPO_ROOT / "tests",
    ]

    gh_count = 0
    with zipfile.ZipFile(gh_zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for p in gh_root_files:
            if p.is_file():
                zf.write(p, p.relative_to(REPO_ROOT).as_posix())
                gh_count += 1
        for d in gh_extra_dirs:
            if d.is_dir():
                for p in sorted(d.rglob("*")):
                    if p.is_file() and "__pycache__" not in p.parts:
                        zf.write(p, p.relative_to(REPO_ROOT).as_posix())
                        gh_count += 1
        for p in dist_files:
            zf.write(p, p.relative_to(REPO_ROOT).as_posix())
            gh_count += 1
        for p in tool_files:
            zf.write(p, p.relative_to(REPO_ROOT).as_posix())
            gh_count += 1

    return {
        "websiteZip": {
            "path": web_zip_path.relative_to(REPO_ROOT).as_posix(),
            "entries": len(dist_files) + len(tool_files),
            "bytes": web_zip_path.stat().st_size,
            "sha256": hashlib.sha256(web_zip_path.read_bytes()).hexdigest(),
        },
        "githubZip": {
            "path": gh_zip_path.relative_to(REPO_ROOT).as_posix(),
            "entries": gh_count,
            "bytes": gh_zip_path.stat().st_size,
            "sha256": hashlib.sha256(gh_zip_path.read_bytes()).hexdigest(),
        },
    }


if __name__ == "__main__":
    print(json.dumps(build_zips(), indent=2))
