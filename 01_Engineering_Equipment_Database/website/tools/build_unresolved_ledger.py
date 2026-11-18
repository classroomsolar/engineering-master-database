#!/usr/bin/env python3
"""Builds the auditable Unresolved Equipment & Source Verification Research Ledger (91 records)
from Master_Database_DB12_Source_Audit_Trail.zip, PV_MODULES primary rows, and researched OEM datasheet citations.

Strictly read-only against Master v13 and dist/data/* (E038 compliance: candidate values never overwrite primary rows).
Outputs: 01_Engineering_Equipment_Database/website/dist/verification/unresolved_research_ledger.json
"""
from __future__ import annotations

import base64
import gzip
import json
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
WEBSITE_DIR = TOOLS_DIR.parent
DIST_DIR = WEBSITE_DIR / "dist"
REPO_ROOT = WEBSITE_DIR.parent.parent
DB12_ZIP = REPO_ROOT / "02_Engineering_Master_Database" / "source_audits" / "Master_Database_DB12_Source_Audit_Trail.zip"
OUT_PATH = DIST_DIR / "verification" / "unresolved_research_ledger.json"

# Researched primary & catalog datasheet findings mapped by (record_id OR manufacturer|model key)
RESEARCH_EVIDENCE = {
    "DB11-PV-04367": {
        "rootCause": "Field entry typo in Vmp (25.3 V instead of 35.5 V)",
        "researchStatus": "CANDIDATE_DATASHEET_FOUND_OWNER_REVIEW_REQUIRED",
        "candidateSpecs": {"Pmax_W": 385, "Voc_V": 42.0, "Vmp_V": 35.5, "Isc_A": 11.44, "Imp_A": 10.88, "SysVdc": 1000},
        "summary": "Legacy DB stored Vmp=25.3 V (25.3*10.91=276.02 W, -28.3% vs 385 W). Official LG NeON H Black LG385N1K-E6 datasheet lists Voc=42.0 V, Vmp=35.5 V, Isc=11.44 A, Imp=10.88 A (386.24 W, eff 20.9%).",
        "sources": ["LG Electronics LG385N1K-E6 NeON H Black Datasheet"],
    },
    "DB11-PV-05905": {
        "rootCause": "Dropped zero typo in Imp (1.45 A instead of 10.45 A) + revision split",
        "researchStatus": "CANDIDATE_DATASHEET_FOUND_OWNER_REVIEW_REQUIRED",
        "candidateSpecs": {"Pmax_W": 395, "Voc_V": "45.03-45.68", "Vmp_V": "37.32-37.81", "Isc_A": "11.13-12.08", "Imp_A": "10.58-11.43", "SysVdc": 1000},
        "summary": "Legacy DB stored Imp=1.45 A (37.81*1.45=54.82 W, -86.1%). Arithmetic shows 10.45 A was truncated to 1.45 A, while Qcells ML-G10+/t 395 also has two regional datasheet revisions (10.58 A vs 11.43 A); requires OEM revision confirmation.",
        "sources": ["Qcells North America Q.PEAK DUO BLK ML-G10+/t 395 Datasheet (North America / Regional Rev)"],
    },
    "DB11-PV-04719": {
        "rootCause": "Column-shift error (Isc=13.06 A copied into Voc) + cell-circuit ambiguity",
        "researchStatus": "CANDIDATE_DATASHEET_FOUND_OWNER_REVIEW_REQUIRED",
        "candidateSpecs": {"Pmax_W": 405, "Voc_V": 40.7, "Vmp_V": 34.9, "Isc_A": 12.62, "Imp_A": 11.61, "SysVdc": 1000},
        "summary": "Legacy DB stored Voc=13.06 V (essentially Isc=13.07 A shifted into Voc). Maxeon SPR-MAX3-405-COM-R datasheet reports Voc=40.7 V, Vmp=34.9 V, Isc=12.62 A, Imp=11.61 A (405.19 W).",
        "sources": ["Maxeon Solar Technologies SPR-MAX3-405-COM-R Datasheet"],
    },
    "DB11-PV-04721": {
        "rootCause": "Column-shift error (Isc=6.53 A copied into Voc) + LV/HV cell-variant split",
        "researchStatus": "CANDIDATE_DATASHEET_FOUND_OWNER_REVIEW_REQUIRED",
        "candidateSpecs": {"Pmax_W": 410, "Voc_V": "40.7 (LV) / ~75.6 (HV)", "Vmp_V": "35.1 (LV) / 66.9-68.79 (HV)", "Isc_A": "12.63 (LV) / 6.54 (HV)", "Imp_A": "11.68 (LV) / 5.96-6.13 (HV)", "SysVdc": 1500},
        "summary": "Legacy DB stored Voc=6.53 V (duplicate of Isc=6.54 A). Maxeon 3 410W exists in both parallel-low-voltage (~35.1 V Vmp) and series-high-voltage 104-cell (~66.9-68.8 V Vmp) commercial releases.",
        "sources": ["Maxeon Solar Technologies SPR-MAX3-410 Commercial Datasheet Variants"],
    },
    "DB11-PV-01334": {
        "rootCause": "STC Imp discrepancy (12.2 A stored vs ~12.91 A datasheet)",
        "researchStatus": "CANDIDATE_DATASHEET_FOUND_OWNER_REVIEW_REQUIRED",
        "candidateSpecs": {"Pmax_W": 530, "Voc_V": "49.3-49.5", "Vmp_V": 41.05, "Isc_A": "13.61-13.80", "Imp_A": 12.91, "SysVdc": 1500},
        "summary": "Legacy DB stored Vmp=41.05 V, Imp=12.2 A (500.81 W, -5.51% vs 530 W). Elin Energy 144-cell 182mm PERC ELNSM72M-HC-530 datasheet specifies Imp~12.91 A at STC (529.96 W).",
        "sources": ["Elin Energy (Sirius PV) ELNSM72M-HC-530 Datasheet"],
    },
    "DB11-PV-01343": {
        "rootCause": "STC Imp discrepancy (12.2 A stored vs ~12.91 A front STC) on bifacial model",
        "researchStatus": "CANDIDATE_DATASHEET_FOUND_OWNER_REVIEW_REQUIRED",
        "candidateSpecs": {"Pmax_W": 530, "Voc_V": "49.3-49.5", "Vmp_V": 41.05, "Isc_A": "13.61-13.80", "Imp_A": 12.91, "SysVdc": 1500},
        "summary": "Identical 12.2 A legacy Imp discrepancy (-5.51%) on bifacial ELNSM72M-HC-BF-530; exact front STC vs bifacial gain table requires OEM PDF verification.",
        "sources": ["Elin Energy (Sirius PV) ELNSM72M-HC-BF-530 Datasheet"],
    },
    "DB11-PV-01352": {
        "rootCause": "STC Imp discrepancy (12.2 A stored) on 1000V LV variant",
        "researchStatus": "CANDIDATE_DATASHEET_FOUND_OWNER_REVIEW_REQUIRED",
        "candidateSpecs": {"Pmax_W": 530, "Voc_V": "49.3-49.5", "Vmp_V": 41.05, "Isc_A": "13.61-13.80", "Imp_A": 12.91, "SysVdc": 1000},
        "summary": "1000 Vdc ELNSM72M-HC-LV-530 variant carrying the same 12.2 A legacy Imp entry (-5.51%); exact -LV-530 sub-sheet review needed.",
        "sources": ["Elin Energy (Sirius PV) ELNSM72M-HC-LV-530 Listing"],
    },
    "DB11-PV-04154": {
        "rootCause": "Positive tolerance / 72-vs-144-cell revision conflict (39.3*9.77=383.96 W)",
        "researchStatus": "CANDIDATE_DATASHEET_FOUND_OWNER_REVIEW_REQUIRED",
        "candidateSpecs": {"Pmax_W": 365, "Isc_A": 9.83, "Imp_A": 9.37, "SysVdc": 1000},
        "summary": "Legacy DB yields 383.96 W (+5.20% above 365 W). KOSOL KE365M published 72-cell datasheet reports Isc=9.83 A, Imp=9.37 A, while 72-cell vs 144-half-cut variants also exist.",
        "sources": ["KOSOL Energie KE365M Technical Specification"],
    },
    "PVM-014632": {
        "rootCause": "Variant (-72B vs -72) and +5.2% Vmp*Imp discrepancy (178.88 W vs 170 W)",
        "researchStatus": "CANDIDATE_DATASHEET_FOUND_OWNER_REVIEW_REQUIRED",
        "candidateSpecs": {"Pmax_W": 170, "Voc_V": 42.6, "Vmp_V": 35.5, "Isc_A": 5.36, "Imp_A": 4.79, "SysVdc": 1000},
        "summary": "Legacy JKM170M-72B stored Voc=44.4 V, Vmp=37.5 V, Imp=4.77 A (178.88 W, +5.22%). OEM JKM-170M-72 datasheet lists Voc=42.6 V, Vmp=35.5 V, Isc=5.36 A, Imp=4.79 A (170.05 W); -72B black-frame confirmation required.",
        "sources": ["Jinko Solar JKM-170M-72 Technical Datasheet"],
    },
    "PVM-020524": {
        "rootCause": "Mismatched lower-wattage row (~245 W) stored under Plus SW 275 mono black",
        "researchStatus": "CANDIDATE_DATASHEET_FOUND_OWNER_REVIEW_REQUIRED",
        "candidateSpecs": {"Pmax_W": 275, "Voc_V": 39.4, "Vmp_V": 31.0, "Isc_A": 9.58, "Imp_A": 8.94, "SysVdc": 1000},
        "summary": "Legacy DB stored Voc=37.5 V, Vmp=30.8 V, Imp=7.96 A (245.17 W, -10.85% vs 275 W). SolarWorld Sunmodule Plus SW 275 mono black datasheet lists Voc=39.4 V, Vmp=31.0 V, Isc=9.58 A, Imp=8.94 A (277.14 W).",
        "sources": ["SolarWorld Sunmodule Plus SW 275 mono black Datasheet"],
    },
    "PVM-009246": {
        "rootCause": "Flash/template mismatch (238.89 W vs 255 W nameplate, -6.32%)",
        "researchStatus": "CANDIDATE_DATASHEET_FOUND_OWNER_REVIEW_REQUIRED",
        "candidateSpecs": {"Pmax_W": 255, "Voc_V": 38.1, "Vmp_V": 30.92, "Isc_A": 8.84, "Imp_A": 8.25, "SysVdc": 1000},
        "summary": "Legacy DB stored Vmp=29.42 V, Imp=8.12 A (238.89 W). Perlight Plus+ PLM-255M-60 datasheet lists Voc=38.10 V, Vmp=30.92 V, Isc=8.84 A, Imp=8.25 A (255.09 W).",
        "sources": ["Perlight Solar Plus+ PLM-255M-60 Datasheet"],
    },
    "PVM-008770": {
        "rootCause": "Legacy row (~155 W) copied into HCP185D-24 (-16.20% mismatch)",
        "researchStatus": "CANDIDATE_DATASHEET_FOUND_OWNER_REVIEW_REQUIRED",
        "candidateSpecs": {"Pmax_W": 185, "Voc_V": 44.3, "Vmp_V": 36.4, "Isc_A": 5.16, "Imp_A": 5.08, "SysVdc": 1000},
        "summary": "Legacy DB stored Vmp=34.3 V, Imp=4.52 A (155.04 W, -16.20%). HongChen Solar HCPXD-24 (HCP185D-24) datasheet lists Voc=44.3 V, Vmp=36.4 V, Isc=5.16 A, Imp=5.08 A (184.91 W).",
        "sources": ["HongChen Solar HCP185D-24 (HCPXD-24 Series) Datasheet"],
    },
    "PVM-024093": {
        "rootCause": "60-cell vs 72-cell datasheet mismatch & -7.90% deficit (253.27 W vs 275 W)",
        "researchStatus": "CANDIDATE_DATASHEET_FOUND_OWNER_REVIEW_REQUIRED",
        "candidateSpecs": {"Pmax_W": 275, "Voc_V": 37.6, "Vmp_V": 31.69, "Isc_A": 9.25, "Imp_A": 8.60, "SysVdc": 1000},
        "summary": "Legacy DB recorded 72-cell-like Voc=44.22 V, Vmp=35.03 V, Imp=7.23 A (253.27 W). Atersa A-275P GS datasheet specifies 60-cell Voc=37.6 V, Vmp=31.69 V, Isc=9.25 A, Imp=8.60 A (272.53 W); verify A-275P vs GS suffix.",
        "sources": ["Atersa A-275P GS Polycrystalline Datasheet"],
    },
    "PVM-012429": {
        "rootCause": "Positive flash-bin / datasheet match verification (404.2*...)?",
        "researchStatus": "CANDIDATE_DATASHEET_FOUND_OWNER_REVIEW_REQUIRED",
        "candidateSpecs": {"Pmax_W": 390, "Voc_V": 48.64, "Vmp_V": 40.42, "Isc_A": 10.15, "Imp_A": 9.65, "SysVdc": 1500},
        "summary": "BYD390MIK-36 datasheet specifies Voc=48.64 V, Vmp=40.42 V, Isc=10.15 A, Imp=9.65 A (390.05 W).",
        "sources": ["BYD BYD390MIK-36 Datasheet & CEC Listing"],
    },
    "PVM-012435": {
        "rootCause": "Swapped/legacy Pmp=390 W while Vmp*Imp=420.72 W matches model BYD420MIK-36",
        "researchStatus": "TYPO_OR_SWAPPED_FIELD_DETECTED_OWNER_REVIEW_REQUIRED",
        "candidateSpecs": {"Pmax_W": 420, "Voc_V": 50.34, "Vmp_V": 41.78, "Isc_A": 10.57, "Imp_A": 10.07, "SysVdc": 1500},
        "summary": "Legacy record pairs BYD420MIK-36 with Pmp=390 W (+7.88% delta), whereas its stored Vmp=41.78 V and Imp=10.07 A multiply to 420.72 W matching the 420 W model name and CEC PVsyst tier.",
        "sources": ["CEC PV Module Registry & PVsyst BYD420MIK-36 Parameters"],
    },
    "PVM-012436": {
        "rootCause": "Swapped/legacy Pmp=395 W while Vmp*Imp=415.50 W matches model BYD415MIK-36",
        "researchStatus": "TYPO_OR_SWAPPED_FIELD_DETECTED_OWNER_REVIEW_REQUIRED",
        "candidateSpecs": {"Pmax_W": 415, "Voc_V": 50.06, "Vmp_V": 41.55, "Isc_A": 10.50, "Imp_A": 10.00, "SysVdc": 1500},
        "summary": "Legacy record pairs BYD415MIK-36 with Pmp=395 W (+5.19% delta), whereas its stored Vmp=41.55 V and Imp=10.00 A multiply to 415.50 W matching the 415 W model name and CEC PVsyst tier.",
        "sources": ["CEC PV Module Registry & PVsyst BYD415MIK-36 Parameters"],
    },
    "PVM-001676": {
        "rootCause": "Thin-film CIGS sorting/stabilization variance (109.92 W vs 100 W, +9.92%)",
        "researchStatus": "REMAINS_WITHHELD_NO_OEM_PUBLICATION",
        "candidateSpecs": {"Pmax_W": 100, "Voc_V": "53.3-56.9", "Vmp_V": "38.8-40.4", "Isc_A": "2.57-3.19", "Imp_A": "2.54-2.72", "SysVdc": 1000},
        "summary": "Avancis PowerMax 100 FB CIGS archive specs vary by production year and light-soaking stabilization; legacy tuple (45.8*2.40=109.92 W) conflicts with published 38.8-40.4 V Vmp sub-generations.",
        "sources": ["Avancis PowerMax 100 / PowerMax SMART Archive Documentation"],
    },
    "PVM-002021": {
        "rootCause": "Legacy FLEX-02 70N tuple (73.52 W) vs FLEX-01 70N / FLEX-02NS sheets",
        "researchStatus": "REMAINS_WITHHELD_NO_OEM_PUBLICATION",
        "candidateSpecs": {"Pmax_W": 70, "Voc_V": "23.7 (FLEX-02NS) / 27.9 (FLEX-01)", "Vmp_V": "18.5 / 22.3", "Isc_A": "4.49 / 3.70", "Imp_A": "3.79 / 3.25", "SysVdc": 1000},
        "summary": "Exact FLEX-02 70N OEM sheet absent; legacy 19.5*3.77=73.52 W (+5.02%) differs from published FLEX-01 70N (22.3*3.25) and FLEX-02NS 70NS (18.5*3.79) datasheets.",
        "sources": ["MiaSolé FLEX-01 / FLEX-02NS Technical Datasheets"],
    },
    "PVM-022149": {
        "rootCause": "-12.5% deficit (210.00 W vs 240 W) with no surviving OEM UL-240D-96 PDF",
        "researchStatus": "REMAINS_WITHHELD_NO_OEM_PUBLICATION",
        "candidateSpecs": None,
        "summary": "Legacy DB stored Vmp=41.42 V, Imp=5.07 A (210.00 W, -12.50% vs 240 W). No authoritative Ningbo Ulica UL-240D-96 OEM datasheet found online; safely withheld.",
        "sources": ["DB12 Source Audit Archive (No surviving OEM PDF)"],
    },
    "PVM-015399": {
        "rootCause": "-5.12% deficit (36.05 W vs 38 W) on internal CIGS tracking code AR931200138",
        "researchStatus": "REMAINS_WITHHELD_NO_OEM_PUBLICATION",
        "candidateSpecs": None,
        "summary": "AxunTek Solar Energy AR931200138 is a 38 W CIGS legacy registry entry with no surviving public OEM electrical datasheet; safely withheld.",
        "sources": ["CEC Archive Listing (AR931200138, no OEM PDF)"],
    },
    "DB11-PV-01612": {
        "rootCause": "-17.14% deficit (14.50 W vs 17.5 W) on 20-cell BIPV roof tile",
        "researchStatus": "REMAINS_WITHHELD_NO_OEM_PUBLICATION",
        "candidateSpecs": {"Pmax_W": 17.5, "ModuleType": "20-cell monocrystalline BIPV concrete tile"},
        "summary": "Ergosun 17.5W Black legacy row yields 10.0*1.45=14.50 W (-17.14%); no public Ergosun 17.5W PDF with Imp/Vmp published outside legacy CEC lists.",
        "sources": ["CEC BIPV Registry (Ergosun 17.5W Black)"],
    },
    "DB11-PV-01614": {
        "rootCause": "+5.38% positive tolerance / legacy bin (57.96 W vs 55 W) on 24-cell BIPV tile",
        "researchStatus": "REMAINS_WITHHELD_NO_OEM_PUBLICATION",
        "candidateSpecs": {"Pmax_W": 55, "Voc_V": 14.5, "Vmp_V": 12.0, "Isc_A": 5.3, "Imp_A": 4.83},
        "summary": "Ergosun 55W 24-cell concrete roof tile records Vmp=12.0 V, Imp=4.83 A (57.96 W, +5.38%) across registry archives without a public OEM STC tolerance sheet.",
        "sources": ["CEC / PVsyst Registry Reference (Ergosun 55W)"],
    },
}


def enrich_by_group(rid: str, mfg: str, model: str) -> dict:
    if rid in RESEARCH_EVIDENCE:
        return RESEARCH_EVIDENCE[rid]

    # SunPower SPR-A4xx-COM & -MLSD (11 records)
    if mfg == "SunPower" and model.startswith("SPR-A"):
        is_mlsd = model.endswith("-MLSD")
        return {
            "rootCause": "Legacy 72-cell voltage tuple mixed with 66-cell SPR-A commercial series (+5.2% to +9.3%)",
            "researchStatus": "CANDIDATE_DATASHEET_FOUND_OWNER_REVIEW_REQUIRED",
            "candidateSpecs": {
                "SPR-A400-COM": {"Voc_V": 48.1, "Vmp_V": 39.5, "Isc_A": 10.9, "Imp_A": 10.1},
                "SPR-A415-COM": {"Voc_V": 48.2, "Vmp_V": 40.3, "Isc_A": 10.9, "Imp_A": 10.3},
                "note": "Official Maxeon/SunPower A-Series commercial sheets use ~48V Voc / ~40V Vmp (66-cell G5), whereas legacy DB kept constant Imp=10.1 A at Voc 52.1-55.3 V.",
            },
            "summary": f"{model} ({'1000V MLSD' if is_mlsd else '1500V COM'}) carries constant legacy Imp=10.1 A across 400-425 W with Voc 52.1-55.3 V (+6% to +9.3% Vmp*Imp drift). Official 66-cell A-Series commercial sheets publish Voc ~48.1-48.2 V and Imp 10.1-10.3 A.",
            "sources": ["SunPower / Maxeon A-Series Commercial SPR-A400/A415/A425-COM Datasheet"],
        }

    # Shared Cross-OEM 275W Cluster (ET Solar, URE, GES, Centrosolar EP7 275) -> 309.99 W template vs 275 W
    if model in ("ET-A-P672275", "ET-A-P672275B", "7C00-6C275", "7C00-6C275-B", "EP7 275 SW", "EP7 275 BW"):
        return {
            "rootCause": "Cross-OEM CEC 310 W template tuple (35.59*8.71=309.99 W, +12.72%) applied to 275 W SKUs",
            "researchStatus": "CANDIDATE_DATASHEET_FOUND_OWNER_REVIEW_REQUIRED",
            "candidateSpecs": {"Pmax_W": 275, "Voc_V": 43.78, "Vmp_V": 36.72, "Isc_A": 7.96, "Imp_A": 7.49, "SysVdc": 1000},
            "summary": f"{mfg} {model} shares an identical 309.99 W tuple across 11 DB records (+12.72% above 275 W). OEM ET Solar ET-P672275 datasheet gives Voc=43.78 V, Vmp=36.72 V, Isc=7.96 A, Imp=7.49 A (275.03 W); exact OEM rebadge confirmation needed.",
            "sources": ["ET Solar ET-P672275 Datasheet", "CEC Rebadged 72-Cell Listing Audit"],
        }

    # Shared Cross-OEM 285W / 290W Cluster (Heliene, Helios Energy Europe, Centrosolar THP)
    if model in ("72P285", "72P285-HD", "THP7285", "72P290", "72P290-HD", "THP7290"):
        watt = 285 if "285" in model else 290
        return {
            "rootCause": f"Shared OEM +5.5% to +5.9% flash-test bin tuple ({'301.93 W' if watt==285 else '305.97 W'} vs {watt} W)",
            "researchStatus": "REMAINS_WITHHELD_NO_OEM_PUBLICATION",
            "candidateSpecs": {"Pmax_W": watt, "LegacyFlashTuple_W": 301.93 if watt == 285 else 305.97},
            "summary": f"{mfg} {model} shares an identical Heliene/Centrosolar/Helios 72-cell tuple yielding {'301.93 W (+5.94%)' if watt==285 else '305.97 W (+5.51%)'} over {watt} W nominal; only PVsyst/registry flash echoes survive without an exact UL/STC PDF for this suffix.",
            "sources": ["CEC / PVsyst Flash-Test Registry Comparison (Heliene / Centrosolar / Helios)"],
        }

    # Shared Cross-OEM 280W Cluster (TSEC, Ritek, Sunarray)
    if model in ("TS72-6P2-280", "TS72-6P3-280A", "PM280", "SUNARRAY-M6B2612-280"):
        return {
            "rootCause": "Shared Taiwanese OEM +5.08% bin tuple (37.15*7.92=294.23 W vs 280 W)",
            "researchStatus": "REMAINS_WITHHELD_NO_OEM_PUBLICATION",
            "candidateSpecs": {"Pmax_W": 280, "Voc_V": 44.86, "Vmp_V": 37.15, "Isc_A": 8.44, "Imp_A": 7.92},
            "summary": f"{mfg} {model} repeats the exact same TSEC/Ritek/Sunarray 72-cell test tuple (294.23 W vs 280 W nameplate, +5.08%). No standalone OEM PDF separates PTC/positive-sorting vs nominal STC.",
            "sources": ["CEC / PVsyst TSEC 280W Reference Tuple"],
        }

    # KISCO GETWATT 240M-C1U .. 254M-C1U (15 records)
    if mfg == "KISCO" and model.startswith("GETWATT"):
        return {
            "rootCause": "Uniform -5.6% systematic Vmp*Imp deficit across 1 W increments (no OEM datasheet)",
            "researchStatus": "REMAINS_WITHHELD_NO_OEM_PUBLICATION",
            "candidateSpecs": None,
            "summary": f"KISCO {model} belongs to a 15-step 240-254 W series whose legacy Vmp*Imp systematically runs ~5.6% below nameplate. No surviving South Korean KISCO GETWATT C1U OEM datasheet is publicly indexed; safely withheld.",
            "sources": ["DB12 Source Audit Archive (KISCO GETWATT C1U series)"],
        }

    # APOS / Gintech 200M & 205M (4 records)
    if mfg in ("APOS Energy", "Gintech Energy"):
        return {
            "rootCause": "Shared Gintech/APOS +5.5% to +8.1% positive mismatch (216.2-216.5 W vs 200/205 W)",
            "researchStatus": "REMAINS_WITHHELD_NO_OEM_PUBLICATION",
            "candidateSpecs": {"Pmax_W": 200 if "200" in model else 205, "Voc_V": 35.9, "Isc_A": "8.01-8.02"},
            "summary": f"{mfg} {model} repeats identical legacy Vmp=29.3 V, Imp=7.38-7.39 A (216.2-216.5 W) without an original Gintech/APOS OEM STC PDF confirming Vmp/Imp.",
            "sources": ["CEC Legacy Poly/Mono Registry (Gintech GTE / APOS AP)"],
        }

    # LG235P1W / LG230P1W
    if mfg == "LG Electronics Inc.":
        return {
            "rootCause": "-5.2% to -6.3% Imp deficit (Imp=7.39 A stored on both 230 W and 235 W)",
            "researchStatus": "CANDIDATE_DATASHEET_FOUND_OWNER_REVIEW_REQUIRED",
            "candidateSpecs": {"Pmax_W": 230 if "230" in model else 235, "Voc_V": "36.3-36.4", "Vmp_V": "~29.1-29.5", "Isc_A": "8.26-8.39", "Imp_A": "~7.91-8.02"},
            "summary": f"Legacy {model} repeated Imp=7.39 A across both 230 W and 235 W bins (~218-220 W). Sibling LG 60-cell P1C/P1W registry listings indicate Imp near ~7.9-8.0 A, pending exact P1W OEM PDF.",
            "sources": ["LG Electronics Legacy 60-Cell Poly Registry (LG230P1W / LG235P1W)"],
        }

    # 15 Repeated-Name Configuration Claims
    if mfg == "Suniva" and model == "ART245-60-3-1":
        return {
            "rootCause": "600 Vdc vs 1000 Vdc UL/IEC dual-certification placeholder (0 V/I/P stored)",
            "researchStatus": "BIN_OR_VOLTAGE_VARIANT_REQUIRES_PHYSICAL_LABEL",
            "candidateSpecs": {"Pmax_W": 245, "Voc_V": 37.30, "Vmp_V": 31.20, "Isc_A": 8.54, "Imp_A": 7.87, "SysVdc": "600 / 1000"},
            "summary": "Two Suniva ART245-60-3-1 records share identical names with 0 V/I/P placeholders differing by 600 Vdc vs 1000 Vdc certification. OEM ART245-60-3-1 STC specs: Voc=37.30 V, Vmp=31.20 V, Isc=8.54 A, Imp=7.87 A (245.54 W).",
            "sources": ["Suniva ART245-60-3-1 Datasheet"],
        }

    if mfg == "Photowatt" and model == "PW6-123":
        return {
            "rootCause": "Two distinct CEC source claims (0 V/I/P placeholder) under identical PW6-123 string",
            "researchStatus": "BIN_OR_VOLTAGE_VARIANT_REQUIRES_PHYSICAL_LABEL",
            "candidateSpecs": {"Pmax_W": 123, "Voc_V": 21.9, "Vmp_V": 17.6, "Isc_A": "7.0-7.6", "Imp_A": 7.6, "Cells": 36},
            "summary": "Two Photowatt PW6-123 claim rows hold 0 V/I/P placeholders. Published PW6-123 36-cell poly datasheet gives 123 Wp, Voc=21.9 V, Vmp=17.6 V, Imp=7.6 A, Isc=7.0-7.6 A (770/1000 V IEC).",
            "sources": ["Photowatt PW6-123 Multicrystalline Datasheet"],
        }

    if mfg == "MoserBaersolar" and model == "MBPV-CAAP BB":
        return {
            "rootCause": "Multi-wattage (230-245 W) & dual-voltage (600/1000 V) family mapped to one string",
            "researchStatus": "BIN_OR_VOLTAGE_VARIANT_REQUIRES_PHYSICAL_LABEL",
            "candidateSpecs": {
                "230W": {"Vmp_V": 29.50, "Imp_A": 7.80, "Voc_V": 37.25, "Isc_A": 8.34},
                "235W": {"Vmp_V": 30.59, "Imp_A": 7.68, "Voc_V": 37.34, "Isc_A": 8.24},
                "240W": {"Vmp_V": 30.80, "Imp_A": 7.80, "Voc_V": 37.69, "Isc_A": 8.34},
                "245W": {"Vmp_V": 30.67, "Imp_A": 7.99, "Voc_V": 37.77, "Isc_A": 8.55},
            },
            "summary": "Four Moser Baer MBPV-CAAP BB records (two 600 Vdc, two 1000 Vdc) store 0 V/I/P placeholders because MBPV-CAAP BB spans multiple wattage bins (230-245 Wp) without wattage suffix qualification.",
            "sources": ["Moser Baer Solar MBPV-CAAP BB Series Datasheet"],
        }

    if mfg == "Q.CELLS" and model == "QQ..BPPARROSOE 225-240":
        return {
            "rootCause": "Three distinct 225-240 W family claims mapped to truncated/encoded family string",
            "researchStatus": "BIN_OR_VOLTAGE_VARIANT_REQUIRES_PHYSICAL_LABEL",
            "candidateSpecs": {"PowerRange_W": "225-240", "SysVdc": 1000},
            "summary": "Three legacy 1000 Vdc Q.CELLS claim rows use an un-disambiguated range label ('QQ..BPPARROSOE 225-240') with 0 V/I/P placeholders; requires physical nameplate bin & exact suffix qualification.",
            "sources": ["DB12 Source Audit Evidence (Q.CELLS 225-240 family)"],
        }

    if mfg == "Hanwha Qcells Co. Ltd." and model == "Q.PEAK DUO ML-G-10.a":
        return {
            "rootCause": "4 distinct STC wattage bins (400/405/410/415 W) sharing un-suffixed model string",
            "researchStatus": "BIN_OR_VOLTAGE_VARIANT_REQUIRES_PHYSICAL_LABEL",
            "candidateSpecs": {
                "400W_bin": "Vmp 37.59 V * Imp 10.64 A = 399.96 W",
                "405W_bin": "Vmp 37.85 V * Imp 10.70 A = 405.00 W",
                "410W_bin": "Vmp 38.11 V * Imp 10.76 A = 410.06 W",
                "415W_bin": "Vmp 38.37 V * Imp 10.82 A = 415.16 W",
            },
            "summary": "Four distinct CEC electrical rows (400 W, 405 W, 410 W, 415 W) exist in PV_MODULES with electrically consistent Vmp*Imp values, but omit the wattage suffix on the model name string.",
            "sources": ["Hanwha Qcells Q.PEAK DUO ML-G10.a 400-415W Bin Specification"],
        }

    return {
        "rootCause": "Pending OEM datasheet authentication",
        "researchStatus": "REMAINS_WITHHELD_NO_OEM_PUBLICATION",
        "candidateSpecs": None,
        "summary": "Retained under DB12 hold pending primary OEM publication.",
        "sources": ["DB12 Source Audit Trail"],
    }


def main() -> None:
    raw = json.loads((DIST_DIR / "data" / "catalog.js").read_text(encoding="utf-8")[len("window.DB_CATALOG="):-2])
    pv_meta = next(m for m in raw["sheets"] if m["name"] == "PV_MODULES")
    headers = pv_meta["headers"]
    id_idx = headers.index("Record ID")
    mid_json = json.dumps(pv_meta["id"])

    rows_by_id = {}
    for i, ch in enumerate(pv_meta["chunks"]):
        prefix = f"window.DBReceive({mid_json},{i},"
        txt = (DIST_DIR / ch["file"]).read_text(encoding="utf-8")
        payload = json.loads(txt[len(prefix):-3])
        d = json.loads(gzip.decompress(base64.b64decode(payload))) if isinstance(payload, str) else payload
        for r in d["rows"]:
            if r[0] == pv_meta["headerRow"]:
                continue
            vals = r[1]
            rows_by_id[str(vals[id_idx])] = {headers[j]: vals[j] for j in range(len(headers))}

    with zipfile.ZipFile(DB12_ZIP) as z:
        decisions = json.loads(z.read("evidence/record_decisions.json"))

    unresolved = [
        d for d in decisions
        if d.get("outcome") in ("NO_SAFE_REPLACEMENT_AUTHENTICATED", "DISTINCT_SOURCE_CLAIMS_NOT_PHYSICAL_PRODUCT_CERTIFICATION")
    ]

    entries = []
    status_counts = Counter()
    outcome_counts = Counter()

    for d in unresolved:
        rid = d["record_id"]
        row = rows_by_id.get(rid, {})
        note = str(row.get("Note") or "")
        legacy = None
        legacy_product_w = None
        discrepancy_pct = None

        if "Reported legacy combination:" in note:
            raw_leg = note.split("Reported legacy combination:")[1].split(". Review evidence:")[0].strip()
            try:
                legacy = json.loads(raw_leg)
                vmp = legacy.get("Vmp")
                imp = legacy.get("Imp")
                pmp = legacy.get("Pmp")
                if isinstance(vmp, (int, float)) and isinstance(imp, (int, float)):
                    legacy_product_w = round(vmp * imp, 2)
                    if isinstance(pmp, (int, float)) and pmp > 0:
                        discrepancy_pct = round((legacy_product_w - pmp) / pmp * 100.0, 2)
            except json.JSONDecodeError:
                pass
        else:
            # For ML-G-10.a etc. where live Vmp/Imp are populated
            vmp = row.get("Vmp (V)")
            imp = row.get("Imp (A)")
            if isinstance(vmp, (int, float)) and isinstance(imp, (int, float)) and (vmp > 0 or imp > 0):
                legacy_product_w = round(vmp * imp, 2)

        ev = enrich_by_group(rid, d.get("manufacturer", ""), d.get("model", ""))
        status_counts[ev["researchStatus"]] += 1
        outcome_counts[d["outcome"]] += 1

        entries.append({
            "recordId": rid,
            "table": d.get("table", "PV_MODULES"),
            "manufacturer": d.get("manufacturer", ""),
            "model": d.get("model", ""),
            "db12Outcome": d.get("outcome"),
            "db12State": d.get("state"),
            "issue": d.get("issue"),
            "stored": {
                "maxSystemVdc": row.get("Max System (Vdc)"),
                "cells": row.get("Cells"),
                "nameplateW": row.get("Nameplate Size (W)"),
                "pmpW": row.get("Pmp (W)"),
                "vocV": round(row["Voc (V)"], 3) if isinstance(row.get("Voc (V)"), (int, float)) else row.get("Voc (V)"),
                "iscA": round(row["Isc (A)"], 3) if isinstance(row.get("Isc (A)"), (int, float)) else row.get("Isc (A)"),
                "vmpV": round(row["Vmp (V)"], 3) if isinstance(row.get("Vmp (V)"), (int, float)) else row.get("Vmp (V)"),
                "impA": round(row["Imp (A)"], 3) if isinstance(row.get("Imp (A)"), (int, float)) else row.get("Imp (A)"),
            },
            "legacyCombination": legacy,
            "computedProductW": legacy_product_w,
            "discrepancyPct": discrepancy_pct,
            "researchStatus": ev["researchStatus"],
            "rootCause": ev["rootCause"],
            "researchSummary": ev["summary"],
            "candidateSpecs": ev["candidateSpecs"],
            "sources": ev["sources"],
            "governancePolicy": "READ_ONLY_CANDIDATE — Do not overwrite Master v13 primary rows without physical nameplate or owner sign-off (E038).",
        })

    ledger = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "totalUnresolvedRecords": len(entries),
        "outcomeBreakdown": dict(outcome_counts),
        "researchDispositionBreakdown": dict(status_counts),
        "ownerReviewRequired": True,
        "records": entries,
    }

    OUT_PATH.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "totalUnresolvedRecords": len(entries),
        "outcomeBreakdown": dict(outcome_counts),
        "researchDispositionBreakdown": dict(status_counts),
    }, indent=2))


if __name__ == "__main__":
    main()
