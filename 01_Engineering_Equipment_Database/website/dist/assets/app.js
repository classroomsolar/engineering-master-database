(function () {
  "use strict";

  const H = window.IntegrityHelpers;
  const I = H.I;
  const EMPTY_TOKEN = H.EMPTY_VALUE_TOKEN;
  const CATALOG =
    window.EQUIPMENT_CATALOG && typeof window.EQUIPMENT_CATALOG === "object"
      ? window.EQUIPMENT_CATALOG
      : { collections: [], references: [], catalogRecords: 0 };
  const DB_CATALOG =
    window.DB_CATALOG && typeof window.DB_CATALOG === "object"
      ? window.DB_CATALOG
      : { sheets: [] };

  const SVG_NS = "http://www.w3.org/2000/svg";
  const ICON_PATHS = {
    menu: ["M3 6h18M3 12h18M3 18h18"],
    grid: ["M3 3h7v7H3zM14 3h7v7h-7zM14 14h7v7h-7zM3 14h7v7H3z"],
    book: ["M4 19.5A2.5 2.5 0 0 1 6.5 17H20", "M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"],
    sun: ["M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42", "M12 7a5 5 0 1 0 0 10 5 5 0 0 0 0-10z"],
    moon: ["M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"],
    search: ["M11 19a8 8 0 1 0 0-16 8 8 0 0 0 0 16z", "M21 21l-4.35-4.35"],
    reset: ["M3 12a9 9 0 1 0 3-6.7L3 8", "M3 3v5h5"],
    close: ["M18 6L6 18", "M6 6l12 12"],
  };

  function createIconSvg(name) {
    const svg = document.createElementNS(SVG_NS, "svg");
    svg.setAttribute("viewBox", "0 0 24 24");
    svg.setAttribute("fill", "none");
    svg.setAttribute("stroke", "currentColor");
    svg.setAttribute("stroke-width", "1.9");
    svg.setAttribute("stroke-linecap", "round");
    svg.setAttribute("stroke-linejoin", "round");
    svg.setAttribute("aria-hidden", "true");
    const paths = ICON_PATHS[name] || ICON_PATHS.grid;
    for (const d of paths) {
      const p = document.createElementNS(SVG_NS, "path");
      p.setAttribute("d", d);
      svg.appendChild(p);
    }
    return svg;
  }

  function hydrateStaticIcons() {
    document.querySelectorAll(".icon-slot[data-icon]").forEach((slot) => {
      slot.replaceChildren(createIconSvg(slot.dataset.icon));
    });
  }

  function el(tag, attrs, children) {
    const node = document.createElement(tag);
    if (attrs) {
      for (const [k, v] of Object.entries(attrs)) {
        if (v === null || v === undefined || v === false) continue;
        if (k === "className") node.className = v;
        else if (k === "text") node.textContent = String(v);
        else if (k === "style" && typeof v === "object") Object.assign(node.style, v);
        else if (k.startsWith("on") && typeof v === "function") node.addEventListener(k.slice(2).toLowerCase(), v);
        else node.setAttribute(k, v === true ? "" : String(v));
      }
    }
    if (children !== undefined && children !== null) {
      const list = Array.isArray(children) ? children : [children];
      for (const child of list) {
        if (child === null || child === undefined || child === false) continue;
        if (typeof child === "string" || typeof child === "number") {
          node.appendChild(document.createTextNode(String(child)));
        } else {
          node.appendChild(child);
        }
      }
    }
    return node;
  }

  const collator = new Intl.Collator("en", { numeric: true, sensitivity: "base" });
  const fmtInt = (n) => Number(n || 0).toLocaleString("en-US");

  async function gunzipBase64Json(b64) {
    const bin = atob(b64);
    const bytes = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i += 1) {
      bytes[i] = bin.charCodeAt(i);
    }
    const ds = new DecompressionStream("gzip");
    const stream = new Blob([bytes]).stream().pipeThrough(ds);
    const text = await new Response(stream).text();
    return JSON.parse(text);
  }

  const pendingCollection = new Map();
  const pendingSearch = new Map();
  const pendingSheet = new Map();

  window.CollectionReceive = function (id, b64) {
    const entry = pendingCollection.get(id);
    if (!entry) return;
    gunzipBase64Json(b64).then(entry.resolve, entry.reject);
  };

  window.SearchReceive = function (id, b64) {
    const entry = pendingSearch.get(id);
    if (!entry) return;
    gunzipBase64Json(b64).then(entry.resolve, entry.reject);
  };

  window.DBReceive = function (sheetId, chunkIdx, b64) {
    const key = `${sheetId}:${chunkIdx}`;
    const entry = pendingSheet.get(key);
    if (!entry) return;
    gunzipBase64Json(b64).then(entry.resolve, entry.reject);
  };

  function injectScript(src) {
    return new Promise((resolve, reject) => {
      const s = document.createElement("script");
      s.src = src;
      s.async = true;
      s.onload = () => resolve();
      s.onerror = () => reject(new Error(`Failed to load ${src}`));
      document.head.appendChild(s);
    });
  }

  const collectionCache = new Map();
  const searchLoadedIds = new Set();
  const sheetChunkCache = new Map();
  const sheetMetaById = new Map(((DB_CATALOG && DB_CATALOG.sheets) || []).map((s) => [s.id, s]));

  async function loadCollectionData(meta) {
    if (collectionCache.has(meta.id)) return collectionCache.get(meta.id);
    const dataPromise = new Promise((resolve, reject) => {
      pendingCollection.set(meta.id, { resolve, reject });
    });
    await injectScript(meta.file);
    const decoded = await dataPromise;
    pendingCollection.delete(meta.id);
    const records = decoded.records || decoded || [];
    const facets = H.extractCollectionFacets(records, meta.id);
    const payload = { meta, records, facets };
    collectionCache.set(meta.id, payload);
    return payload;
  }

  async function ensureSearchIndexLoaded(meta) {
    if (!meta || !meta.searchFile || searchLoadedIds.has(meta.id)) return;
    if (pendingSearch.has(meta.id)) return;
    const statusEl = document.getElementById("search-index-status");
    if (statusEl) statusEl.textContent = "Indexing...";
    const dataPromise = new Promise((resolve, reject) => {
      pendingSearch.set(meta.id, { resolve, reject });
    });
    try {
      await injectScript(meta.searchFile);
      const decoded = await dataPromise;
      const arr = decoded.search || [];
      const cached = collectionCache.get(meta.id);
      if (cached && cached.records) {
        for (let i = 0; i < cached.records.length && i < arr.length; i += 1) {
          cached.records[i][I.search] = arr[i] || "";
        }
      }
      searchLoadedIds.add(meta.id);
      if (statusEl) statusEl.textContent = "Full index ready";
    } catch (_err) {
      if (statusEl) statusEl.textContent = "";
    } finally {
      pendingSearch.delete(meta.id);
    }
  }

  async function loadSheetChunk(sheetId, chunkIdx) {
    const key = `${sheetId}:${chunkIdx}`;
    if (sheetChunkCache.has(key)) return sheetChunkCache.get(key);
    const sMeta = sheetMetaById.get(sheetId);
    if (!sMeta || !sMeta.chunks || !sMeta.chunks[chunkIdx]) return null;
    const p = new Promise((resolve, reject) => {
      pendingSheet.set(key, { resolve, reject });
    });
    await injectScript(sMeta.chunks[chunkIdx].file);
    const decoded = await p;
    pendingSheet.delete(key);
    sheetChunkCache.set(key, decoded);
    return decoded;
  }

  async function loadSheetRow(sheetId, targetRowNum) {
    const sMeta = sheetMetaById.get(sheetId);
    if (!sMeta) return null;
    const chunkCount = (sMeta.chunks || []).length;
    for (let idx = 0; idx < chunkCount; idx += 1) {
      const chunk = await loadSheetChunk(sheetId, idx);
      if (!chunk || !Array.isArray(chunk.rows)) continue;
      for (let i = 0; i < chunk.rows.length; i += 1) {
        if (chunk.rows[i][0] === targetRowNum) {
          return { meta: sMeta, row: chunk.rows[i] };
        }
      }
    }
    return null;
  }

  const state = {
    theme: localStorage.getItem("edb_theme") || "dark",
    activeView: "catalog",
    activeCategoryId: CATALOG.collections[0] ? CATALOG.collections[0].id : "pv-modules",
    catFilterQuery: "",
    filters: H.createDefaultFilters(),
    sortKey: "model",
    sortDir: "asc",
    pageSize: 100,
    page: 1,
    filteredIndices: [],
    selectedRecordUid: null,
    // Consolidated References Workspace
    activeRefId: CATALOG.references[0] ? CATALOG.references[0].id : "s002",
    refListQuery: "",
    refGlobalQuery: "",
    refColFilters: [],
    refActiveRows: [],
    refActiveHeaders: [],
    refFilteredRows: [],
    refPageSize: 100,
    refPage: 1,
  };

  function applyTheme(theme) {
    state.theme = theme === "light" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", state.theme);
    localStorage.setItem("edb_theme", state.theme);
    const slot = document.getElementById("theme-icon-slot");
    if (slot) {
      slot.replaceChildren(createIconSvg(state.theme === "dark" ? "sun" : "moon"));
    }
  }

  function switchWorkspace(view) {
    state.activeView = view === "references" ? "references" : "catalog";
    const isRefs = state.activeView === "references";

    document.getElementById("nav-catalog-btn").classList.toggle("is-active", !isRefs);
    document.getElementById("nav-refs-btn").classList.toggle("is-active", isRefs);

    document.getElementById("catalog-workspace").hidden = isRefs;
    document.getElementById("references-workspace").hidden = !isRefs;

    document.getElementById("sidebar-catalog-pane").hidden = isRefs;
    document.getElementById("sidebar-refs-pane").hidden = !isRefs;

    closeMobileSidebar();
    closeRecordDrawer();

    if (isRefs && !state.refActiveHeaders.length) {
      selectReferenceTable(state.activeRefId);
    } else if (isRefs) {
      renderRefSidebar();
    }
  }

  // Category Rail
  function renderCategoryRail() {
    const rail = document.getElementById("category-rail");
    const q = state.catFilterQuery.trim().toLowerCase();
    const groups = new Map();
    for (const c of CATALOG.collections) {
      if (q) {
        const hay = `${c.label} ${c.family} ${(c.types || []).join(" ")} ${c.id}`.toLowerCase();
        if (!hay.includes(q)) continue;
      }
      if (!groups.has(c.family)) groups.set(c.family, []);
      groups.get(c.family).push(c);
    }

    const frag = document.createDocumentFragment();
    if (groups.size === 0) {
      frag.appendChild(el("div", { className: "empty-state-cell", text: "No matching categories." }));
    } else {
      for (const [family, items] of groups.entries()) {
        const famTotal = items.reduce((acc, it) => acc + (it.count || 0), 0);
        const groupEl = el("div", { className: "cat-group" }, [
          el("div", { className: "cat-group-title" }, [
            el("span", { text: family }),
            el("span", { className: "tabular-nums", text: fmtInt(famTotal) }),
          ]),
        ]);
        for (const item of items) {
          groupEl.appendChild(
            el(
              "button",
              {
                type: "button",
                className: `cat-item${item.id === state.activeCategoryId ? " is-active" : ""}`,
                "data-cat-id": item.id,
                onClick: () => selectCategory(item.id),
              },
              [
                el("span", { className: "cat-item-label", text: item.label }),
                el("span", { className: "cat-item-count tabular-nums", text: fmtInt(item.count) }),
              ]
            )
          );
        }
        frag.appendChild(groupEl);
      }
    }
    rail.replaceChildren(frag);
  }

  function ensureColFilterObj(key) {
    if (!state.filters.cols[key]) {
      state.filters.cols[key] = { text: "", select: "", min: "", max: "" };
    }
    return state.filters.cols[key];
  }

  let debounceCatalogTimer = null;
  function debouncedRecompute() {
    clearTimeout(debounceCatalogTimer);
    debounceCatalogTimer = setTimeout(() => recomputeCatalog(true), 110);
  }

  function syncColumnFilterStyles() {
    document.querySelectorAll("#catalog-thead [data-col-filter]").forEach((node) => {
      const v = node.value;
      node.classList.toggle("is-filtered", Boolean(v !== "" && v !== null && v !== undefined));
    });
    const gIn = document.getElementById("global-search-input");
    if (gIn) {
      gIn.value = state.filters.query || "";
      gIn.classList.toggle("is-filtered", Boolean(state.filters.query));
    }
  }

  // Dynamic Column Builder for Active Category
  function buildCategoryTableHead(facets) {
    const schema = facets.schema;
    const cols = schema.columns;
    const table = document.getElementById("catalog-table");
    const colgroup = document.getElementById("catalog-colgroup");
    const thead = document.getElementById("catalog-thead");

    table.style.minWidth = `${Math.max(820, cols.length * 165)}px`;

    // Clean column widths tailored to active column count
    const specCount = schema.specCols.length;
    const cgNodes = [];
    if (specCount === 0) {
      cgNodes.push(el("col", { style: { width: "40%" } }));
      cgNodes.push(el("col", { style: { width: "35%" } }));
      cgNodes.push(el("col", { style: { width: "25%" } }));
    } else {
      const idModelW = specCount >= 5 ? "15%" : "22%";
      const idMakerW = specCount >= 5 ? "13%" : "18%";
      const idTypeW = specCount >= 5 ? "11%" : "14%";
      const remPct = 100 - (parseFloat(idModelW) + parseFloat(idMakerW) + parseFloat(idTypeW));
      const eachSpecPct = (remPct / specCount).toFixed(2) + "%";
      cgNodes.push(el("col", { style: { width: idModelW } }));
      cgNodes.push(el("col", { style: { width: idMakerW } }));
      cgNodes.push(el("col", { style: { width: idTypeW } }));
      for (let i = 0; i < specCount; i += 1) {
        cgNodes.push(el("col", { style: { width: eachSpecPct } }));
      }
    }
    colgroup.replaceChildren(...cgNodes);

    const hRow = el("tr", { className: "col-header-row" });
    const fRow = el("tr", { className: "col-filter-row", "aria-label": "Per-column equipment filters" });

    for (const col of cols) {
      // Header cell with sort button
      hRow.appendChild(
        el("th", { scope: "col" }, [
          el(
            "button",
            {
              className: "sort-btn",
              type: "button",
              onClick: () => {
                if (state.sortKey === col.key) {
                  state.sortDir = state.sortDir === "asc" ? "desc" : "asc";
                } else {
                  state.sortKey = col.key;
                  state.sortDir = "asc";
                }
                recomputeCatalog(false);
              },
            },
            [
              el("span", { text: col.label }),
              el("span", { className: "sort-indicator", "data-sort-ind": col.key }),
            ]
          ),
        ])
      );

      // Dedicated per-column filter cell
      if (col.key === "model") {
        fRow.appendChild(
          el("th", null, [
            el("input", {
              type: "search",
              className: "cf-input",
              placeholder: "Filter model / ID...",
              "aria-label": "Filter Equipment or Model",
              "data-col-filter": "model",
              value: state.filters.modelQuery,
              onInput: (ev) => {
                state.filters.modelQuery = ev.target.value;
                syncColumnFilterStyles();
                debouncedRecompute();
              },
            }),
          ])
        );
      } else if (col.key === "maker") {
        const makerOpts = [el("option", { value: "", text: `All makers (${facets.makers.length})` })];
        if (facets.blankMakerCount > 0) {
          makerOpts.push(
            el("option", {
              value: EMPTY_TOKEN,
              text: `(Unstated) (${fmtInt(facets.blankMakerCount)})`,
            })
          );
        }
        for (const m of facets.makers) {
          makerOpts.push(el("option", { value: m.value, text: `${m.value} (${fmtInt(m.count)})` }));
        }
        const makerSel = el(
          "select",
          {
            className: "cf-select",
            "aria-label": "Filter Manufacturer exact value",
            "data-col-filter": "maker",
            onChange: (ev) => {
              state.filters.maker = ev.target.value;
              syncColumnFilterStyles();
              recomputeCatalog(true);
            },
          },
          makerOpts
        );
        makerSel.value = state.filters.maker || "";

        fRow.appendChild(
          el("th", null, [
            el("div", { className: "cf-stack" }, [
              makerSel,
              el("input", {
                type: "search",
                className: "cf-input cf-input-xs",
                placeholder: "Contains maker...",
                "aria-label": "Filter Manufacturer text",
                "data-col-filter": "makerQuery",
                value: state.filters.makerQuery,
                onInput: (ev) => {
                  state.filters.makerQuery = ev.target.value;
                  syncColumnFilterStyles();
                  debouncedRecompute();
                },
              }),
            ]),
          ])
        );
      } else if (col.key === "type") {
        const typeOpts = [el("option", { value: "", text: `All types (${facets.types.length})` })];
        for (const t of facets.types) {
          typeOpts.push(el("option", { value: t.value, text: `${t.value} (${fmtInt(t.count)})` }));
        }
        const typeSel = el(
          "select",
          {
            className: "cf-select",
            "aria-label": "Filter Equipment Type",
            "data-col-filter": "type",
            onChange: (ev) => {
              state.filters.type = ev.target.value;
              syncColumnFilterStyles();
              recomputeCatalog(true);
            },
          },
          typeOpts
        );
        typeSel.value = state.filters.type || "";
        fRow.appendChild(el("th", null, [typeSel]));
      } else {
        // Dynamic Single-Unit Spec Column Filter
        const sf = facets.specFacets[col.key] || { values: [], blankCount: 0, range: null };
        const cf = ensureColFilterObj(col.key);
        const stackChildren = [];

        if (col.filterType === "range_select" || col.filterType === "text_select") {
          const selOpts = [
            el("option", {
              value: "",
              text: col.unit ? `All (${col.unit})` : "All values",
            }),
          ];
          if (sf.blankCount > 0 && sf.values.length > 0) {
            selOpts.push(
              el("option", {
                value: EMPTY_TOKEN,
                text: `Not specified (${fmtInt(sf.blankCount)})`,
              })
            );
          }
          const maxVals = Math.min(sf.values.length, 80);
          for (let i = 0; i < maxVals; i += 1) {
            const v = sf.values[i];
            selOpts.push(el("option", { value: v.value, text: `${v.value} (${fmtInt(v.count)})` }));
          }
          const sel = el(
            "select",
            {
              className: "cf-select",
              "aria-label": `Filter ${col.label}`,
              "data-col-filter": `${col.key}:select`,
              onChange: (ev) => {
                ensureColFilterObj(col.key).select = ev.target.value;
                syncColumnFilterStyles();
                recomputeCatalog(true);
              },
            },
            selOpts
          );
          sel.value = cf.select || "";
          stackChildren.push(sel);
        }

        if (col.filterType === "range" || col.filterType === "range_select") {
          const tip = sf.range
            ? `Range: ${H.formatCleanNumber(sf.range.min)} – ${H.formatCleanNumber(sf.range.max)}${col.unit ? ` ${col.unit}` : ""}`
            : `Filter ${col.label}`;
          stackChildren.push(
            el("div", { className: "cf-range" }, [
              el("input", {
                type: "number",
                step: "any",
                className: "cf-num",
                placeholder: "Min",
                title: tip,
                "aria-label": `Minimum ${col.label}`,
                "data-col-filter": `${col.key}:min`,
                value: cf.min || "",
                onInput: (ev) => {
                  ensureColFilterObj(col.key).min = ev.target.value;
                  syncColumnFilterStyles();
                  debouncedRecompute();
                },
              }),
              el("span", { className: "cf-dash", text: "–" }),
              el("input", {
                type: "number",
                step: "any",
                className: "cf-num",
                placeholder: "Max",
                title: tip,
                "aria-label": `Maximum ${col.label}`,
                "data-col-filter": `${col.key}:max`,
                value: cf.max || "",
                onInput: (ev) => {
                  ensureColFilterObj(col.key).max = ev.target.value;
                  syncColumnFilterStyles();
                  debouncedRecompute();
                },
              }),
            ])
          );
        }

        if (col.filterType === "text" || col.filterType === "text_select") {
          stackChildren.push(
            el("input", {
              type: "search",
              className: `cf-input${col.filterType === "text_select" ? " cf-input-xs" : ""}`,
              placeholder: col.filterType === "text_select" ? "Contains..." : `Filter ${col.label}...`,
              "aria-label": `Filter ${col.label}`,
              "data-col-filter": `${col.key}:text`,
              value: cf.text || "",
              onInput: (ev) => {
                ensureColFilterObj(col.key).text = ev.target.value;
                syncColumnFilterStyles();
                debouncedRecompute();
              },
            })
          );
        }

        fRow.appendChild(
          el("th", null, [
            stackChildren.length > 1
              ? el("div", { className: "cf-stack" }, stackChildren)
              : stackChildren[0],
          ])
        );
      }
    }

    thead.replaceChildren(hRow, fRow);
    syncColumnFilterStyles();
  }

  function sortFilteredIndices(records, indices, normCache, schema) {
    const key = state.sortKey;
    const mult = state.sortDir === "desc" ? -1 : 1;
    const colDef = schema.columns.find((c) => c.key === key) || schema.columns[0];

    indices.sort((ia, ib) => {
      const a = records[ia];
      const b = records[ib];
      if (colDef.key === "model" || colDef.key === "maker" || colDef.key === "type") {
        const idx = colDef.key === "maker" ? I.maker : colDef.key === "type" ? I.type : I.model;
        return collator.compare(a[idx] || "", b[idx] || "") * mult;
      }
      const ca = normCache[ia]?.[colDef.key];
      const cb = normCache[ib]?.[colDef.key];
      if (!ca && !cb) return 0;
      if (!ca) return 1;
      if (!cb) return -1;
      if (ca.num !== null && cb.num !== null) {
        return (ca.num - cb.num) * mult;
      }
      if (ca.num !== null) return -1 * mult;
      if (cb.num !== null) return 1 * mult;
      return collator.compare(ca.text, cb.text) * mult;
    });

    document.querySelectorAll("#catalog-thead [data-sort-ind]").forEach((ind) => {
      ind.textContent = ind.dataset.sortInd === state.sortKey ? (state.sortDir === "asc" ? "▲" : "▼") : "";
    });
  }

  function renderActiveFilterChips(schema) {
    const bar = document.getElementById("active-filters-bar");
    const chipsWrap = document.getElementById("active-filter-chips");
    const resetBtn = document.getElementById("reset-all-filters-btn");
    const f = state.filters;
    const chips = [];

    const addChip = (label, onRemove) => {
      chips.push(
        el(
          "button",
          {
            type: "button",
            className: "filter-chip",
            title: "Remove filter",
            onClick: () => {
              onRemove();
              buildCategoryTableHead(collectionCache.get(state.activeCategoryId).facets);
              recomputeCatalog(true);
            },
          },
          [el("span", { text: label }), el("span", { text: "×" })]
        )
      );
    };

    if (f.query) addChip(`Search: "${f.query}"`, () => { f.query = ""; });
    if (f.modelQuery) addChip(`Model/ID: "${f.modelQuery}"`, () => { f.modelQuery = ""; });
    if (f.maker) addChip(`Manufacturer: ${f.maker === EMPTY_TOKEN ? "(Unstated)" : f.maker}`, () => { f.maker = ""; });
    if (f.makerQuery) addChip(`Maker contains: "${f.makerQuery}"`, () => { f.makerQuery = ""; });
    if (f.type) addChip(`Type: ${f.type}`, () => { f.type = ""; });

    for (const col of schema.specCols) {
      const cf = f.cols[col.key];
      if (!cf) continue;
      if (cf.select) {
        const lbl = cf.select === EMPTY_TOKEN ? "Not specified" : cf.select;
        addChip(`${col.label}: ${lbl}`, () => { cf.select = ""; });
      }
      if (cf.text) {
        addChip(`${col.label}: "${cf.text}"`, () => { cf.text = ""; });
      }
      if ((cf.min !== undefined && cf.min !== "") || (cf.max !== undefined && cf.max !== "")) {
        addChip(`${col.label}: ${cf.min || "−∞"} to ${cf.max || "+∞"}`, () => {
          cf.min = "";
          cf.max = "";
        });
      }
    }

    const active = chips.length > 0;
    bar.hidden = !active;
    resetBtn.hidden = !active;
    chipsWrap.replaceChildren(...chips);
  }

  function renderTableRows(records, normCache, schema) {
    const tbody = document.getElementById("catalog-tbody");
    const total = state.filteredIndices.length;
    const totalPages = Math.max(1, Math.ceil(total / state.pageSize));
    if (state.page > totalPages) state.page = totalPages;
    if (state.page < 1) state.page = 1;

    const start = (state.page - 1) * state.pageSize;
    const end = Math.min(total, start + state.pageSize);

    document.getElementById("cat-matched-badge").textContent = `${fmtInt(total)} ${total === 1 ? "record" : "records"}`;
    document.getElementById("pager-summary").textContent =
      total === 0 ? "0 matching records" : `${fmtInt(start + 1)}–${fmtInt(end)} of ${fmtInt(total)}`;
    document.getElementById("page-first-btn").disabled = state.page <= 1;
    document.getElementById("page-prev-btn").disabled = state.page <= 1;
    document.getElementById("page-next-btn").disabled = state.page >= totalPages;
    document.getElementById("page-last-btn").disabled = state.page >= totalPages;

    const colSpan = schema.columns.length;
    if (total === 0) {
      tbody.replaceChildren(
        el("tr", null, [
          el("td", { colSpan, className: "empty-state-cell" }, [
            el("div", { text: "No equipment records match the active filters." }),
          ]),
        ])
      );
      return;
    }

    const frag = document.createDocumentFragment();
    for (let p = start; p < end; p += 1) {
      const recIdx = state.filteredIndices[p];
      const r = records[recIdx];
      const rowCells = (normCache && normCache[recIdx]) || H.extractNormalizedRow(state.activeCategoryId, r);

      const tdNodes = [
        el("td", null, [
          el("div", { className: "cell-primary", text: r[I.model] || "—" }),
          el("div", { className: "cell-sub mono", text: r[I.rid] || r[I.id] }),
        ]),
        el("td", null, [
          el("div", { className: r[I.maker] ? "cell-primary" : "cell-sub", text: r[I.maker] || "(Unstated)" }),
        ]),
        el("td", null, [
          el("div", { className: "cell-primary", text: r[I.type] || "—" }),
        ]),
      ];

      for (const col of schema.specCols) {
        const cell = rowCells[col.key];
        tdNodes.push(
          el("td", { className: col.sortType === "num" ? "tabular-nums" : "" }, [
            el("div", { className: cell ? "cell-primary" : "cell-sub", text: cell ? cell.text : "—" }),
          ])
        );
      }

      frag.appendChild(
        el(
          "tr",
          {
            className: r[I.id] === state.selectedRecordUid ? "is-selected" : "",
            tabIndex: 0,
            onClick: () => openRecordDrawer(r),
            onKeydown: (ev) => {
              if (ev.key === "Enter" || ev.key === " ") {
                ev.preventDefault();
                openRecordDrawer(r);
              }
            },
          },
          tdNodes
        )
      );
    }
    tbody.replaceChildren(frag);
  }

  function recomputeCatalog(resetPage = true) {
    const cached = collectionCache.get(state.activeCategoryId);
    if (!cached) return;
    if (resetPage) state.page = 1;

    const { normCache, schema } = cached.facets;
    const matched = H.filterCollectionRecords(cached.records, state.filters, state.activeCategoryId, normCache);
    sortFilteredIndices(cached.records, matched, normCache, schema);
    state.filteredIndices = matched;

    renderActiveFilterChips(schema);
    renderTableRows(cached.records, normCache, schema);
  }

  async function selectCategory(catId) {
    const meta = CATALOG.collections.find((c) => c.id === catId);
    if (!meta) return;

    state.activeCategoryId = catId;
    state.filters = H.createDefaultFilters();
    state.sortKey = "model";
    state.sortDir = "asc";
    state.page = 1;

    if (state.activeView !== "catalog") {
      switchWorkspace("catalog");
    }

    renderCategoryRail();
    closeMobileSidebar();

    document.getElementById("cat-family-label").textContent = meta.family;
    document.getElementById("cat-file-label").textContent = meta.id;
    document.getElementById("cat-title").textContent = meta.label;
    document.getElementById("cat-description").textContent = meta.description;
    document.getElementById("cat-matched-badge").textContent = `${fmtInt(meta.count)} records`;
    document.getElementById("search-index-status").textContent = meta.searchFile ? "Deep index on demand" : "";

    const initialSchema = H.getCategorySchema(catId);
    document.getElementById("catalog-tbody").replaceChildren(
      el("tr", null, [
        el("td", { colSpan: initialSchema.columns.length, className: "empty-state-cell", text: `Loading ${meta.label}...` }),
      ])
    );

    const payload = await loadCollectionData(meta);
    if (state.activeCategoryId !== catId) return;
    buildCategoryTableHead(payload.facets);
    recomputeCatalog(true);
  }

  // Record Technical Detail Drawer (Zero internal audit jargon, zero .xlsx downloads)
  async function openRecordDrawer(r) {
    state.selectedRecordUid = r[I.id];
    const cached = collectionCache.get(state.activeCategoryId);
    if (cached) renderTableRows(cached.records, cached.facets.normCache, cached.facets.schema);

    document.getElementById("drawer-rid").textContent = r[I.rid] || r[I.id];
    document.getElementById("drawer-title").textContent = r[I.model] || r[I.rid];
    document.getElementById("drawer-sub").textContent = `${r[I.maker] || "Unstated manufacturer"} · ${r[I.type] || "Equipment"}`;

    const drawer = document.getElementById("detail-drawer");
    const backdrop = document.getElementById("drawer-backdrop");
    drawer.hidden = false;
    backdrop.hidden = false;

    const schema = H.getCategorySchema(state.activeCategoryId);
    const rowCells = H.extractNormalizedRow(state.activeCategoryId, r);

    const kvNodes = [
      el("div", { className: "kv-key", text: "Record ID" }),
      el("div", { className: "kv-val mono", text: r[I.rid] || "—" }),
      el("div", { className: "kv-key", text: "Manufacturer" }),
      el("div", { className: "kv-val", text: r[I.maker] || "(Unstated)" }),
      el("div", { className: "kv-key", text: "Model" }),
      el("div", { className: "kv-val", text: r[I.model] || "—" }),
      el("div", { className: "kv-key", text: "Equipment Type" }),
      el("div", { className: "kv-val", text: r[I.type] || "—" }),
    ];

    for (const col of schema.specCols) {
      const cell = rowCells[col.key];
      if (!cell) continue;
      kvNodes.push(el("div", { className: "kv-key", text: col.label }));
      kvNodes.push(el("div", { className: "kv-val tabular-nums", text: cell.text }));
    }

    const summaryCard = el("section", { className: "drawer-section" }, [
      el("h3", { text: "Normalized Technical Specifications" }),
      el("div", { className: "kv-grid" }, kvNodes),
    ]);

    const refs = (r[I.refs] || []).slice(0, 8);
    const provenanceCard = el("section", { className: "drawer-section" }, [
      el("h3", { text: `Technical Datasheets & Records (${(r[I.refs] || []).length})` }),
      el("div", { className: "muted", text: refs.length ? "Loading linked specifications..." : "No additional rows attached." }),
    ]);

    document.getElementById("drawer-body").replaceChildren(summaryCard, provenanceCard);
    if (!refs.length) return;

    const loadedRows = await Promise.all(refs.map((ref) => loadSheetRow(ref[0], ref[1])));
    const sourceFrag = document.createDocumentFragment();
    sourceFrag.appendChild(el("h3", { text: `Technical Datasheets & Records (${(r[I.refs] || []).length})` }));

    const INTERNAL_FIELD_RE = /^(audit|migration|review|quality|selection.?gate|source.?state|data.?status|cross.?basis|consistency|flag|unresolved)/i;

    refs.forEach((ref, idx) => {
      const hit = loadedRows[idx];
      const sMeta = sheetMetaById.get(ref[0]);
      const block = el("div", { className: "source-block" }, [
        el("div", { className: "source-block-head" }, [
          el("span", { text: `${sMeta ? sMeta.name : ref[0]} · ${ref[2] || "Source"}` }),
        ]),
      ]);

      if (hit && hit.row) {
        const kv = el("div", { className: "kv-grid" });
        const headers = hit.meta.headers || [];
        const vals = hit.row[1] || [];
        let renderedFields = 0;
        for (let c = 0; c < headers.length; c += 1) {
          const hdr = String(headers[c] || "").trim();
          if (!hdr || INTERNAL_FIELD_RE.test(hdr)) continue;
          const v = vals[c];
          if (v === null || v === undefined || String(v).trim() === "") continue;
          const strVal = H.formatReferenceCell(v);
          kv.appendChild(el("div", { className: "kv-key", text: hdr }));
          if (/^https:\/\/\S+$/i.test(strVal)) {
            kv.appendChild(
              el("div", { className: "kv-val" }, [
                el("a", {
                  className: "kv-link",
                  href: strVal,
                  target: "_blank",
                  rel: "noopener noreferrer",
                  text: strVal,
                }),
              ])
            );
          } else {
            kv.appendChild(el("div", { className: "kv-val", text: strVal }));
          }
          renderedFields += 1;
        }
        if (renderedFields > 0) {
          block.appendChild(kv);
        } else {
          block.appendChild(el("div", { className: "muted", text: "Matched in catalog index." }));
        }
      } else {
        block.appendChild(el("div", { className: "muted", text: `Catalog entry ${ref[0]}` }));
      }
      sourceFrag.appendChild(block);
    });

    provenanceCard.replaceChildren(sourceFrag);
  }

  function closeRecordDrawer() {
    document.getElementById("detail-drawer").hidden = true;
    document.getElementById("drawer-backdrop").hidden = true;
  }

  // Consolidated Engineering References Workspace (34 Curated Tables, Per-Column Filters, Zero Downloads)
  function renderRefSidebar() {
    const listEl = document.getElementById("ref-list");
    const q = state.refListQuery.trim().toLowerCase();
    const groups = new Map();
    for (const ref of CATALOG.references) {
      if (q && !`${ref.label} ${ref.name} ${ref.group}`.toLowerCase().includes(q)) continue;
      if (!groups.has(ref.group)) groups.set(ref.group, []);
      groups.get(ref.group).push(ref);
    }
    const frag = document.createDocumentFragment();
    if (groups.size === 0) {
      frag.appendChild(el("div", { className: "empty-state-cell", text: "No matching reference tables." }));
    } else {
      for (const [grp, items] of groups.entries()) {
        const groupEl = el("div", { className: "cat-group" }, [
          el("div", { className: "cat-group-title" }, [
            el("span", { text: grp }),
            el("span", { className: "tabular-nums", text: String(items.length) }),
          ]),
        ]);
        for (const it of items) {
          groupEl.appendChild(
            el(
              "button",
              {
                type: "button",
                className: `cat-item${it.id === state.activeRefId ? " is-active" : ""}`,
                "data-ref-id": it.id,
                onClick: () => selectReferenceTable(it.id),
              },
              [
                el("span", { className: "cat-item-label", text: it.label }),
                el("span", { className: "cat-item-count tabular-nums", text: fmtInt(it.rows) }),
              ]
            )
          );
        }
        frag.appendChild(groupEl);
      }
    }
    listEl.replaceChildren(frag);
  }

  function filterAndPaginateReferenceRows(resetPage = true) {
    if (resetPage) state.refPage = 1;
    const gq = state.refGlobalQuery.trim().toLowerCase();
    const colFs = state.refColFilters.map((v) => String(v || "").trim().toLowerCase());
    const hasAnyCol = colFs.some(Boolean);
    document.getElementById("ref-clear-cols-btn").hidden = !hasAnyCol && !gq;

    const matched = [];
    for (let i = 0; i < state.refActiveRows.length; i += 1) {
      const cells = state.refActiveRows[i][1] || [];
      let ok = true;
      for (let c = 0; c < colFs.length; c += 1) {
        if (colFs[c]) {
          const formatted = H.formatReferenceCell(cells[c]).toLowerCase();
          if (!formatted.includes(colFs[c])) {
            ok = false;
            break;
          }
        }
      }
      if (!ok) continue;
      if (gq) {
        const rowStr = cells.map((x) => H.formatReferenceCell(x)).join(" ").toLowerCase();
        if (!rowStr.includes(gq)) continue;
      }
      matched.push(state.refActiveRows[i]);
    }
    state.refFilteredRows = matched;
    renderRefPage();
  }

  function renderRefPage() {
    const total = state.refFilteredRows.length;
    const allCount = state.refActiveRows.length;
    const totalPages = Math.max(1, Math.ceil(total / state.refPageSize));
    if (state.refPage > totalPages) state.refPage = totalPages;
    if (state.refPage < 1) state.refPage = 1;

    const start = (state.refPage - 1) * state.refPageSize;
    const end = Math.min(total, start + state.refPageSize);

    document.getElementById("ref-row-count").textContent =
      total === allCount ? `${fmtInt(total)} rows` : `${fmtInt(total)} / ${fmtInt(allCount)} rows`;
    document.getElementById("ref-pager-summary").textContent =
      total === 0 ? "0 matching rows" : `${fmtInt(start + 1)}–${fmtInt(end)} of ${fmtInt(total)}`;

    document.getElementById("ref-page-first-btn").disabled = state.refPage <= 1;
    document.getElementById("ref-page-prev-btn").disabled = state.refPage <= 1;
    document.getElementById("ref-page-next-btn").disabled = state.refPage >= totalPages;
    document.getElementById("ref-page-last-btn").disabled = state.refPage >= totalPages;

    const tbody = document.getElementById("ref-tbody");
    if (total === 0) {
      tbody.replaceChildren(
        el("tr", null, [
          el("td", {
            colSpan: Math.max(1, state.refActiveHeaders.length),
            className: "empty-state-cell",
            text: "No reference rows match the column filters.",
          }),
        ])
      );
      return;
    }

    const frag = document.createDocumentFragment();
    for (let i = start; i < end; i += 1) {
      const cells = state.refFilteredRows[i][1] || [];
      const tr = el("tr");
      for (let c = 0; c < state.refActiveHeaders.length; c += 1) {
        const text = H.formatReferenceCell(cells[c]);
        if (/^https:\/\/\S+$/i.test(text)) {
          tr.appendChild(
            el("td", null, [
              el("a", { className: "kv-link", href: text, target: "_blank", rel: "noopener noreferrer", text }),
            ])
          );
        } else {
          tr.appendChild(el("td", { className: /^-?[\d,]+(?:\.\d+)?$/.test(text) ? "tabular-nums" : "", text }));
        }
      }
      frag.appendChild(tr);
    }
    tbody.replaceChildren(frag);
  }

  async function selectReferenceTable(sheetId) {
    state.activeRefId = sheetId;
    renderRefSidebar();
    closeMobileSidebar();

    const refMeta = CATALOG.references.find((r) => r.id === sheetId);
    const sMeta = sheetMetaById.get(sheetId);

    document.getElementById("ref-active-group").textContent = refMeta ? refMeta.group : "Engineering reference";
    document.getElementById("ref-active-code").textContent = refMeta ? refMeta.name : sheetId;
    document.getElementById("ref-active-title").textContent = refMeta ? refMeta.label : sheetId;
    document.getElementById("ref-active-meta").textContent = sMeta
      ? `${fmtInt(sMeta.rowCount)} rows · ${sMeta.colCount} columns · Per-column filterable`
      : "";

    document.getElementById("ref-tbody").replaceChildren(
      el("tr", null, [el("td", { colSpan: 4, className: "empty-state-cell", text: "Loading reference table..." })])
    );

    const chunkCount = sMeta && Array.isArray(sMeta.chunks) ? sMeta.chunks.length : 1;
    const chunks = await Promise.all(
      Array.from({ length: chunkCount }, (_, idx) => loadSheetChunk(sheetId, idx))
    );
    if (state.activeRefId !== sheetId || !chunks[0]) return;

    const headerRow = chunks[0].rows[0] || [];
    const headers = (sMeta && sMeta.headers) || headerRow[1] || [];
    const allRows = [];
    chunks.forEach((chk, idx) => {
      if (!chk || !Array.isArray(chk.rows)) return;
      const rows = idx === 0 ? chk.rows.slice(1) : chk.rows;
      for (let i = 0; i < rows.length; i += 1) {
        allRows.push(rows[i]);
      }
    });

    state.refActiveHeaders = headers;
    state.refActiveRows = allRows;
    state.refColFilters = new Array(headers.length).fill("");
    state.refGlobalQuery = "";
    state.refPage = 1;
    document.getElementById("ref-row-search").value = "";

    const hRow = el("tr", { className: "col-header-row" });
    const fRow = el("tr", { className: "col-filter-row", "aria-label": "Per-column reference table filters" });
    headers.forEach((hdr, cIdx) => {
      hRow.appendChild(el("th", null, [el("div", { className: "ref-th-label", text: hdr })]));
      fRow.appendChild(
        el("th", null, [
          el("input", {
            type: "search",
            className: "cf-input cf-input-xs",
            placeholder: `Filter ${hdr}...`,
            "aria-label": `Filter ${hdr}`,
            onInput: (ev) => {
              state.refColFilters[cIdx] = ev.target.value;
              ev.target.classList.toggle("is-filtered", Boolean(ev.target.value));
              filterAndPaginateReferenceRows(true);
            },
          }),
        ])
      );
    });
    document.getElementById("ref-thead").replaceChildren(hRow, fRow);
    filterAndPaginateReferenceRows(true);
  }

  function closeMobileSidebar() {
    document.getElementById("category-sidebar").classList.remove("is-open");
    document.getElementById("sidebar-backdrop").hidden = true;
    document.getElementById("sidebar-backdrop").classList.remove("is-open");
  }

  function bindEvents() {
    document.getElementById("theme-toggle-btn").addEventListener("click", () => {
      applyTheme(state.theme === "dark" ? "light" : "dark");
    });

    document.getElementById("mobile-nav-btn").addEventListener("click", () => {
      const sb = document.getElementById("category-sidebar");
      const bd = document.getElementById("sidebar-backdrop");
      const open = !sb.classList.contains("is-open");
      sb.classList.toggle("is-open", open);
      bd.hidden = !open;
      bd.classList.toggle("is-open", open);
    });
    document.getElementById("sidebar-backdrop").addEventListener("click", closeMobileSidebar);

    document.getElementById("nav-catalog-btn").addEventListener("click", () => switchWorkspace("catalog"));
    document.getElementById("nav-refs-btn").addEventListener("click", () => switchWorkspace("references"));

    document.getElementById("cat-search-input").addEventListener("input", (ev) => {
      state.catFilterQuery = ev.target.value;
      renderCategoryRail();
    });

    document.getElementById("reset-all-filters-btn").addEventListener("click", () => {
      state.filters = H.createDefaultFilters();
      const cached = collectionCache.get(state.activeCategoryId);
      if (cached) buildCategoryTableHead(cached.facets);
      recomputeCatalog(true);
    });

    const gInput = document.getElementById("global-search-input");
    gInput.addEventListener("focus", () => {
      const meta = CATALOG.collections.find((c) => c.id === state.activeCategoryId);
      ensureSearchIndexLoaded(meta).then(() => {
        if (state.filters.query) recomputeCatalog(false);
      });
    });
    gInput.addEventListener("input", (ev) => {
      state.filters.query = ev.target.value;
      ev.target.classList.toggle("is-filtered", Boolean(ev.target.value));
      const meta = CATALOG.collections.find((c) => c.id === state.activeCategoryId);
      if (ev.target.value.trim()) {
        ensureSearchIndexLoaded(meta).then(() => recomputeCatalog(false));
      }
      debouncedRecompute();
    });

    // Catalog pagination
    const redrawCatalogPage = () => {
      const c = collectionCache.get(state.activeCategoryId);
      if (c) renderTableRows(c.records, c.facets.normCache, c.facets.schema);
    };
    document.getElementById("page-size-select").addEventListener("change", (ev) => {
      state.pageSize = Number(ev.target.value) || 100;
      state.page = 1;
      redrawCatalogPage();
    });
    document.getElementById("page-first-btn").addEventListener("click", () => {
      state.page = 1;
      redrawCatalogPage();
    });
    document.getElementById("page-prev-btn").addEventListener("click", () => {
      state.page -= 1;
      redrawCatalogPage();
    });
    document.getElementById("page-next-btn").addEventListener("click", () => {
      state.page += 1;
      redrawCatalogPage();
    });
    document.getElementById("page-last-btn").addEventListener("click", () => {
      state.page = Math.ceil(state.filteredIndices.length / state.pageSize) || 1;
      redrawCatalogPage();
    });

    // References events
    document.getElementById("ref-list-search").addEventListener("input", (ev) => {
      state.refListQuery = ev.target.value;
      renderRefSidebar();
    });
    document.getElementById("ref-row-search").addEventListener("input", (ev) => {
      state.refGlobalQuery = ev.target.value;
      filterAndPaginateReferenceRows(true);
    });
    document.getElementById("ref-clear-cols-btn").addEventListener("click", () => {
      state.refGlobalQuery = "";
      state.refColFilters = state.refColFilters.map(() => "");
      document.getElementById("ref-row-search").value = "";
      document.querySelectorAll("#ref-thead input").forEach((inp) => {
        inp.value = "";
        inp.classList.remove("is-filtered");
      });
      filterAndPaginateReferenceRows(true);
    });
    document.getElementById("ref-page-size-select").addEventListener("change", (ev) => {
      state.refPageSize = Number(ev.target.value) || 100;
      state.refPage = 1;
      renderRefPage();
    });
    document.getElementById("ref-page-first-btn").addEventListener("click", () => {
      state.refPage = 1;
      renderRefPage();
    });
    document.getElementById("ref-page-prev-btn").addEventListener("click", () => {
      state.refPage -= 1;
      renderRefPage();
    });
    document.getElementById("ref-page-next-btn").addEventListener("click", () => {
      state.refPage += 1;
      renderRefPage();
    });
    document.getElementById("ref-page-last-btn").addEventListener("click", () => {
      state.refPage = Math.ceil(state.refFilteredRows.length / state.refPageSize) || 1;
      renderRefPage();
    });

    // Drawer
    document.getElementById("drawer-close-btn").addEventListener("click", closeRecordDrawer);
    document.getElementById("drawer-backdrop").addEventListener("click", closeRecordDrawer);

    // Keyboard shortcuts
    document.addEventListener("keydown", (ev) => {
      if ((ev.metaKey || ev.ctrlKey) && ev.key.toLowerCase() === "k") {
        ev.preventDefault();
        const target = state.activeView === "references" ? "ref-list-search" : "cat-search-input";
        document.getElementById(target).focus();
      } else if (ev.key === "/" && !["INPUT", "TEXTAREA", "SELECT"].includes(document.activeElement?.tagName)) {
        ev.preventDefault();
        const target = state.activeView === "references" ? "ref-row-search" : "global-search-input";
        document.getElementById(target).focus();
      } else if (ev.key === "Escape") {
        closeRecordDrawer();
      }
    });
  }

  function init() {
    hydrateStaticIcons();
    applyTheme(state.theme);
    const collections = Array.isArray(CATALOG.collections) ? CATALOG.collections : [];
    const references = Array.isArray(CATALOG.references) ? CATALOG.references : [];
    document.getElementById("brand-meta").textContent = `${fmtInt(CATALOG.catalogRecords)} records · ${collections.length} types`;
    document.getElementById("nav-refs-count").textContent = String(references.length);

    bindEvents();
    renderCategoryRail();
    renderRefSidebar();

    if (!collections.length) {
      document.getElementById("catalog-tbody").replaceChildren(
        el("tr", null, [
          el("td", {
            colSpan: 3,
            className: "empty-state-cell",
            text: "Catalog metadata scripts did not load.",
          }),
        ])
      );
      return;
    }
    selectCategory(state.activeCategoryId);
  }

  init();
})();
