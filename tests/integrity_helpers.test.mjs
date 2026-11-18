import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import zlib from "node:zlib";

await import("../01_Engineering_Equipment_Database/website/dist/assets/integrity_helpers.js");
const helpers = globalThis.IntegrityHelpers;

const DIST_DIR = path.resolve("01_Engineering_Equipment_Database/website/dist");
const VERIF_DIR = path.join(DIST_DIR, "verification");
const QUARANTINE_DIR = path.resolve("01_Engineering_Equipment_Database/quarantine");

function decodeCollection(relFile) {
  const txt = fs.readFileSync(path.join(DIST_DIR, relFile), "utf8");
  const m = txt.match(/window\.CollectionReceive\([^,]+,\s*"([^"]+)"/);
  assert.ok(m, `Expected CollectionReceive wrapper in ${relFile}`);
  return JSON.parse(zlib.gunzipSync(Buffer.from(m[1], "base64")).toString("utf8"));
}

test("Catalog index reflects clean post-quarantine totals (195,478 records, 39,275 PV modules) and 34 curated references", () => {
  assert.equal(fs.existsSync(path.join(VERIF_DIR, "unresolved_research_ledger.json")), false);

  const idxTxt = fs.readFileSync(path.join(DIST_DIR, "collections", "index.js"), "utf8");
  const catalog = JSON.parse(idxTxt.replace(/^window\.EQUIPMENT_CATALOG=/, "").replace(/;\s*$/, ""));

  assert.equal(catalog.catalogRecords, 195478);
  assert.equal(catalog.collections.length, 29);
  const pv = catalog.collections.find((c) => c.id === "pv-modules");
  assert.equal(pv.count, 39275);

  assert.equal(catalog.references.length, 34);
  const refIds = new Set(catalog.references.map((r) => r.id));
  for (const banned of ["s084", "s086", "s111", "s079", "s025", "s027", "s106", "s078"]) {
    assert.equal(refIds.has(banned), false, `Excluded reference ${banned} must not be in catalog`);
  }
});

test("Live database and repository contain zero quarantined material, zero custom/blank/template records, and zero unverified/conflict flags", () => {
  assert.equal(fs.existsSync(QUARANTINE_DIR), false, "Quarantine folder must be permanently deleted");

  const idxTxt = fs.readFileSync(path.join(DIST_DIR, "collections", "index.js"), "utf8");
  const catalog = JSON.parse(idxTxt.replace(/^window\.EQUIPMENT_CATALOG=/, "").replace(/;\s*$/, ""));
  const forbiddenIds = new Set([
    "PVM-025864",
    "IBR-CEC-000403",
    "NGR-PGR-LRG-13P8-400A-10S-TEMPLATE",
    "IBR-CEC-000253",
    "IBR-CEC-000254",
    "DB09-GND-00057",
    "DB09-GND-00058",
    "DB09-GND-00059",
    "DB09-GND-00060",
  ]);

  for (const col of catalog.collections) {
    const data = decodeCollection(col.file);
    assert.equal(data.records.length, col.count);
    for (const r of data.records) {
      assert.equal(forbiddenIds.has(r[1]), false, `Quarantined/deleted ID ${r[1]} leaked into ${col.id}`);
      assert.equal(Boolean(r[8]), false, `Stale review=true flag left on ${col.id}:${r[1]}`);
      assert.equal(
        /USER_PROVIDED_UNVERIFIED|UNIT_REVIEW_REQUIRED|SOURCE_CONFLICT|SCCR_UNRESOLVED|RESIDUAL_WAVEFORM_PENDING|PARAMETERS_NOT_QUALIFIED|BLOCKED_RATING_BASIS/i.test(String(r[7] || "")),
        false,
        `Unverified quality flag on ${col.id}:${r[1]} (${r[7]})`
      );
    }
  }
});

test("Inverters, EV-charging, and Controllers preserve slash-separated multi-voltage AC specs and separate single-unit columns", () => {
  const schema = helpers.getCategorySchema("inverters");
  assert.deepEqual(
    schema.specCols.map((c) => c.label),
    ["Power (kW)", "Apparent Power (kVA)", "AC Voltage (V)"]
  );

  const invW = helpers.extractNormalizedRow("inverters", [
    "INV:1", "INV-1", "SMA", "SB20000", "Inverter", ["20000", "W", "Pmax"], ["0.48", "kV", "Vac"], "", false, ["ACTIVE"], [], null, 0, 0, "", ""
  ]);
  assert.equal(invW.kw.num, 20);
  assert.equal(invW.kw.text, "20 kW");
  assert.equal(invW.kva, undefined);
  assert.equal(invW.v.num, 480);
  assert.equal(invW.v.text, "480 V");

  const invSlash = helpers.extractNormalizedRow("inverters", [
    "INV:2", "DB11-PCS-00069", "GoodWe", "GW22KLV-SMT-US", "Inverter", ["22", "kW", ""], ["208/240", "V", ""], "", false, ["ACTIVE"], [], null, 0, 0, "", ""
  ]);
  assert.equal(invSlash.v.num, 240);
  assert.equal(invSlash.v.text, "208/240 V");

  const evSlash = helpers.extractNormalizedRow("ev-charging", [
    "EV:1", "DB11-V2G-00003", "dcbel", "Ara", "Bidirectional Charger", ["7.6", "kW", ""], ["208/240", "Vac", ""], "", false, ["ACTIVE"], [], null, 0, 0, "", ""
  ]);
  assert.equal(evSlash.v.num, 240);
  assert.equal(evSlash.v.text, "208/240 V");

  const ctlSlash = helpers.extractNormalizedRow("controllers", [
    "CTL:1", "DB11-PCS-00017", "Enphase", "IQ Gateway", "PCS", ["0", "kW", ""], ["120/208/240", "V", ""], "", false, ["ACTIVE"], [], null, 0, 0, "", ""
  ]);
  assert.equal(ctlSlash.v.num, 240);
  assert.equal(ctlSlash.v.text, "120/208/240 V");

  const invMva = helpers.extractNormalizedRow("inverters", [
    "INV:3", "INV-3", "Fronius", "Verto 33.3", "Inverter", ["0.0333", "MVA", "Smax"], ["0.4", "kV", ""], "", false, [], [], null, 0, 0, "", ""
  ]);
  assert.equal(invMva.kw, undefined);
  assert.equal(invMva.kva.num, 33.3);
  assert.equal(invMva.kva.text, "33.3 kVA");
  assert.equal(invMva.v.num, 400);
});

test("Energy Storage, Motors, Grounding, Fuses, Conductors, and Breakers enforce single-unit columns and suppress 0 placeholders", () => {
  const essKva = helpers.extractNormalizedRow("energy-storage", [
    "ESS:1", "ESS-1", "Maker", "M1", "Energy storage system", ["34.5*", "kVA", ""], ["208/240", "V", ""], "", false, [], [], null, 0, 0, "", ""
  ]);
  assert.equal(essKva.kva.num, 34.5);
  assert.equal(essKva.kva.text, "34.5 kVA");
  assert.equal(essKva.kwh, undefined);
  assert.equal(essKva.v.text, "208/240 V");

  const essCell = helpers.extractNormalizedRow("energy-storage", [
    "ESS:2", "ESS-2", "Enersys", "Cell2V", "Battery", ["2552", "Ah", ""], ["2.055000066757202", "V/cell", ""], "", false, [], [], null, 0, 0, "", ""
  ]);
  assert.equal(essCell.ah.num, 2552);
  assert.equal(essCell.ah.text, "2,552 Ah");
  assert.equal(essCell.vcell.num, 2.055);
  assert.equal(essCell.vcell.text, "2.055 V/cell");

  const motHp = helpers.extractNormalizedRow("motors", [
    "MOT:1", "MOT-1", "WEG", "W22", "Motor", ["250", "HP", ""], ["4.16", "kV", ""], "", false, [], [], null, 0, 0, "", ""
  ]);
  assert.equal(motHp.hp.num, 250);
  assert.equal(motHp.kva, undefined);
  assert.equal(motHp.kv.num, 4.16);

  // Zero-placeholder suppression on unrated EPRI conductors and Cooper Isolation Links
  const condZero = helpers.extractNormalizedRow("conductors", [
    "CND:1", "TCD-000107", "Generic", "556.5 kcmil", "Transmission conductor", ["0", "A", "Ampacity (A)"], ["", "", ""], "", false, [], [], null, 0, 0, "", ""
  ]);
  assert.equal(condZero.a, undefined);

  const fuseZero = helpers.extractNormalizedRow("fuses", [
    "FUS:0", "FUS-002641", "Cooper", "Isolation Link", "Fuse", ["0", "kV", "Maximum Rating"], ["", "", ""], "", false, [], [], null, 0, 0, "", ""
  ]);
  assert.equal(fuseZero.kv, undefined);
  assert.equal(fuseZero.a, undefined);

  const fuseV = helpers.extractNormalizedRow("fuses", [
    "FUS:1", "FUS-1", "Bussmann", "FWP-1500", "Fuse", ["1500", "V", "Maximum Rating"], ["", "", ""], "", false, [], [], null, 0, 0, "", ""
  ]);
  assert.equal(fuseV.a, undefined);
  assert.equal(fuseV.kv.num, 1.5);
  assert.equal(fuseV.kv.text, "1.5 kV");

  const brkDc = helpers.extractNormalizedRow("breakers", [
    "BRK:1", "BRK-1", "ABB", "Tmax DC", "LV breaker", ["1200", "A", ""], ["250", "(source)", ""], "", false, [], [], null, 0, 0, "", ""
  ]);
  assert.equal(brkDc.a.num, 1200);
  assert.equal(brkDc.kv.num, 0.25);
  assert.equal(brkDc.kv.text, "0.25 kV");

  const brkTrip = helpers.extractNormalizedRow("breakers", [
    "BRK:2", "BRK-2", "ABB", "PR121", "Trip unit", ["121", "", "Rating Or Variant"], ["", "", ""], "", false, [], [], null, 0, 0, "", ""
  ]);
  assert.equal(brkTrip.a, undefined);
  assert.equal(brkTrip.code.text, "121");

  const gndRod = helpers.extractNormalizedRow("grounding", [
    "GND:1", "GND-1", "", "Ground Rod 10ft", "Ground electrode", ["10", "ft", "Length"], ["", "", ""], "", false, [], [], null, 0, 0, "", ""
  ]);
  assert.equal(gndRod.ft.num, 10);
  assert.equal(gndRod.a, undefined);
});

test("formatReferenceCell strips binary floating point tails cleanly", () => {
  assert.equal(helpers.formatReferenceCell(26.79999923706055), "26.8");
  assert.equal(helpers.formatReferenceCell("26.79999923706055"), "26.8");
  assert.equal(helpers.formatReferenceCell(null), "—");
  assert.equal(helpers.formatReferenceCell("CU 600V"), "CU 600V");
});

test("extractCollectionFacets and filterCollectionRecords filter across every dynamic single-unit column", () => {
  const sampleInverters = [
    ["INV:1", "I-001", "Anker", "A17E1", "Inverter control configuration", ["7.68", "kW", ""], ["240", "V", ""], "", false, [], [], null, 0, 0, "", ""],
    ["INV:2", "I-002", "SMA", "STP20", "Inverter", ["20000", "W", ""], ["0.48", "kV", ""], "", false, [], [], null, 0, 0, "", ""],
    ["INV:3", "I-003", "", "SG53", "Inverter", ["0.053", "MVA", ""], ["0.48", "kV", ""], "", false, [], [], null, 0, 0, "", ""],
  ];

  const facets = helpers.extractCollectionFacets(sampleInverters, "inverters");
  assert.equal(facets.total, 3);
  assert.equal(facets.blankMakerCount, 1);
  assert.equal(facets.specFacets.kw.range.min, 7.68);
  assert.equal(facets.specFacets.kw.range.max, 20);
  assert.equal(facets.specFacets.kva.range.min, 53);

  assert.deepEqual(
    helpers.filterCollectionRecords(sampleInverters, { cols: { kw: { min: "5", max: "25" } } }, "inverters", facets.normCache),
    [0, 1]
  );
  assert.deepEqual(
    helpers.filterCollectionRecords(sampleInverters, { cols: { kva: { min: "50", max: "60" } } }, "inverters", facets.normCache),
    [2]
  );
  assert.deepEqual(
    helpers.filterCollectionRecords(sampleInverters, { cols: { v: { select: "480 V" } } }, "inverters", facets.normCache),
    [1, 2]
  );
  assert.deepEqual(
    helpers.filterCollectionRecords(sampleInverters, { maker: helpers.EMPTY_VALUE_TOKEN }, "inverters", facets.normCache),
    [2]
  );
  assert.deepEqual(
    helpers.filterCollectionRecords(sampleInverters, { modelQuery: "stp20" }, "inverters", facets.normCache),
    [1]
  );
});
