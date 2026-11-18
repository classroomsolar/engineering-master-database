#!/usr/bin/env python3
"""Cleans website dist collections & curates references without touching 02_Engineering_Master_Database."""
from __future__ import annotations

import base64
import gzip
import hashlib
import json
import re
from pathlib import Path

WEBSITE_DIR = Path(__file__).resolve().parent.parent
DIST_DIR = WEBSITE_DIR / "dist"
COLLECTIONS_DIR = DIST_DIR / "collections"
VERIF_DIR = DIST_DIR / "verification"

KEPT_REF_GROUPS = {
    "s002": ("Cable & conductor standards", "Cable types & thermal specs"),
    "s033": ("Cable & conductor standards", "Conductor materials"),
    "s034": ("Cable & conductor standards", "Conductor sizes (AWG / kcmil)"),
    "s035": ("Cable & conductor standards", "Cable short-circuit k-factors"),
    "s036": ("Cable & conductor standards", "Insulation thermal classes"),
    "s048": ("Cable & conductor standards", "NEC ampacity table routing"),
    "s049": ("Cable & conductor standards", "Ampacity ambient temp factors"),
    "s050": ("Cable & conductor standards", "Ampacity bundling (CCC) factors"),
    "s051": ("Cable & conductor standards", "Ampacity parameters"),
    "s052": ("Cable & conductor standards", "NEC 2020 ampacity tables"),
    "s053": ("Cable & conductor standards", "NEC 2023 ampacity tables"),
    "s056": ("Cable & conductor standards", "Cable fault current limits"),
    "s062": ("Cable & conductor standards", "Cable physical dimensions"),
    "s066": ("Cable & conductor standards", "Cable AC impedance defaults"),
    "s077": ("Cable & conductor standards", "Conductor physical properties"),
    "s042": ("Tray, conduit & grounding rules", "Box fill volume allowances"),
    "s058": ("Tray, conduit & grounding rules", "Tray thermal expansion rules"),
    "s060": ("Tray, conduit & grounding rules", "Cable cleat size mapping"),
    "s061": ("Tray, conduit & grounding rules", "Tray accessory rules"),
    "s063": ("Tray, conduit & grounding rules", "NEC ladder & solid tray fill"),
    "s064": ("Tray, conduit & grounding rules", "NEC channel tray fill"),
    "s065": ("Tray, conduit & grounding rules", "Tray engineering defaults"),
    "s067": ("Tray, conduit & grounding rules", "Tray EGC minimum metal area"),
    "s068": ("Tray, conduit & grounding rules", "EGC size by OCPD rating"),
    "s069": ("Tray, conduit & grounding rules", "EGC size OCPD thresholds"),
    "s070": ("Tray, conduit & grounding rules", "Tray EGC area thresholds"),
    "s071": ("Tray, conduit & grounding rules", "Tray width dimension codes"),
    "s072": ("Tray, conduit & grounding rules", "Tray barrier & cover codes"),
    "s073": ("Tray, conduit & grounding rules", "Tray grounding accessories"),
    "s006": ("Performance, protection & reliability", "Battery discharge performance"),
    "s009": ("Performance, protection & reliability", "Motor characteristic curves"),
    "s055": ("Performance, protection & reliability", "Motor locked-rotor kVA codes"),
    "s045": ("Performance, protection & reliability", "IEEE / IEC protection curves"),
    "s021": ("Performance, protection & reliability", "Equipment reliability data"),
}


def decode_js_payload(path: Path, fn_name: str) -> dict:
    txt = path.read_text(encoding="utf-8")
    m = re.search(rf"window\.{fn_name}\([^,]+,\s*\"([^\"]+)\"", txt)
    if not m:
        raise RuntimeError(f"Could not parse {fn_name} in {path}")
    raw = gzip.decompress(base64.b64decode(m.group(1)))
    return json.loads(raw.decode("utf-8"))


def encode_js_payload(path: Path, fn_name: str, arg_id: str, payload: dict) -> tuple[int, str]:
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    gz = gzip.compress(raw, compresslevel=9, mtime=0)
    b64 = base64.b64encode(gz).decode("ascii")
    js = f'window.{fn_name}("{arg_id}","{b64}");'
    path.write_text(js, encoding="utf-8")
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    return path.stat().st_size, sha


def main() -> None:
    ledger_path = VERIF_DIR / "unresolved_research_ledger.json"
    pv_path = COLLECTIONS_DIR / "pv-modules.js"
    pv_search_path = COLLECTIONS_DIR / "pv-modules.search.js"
    index_path = COLLECTIONS_DIR / "index.js"

    if ledger_path.exists():
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
        unresolved_ids = {r["recordId"] for r in ledger.get("records", []) if r.get("recordId")}
    else:
        unresolved_ids = set()

    pv_data = decode_js_payload(pv_path, "CollectionReceive")
    pv_search = decode_js_payload(pv_search_path, "SearchReceive")

    old_recs = pv_data["records"]
    old_search = pv_search["search"]
    if len(old_recs) != len(old_search):
        raise RuntimeError(f"Mismatch pv records ({len(old_recs)}) vs search ({len(old_search)})")

    if unresolved_ids:
        keep_indices = [i for i, r in enumerate(old_recs) if r[1] not in unresolved_ids]
        removed = len(old_recs) - len(keep_indices)
        if removed != len(unresolved_ids):
            raise RuntimeError(f"Expected to remove {len(unresolved_ids)}, removed {removed}")
        pv_data["records"] = [old_recs[i] for i in keep_indices]
        pv_data["count"] = len(pv_data["records"])
        pv_search["search"] = [old_search[i] for i in keep_indices]
        pv_bytes, pv_sha = encode_js_payload(pv_path, "CollectionReceive", "pv-modules", pv_data)
        pv_s_bytes, pv_s_sha = encode_js_payload(pv_search_path, "SearchReceive", "pv-modules", pv_search)
        ledger_path.unlink()
    else:
        pv_bytes = pv_path.stat().st_size
        pv_sha = hashlib.sha256(pv_path.read_bytes()).hexdigest()
        pv_s_bytes = pv_search_path.stat().st_size
        pv_s_sha = hashlib.sha256(pv_search_path.read_bytes()).hexdigest()

    makers = {str(r[2] or "").strip() for r in pv_data["records"] if str(r[2] or "").strip()}

    idx_txt = index_path.read_text(encoding="utf-8")
    catalog = json.loads(idx_txt.split("window.EQUIPMENT_CATALOG=", 1)[1].rstrip(";\n "))

    for c in catalog["collections"]:
        if c["id"] == "pv-modules":
            c["count"] = len(pv_data["records"])
            c["manufacturers"] = len(makers)
            c["bytes"] = pv_bytes
            c["sha256"] = pv_sha
            c["searchBytes"] = pv_s_bytes
            c["searchSha256"] = pv_s_sha

    catalog["catalogRecords"] = sum(int(c["count"]) for c in catalog["collections"])

    curated_refs = []
    for ref in catalog.get("references", []):
        rid = ref.get("id")
        if rid in KEPT_REF_GROUPS:
            grp, lbl = KEPT_REF_GROUPS[rid]
            curated_refs.append({
                "id": rid,
                "group": grp,
                "name": ref["name"],
                "label": lbl,
                "rows": ref["rows"],
            })

    order = list(KEPT_REF_GROUPS.keys())
    curated_refs.sort(key=lambda r: order.index(r["id"]))
    catalog["references"] = curated_refs

    index_path.write_text(
        "window.EQUIPMENT_CATALOG=" + json.dumps(catalog, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8",
    )

    print(json.dumps({
        "pvModulesRemaining": len(pv_data["records"]),
        "catalogRecordsTotal": catalog["catalogRecords"],
        "curatedReferences": len(curated_refs),
        "ledgerRemoved": not ledger_path.exists(),
    }, indent=2))


if __name__ == "__main__":
    main()
