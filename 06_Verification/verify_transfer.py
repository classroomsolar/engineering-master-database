"""Verify original transfer identities without rewriting the historical manifest.

``inputs`` protects all historical files except the explicitly maintained public
application code below. Differences in that code are still included in the report.
``snapshot`` additionally requires every historical byte and forbids new sources.
Git metadata, local .venv environments, Python caches and explicitly named *new*
output paths are ignored.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys
import zipfile
import zlib

SITE = "01_Engineering_Equipment_Database/website/"
EDITABLE_CODE = frozenset({
    "06_Verification/verify_transfer.py",
    SITE + "tools/build_collections.py",
    SITE + "tools/verify_collections.py",
    SITE + "dist/index.html",
    SITE + "dist/assets/app.js",
    SITE + "dist/assets/app.css",
})
NEW_SOURCE_DIRECTORIES = (
    ".github/workflows/", "06_Verification/tests/", "docs/",
    SITE + "tools/", SITE + "tests/", SITE + "docs/",
)
NEW_SOURCE_FILES = frozenset({"README.md", ".gitignore"})


def safe_name(value: object) -> str:
    """Require a canonical relative POSIX path, with no alternate spelling."""
    if not isinstance(value, str) or not value or "\\" in value:
        raise ValueError("path must be a nonempty relative POSIX string")
    if any(ord(char) < 32 for char in value) or ":" in value:
        raise ValueError("path contains a control character or drive separator")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in (".", "..", "") for part in value.split("/")):
        raise ValueError("path must be canonical and remain inside the root")
    if path.as_posix() != value or ".git" in path.parts:
        raise ValueError("path is not canonical or addresses Git metadata")
    return value


def no_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key: " + key)
        result[key] = value
    return result


def read_manifest(path: Path) -> list[dict]:
    if path.is_symlink():
        raise ValueError("manifest must not be a symlink")
    document = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=no_duplicate_keys)
    if not isinstance(document, dict) or document.get("algorithm") != "SHA-256":
        raise ValueError("manifest must declare algorithm SHA-256")
    files = document.get("files")
    if not isinstance(files, list) or not files:
        raise ValueError("manifest files must be a nonempty list")
    seen = set()
    for item in files:
        if not isinstance(item, dict):
            raise ValueError("manifest file entries must be objects")
        name = safe_name(item.get("path"))
        if name == "SHA256_MANIFEST.json" or name in seen:
            raise ValueError("duplicate or self-referential manifest path: " + name)
        seen.add(name)
        size, digest = item.get("bytes"), item.get("sha256")
        if type(size) is not int or size < 0:
            raise ValueError("invalid byte count: " + name)
        if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
            raise ValueError("invalid SHA-256: " + name)
    return files


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def has_symlink(root: Path, name: str) -> bool:
    current = root
    for part in PurePosixPath(name).parts:
        current /= part
        if current.is_symlink():
            return True
    return False


def ignored_metadata(name: str) -> bool:
    parts = PurePosixPath(name).parts
    return any(part in (".git", ".venv", "__pycache__") for part in parts) or name.endswith((".pyc", ".pyo"))


def under(name: str, directories: list[str]) -> bool:
    return any(name == directory or name.startswith(directory + "/") for directory in directories)


def verify(root: Path, mode: str, outputs: list[str]) -> dict:
    report = {"result": "FAIL", "mode": mode, "manifest": "SHA256_MANIFEST.json",
              "filesChecked": 0, "protectedFiles": 0, "historicalCodeChanges": [],
              "addedFiles": [], "ignoredOutputs": [], "failures": []}
    failures = report["failures"]
    try:
        files = read_manifest(root / "SHA256_MANIFEST.json")
    except (OSError, ValueError, TypeError) as exc:
        failures.append("Invalid manifest: " + str(exc))
        return report
    expected = {item["path"] for item in files}
    for item in files:
        name = item["path"]
        protected = mode == "snapshot" or name not in EDITABLE_CODE
        report["protectedFiles"] += int(protected)
        path = root / name
        if has_symlink(root, name):
            failures.append("Symlink in historical path: " + name)
            continue
        if not path.is_file():
            failures.append("Missing: " + name)
            continue
        try:
            actual_size, actual_hash = path.stat().st_size, digest(path)
            report["filesChecked"] += 1
            if actual_size != item["bytes"] or actual_hash != item["sha256"]:
                if name in EDITABLE_CODE:
                    report["historicalCodeChanges"].append({
                        "path": name, "originalSha256": item["sha256"], "currentSha256": actual_hash,
                        "originalBytes": item["bytes"], "currentBytes": actual_size,
                    })
                if protected:
                    failures.append("Changed: " + name)
            if path.suffix.lower() in (".zip", ".xlsx", ".xlsm"):
                with zipfile.ZipFile(path) as archive:
                    bad = archive.testzip()
                    if bad:
                        failures.append("Archive CRC failure: " + name + " / " + bad)
        except (OSError, ValueError, RuntimeError, zipfile.BadZipFile, EOFError, zlib.error) as exc:
            failures.append("Unreadable or invalid archive: " + name + " / " + str(exc))
    def walk_error(exc):
        failures.append("Cannot inspect directory: " + str(exc))
    for directory, directories, names in os.walk(root, followlinks=False, onerror=walk_error):
        base = Path(directory)
        # Inspect symlink directories as entries without descending into them.
        entries = names + [name for name in directories if (base / name).is_symlink()]
        directories[:] = [name for name in directories if not (base / name).is_symlink()
                           and not ignored_metadata((base / name).relative_to(root).as_posix())]
        for entry in entries:
            path = base / entry
            name = path.relative_to(root).as_posix()
            if name in expected or name == "SHA256_MANIFEST.json" or ignored_metadata(name):
                continue
            if path.is_symlink():
                failures.append("Unmanifested symlink: " + name)
            elif under(name, outputs):
                report["ignoredOutputs"].append(name)
            else:
                report["addedFiles"].append(name)
                allowed = name in NEW_SOURCE_FILES or name.startswith(NEW_SOURCE_DIRECTORIES)
                if mode == "snapshot" or not allowed:
                    failures.append("Unmanifested: " + name)
    for key in ("addedFiles", "ignoredOutputs", "failures"):
        report[key].sort()
    report["result"] = "FAIL" if failures else "PASS"
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--mode", choices=("inputs", "snapshot"), default="inputs")
    parser.add_argument("--allow-output", action="append", default=[], metavar="RELATIVE_PATH",
                        help="ignore new files at this path; never skips historical files")
    parser.add_argument("--output", type=Path, help="also write JSON here; stdout always receives JSON")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        outputs = [safe_name(name) for name in args.allow_output]
        if not root.is_dir():
            raise ValueError("root must be an existing directory")
        if args.output:
            destination = args.output.absolute()
            if destination.is_symlink() or any(parent.is_symlink() for parent in destination.parents):
                raise ValueError("output path must not contain symlinks")
            if destination.resolve() == root / "SHA256_MANIFEST.json":
                raise ValueError("output must not overwrite the historical manifest")
            # Any preexisting file is evidence/source; never replace it implicitly.
            if destination.exists():
                raise ValueError("output already exists; choose a new report path")
            try:
                relative = destination.relative_to(root).as_posix()
            except ValueError:
                relative = None
            if relative:
                safe_name(relative)
                historical = {item["path"] for item in read_manifest(root / "SHA256_MANIFEST.json")}
                if relative in historical:
                    raise ValueError("output must not overwrite a historical manifest path")
                outputs.append(relative)
        report = verify(root, args.mode, outputs)
        if args.output:
            destination.parent.mkdir(parents=True, exist_ok=True)
            # Exclusive creation prevents accidentally overwriting earlier evidence.
            with destination.open("x", encoding="utf-8") as stream:
                stream.write(json.dumps(report, indent=2) + "\n")
    except (OSError, ValueError) as exc:
        report = {"result": "FAIL", "mode": args.mode, "failures": [str(exc)]}
    print(json.dumps(report, indent=2))
    return 0 if report["result"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
