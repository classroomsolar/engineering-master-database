/**
 * Pure deterministic single-unit schema normalization, dynamic per-column facets,
 * strict single-unit filtering, and clean engineering display formatting.
 * Works both in browser (<script>) and Node ESM (node:test).
 */
(function (root, factory) {
  const api = factory();
  root.IntegrityHelpers = api;
  if (typeof globalThis !== "undefined") {
    globalThis.IntegrityHelpers = api;
  }
  if (typeof module === "object" && module && module.exports) {
    module.exports = api;
  }
})(typeof window !== "undefined" ? window : globalThis, function () {
  "use strict";

  const I = {
    id: 0,
    rid: 1,
    maker: 2,
    model: 3,
    type: 4,
    rating: 5,
    voltage: 6,
    quality: 7,
    review: 8,
    states: 9,
    refs: 10,
    primary: 11,
    registry: 12,
    candidate: 13,
    search: 14,
    gate: 15,
  };

  const EMPTY_VALUE_TOKEN = "__EMPTY__";

  const BASE_IDENTITY_COLUMNS = [
    { key: "model", label: "Equipment / Model", filterType: "text", sortType: "text" },
    { key: "maker", label: "Manufacturer", filterType: "maker", sortType: "text" },
    { key: "type", label: "Equipment Type", filterType: "select", sortType: "text" },
  ];

  const CATEGORY_SPEC_COLUMNS = {
    "pv-modules": [
      { key: "w", label: "Nameplate Power (W)", unit: "W", filterType: "range", sortType: "num" },
      { key: "vdc", label: "Max System Voltage (Vdc)", unit: "Vdc", filterType: "range_select", sortType: "num" },
    ],
    "inverters": [
      { key: "kw", label: "Power (kW)", unit: "kW", filterType: "range", sortType: "num" },
      { key: "kva", label: "Apparent Power (kVA)", unit: "kVA", filterType: "range", sortType: "num" },
      { key: "v", label: "AC Voltage (V)", unit: "V", filterType: "range_select", sortType: "num" },
    ],
    "energy-storage": [
      { key: "kwh", label: "Energy (kWh)", unit: "kWh", filterType: "range", sortType: "num" },
      { key: "ah", label: "Capacity (Ah)", unit: "Ah", filterType: "range", sortType: "num" },
      { key: "kw", label: "Power (kW)", unit: "kW", filterType: "range", sortType: "num" },
      { key: "kva", label: "Apparent Power (kVA)", unit: "kVA", filterType: "range", sortType: "num" },
      { key: "v", label: "AC Voltage (V)", unit: "V", filterType: "range_select", sortType: "num" },
      { key: "vcell", label: "Cell Voltage (V/cell)", unit: "V/cell", filterType: "range", sortType: "num" },
    ],
    "optimizers": [
      { key: "w", label: "Input Power (W)", unit: "W", filterType: "range", sortType: "num" },
      { key: "vdc", label: "Max Input Voltage (Vdc)", unit: "Vdc", filterType: "range_select", sortType: "num" },
    ],
    "ev-charging": [
      { key: "kw", label: "Power (kW)", unit: "kW", filterType: "range", sortType: "num" },
      { key: "v", label: "Nominal Voltage (V)", unit: "V", filterType: "range_select", sortType: "num" },
    ],
    "cables": [
      { key: "kv", label: "Voltage Class (kV)", unit: "kV", filterType: "range_select", sortType: "num" },
    ],
    "conductors": [
      { key: "a", label: "Ampacity (A)", unit: "A", filterType: "range", sortType: "num" },
    ],
    "transformers": [
      { key: "kva", label: "Apparent Power (kVA)", unit: "kVA", filterType: "range", sortType: "num" },
      { key: "kv", label: "Primary Voltage (kV)", unit: "kV", filterType: "range_select", sortType: "num" },
      { key: "ratio", label: "Ratio / Configuration", unit: "", filterType: "text", sortType: "text" },
    ],
    "motors": [
      { key: "hp", label: "Mechanical Power (HP)", unit: "HP", filterType: "range", sortType: "num" },
      { key: "kva", label: "Apparent Power (kVA)", unit: "kVA", filterType: "range", sortType: "num" },
      { key: "kv", label: "Voltage (kV)", unit: "kV", filterType: "range_select", sortType: "num" },
    ],
    "generators": [
      { key: "mva", label: "Apparent Power (MVA)", unit: "MVA", filterType: "range", sortType: "num" },
      { key: "kv", label: "Rated Voltage (kV)", unit: "kV", filterType: "range_select", sortType: "num" },
    ],
    "switchgear": [
      { key: "a", label: "Rated Current (A)", unit: "A", filterType: "range", sortType: "num" },
      { key: "kv", label: "Rated Voltage (kV)", unit: "kV", filterType: "range_select", sortType: "num" },
    ],
    "disconnects": [
      { key: "a", label: "Continuous Current (A)", unit: "A", filterType: "range", sortType: "num" },
      { key: "vspec", label: "Rated Voltage Spec", unit: "", filterType: "text_select", sortType: "text" },
    ],
    "breakers": [
      { key: "a", label: "Rated Current (A)", unit: "A", filterType: "range", sortType: "num" },
      { key: "kv", label: "Rated Voltage (kV)", unit: "kV", filterType: "range_select", sortType: "num" },
      { key: "code", label: "Trip / Variant Code", unit: "", filterType: "text", sortType: "text" },
    ],
    "fuses": [
      { key: "a", label: "Current Rating (A)", unit: "A", filterType: "range", sortType: "num" },
      { key: "kv", label: "Voltage Rating (kV)", unit: "kV", filterType: "range_select", sortType: "num" },
    ],
    "reclosers": [
      { key: "a", label: "Rated Current (A)", unit: "A", filterType: "range", sortType: "num" },
      { key: "kv", label: "Rated Voltage (kV)", unit: "kV", filterType: "range_select", sortType: "num" },
      { key: "code", label: "Curve / Rating Code", unit: "", filterType: "text", sortType: "text" },
    ],
    "controllers": [
      { key: "kw", label: "Power (kW)", unit: "kW", filterType: "range", sortType: "num" },
      { key: "v", label: "Voltage (V)", unit: "V", filterType: "range_select", sortType: "num" },
      { key: "code", label: "Curve / Control Code", unit: "", filterType: "text", sortType: "text" },
    ],
    "surge-protection": [
      { key: "mcov", label: "MCOV Rating (kV RMS)", unit: "kV", filterType: "range", sortType: "num" },
      { key: "kv", label: "System Voltage (kV)", unit: "kV", filterType: "range_select", sortType: "num" },
    ],
    "grounding": [
      { key: "a", label: "Current Rating (A)", unit: "A", filterType: "range", sortType: "num" },
      { key: "kv", label: "System Voltage (kV)", unit: "kV", filterType: "range_select", sortType: "num" },
      { key: "ft", label: "Electrode Length (ft)", unit: "ft", filterType: "range", sortType: "num" },
    ],
    "cable-trays": [
      { key: "in", label: "Tray Width (in)", unit: "in", filterType: "range", sortType: "num" },
    ],
    "conduits": [
      { key: "in", label: "Trade Size (in)", unit: "in", filterType: "range", sortType: "num" },
    ],
    "terminations": [
      { key: "a", label: "Rated Current (A)", unit: "A", filterType: "range", sortType: "num" },
      { key: "vspec", label: "Voltage Class Spec", unit: "", filterType: "text_select", sortType: "text" },
    ],
    "parts": [
      { key: "size", label: "Nominal Size", unit: "", filterType: "text_select", sortType: "text" },
    ],
    "meters": [],
    "relays": [],
    "controlled-switching": [],
    "rectifiers": [],
    "cable-cleats": [],
    "enclosures": [],
    "fire-protection": [],
  };

  function getCategorySchema(catId) {
    const specCols = CATEGORY_SPEC_COLUMNS[catId] || [];
    return {
      catId,
      specCols,
      columns: [...BASE_IDENTITY_COLUMNS, ...specCols],
    };
  }

  function cleanFloatNumber(val) {
    if (val === null || val === undefined || !Number.isFinite(val)) return null;
    if (Object.is(val, -0)) return 0;
    // Eliminate binary float precision tails like 33.300000000000004 or 2.055000066757202
    const rounded = Number(val.toPrecision(10));
    if (Math.abs(rounded) < 1e-12) return 0;
    const str = String(rounded);
    if (/\.(?:\d*?)(?:0000\d+|9999\d+)$/.test(str)) {
      return Number(rounded.toFixed(4));
    }
    return rounded;
  }

  function formatCleanNumber(val) {
    const num = cleanFloatNumber(val);
    if (num === null) return "";
    const abs = Math.abs(num);
    if (abs >= 1000) {
      return Number(num.toFixed(2)).toLocaleString("en-US", { maximumFractionDigits: 2 });
    }
    if (Number.isInteger(num)) return String(num);
    if (abs >= 1) return Number(num.toFixed(4)).toString();
    return Number(num.toFixed(5)).toString();
  }

  function formatReferenceCell(val) {
    if (val === null || val === undefined) return "—";
    if (typeof val === "number") {
      if (!Number.isFinite(val)) return "—";
      return String(cleanFloatNumber(val));
    }
    const s = String(val).trim();
    if (!s) return "—";
    if (/^[-+]?\d+\.\d{7,}$/.test(s)) {
      const n = Number(s);
      if (Number.isFinite(n)) {
        return String(Number(n.toFixed(4)));
      }
    }
    return s;
  }

  function parseScalarNumber(rawStr) {
    const s = String(rawStr ?? "").trim();
    if (!s) return null;
    // Strip trailing '*' markers such as "34.5*" and commas
    const cleaned = s.replace(/,/g, "").replace(/\*+$/, "").trim();
    if (/^[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?$/.test(cleaned)) {
      const n = Number(cleaned);
      return Number.isFinite(n) ? cleanFloatNumber(n) : null;
    }
    const m = cleaned.match(/^([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)\s*\*?\s*(kV|Vdc|Vac|V|kVA|MVA|kW|MW|W|A|Ah|kWh|HP|in|ft)$/i);
    if (m) {
      const n = Number(m[1]);
      return Number.isFinite(n) ? cleanFloatNumber(n) : null;
    }
    return null;
  }

  function parseInlineNumericAndUnit(rawStr, fallbackUnit) {
    const s = String(rawStr ?? "").trim();
    const fb = String(fallbackUnit ?? "").trim();
    if (!s) return { num: null, unit: fb, raw: "" };
    const cleaned = s.replace(/,/g, "").replace(/\*+$/, "").trim();
    const m = cleaned.match(/^([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)\s*(kV|Vdc|Vac|V|kVA|MVA|kW|MW|W|A|Ah|kWh|HP|in|ft)?$/i);
    if (m) {
      const n = Number(m[1]);
      if (Number.isFinite(n)) {
        return {
          num: cleanFloatNumber(n),
          unit: m[2] ? m[2] : fb,
          raw: s,
        };
      }
    }
    return { num: null, unit: fb, raw: s };
  }

  function setNumField(cells, key, num, unit) {
    const cleaned = cleanFloatNumber(num);
    if (cleaned === null) return;
    cells[key] = {
      num: cleaned,
      text: unit ? `${formatCleanNumber(cleaned)} ${unit}` : formatCleanNumber(cleaned),
    };
  }

  function setTextField(cells, key, text) {
    const s = String(text ?? "").trim();
    if (!s || /^not applicable$/i.test(s)) return;
    cells[key] = {
      num: null,
      text: s,
    };
  }

  function setVoltageOrSlashField(cells, key, vRawStr, vUnitStr, vParsed) {
    if (vParsed.num !== null) {
      if (vUnitStr === "V" || vUnitStr === "Vac" || vUnitStr === "Vdc") {
        setNumField(cells, key, vParsed.num, "V");
      } else if (vUnitStr === "kV") {
        setNumField(cells, key, vParsed.num * 1000, "V");
      }
      return;
    }
    if ((vUnitStr === "V" || vUnitStr === "Vac" || vUnitStr === "kV") && /^\d+(?:\.\d+)?(?:\/\d+(?:\.\d+)?)+$/.test(vRawStr)) {
      const nums = vRawStr.split("/").map(Number).filter(Number.isFinite);
      if (nums.length) {
        const mult = vUnitStr === "kV" ? 1000 : 1;
        const maxV = cleanFloatNumber(Math.max(...nums) * mult);
        const disp = mult === 1000 ? nums.map((n) => formatCleanNumber(n * 1000)).join("/") : vRawStr;
        cells[key] = { num: maxV, text: `${disp} V` };
      }
    }
  }

  /**
   * Maps any raw compact record tuple to strictly single-unit per-column values.
   * Never guesses power factor or mixes different units inside one column.
   */
  function extractNormalizedRow(catId, r) {
    const cells = {};
    const rawR = Array.isArray(r[I.rating]) ? r[I.rating] : ["", "", ""];
    const rawV = Array.isArray(r[I.voltage]) ? r[I.voltage] : ["", "", ""];

    const rRawStr = String(rawR[0] ?? "").trim();
    const rUnitStr = String(rawR[1] ?? "").trim();
    const vRawStr = String(rawV[0] ?? "").trim();
    const vUnitStr = String(rawV[1] ?? "").trim();

    const rParsed = parseInlineNumericAndUnit(rRawStr, rUnitStr);
    const vParsed = parseInlineNumericAndUnit(vRawStr, vUnitStr);

    if (catId === "pv-modules" || catId === "optimizers") {
      if (rUnitStr === "W" && rParsed.num !== null && rParsed.num > 0) setNumField(cells, "w", rParsed.num, "W");
      if (vUnitStr === "Vdc" && vParsed.num !== null && vParsed.num > 0) setNumField(cells, "vdc", vParsed.num, "Vdc");
    } else if (catId === "inverters") {
      if (rParsed.num !== null && rParsed.num > 0) {
        if (rUnitStr === "kW") setNumField(cells, "kw", rParsed.num, "kW");
        else if (rUnitStr === "W") setNumField(cells, "kw", rParsed.num / 1000, "kW");
        else if (rUnitStr === "MW") setNumField(cells, "kw", rParsed.num * 1000, "kW");
        else if (rUnitStr === "kVA") setNumField(cells, "kva", rParsed.num, "kVA");
        else if (rUnitStr === "MVA") setNumField(cells, "kva", rParsed.num * 1000, "kVA");
      }
      setVoltageOrSlashField(cells, "v", vRawStr, vUnitStr, vParsed);
    } else if (catId === "energy-storage") {
      if (rParsed.num !== null) {
        if (rUnitStr === "kWh") setNumField(cells, "kwh", rParsed.num, "kWh");
        else if (rUnitStr === "Ah") setNumField(cells, "ah", rParsed.num, "Ah");
        else if (rUnitStr === "kW") setNumField(cells, "kw", rParsed.num, "kW");
        else if (rUnitStr === "W") setNumField(cells, "kw", rParsed.num / 1000, "kW");
        else if (rUnitStr === "kVA") setNumField(cells, "kva", rParsed.num, "kVA");
        else if (rUnitStr === "MVA") setNumField(cells, "kva", rParsed.num * 1000, "kVA");
      }
      if (vUnitStr === "V/cell" && vParsed.num !== null) {
        setNumField(cells, "vcell", vParsed.num, "V/cell");
      } else {
        setVoltageOrSlashField(cells, "v", vRawStr, vUnitStr, vParsed);
        if (!cells.v && (vUnitStr === "Vac" || vUnitStr === "V") && vRawStr && !/^not applicable$/i.test(vRawStr)) {
          setTextField(cells, "v", `${vRawStr} V`);
        }
      }
    } else if (catId === "ev-charging") {
      if (rParsed.num !== null && rParsed.num > 0) {
        if (rUnitStr === "kW") setNumField(cells, "kw", rParsed.num, "kW");
        else if (rUnitStr === "W") setNumField(cells, "kw", rParsed.num / 1000, "kW");
      }
      setVoltageOrSlashField(cells, "v", vRawStr, vUnitStr, vParsed);
    } else if (catId === "cables") {
      if (vUnitStr === "kV" && vParsed.num !== null && vParsed.num > 0) setNumField(cells, "kv", vParsed.num, "kV");
    } else if (catId === "conductors") {
      if (rUnitStr === "A" && rParsed.num !== null && rParsed.num > 0) setNumField(cells, "a", rParsed.num, "A");
    } else if (catId === "transformers") {
      if (rUnitStr === "kVA" && rParsed.num !== null) {
        setNumField(cells, "kva", rParsed.num, "kVA");
      } else if (rUnitStr === "MVA" && rParsed.num !== null) {
        setNumField(cells, "kva", rParsed.num * 1000, "kVA");
      } else if (rRawStr && !rUnitStr) {
        setTextField(cells, "ratio", rRawStr);
      }
      if (vUnitStr === "kV" && vParsed.num !== null) setNumField(cells, "kv", vParsed.num, "kV");
    } else if (catId === "motors") {
      if (rParsed.num !== null) {
        if (rUnitStr === "HP") setNumField(cells, "hp", rParsed.num, "HP");
        else if (rUnitStr === "kVA") setNumField(cells, "kva", rParsed.num, "kVA");
      }
      if (vUnitStr === "kV" && vParsed.num !== null) setNumField(cells, "kv", vParsed.num, "kV");
    } else if (catId === "generators") {
      if (rUnitStr === "MVA" && rParsed.num !== null) setNumField(cells, "mva", rParsed.num, "MVA");
      else if (rUnitStr === "kVA" && rParsed.num !== null) setNumField(cells, "mva", rParsed.num / 1000, "MVA");
      if (vUnitStr === "kV" && vParsed.num !== null) setNumField(cells, "kv", vParsed.num, "kV");
    } else if (catId === "switchgear") {
      if (rUnitStr === "A" && rParsed.num !== null) setNumField(cells, "a", rParsed.num, "A");
      if (vUnitStr === "kV" && vParsed.num !== null) setNumField(cells, "kv", vParsed.num, "kV");
    } else if (catId === "disconnects") {
      if (rUnitStr === "A" && rParsed.num !== null) setNumField(cells, "a", rParsed.num, "A");
      if (vRawStr) setTextField(cells, "vspec", vRawStr);
    } else if (catId === "breakers") {
      if (rUnitStr === "A" && rParsed.num !== null) {
        setNumField(cells, "a", rParsed.num, "A");
      } else if (rRawStr && !rUnitStr) {
        setTextField(cells, "code", rRawStr);
      }
      if (vUnitStr === "kV" && vParsed.num !== null) {
        setNumField(cells, "kv", vParsed.num, "kV");
      } else if (vUnitStr === "(source)") {
        if (/kV$/i.test(vRawStr) && vParsed.num !== null) {
          setNumField(cells, "kv", vParsed.num, "kV");
        } else if (vParsed.num !== null) {
          // LV_BREAKERS: AC voltages are <= 1.25 (already kV), DC voltages are >= 48 (Vdc -> V/1000 = kV)
          const kvVal = vParsed.num >= 48 ? vParsed.num / 1000 : vParsed.num;
          setNumField(cells, "kv", kvVal, "kV");
        }
      }
    } else if (catId === "fuses") {
      if (rUnitStr === "A" && rParsed.num !== null && rParsed.num > 0) {
        setNumField(cells, "a", rParsed.num, "A");
      } else if ((rUnitStr === "kV" || rUnitStr === "V") && !vRawStr && rParsed.num !== null) {
        // Legacy fuse voltage rows stored in Rating field -> cleanly normalize into Voltage Rating (kV)
        const kvVal = rUnitStr === "V" ? rParsed.num / 1000 : rParsed.num;
        if (kvVal > 0) setNumField(cells, "kv", kvVal, "kV");
      }
      if (vUnitStr === "kV" && vParsed.num !== null && vParsed.num > 0) {
        setNumField(cells, "kv", vParsed.num, "kV");
      } else if (vUnitStr === "V" && vParsed.num !== null && vParsed.num > 0) {
        setNumField(cells, "kv", vParsed.num / 1000, "kV");
      }
    } else if (catId === "reclosers") {
      if (rUnitStr === "A" && rParsed.num !== null) {
        setNumField(cells, "a", rParsed.num, "A");
      } else if (rRawStr && !rUnitStr) {
        setTextField(cells, "code", rRawStr);
      }
      if (vUnitStr === "kV" && vParsed.num !== null) setNumField(cells, "kv", vParsed.num, "kV");
    } else if (catId === "controllers") {
      if (rUnitStr === "kW" && rParsed.num !== null) {
        setNumField(cells, "kw", rParsed.num, "kW");
      } else if (rUnitStr === "W" && rParsed.num !== null) {
        setNumField(cells, "kw", rParsed.num / 1000, "kW");
      } else if (rRawStr && !rUnitStr) {
        setTextField(cells, "code", rRawStr);
      }
      setVoltageOrSlashField(cells, "v", vRawStr, vUnitStr, vParsed);
    } else if (catId === "surge-protection") {
      if (rUnitStr === "kV MCOV" && rParsed.num !== null) setNumField(cells, "mcov", rParsed.num, "kV");
      if (vUnitStr === "kV" && vParsed.num !== null) setNumField(cells, "kv", vParsed.num, "kV");
    } else if (catId === "grounding") {
      if (rUnitStr === "A" && rParsed.num !== null) setNumField(cells, "a", rParsed.num, "A");
      else if (rUnitStr === "ft" && rParsed.num !== null) setNumField(cells, "ft", rParsed.num, "ft");
      if (vUnitStr === "kV" && vParsed.num !== null) setNumField(cells, "kv", vParsed.num, "kV");
    } else if (catId === "cable-trays" || catId === "conduits") {
      if (rParsed.num !== null) setNumField(cells, "in", rParsed.num, "in");
    } else if (catId === "terminations") {
      if (rUnitStr === "A" && rParsed.num !== null) setNumField(cells, "a", rParsed.num, "A");
      if (vRawStr) setTextField(cells, "vspec", vRawStr);
    } else if (catId === "parts") {
      if (rRawStr) setTextField(cells, "size", rRawStr);
    }

    return cells;
  }

  function createDefaultFilters() {
    return {
      query: "",
      modelQuery: "",
      maker: "",
      makerQuery: "",
      type: "",
      cols: {},
    };
  }

  function hasActiveColumnFilters(f) {
    if (!f) return false;
    if (f.query || f.modelQuery || f.maker || f.makerQuery || f.type) return true;
    const cols = f.cols || {};
    for (const key of Object.keys(cols)) {
      const cf = cols[key];
      if (!cf) continue;
      if (cf.text || cf.select || (cf.min !== undefined && cf.min !== "") || (cf.max !== undefined && cf.max !== "")) {
        return true;
      }
    }
    return false;
  }

  function extractCollectionFacets(records, catId) {
    const schema = getCategorySchema(catId);
    const makerCounts = new Map();
    const typeCounts = new Map();
    const specValueCounts = {};
    const specBlankCounts = {};
    const specRanges = {};

    for (const col of schema.specCols) {
      specValueCounts[col.key] = new Map();
      specBlankCounts[col.key] = 0;
      specRanges[col.key] = { min: Infinity, max: -Infinity, count: 0 };
    }

    let blankMakerCount = 0;
    const list = records || [];
    const normCache = new Array(list.length);

    for (let i = 0; i < list.length; i += 1) {
      const r = list[i];
      const rowCells = extractNormalizedRow(catId, r);
      normCache[i] = rowCells;

      const maker = String(r[I.maker] || "").trim();
      if (maker) {
        makerCounts.set(maker, (makerCounts.get(maker) || 0) + 1);
      } else {
        blankMakerCount += 1;
      }

      const type = String(r[I.type] || "").trim();
      if (type) {
        typeCounts.set(type, (typeCounts.get(type) || 0) + 1);
      }

      for (const col of schema.specCols) {
        const cell = rowCells[col.key];
        if (!cell) {
          specBlankCounts[col.key] += 1;
          continue;
        }
        const vc = specValueCounts[col.key];
        vc.set(cell.text, (vc.get(cell.text) || 0) + 1);
        if (cell.num !== null) {
          const rng = specRanges[col.key];
          if (cell.num < rng.min) rng.min = cell.num;
          if (cell.num > rng.max) rng.max = cell.num;
          rng.count += 1;
        }
      }
    }

    const sortByCountDesc = (entries) =>
      entries
        .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
        .map(([value, count]) => ({ value, count }));

    const specFacets = {};
    for (const col of schema.specCols) {
      const rng = specRanges[col.key];
      specFacets[col.key] = {
        values: sortByCountDesc(Array.from(specValueCounts[col.key].entries())),
        blankCount: specBlankCounts[col.key],
        range: rng.min <= rng.max ? { min: rng.min, max: rng.max, count: rng.count } : null,
      };
    }

    return {
      catId,
      schema,
      total: list.length,
      normCache,
      makers: sortByCountDesc(Array.from(makerCounts.entries())),
      blankMakerCount,
      types: sortByCountDesc(Array.from(typeCounts.entries())),
      specFacets,
    };
  }

  function filterCollectionRecords(records, filters, catId, existingNormCache) {
    const list = records || [];
    const f = filters || {};
    const schema = getCategorySchema(catId);

    const q = String(f.query || "").trim().toLowerCase();
    const mq = String(f.modelQuery || "").trim().toLowerCase();
    const maker = String(f.maker || "").trim();
    const makerQ = String(f.makerQuery || "").trim().toLowerCase();
    const type = String(f.type || "").trim();
    const colFilters = f.cols || {};

    const activeSpecChecks = [];
    for (const col of schema.specCols) {
      const cf = colFilters[col.key];
      if (!cf) continue;
      const textQ = String(cf.text || "").trim().toLowerCase();
      const selVal = String(cf.select || "").trim();
      const hasMin = cf.min !== undefined && cf.min !== "" && cf.min !== null && Number.isFinite(Number(cf.min));
      const hasMax = cf.max !== undefined && cf.max !== "" && cf.max !== null && Number.isFinite(Number(cf.max));
      if (!textQ && !selVal && !hasMin && !hasMax) continue;
      activeSpecChecks.push({
        key: col.key,
        textQ,
        selVal,
        hasMin,
        minNum: hasMin ? Number(cf.min) : null,
        hasMax,
        maxNum: hasMax ? Number(cf.max) : null,
      });
    }

    const matched = [];

    for (let i = 0; i < list.length; i += 1) {
      const r = list[i];
      const rowCells = existingNormCache ? existingNormCache[i] : extractNormalizedRow(catId, r);

      if (mq) {
        const model = String(r[I.model] || "").toLowerCase();
        const rid = String(r[I.rid] || "").toLowerCase();
        if (!model.includes(mq) && !rid.includes(mq)) continue;
      }

      if (maker) {
        const rmaker = String(r[I.maker] || "").trim();
        if (maker === EMPTY_VALUE_TOKEN) {
          if (rmaker !== "") continue;
        } else if (rmaker !== maker) {
          continue;
        }
      }

      if (makerQ) {
        const rmakerLower = String(r[I.maker] || "").toLowerCase();
        if (!rmakerLower.includes(makerQ)) continue;
      }

      if (type) {
        if (String(r[I.type] || "").trim() !== type) continue;
      }

      let specOk = true;
      for (let s = 0; s < activeSpecChecks.length; s += 1) {
        const chk = activeSpecChecks[s];
        const cell = rowCells[chk.key];
        if (chk.selVal) {
          if (chk.selVal === EMPTY_VALUE_TOKEN) {
            if (cell) {
              specOk = false;
              break;
            }
          } else if (!cell || cell.text !== chk.selVal) {
            specOk = false;
            break;
          }
        }
        if (chk.textQ) {
          if (!cell || !cell.text.toLowerCase().includes(chk.textQ)) {
            specOk = false;
            break;
          }
        }
        if (chk.hasMin || chk.hasMax) {
          if (!cell || cell.num === null) {
            specOk = false;
            break;
          }
          if (chk.hasMin && cell.num < chk.minNum) {
            specOk = false;
            break;
          }
          if (chk.hasMax && cell.num > chk.maxNum) {
            specOk = false;
            break;
          }
        }
      }
      if (!specOk) continue;

      if (q) {
        const specHay = schema.specCols
          .map((c) => (rowCells[c.key] ? rowCells[c.key].text : ""))
          .filter(Boolean)
          .join(" ");
        const hay =
          String(r[I.search] || "") ||
          [r[I.rid], r[I.maker], r[I.model], r[I.type], specHay]
            .join(" ")
            .toLowerCase();
        if (!hay.includes(q)) continue;
      }

      matched.push(i);
    }

    return matched;
  }

  return {
    I,
    EMPTY_VALUE_TOKEN,
    BASE_IDENTITY_COLUMNS,
    CATEGORY_SPEC_COLUMNS,
    getCategorySchema,
    cleanFloatNumber,
    formatCleanNumber,
    formatReferenceCell,
    parseScalarNumber,
    extractNormalizedRow,
    createDefaultFilters,
    hasActiveColumnFilters,
    extractCollectionFacets,
    filterCollectionRecords,
  };
});
