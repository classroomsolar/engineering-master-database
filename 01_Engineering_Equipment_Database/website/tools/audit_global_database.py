#!/usr/bin/env python3
"""Global deterministic quality & schema audit across all 117 worksheets (116 data tables + 1 index)
in 01_Engineering_Equipment_Database/website/dist/data/.

Read-only with respect to original workbook data, spreadsheets, and collections.
Outputs: dist/verification/global_database_audit.json
"""
from __future__ import annotations

import base64
import gzip
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
OUT_PATH = DIST / "verification" / "global_database_audit.json"

ERROR_TOKENS = {"#REF!", "#DIV/0!", "#VALUE!", "#N/A", "#NAME?", "#NUM!", "#NULL!", "NaN", "Infinity", "-Infinity"}
NUMERIC_RE = re.compile(r"^-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?$")

EQUIPMENT_PRIMARY_TABLES = {
    "PV_MODULES", "IBR", "BATTERIES", "BATTERY_PERFORMANCE", "CABLES",
    "TRANSMISSION_CONDUCTORS", "TRANSFORMERS", "MOTORS_NAMEPLATE",
    "MOTOR_CHARACTERISTICS", "MOTOR_MODELS", "MOTOR_LOCKED_ROTOR_CODES",
    "HV_BREAKERS", "HV_BREAKERS_EXTENDED", "LV_BREAKERS", "FUSES", "RELAYS",
    "RECLOSERS", "TRIP_DEVICES", "OVERLOAD_HEATERS", "ELECTRONIC_CONTROLLERS",
    "CSD_DEVICES", "FIRE_PROTECTION", "CONDUIT_FIRE_PROTECTION", "HARMONICS",
    "RECTIFIERS", "RAILWAY_LOADS", "SWITCHGEAR", "INSTRUMENT_TRANSFORMERS",
    "DISCONNECTS", "NEUTRAL_GROUNDING_RESISTORS", "SURGE_ARRESTERS",
    "CABLE_TRAYS", "ENCLOSURES", "TERMINATIONS", "GENERATORS",
    "CABLE_TRAY_EQUIPMENT", "CABLE_CLEAT_SIZES", "TRAY_ACCESSORY_RULES",
    "TRAY_GROUNDING_ACCESSORIES", "BREAKER_LUGS", "PV_OPTIMIZERS",
}


def decode_chunk(rel_path: str, prefix: str) -> dict:
    raw_text = (DIST / rel_path).read_text(encoding="utf-8")
    if not raw_text.startswith(prefix) or not raw_text.endswith(");\n"):
        raise ValueError(f"Unexpected chunk wrapper in {rel_path}")
    payload = json.loads(raw_text[len(prefix):-3])
    if isinstance(payload, str):
        return json.loads(gzip.decompress(base64.b64decode(payload)))
    return payload


def classify_sheet(name: str) -> str:
    if name in ("INDEX", "SUMMARY", "TABLE_OF_CONTENTS") or "INDEX" in name:
        return "Workbook Index"
    if name in EQUIPMENT_PRIMARY_TABLES:
        return "Primary Equipment"
    if name.startswith("CEC_"):
        return "Registry & Source Links"
    if "REVIEW" in name or "AUDIT" in name or "NORMALIZATION" in name:
        return "Audit & Normalization"
    return "Engineering Reference & Curves"


def norm_str(val) -> str:
    if val is None:
        return ""
    return " ".join(str(val).strip().lower().split())


def find_header_indices(headers: list[str], candidates: list[str]) -> int | None:
    lowered = [norm_str(h) for h in headers]
    for cand in candidates:
        c = cand.lower()
        for idx, h in enumerate(lowered):
            if h == c:
                return idx
    for cand in candidates:
        c = cand.lower()
        for idx, h in enumerate(lowered):
            if c in h:
                return idx
    return None


def main() -> None:
    catalog_text = (DIST / "data" / "catalog.js").read_text(encoding="utf-8")
    catalog = json.loads(catalog_text[len("window.DB_CATALOG="):-2])
    sheets = catalog["sheets"]

    total_rows = 0
    total_cells_non_empty = 0
    total_grid_cells = 0
    total_formulas = 0
    total_error_tokens = 0
    total_exact_duplicate_rows = 0
    total_repeated_key_groups = 0
    total_repeated_identity_groups = 0
    sheets_with_id_col = 0
    sheets_audited = []
    category_counts: Counter[str] = Counter()
    pv_physics = {
        "totalRows": 0,
        "completeTuples": 0,
        "within2Pct": 0,
        "drift2To5Pct": 0,
        "mismatchOver5Pct": 0,
        "withheldVmpOrImp": 0,
        "zeroTupleRows": 0,
    }

    for m in sheets:
        sid = m["id"]
        sname = m["name"]
        headers = m["headers"]
        header_row = m["headerRow"]
        sheet_cat = classify_sheet(sname)
        category_counts[sheet_cat] += 1

        all_rows = []
        for i, ch in enumerate(m["chunks"]):
            prefix = f"window.DBReceive({json.dumps(sid)},{i},"
            decoded = decode_chunk(ch["file"], prefix)
            for r in decoded["rows"]:
                if r[0] != header_row:
                    all_rows.append(r)

        row_count = len(all_rows)
        col_count = len(headers)
        grid_cells = row_count * col_count
        non_empty = 0
        formulas = 0
        error_tokens = 0
        type_counts: Counter[str] = Counter()
        col_non_empty = [0] * col_count

        lowered_h = [norm_str(h) for h in headers]
        id_idx = None
        for cand in ("record id", "equipment id", "cable id", "id"):
            if cand in lowered_h:
                id_idx = lowered_h.index(cand)
                break
        mfg_idx = find_header_indices(headers, ["Manufacturer", "MANUFACTURER", "Maker", "Brand", "Company", "Vendor"])
        model_idx = find_header_indices(headers, ["Model", "MODEL", "Model Number", "Catalog Number", "Part Number", "Type"])

        row_tuples = Counter()
        id_counter = Counter()
        identity_counter = Counter()

        # PV physics indices
        is_pv = sname == "PV_MODULES"
        if is_pv:
            pv_vmp_i = find_header_indices(headers, ["Vmp (V)"])
            pv_imp_i = find_header_indices(headers, ["Imp (A)"])
            pv_voc_i = find_header_indices(headers, ["Voc (V)"])
            pv_isc_i = find_header_indices(headers, ["Isc (A)"])
            pv_pmp_i = find_header_indices(headers, ["Pmp (W)", "Nameplate Size (W)"])

        for r in all_rows:
            vals = r[1]
            types = r[2]
            form_map = r[4]
            formulas += len(form_map)

            norm_row = []
            for ci in range(col_count):
                v = vals[ci] if ci < len(vals) else None
                t = types[ci] if ci < len(types) else ""
                if t:
                    type_counts[t] += 1
                if v is not None and str(v).strip() != "":
                    non_empty += 1
                    col_non_empty[ci] += 1
                    sv = str(v).strip()
                    if sv in ERROR_TOKENS:
                        error_tokens += 1
                    norm_row.append(sv)
                else:
                    norm_row.append("")

            row_tuples[tuple(norm_row)] += 1

            if id_idx is not None and id_idx < len(vals):
                rid = str(vals[id_idx] or "").strip()
                if rid:
                    id_counter[rid] += 1

            if mfg_idx is not None and model_idx is not None:
                mk = norm_str(vals[mfg_idx] if mfg_idx < len(vals) else "")
                md = norm_str(vals[model_idx] if model_idx < len(vals) else "")
                if mk and md:
                    identity_counter[(mk, md)] += 1

            if is_pv:
                pv_physics["totalRows"] += 1
                try:
                    vmp = float(vals[pv_vmp_i]) if vals[pv_vmp_i] not in (None, "") else None
                    imp = float(vals[pv_imp_i]) if vals[pv_imp_i] not in (None, "") else None
                    voc = float(vals[pv_voc_i]) if vals[pv_voc_i] not in (None, "") else None
                    isc = float(vals[pv_isc_i]) if vals[pv_isc_i] not in (None, "") else None
                    pmp = float(vals[pv_pmp_i]) if vals[pv_pmp_i] not in (None, "") else None
                except (ValueError, TypeError):
                    vmp = imp = voc = isc = pmp = None

                if vmp is None or imp is None:
                    pv_physics["withheldVmpOrImp"] += 1
                elif vmp == 0 and imp == 0 and (voc or 0) == 0 and (isc or 0) == 0:
                    pv_physics["zeroTupleRows"] += 1
                elif pmp and pmp > 0:
                    pv_physics["completeTuples"] += 1
                    prod = vmp * imp
                    pct = abs(prod - pmp) / pmp * 100.0
                    if pct <= 2.0:
                        pv_physics["within2Pct"] += 1
                    elif pct <= 5.0:
                        pv_physics["drift2To5Pct"] += 1
                    else:
                        pv_physics["mismatchOver5Pct"] += 1
                else:
                    pv_physics["withheldVmpOrImp"] += 1

        exact_dup_groups = sum(1 for c in row_tuples.values() if c > 1)
        exact_dup_extra_rows = sum(c - 1 for c in row_tuples.values() if c > 1)
        dup_ids = sum(1 for c in id_counter.values() if c > 1)
        repeated_identities = sum(1 for c in identity_counter.values() if c > 1)
        if id_idx is not None:
            sheets_with_id_col += 1

        fill_rate = round((non_empty / grid_cells * 100.0), 2) if grid_cells else 100.0
        blank_headers = sum(1 for h in headers if not str(h or "").strip())

        total_rows += row_count
        total_cells_non_empty += non_empty
        total_grid_cells += grid_cells
        total_formulas += formulas
        total_error_tokens += error_tokens
        total_exact_duplicate_rows += exact_dup_extra_rows
        total_repeated_key_groups += dup_ids
        total_repeated_identity_groups += repeated_identities

        xlsx_path = DIST / m["file"]
        xlsx_exists = xlsx_path.is_file()

        sheets_audited.append({
            "id": sid,
            "name": sname,
            "category": sheet_cat,
            "rows": row_count,
            "columns": col_count,
            "blankHeaders": blank_headers,
            "nonEmptyCells": non_empty,
            "gridCells": grid_cells,
            "fillRatePct": fill_rate,
            "formulas": formulas,
            "errorTokens": error_tokens,
            "exactDuplicateGroups": exact_dup_groups,
            "exactDuplicateExtraRows": exact_dup_extra_rows,
            "duplicateRecordIds": dup_ids,
            "repeatedIdentityGroups": repeated_identities,
            "hasRecordId": id_idx is not None,
            "hasManufacturerModel": (mfg_idx is not None and model_idx is not None),
            "xlsxAvailable": xlsx_exists,
            "cellTypes": dict(type_counts),
        })

    # Verify SHA256 against equipment_unification.json sourceBlobHashes
    unif = json.loads((DIST / "verification" / "equipment_unification.json").read_text(encoding="utf-8"))
    source_blobs = unif.get("sourceBlobHashes", {})
    blob_verified = 0
    blob_failed = 0
    for rel, digest in source_blobs.items():
        fp = DIST / rel
        if fp.is_file() and hashlib.sha256(fp.read_bytes()).hexdigest() == digest:
            blob_verified += 1
        else:
            blob_failed += 1

    col_idx = json.loads((DIST / "collections" / "index.js").read_text(encoding="utf-8")[len("window.EQUIPMENT_CATALOG="):-2])

    summary = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "auditScope": "Global 117-worksheet / 116-data-table deterministic audit (expanded from 41-table DB12 scan)",
        "workbook": catalog.get("original"),
        "totals": {
            "worksheets": len(sheets),
            "dataTablesExcludingIndex": sum(1 for s in sheets_audited if s["category"] != "Workbook Index"),
            "equipmentCategories": len(col_idx["collections"]),
            "catalogRecords": col_idx["catalogRecords"],
            "totalDataRows": total_rows,
            "nonEmptyCells": total_cells_non_empty,
            "gridCells": total_grid_cells,
            "overallFillRatePct": round(total_cells_non_empty / total_grid_cells * 100.0, 2) if total_grid_cells else 0.0,
            "formulasRetained": total_formulas,
            "spreadsheetErrorTokens": total_error_tokens,
            "exactDuplicateExtraRows": total_exact_duplicate_rows,
            "duplicateRecordIdGroups": total_repeated_key_groups,
            "repeatedIdentityGroups": total_repeated_identity_groups,
            "sheetsWithRecordId": sheets_with_id_col,
            "xlsxDownloadsPresent": sum(1 for s in sheets_audited if s["xlsxAvailable"]),
            "sourceBlobsVerified": blob_verified,
            "sourceBlobsTotal": len(source_blobs),
            "sourceBlobsFailed": blob_failed,
        },
        "categoryBreakdown": dict(category_counts),
        "pvElectricalPhysics": pv_physics,
        "sheets": sheets_audited,
    }

    OUT_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "OK",
        "worksheets": len(sheets),
        "totalDataRows": total_rows,
        "nonEmptyCells": total_cells_non_empty,
        "fillRatePct": summary["totals"]["overallFillRatePct"],
        "formulas": total_formulas,
        "errorTokens": total_error_tokens,
        "exactDupExtraRows": total_exact_duplicate_rows,
        "dupRecordIdGroups": total_repeated_key_groups,
        "repeatedIdentityGroups": total_repeated_identity_groups,
        "sourceBlobsVerified": f"{blob_verified}/{len(source_blobs)}",
        "pvPhysics": pv_physics,
    }, indent=2))


if __name__ == "__main__":
    main()
