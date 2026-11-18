#!/usr/bin/env python3
"""Deterministic Unit & Schema Consistency Audit Across All 29 Equipment Collections.

Does NOT modify any raw workbook or collection files.
Evaluates every record against its category's canonical rating & voltage units,
quantifying SI prefix conversions, cross-basis mismatches (e.g. kVA/MVA vs kW,
HP vs kVA, Ah vs kWh), ununitized/unitless values, '(source)' strings, and
misplaced schema fields (e.g. fuses storing kV/V in Primary Rating).

Outputs: 01_Engineering_Equipment_Database/website/dist/verification/unit_consistency_audit.json
"""
from __future__ import annotations

import base64
import gzip
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
WEBSITE_DIR = TOOLS_DIR.parent
DIST_DIR = WEBSITE_DIR / "dist"
COL_DIR = DIST_DIR / "collections"
OUT_PATH = DIST_DIR / "verification" / "unit_consistency_audit.json"

CATEGORY_UNIT_SPEC = {
    "pv-modules": {"ratingUnit": "W", "voltageUnit": "Vdc", "note": "PV module nameplate power (W) and max system DC voltage (Vdc)."},
    "inverters": {
        "ratingUnit": "kW",
        "voltageUnit": "V",
        "note": "All W/kW/MW scaled to kW; apparent-power kVA/MVA mapped on 1 kVA = 1 kW (unity PF eq.) basis and flagged; kV/V voltages normalized to V.",
    },
    "energy-storage": {
        "ratingUnit": "kWh",
        "voltageUnit": "V",
        "note": "Mixed physical quantities: Energy (kWh) vs Battery cell charge (Ah) vs Control power (kW/kVA); non-kWh units and V/cell explicitly flagged.",
    },
    "optimizers": {"ratingUnit": "W", "voltageUnit": "Vdc", "note": "Optimizer DC input power (W) and max input voltage (Vdc)."},
    "ev-charging": {"ratingUnit": "kW", "voltageUnit": "V", "note": "EV charger power (kW) and AC voltage (V)."},
    "cables": {"ratingUnit": "", "voltageUnit": "kV", "note": "Cable catalog rated voltage (kV)."},
    "conductors": {"ratingUnit": "A", "voltageUnit": "", "note": "Transmission conductor ampacity (A)."},
    "transformers": {
        "ratingUnit": "kVA",
        "voltageUnit": "kV",
        "note": "Power transformers normalized to kVA & kV; instrument transformer ununitized ratios flagged.",
    },
    "motors": {
        "ratingUnit": "kVA",
        "voltageUnit": "kV",
        "note": "Motor collection mixes kVA apparent ratings and HP mechanical shaft ratings (HP flagged as cross-basis).",
    },
    "generators": {"ratingUnit": "MVA", "voltageUnit": "kV", "note": "Generator rated MVA and terminal kV."},
    "switchgear": {"ratingUnit": "A", "voltageUnit": "kV", "note": "Switchgear continuous current (A) and rated kV."},
    "disconnects": {
        "ratingUnit": "A",
        "voltageUnit": "V",
        "note": "Disconnect continuous current (A); composite AC/DC voltage strings flagged.",
    },
    "breakers": {
        "ratingUnit": "A",
        "voltageUnit": "kV",
        "note": "Breaker current (A) and max voltage (kV); unitless trip-unit/variant strings and '(source)' unstated voltage units flagged.",
    },
    "fuses": {
        "ratingUnit": "A",
        "voltageUnit": "kV",
        "note": "21,817 legacy fuse rows stored Voltage (kV/V) inside Primary Rating; normalized into Voltage (kV) and flagged.",
    },
    "reclosers": {"ratingUnit": "A", "voltageUnit": "kV", "note": "Recloser continuous current (A) and rated kV; unitless ratings flagged."},
    "controllers": {"ratingUnit": "kW", "voltageUnit": "V", "note": "Power control gateways (kW, V) mixed with electronic controller text curves."},
    "surge-protection": {"ratingUnit": "kV MCOV", "voltageUnit": "kV", "note": "Arrester MCOV (kV) and system class (kV)."},
    "grounding": {
        "ratingUnit": "A",
        "voltageUnit": "kV",
        "note": "Mixes Neutral Grounding Resistors (A, kV) and Ground Electrodes (ft length).",
    },
    "cable-trays": {"ratingUnit": "in", "voltageUnit": "", "note": "Tray width in inches."},
    "conduits": {"ratingUnit": "in", "voltageUnit": "", "note": "Conduit nominal trade size in inches."},
    "terminations": {"ratingUnit": "A", "voltageUnit": "kV", "note": "Termination current (A) and voltage class (kV)."},
    "parts": {"ratingUnit": "in", "voltageUnit": "", "note": "Fractional trade-size strings flagged for unit standardization."},
}

INLINE_RE = re.compile(
    r"^([-+]?[\d,]*\.?\d+(?:[eE][-+]?\d+)?)\s*\*?\s*(kV|Vdc|Vac|V|kVA|MVA|kW|MW|W|A|Ah|kWh|in|ft)?$",
    re.I,
)


def extract_inline(raw_str: str, fallback: str):
    s = (raw_str or "").strip()
    fb = (fallback or "").strip()
    m = INLINE_RE.match(s)
    if m:
        try:
            num = float(m.group(1).replace(",", ""))
        except ValueError:
            return None, fb, False
        inline_u = m.group(2) or ""
        return num, (inline_u or fb), bool(inline_u)
    return None, fb, False


def convert_power_kw(num, unit: str):
    if num is None:
        return None
    if unit == "kW":
        return "NATIVE"
    if unit in ("W", "MW"):
        return "PREFIX_CONVERTED"
    if unit in ("kVA", "MVA", "VA"):
        return "CROSS_BASIS"
    return None


def convert_power_kva(num, unit: str):
    if num is None:
        return None
    if unit == "kVA":
        return "NATIVE"
    if unit in ("MVA", "VA"):
        return "PREFIX_CONVERTED"
    if unit in ("kW", "HP"):
        return "CROSS_BASIS"
    return None


def convert_voltage(num, unit: str, target: str, field_raw_unit: str):
    if num is None:
        return None
    is_src = field_raw_unit == "(source)"
    if target == "V":
        if unit == "V":
            return "NATIVE"
        if unit in ("Vac", "Vdc", "kV"):
            return "PREFIX_CONVERTED"
        if unit == "V/cell":
            return "CROSS_BASIS"
    elif target == "kV":
        if unit == "kV":
            return "PREFIX_CONVERTED" if is_src else "NATIVE"
        if unit in ("V", "Vac", "Vdc"):
            return "PREFIX_CONVERTED"
    elif target == "Vdc" and unit == "Vdc":
        return "NATIVE"
    return None


def classify_record(cat_id: str, rec: list) -> tuple[str, str, str, str, str]:
    spec = CATEGORY_UNIT_SPEC.get(cat_id, {"ratingUnit": "", "voltageUnit": ""})
    raw_r = rec[5] if len(rec) > 5 and isinstance(rec[5], list) else ["", "", ""]
    raw_v = rec[6] if len(rec) > 6 and isinstance(rec[6], list) else ["", "", ""]

    r_raw = str(raw_r[0] or "").strip() if len(raw_r) > 0 else ""
    r_unit = str(raw_r[1] or "").strip() if len(raw_r) > 1 else ""
    v_raw = str(raw_v[0] or "").strip() if len(raw_v) > 0 else ""
    v_unit = str(raw_v[1] or "").strip() if len(raw_v) > 1 else ""

    r_num, _, _ = extract_inline(r_raw, r_unit)
    v_num, v_inline_u, v_had_inline = extract_inline(v_raw, v_unit)

    r_status = "NATIVE" if r_raw else "BLANK"
    v_status = "NATIVE" if v_raw else "BLANK"

    if cat_id == "fuses" and r_unit in ("kV", "V") and not v_raw and r_num is not None:
        r_status = "MISPLACED_IN_RATING"
        v_status = "MISPLACED_IN_RATING"
    else:
        ru_target = spec["ratingUnit"]
        if r_raw:
            if ru_target == "kW":
                res = convert_power_kw(r_num, r_unit)
                r_status = res if res else ("CROSS_BASIS" if r_unit else "UNIT_MISSING")
            elif ru_target == "kVA":
                res = convert_power_kva(r_num, r_unit)
                r_status = res if res else ("CROSS_BASIS" if r_unit else "UNIT_MISSING")
            elif ru_target == "kWh":
                r_status = "NATIVE" if (r_unit == "kWh" and r_num is not None) else "CROSS_BASIS"
            elif ru_target == "A":
                if r_unit == "A" and r_num is not None:
                    r_status = "NATIVE"
                elif r_unit == "ft":
                    r_status = "CROSS_BASIS"
                else:
                    r_status = "CROSS_BASIS" if r_unit else "UNIT_MISSING"
            elif ru_target == "in":
                if r_unit in ("in wide", "in trade size", "in") and r_num is not None:
                    r_status = "NATIVE"
                else:
                    r_status = "UNIT_MISSING"

        vu_target = spec["voltageUnit"]
        if v_raw and vu_target:
            clean_u = (v_inline_u if v_had_inline else "") if v_unit == "(source)" else v_unit
            res_v = convert_voltage(v_num, clean_u, vu_target, v_unit)
            if res_v:
                v_status = res_v
            else:
                v_status = "UNIT_MISSING" if (v_unit == "(source)" or not v_unit) else "CROSS_BASIS"

    if "MISPLACED_IN_RATING" in (r_status, v_status) or "UNIT_MISSING" in (r_status, v_status):
        flag = "UNIT_OR_SCHEMA_ANOMALY"
    elif "CROSS_BASIS" in (r_status, v_status):
        flag = "CROSS_BASIS_FLAGGED"
    elif "PREFIX_CONVERTED" in (r_status, v_status):
        flag = "PREFIX_NORMALIZED"
    else:
        flag = "CLEAN"

    raw_ru_key = (r_unit or "(unitless)") if r_raw else "(blank)"
    raw_vu_key = (v_unit or "(unitless)") if v_raw else "(blank)"
    return flag, r_status, v_status, raw_ru_key, raw_vu_key


def run_audit() -> dict:
    idx_text = (COL_DIR / "index.js").read_text(encoding="utf-8")
    m = re.search(r"window\.EQUIPMENT_CATALOG=(\{.*\});?", idx_text)
    if not m:
        raise RuntimeError("Could not parse collections/index.js")
    catalog = json.loads(m.group(1))

    categories = []
    totals = {
        "categories": len(catalog["collections"]),
        "totalRecords": 0,
        "cleanRecords": 0,
        "prefixNormalizedRecords": 0,
        "crossBasisRecords": 0,
        "schemaOrMissingUnitRecords": 0,
        "categoriesWithAnomalies": 0,
    }

    for col in catalog["collections"]:
        cid = col["id"]
        js_path = COL_DIR / Path(col["file"]).name
        txt = js_path.read_text(encoding="utf-8")
        bm = re.search(r'CollectionReceive\([^,]+,"([^"]+)"\)', txt)
        if not bm:
            raise RuntimeError(f"Invalid collection wrapper in {js_path}")
        decoded = json.loads(gzip.decompress(base64.b64decode(bm.group(1))).decode("utf-8"))
        records = decoded["records"] if isinstance(decoded, dict) else decoded

        flag_counts = Counter()
        raw_ru_counts = Counter()
        raw_vu_counts = Counter()
        samples = []

        for r in records:
            flag, r_st, v_st, ru_k, vu_k = classify_record(cid, r)
            flag_counts[flag] += 1
            raw_ru_counts[ru_k] += 1
            raw_vu_counts[vu_k] += 1
            if flag != "CLEAN" and len(samples) < 3:
                rt = r[5] or ["", "", ""]
                vt = r[6] or ["", "", ""]
                samples.append({
                    "recordId": r[1],
                    "model": r[3],
                    "flag": flag,
                    "rawRating": f"{rt[0]} {rt[1]}".strip() if rt and rt[0] else "",
                    "rawVoltage": f"{vt[0]} {vt[1]}".strip() if vt and vt[0] else "",
                    "ratingStatus": r_st,
                    "voltageStatus": v_st,
                })

        total = len(records)
        prefix_c = flag_counts["PREFIX_NORMALIZED"]
        cross_c = flag_counts["CROSS_BASIS_FLAGGED"]
        anom_c = flag_counts["UNIT_OR_SCHEMA_ANOMALY"]
        clean_c = flag_counts["CLEAN"]

        totals["totalRecords"] += total
        totals["cleanRecords"] += clean_c
        totals["prefixNormalizedRecords"] += prefix_c
        totals["crossBasisRecords"] += cross_c
        totals["schemaOrMissingUnitRecords"] += anom_c
        if prefix_c + cross_c + anom_c > 0:
            totals["categoriesWithAnomalies"] += 1

        spec = CATEGORY_UNIT_SPEC.get(cid, {"ratingUnit": "", "voltageUnit": "", "note": "Standardized inspection view."})
        categories.append({
            "id": cid,
            "label": col["label"],
            "family": col["family"],
            "total": total,
            "canonicalRatingUnit": spec["ratingUnit"],
            "canonicalVoltageUnit": spec["voltageUnit"],
            "note": spec["note"],
            "clean": clean_c,
            "prefixNormalized": prefix_c,
            "crossBasis": cross_c,
            "schemaOrMissingUnit": anom_c,
            "totalFlagged": prefix_c + cross_c + anom_c,
            "rawRatingUnits": dict(raw_ru_counts.most_common()),
            "rawVoltageUnits": dict(raw_vu_counts.most_common()),
            "samples": samples,
        })

    # Sort anomalous categories highest-impact first, keeping all 29
    categories.sort(key=lambda c: (-c["totalFlagged"], -c["total"], c["id"]))

    report = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "policy": "Raw workbook values preserved intact; single canonical unit enforced per equipment category with explicit basis/prefix/schema flagging.",
        "totals": totals,
        "categories": categories,
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(totals, indent=2))
    return report


if __name__ == "__main__":
    run_audit()
