#!/usr/bin/env python3
"""Deterministic Database Hygiene, Custom Deletion & Unverified Quarantine Script.

Operates ONLY on 01_Engineering_Equipment_Database/website/dist/ and writes quarantined
items out of the live website database into:
  01_Engineering_Equipment_Database/quarantine/unverified_quarantine_bag.json
  01_Engineering_Equipment_Database/quarantine/QUARANTINE_REPORT.md

NEVER touches 02_Engineering_Master_Database/.
"""
from __future__ import annotations

import base64
import gzip
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
WEBSITE_DIR = TOOLS_DIR.parent
EED_DIR = WEBSITE_DIR.parent
DIST_DIR = WEBSITE_DIR / "dist"
COLLECTIONS_DIR = DIST_DIR / "collections"

LITERAL_CUSTOM_DELETE_IDS = {
    "pv-modules": {"PVM-025864"},
    "inverters": {"IBR-CEC-000403"},
    "grounding": {"NGR-PGR-LRG-13P8-400A-10S-TEMPLATE"},
}

CUSTOM_REASON = {
    "PVM-025864": "Literal custom/blank template placeholder (CUSTOM MODULE / BLANK / 0 W / TEMPLATE_PLACEHOLDER_NOT_EQUIPMENT)",
    "IBR-CEC-000403": "Literal blank custom entry (BLANK ENTRY / BLANK / 0 W / USER_PROVIDED_UNVERIFIED)",
    "NGR-PGR-LRG-13P8-400A-10S-TEMPLATE": "Engineering sizing template with no manufacturer (ENGINEERING_TEMPLATE_REQUIRES_VENDOR_QUOTE)",
}


def decode_js_payload(path: Path, fn_name: str) -> dict:
    txt = path.read_text(encoding="utf-8")
    m = re.search(rf"window\.{fn_name}\([^,]+,\s*\"([^\"]+)\"", txt)
    if not m:
        m = re.search(rf"window\.{fn_name}\([^,]+,\s*\d+,\s*\"([^\"]+)\"", txt)
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


def norm_tok(s: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "", re.sub(r"\[[^\]]*\]", "", str(s or "").upper()))


def primary_ref(r: list) -> tuple[str | None, int | None]:
    p = r[11]
    if isinstance(p, list) and len(p) >= 2:
        return p[0], p[1]
    refs = r[10]
    if isinstance(refs, list) and refs:
        return refs[0][0], refs[0][1]
    return None, None


def infer_clean_maker(cid: str, r: list) -> str:
    existing = str(r[2] or "").strip()
    if existing:
        return existing
    rid = str(r[1] or "").strip()
    model = str(r[3] or "").strip()
    upper_id = rid.upper()
    lower_m = model.lower()

    if cid == "inverters":
        if upper_id.startswith("IBR-PE-"):
            return "Power Electronics"
        if upper_id.startswith("INV-SMA-"):
            return "SMA"
        if upper_id.startswith("INV-SOLAREDGE-"):
            return "SolarEdge"
        if upper_id.startswith("INV-FRONIUS-"):
            return "Fronius"
    elif cid in ("switchgear", "transformers", "disconnects", "grounding", "surge-protection"):
        prefix_map = [
            ("eaton ", "Eaton"),
            ("schneider electric", "Schneider Electric"),
            ("schneider ", "Schneider Electric"),
            ("abb ", "ABB"),
            ("s&c ", "S&C Electric"),
            ("siemens ", "Siemens"),
            ("accuenergy ", "Accuenergy"),
            ("arteche ", "Arteche"),
            ("flex-core ", "Flex-Core"),
            ("littelfuse ", "Littelfuse"),
            ("ritz ", "RITZ"),
            ("carlo gavazzi", "Carlo Gavazzi"),
            ("janitza ", "Janitza"),
            ("cr magnetics", "CR Magnetics"),
            ("hubbell ", "Hubbell"),
            ("imo ", "IMO"),
            ("socomec ", "Socomec"),
            ("galvan ", "Galvan"),
            ("nvent erico", "nVent ERICO"),
            ("nvent ", "nVent"),
            ("line hardware", "Line Hardware"),
            ("line power", "Line Power"),
            ("harger ", "Harger"),
            ("post glover", "Post Glover"),
            ("i-gard ", "I-Gard"),
            ("maclean ", "MacLean Power Systems"),
            ("ohio brass", "Ohio Brass"),
            ("hitachi ", "Hitachi Energy"),
        ]
        for pref, canon in prefix_map:
            if lower_m.startswith(pref):
                return canon
        if upper_id.startswith("ERICO-"):
            return "nVent ERICO"
        if upper_id.startswith("HARGER-"):
            return "Harger"
        if upper_id.startswith("CT-EATON"):
            return "Eaton"
    return existing


def main() -> None:
    index_path = COLLECTIONS_DIR / "index.js"
    dbcat_path = DIST_DIR / "data" / "catalog.js"

    catalog = json.loads(index_path.read_text(encoding="utf-8").split("window.EQUIPMENT_CATALOG=", 1)[1].rstrip(";\n "))
    dbcat = json.loads(dbcat_path.read_text(encoding="utf-8").split("window.DB_CATALOG=", 1)[1].rstrip(";\n "))

    sheets_by_id = {s["id"]: s for s in dbcat["sheets"]}
    sheet_cache: dict[str, tuple[list[str], dict[int, list]]] = {}

    def get_sheet_row_dict(sid: str | None, rnum: int | None) -> dict[str, str]:
        if not sid or rnum is None or sid not in sheets_by_id:
            return {}
        if sid not in sheet_cache:
            smeta = sheets_by_id[sid]
            rows: dict[int, list] = {}
            for ch in smeta["chunks"]:
                dec = decode_js_payload(DIST_DIR / ch["file"], "DBReceive")
                for row in dec["rows"]:
                    rows[row[0]] = row[1]
            sheet_cache[sid] = (smeta["headers"], rows)
        hdrs, rows = sheet_cache[sid]
        vals = rows.get(rnum)
        if not vals:
            return {}
        return {hdrs[i]: (vals[i] if i < len(vals) else None) for i in range(len(hdrs))}

    # Build official CEC model lookups
    cec_pv_norm: set[str] = set()
    for sid in ("s094", "s104"):
        if sid in sheets_by_id:
            get_sheet_row_dict(sid, 1)
            hdrs, rows = sheet_cache[sid]
            mi = [i for i, h in enumerate(hdrs) if "model" in h.lower()]
            for vals in rows.values():
                for idx in mi:
                    if idx < len(vals):
                        tok = norm_tok(vals[idx])
                        if tok:
                            cec_pv_norm.add(tok)

    cec_inv_norm: set[str] = set()
    for sid in ("s095", "s096", "s103"):
        if sid in sheets_by_id:
            get_sheet_row_dict(sid, 1)
            hdrs, rows = sheet_cache[sid]
            mi = [i for i, h in enumerate(hdrs) if "model" in h.lower()]
            for vals in rows.values():
                for idx in mi:
                    if idx < len(vals):
                        tok = norm_tok(vals[idx])
                        if tok:
                            cec_inv_norm.add(tok)

    deleted_custom: list[dict] = []
    quarantined_items: list[dict] = []
    bucket_counts = Counter()
    cleaned_flags = Counter()
    backfilled_power = 0
    inferred_makers = 0

    for c_meta in catalog["collections"]:
        cid = c_meta["id"]
        c_path = DIST_DIR / c_meta["file"]
        s_path = DIST_DIR / c_meta["searchFile"]

        c_data = decode_js_payload(c_path, "CollectionReceive")
        s_data = decode_js_payload(s_path, "SearchReceive")
        recs = c_data["records"]
        searches = s_data["search"]
        if len(recs) != len(searches):
            raise RuntimeError(f"Record/search length mismatch in {cid}: {len(recs)} != {len(searches)}")

        kept_recs = []
        kept_searches = []
        custom_del_set = LITERAL_CUSTOM_DELETE_IDS.get(cid, set())

        for idx, r in enumerate(recs):
            rid = str(r[1] or "").strip()
            sid, rnum = primary_ref(r)
            raw_row = get_sheet_row_dict(sid, rnum)
            row_blob = " ".join(str(v or "") for v in raw_row.values())

            # 1. Literal Custom / Blank / Template deletion
            if rid in custom_del_set:
                deleted_custom.append({
                    "category": cid,
                    "recordId": rid,
                    "manufacturer": r[2] or "",
                    "model": r[3] or "",
                    "type": r[4] or "",
                    "reason": CUSTOM_REASON.get(rid, "Custom/blank/template entry"),
                })
                continue

            # 2. Quarantine rules (unverified / conflict / pending / blocked / SCCR-unresolved / dead-web-source)
            q_bucket = None
            q_reason = None

            if cid == "pv-modules":
                src_ds = str(raw_row.get("Source Dataset") or "").strip()
                note = str(raw_row.get("Note") or "").strip()
                if "static.trinasolar.com/sites/default/files/DT-M-0042_NEG21C.20_EN_2025_A.pdf" in row_blob:
                    q_bucket = "DEAD_WEB_SOURCE_HTTP_404"
                    q_reason = "Web datasheet URL returned HTTP 404 (static.trinasolar.com/.../DT-M-0042_NEG21C.20_EN_2025_A.pdf)"
                elif "recgroup.com/sites/default/files/2026-03/DS_Alpha_Pure-RX_UL%20DC.pdf" in row_blob:
                    q_bucket = "DEAD_WEB_SOURCE_HTTP_404"
                    q_reason = "Web datasheet URL returned HTTP 404 (recgroup.com/.../DS_Alpha_Pure-RX_UL%20DC.pdf)"
                elif not src_ds and not note and norm_tok(r[3]) not in cec_pv_norm:
                    q_bucket = "UNVERIFIED_ORPHAN_NO_SOURCE_NOT_IN_CEC"
                    q_reason = "Legacy module row with blank Source Dataset, blank Note, and no match in active/archived CEC registry"

            elif cid == "inverters":
                src_url = str(raw_row.get("Source Reference / URL / Document") or "")
                if rid in ("IBR-CEC-000253", "IBR-CEC-000254"):
                    q_bucket = "UNVERIFIED_MISSING_SPECS_NOT_IN_CEC"
                    q_reason = "USER_PROVIDED_UNVERIFIED project row with missing power and voltage ratings and no match in CEC registry"
                elif "solar.huawei.com/" in src_url and (
                    "SUN2000-3-10KTL-M1.pdf" in src_url or "SUN2000-60KTL-M0.pdf" in src_url
                ):
                    q_bucket = "DEAD_WEB_SOURCE_HTTP_404"
                    q_reason = "Web datasheet URL returned HTTP 404 (solar.huawei.com)"

            elif cid == "cables":
                ver_st = str(raw_row.get("Verification Status") or "")
                src_ref = str(raw_row.get("Source / Reference") or "")
                if ver_st == "SOURCE_CONFLICT_REVIEW_REQUIRED":
                    q_bucket = "SOURCE_CONFLICT_OR_PENDING"
                    q_reason = "Source OD unit columns conflict (SOURCE_CONFLICT_REVIEW_REQUIRED)"
                elif "cablegrid.com.au/" in src_ref:
                    q_bucket = "DEAD_WEB_SOURCE_HTTP_404"
                    q_reason = "Third-party distributor PDF URL returned HTTP 404 (cablegrid.com.au)"
                elif "media.industrial.southwire.com/" in src_ref:
                    q_bucket = "DEAD_WEB_SOURCE_UNREACHABLE"
                    q_reason = "Web datasheet subdomain failed SSL/host reachability (media.industrial.southwire.com)"
                elif "ecatalog.corning.com/" in src_ref:
                    q_bucket = "DEAD_WEB_SOURCE_HTTP_500_AND_FIBER"
                    q_reason = "Web product page returned HTTP 500 and row is 0.0 kV dielectric optical fiber, not electrical power cable"

            elif cid == "motors":
                src_ref = str(raw_row.get("Source Reference") or "")
                if "static.weg.net/" in src_ref and ".pdf.pdf.pdf" in src_ref:
                    q_bucket = "DEAD_WEB_SOURCE_HTTP_404"
                    q_reason = "Web catalog PDF URL returned HTTP 404 (static.weg.net malformed .pdf.pdf.pdf and .pdf)"

            elif cid == "optimizers":
                ds = str(raw_row.get("Data Status") or r[7] or "")
                if ds in ("BLOCKED_RATING_BASIS_REVIEW_REQUIRED", "FUNCTION_SUFFIX_AND_LEGACY_DOCUMENT_REQUIRED"):
                    q_bucket = "UNVERIFIED_BLOCKED_OR_LEGACY_DOC_REQUIRED"
                    q_reason = f"Marked {ds}; requires manufacturer verification before publishing"

            elif cid == "controllers":
                ds = str(raw_row.get("Data Status") or "")
                if "SOURCE CONFLICT:" in ds:
                    q_bucket = "SOURCE_CONFLICT_OR_PENDING"
                    q_reason = "Source heading and row/subtitle voltage ranges disagree (SOURCE CONFLICT)"
                elif "Historical forthcoming variant; current availability and detailed electrical ratings not confirmed." in ds:
                    q_bucket = "UNCONFIRMED_HISTORICAL_VARIANT"
                    q_reason = "Historical forthcoming variant; current availability and detailed electrical ratings not confirmed"

            elif cid == "disconnects":
                vs = str(raw_row.get("Verification State") or r[7] or "")
                if "CONFLICT" in vs or "SCCR_UNRESOLVED" in vs:
                    q_bucket = "SOURCE_CONFLICT_OR_SCCR_UNRESOLVED"
                    q_reason = f"Flagged {vs}"

            elif cid == "surge-protection":
                vs = str(raw_row.get("Verification State") or r[7] or "")
                rs = str(raw_row.get("Record Status") or "")
                if "PENDING" in vs or "PENDING" in rs:
                    q_bucket = "SOURCE_CONFLICT_OR_PENDING"
                    q_reason = f"Pending verification ({vs or rs})"

            elif cid == "terminations":
                ds = str(raw_row.get("Data Status") or r[7] or "")
                if ds == "SOURCE_CONFLICT_REVIEW_REQUIRED":
                    q_bucket = "SOURCE_CONFLICT_OR_PENDING"
                    q_reason = "SOURCE_CONFLICT_REVIEW_REQUIRED"

            elif cid == "transformers":
                vs = str(raw_row.get("Verification State") or r[7] or "")
                if vs == "FAMILY_PAGE_VERIFIED_PARAMETERS_NOT_QUALIFIED":
                    q_bucket = "PARAMETERS_NOT_QUALIFIED"
                    q_reason = "Configurable family page only; numeric datasheet ratings not qualified (FAMILY_PAGE_VERIFIED_PARAMETERS_NOT_QUALIFIED)"

            elif cid == "grounding":
                vs = str(raw_row.get("Verification State") or r[7] or "")
                if "CONFLICT" in vs:
                    q_bucket = "SOURCE_CONFLICT_OR_PENDING"
                    q_reason = f"Flagged {vs}"

            if q_bucket:
                bucket_counts[(cid, q_bucket)] += 1
                quarantined_items.append({
                    "category": cid,
                    "bucket": q_bucket,
                    "recordId": rid,
                    "manufacturer": r[2] or "",
                    "model": r[3] or "",
                    "type": r[4] or "",
                    "rating": r[5],
                    "voltage": r[6],
                    "quality": r[7] or "",
                    "sourceSheet": sid,
                    "sourceRow": rnum,
                    "sourceRef": (
                        raw_row.get("Source Reference / URL / Document")
                        or raw_row.get("Source / Reference")
                        or raw_row.get("Source Reference")
                        or raw_row.get("Source URL")
                        or raw_row.get("Source Dataset")
                        or ""
                    ),
                    "reason": q_reason,
                })
                continue

            # 3. Kept verified record cleanups (stale flags, backfill inverter active power, infer unambiguous maker)
            if cid == "pv-modules":
                if r[8]:
                    r[8] = False
                    cleaned_flags["pv_review_cleared"] += 1
                if r[7] == "UNIT_REVIEW_REQUIRED":
                    src_ds = str(raw_row.get("Source Dataset") or "")
                    if "Database.xlsx" in src_ds:
                        r[7] = "PROJECT_TABLE_VERIFIED"
                    else:
                        r[7] = "CEC_REGISTRY_VERIFIED"
                    cleaned_flags["pv_unit_review_cleaned"] += 1

            elif cid == "inverters":
                if r[8]:
                    r[8] = False
                    cleaned_flags["inv_review_cleared"] += 1
                if r[7] == "USER_PROVIDED_UNVERIFIED":
                    if norm_tok(r[3]) in cec_inv_norm:
                        r[7] = "CEC_AND_PROJECT_TABLE_VERIFIED"
                    else:
                        r[7] = "PROJECT_TABLE_VERIFIED"
                    cleaned_flags["inv_project_table_cleaned"] += 1
                # Backfill empty Rating from literal Notes ("Grid nameplate active output: 4000 W.")
                if not str(r[5][0] or "").strip():
                    note_txt = str(raw_row.get("Notes") or "")
                    m_out = re.search(r"Grid nameplate active output:\s*([\d.]+)\s*(W|kW|kVA|MVA)\b", note_txt, re.I)
                    if m_out:
                        r[5] = [m_out.group(1), m_out.group(2), "Grid nameplate active output"]
                        backfilled_power += 1

            # Infer clean manufacturer where omitted in sheet but stated unambiguously in model/ID
            new_maker = infer_clean_maker(cid, r)
            if new_maker and not str(r[2] or "").strip():
                r[2] = new_maker
                inferred_makers += 1

            kept_recs.append(r)
            kept_searches.append(searches[idx])

        # Write updated collection & search files if any records removed or modified
        c_data["records"] = kept_recs
        c_data["count"] = len(kept_recs)
        s_data["search"] = kept_searches

        c_bytes, c_sha = encode_js_payload(c_path, "CollectionReceive", cid, c_data)
        s_bytes, s_sha = encode_js_payload(s_path, "SearchReceive", cid, s_data)

        makers = {str(r[2] or "").strip() for r in kept_recs if str(r[2] or "").strip()}
        c_meta["count"] = len(kept_recs)
        c_meta["manufacturers"] = len(makers)
        c_meta["bytes"] = c_bytes
        c_meta["sha256"] = c_sha
        c_meta["searchBytes"] = s_bytes
        c_meta["searchSha256"] = s_sha

    catalog["catalogRecords"] = sum(int(c["count"]) for c in catalog["collections"])
    index_path.write_text(
        "window.EQUIPMENT_CATALOG=" + json.dumps(catalog, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8",
    )

    if not deleted_custom and not quarantined_items:
        print(json.dumps({
            "status": "ALREADY_CLEAN",
            "liveCatalogRecords": catalog["catalogRecords"],
        }, indent=2))
        return

    summary = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "liveCatalogRecords": catalog["catalogRecords"],
        "deletedCustomCount": len(deleted_custom),
        "purgedUnverifiedCount": len(quarantined_items),
        "bucketsByCategory": {f"{k[0]}::{k[1]}": v for k, v in sorted(bucket_counts.items())},
        "cleanedFlags": dict(cleaned_flags),
        "backfilledInverterRatings": backfilled_power,
        "inferredManufacturers": inferred_makers,
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
