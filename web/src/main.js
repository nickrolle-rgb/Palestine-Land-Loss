import {
  BASEMAP, DATA, EXTENT_STYLE, FALLBACK_STYLE, HISTORICAL, HISTORICAL_LAYERS,
  BASEMAP_PLACE_LABELS, MANDATE_COLOUR, MECHANISM_STYLE, OSLO_COLOURS,
  OUTPOST_COLOUR, STAGE_COLOURS,
  STYLE_TIMEOUT_MS, TIME,
} from "./config.js";
import { renderAbout, renderDetail } from "./panels.js";
import { resultsMarkup, search } from "./search.js";

const $ = (sel) => document.querySelector(sel);

const state = {
  meta: null,
  data: {},          // layer id -> FeatureCollection (kept raw for time filtering)
  year: TIME.max,
  historicalMode: "off",
  historicalOpacity: 0.75,
  historicalLayer: HISTORICAL,
};

// --------------------------------------------------------------------------
// Data loading
// --------------------------------------------------------------------------

async function loadJSON(name, { optional = false } = {}) {
  // Everything except meta.json is requested with the build version appended, so
  // it can be cached immutably and re-fetched only when it genuinely changes.
  // meta.json is the one file that must be revalidated — it carries the version.
  const version = state.meta && state.meta.build_id;
  const url = version && name !== "meta.json"
    ? `${DATA}/${name}?v=${version}`
    : `${DATA}/${name}`;
  const res = await fetch(url);
  if (!res.ok) {
    if (optional) return null;
    throw new Error(`${name}: ${res.status}`);
  }
  return res.json();
}

const EMPTY = { type: "FeatureCollection", features: [] };

async function loadAll() {
  state.meta = await loadJSON("meta.json");
  // Extent layers are derived from EXTENT_STYLE rather than listed again, so
  // adding a measure in one place cannot leave the loader behind.
  const names = {
    ...Object.fromEntries(
      Object.keys(EXTENT_STYLE).map((k) => [k, `settlements_${k}.geojson`])
    ),
    localities: "localities.geojson",
    oslo: "oslo_areas.geojson",
    barrier: "barrier.geojson",
    incidents: "incidents.geojson",
    mandate: "mandate_palestine.geojson",
    firing: "firing_zones.geojson",
    villages: "village_boundaries.geojson",
    resource: "resource_destruction.geojson",
  };
  // Interview metadata is looked up on click, not carried on every map feature.
  state.oralHistories = (await loadJSON("oral_histories.json", { optional: true })) || { localities: {} };
  await Promise.all(
    Object.entries(names).map(async ([key, file]) => {
      state.data[key] = (await loadJSON(file, { optional: true })) || EMPTY;
    })
  );
}

// --------------------------------------------------------------------------
// Time resolution
// --------------------------------------------------------------------------

/** Highest stage an entity had reached by the end of `year`, or null. */
function stageAt(props, year) {
  const history = props.stage_history || [];
  let best = null;
  for (const ev of history) {
    if (!ev.valid_from) continue;
    const from = Number(ev.valid_from.slice(0, 4));
    if (from <= year && (best === null || ev.stage > best)) best = ev.stage;
  }
  return best;
}

/** Re-derive per-feature time properties and push to the map source. */
function applyTime(map) {
  for (const key of Object.keys(EXTENT_STYLE)) {
    const fc = state.data[key];
    const out = {
      type: "FeatureCollection",
      features: fc.features
        .map((f) => {
          const stage = stageAt(f.properties, state.year);
          if (stage !== null) {
            return { ...f, properties: { ...f.properties, stage_at: stage } };
          }
          // Not everything on these layers is a settlement moving through the
          // planning pipeline. A municipal boundary is a jurisdiction that
          // either exists or does not, and it carries no stage history — so
          // filtering it by stage silently emptied the layer and left its
          // checkbox doing nothing. Where the source gives a declaration date,
          // honour that instead; otherwise the boundary is simply present.
          const declared = f.properties.declared_date;
          if (declared && Number(declared.slice(0, 4)) > state.year) return null;
          return f;
        })
        .filter(Boolean),
    };
    map.getSource(`settlements-${key}`)?.setData(out);
  }

  const inc = {
    type: "FeatureCollection",
    features: state.data.incidents.features.filter((f) => {
      const d = f.properties.date;
      return !d || Number(d.slice(0, 4)) <= state.year;
    }),
  };
  map.getSource("incidents")?.setData(inc);

  $("#time-readout").textContent = state.epoch ? state.epoch.label : state.year;
  const shown = map.getSource("settlements-built_up")
    ? state.data.built_up.features.filter(
        (f) => stageAt(f.properties, state.year) !== null
      ).length
    : 0;
  $("#stage-readout").textContent =
    `${shown} settlement${shown === 1 ? "" : "s"} with evidence as at ${state.year}`;

  // With only one observation date in the current sources, the slider drops to
  // zero before 2021. That is truthful but reads as a broken map, so name the
  // gap explicitly rather than letting the user assume the data failed to load.
  const gap = $("#time-gap");
  if (shown === 0 && state.earliestYear && state.year < state.earliestYear) {
    gap.hidden = false;
    gap.textContent =
      `No stage evidence before ${state.earliestYear}. The dated planning records ` +
      `that would fill this slider (land declarations, deposited plans, tenders) ` +
      `come from Peace Now and are not yet integrated.`;
  } else {
    gap.hidden = true;
  }
}

/** Move localities to their historical position while a historical sheet shows.
 *
 * The two sources place a town differently: Palestine Open Maps marks the 1945
 * village, OCHA the present-day administrative centre. Beituniya's differ by
 * 1.2 km. Drawn at the modern position over a 1940s survey, the dot floats away
 * from the village it names — which is what "our locations struggle to find
 * their map location" looks like. So over a historical sheet we use the
 * historical coordinate where the merge kept one.
 */
function applyLocalityPositions(map) {
  const historical = state.historicalMode !== "off";
  const fc = state.data.localities;
  const out = {
    type: "FeatureCollection",
    features: fc.features.map((f) => {
      const hist = f.properties.historic_coordinates;
      if (!historical || !hist) return f;
      return {
        ...f,
        geometry: { type: "Point", coordinates: hist },
        properties: { ...f.properties, positioned_as: "historical" },
      };
    }),
  };
  map.getSource("localities")?.setData(out);

  const note = $("#position-note");
  if (note) {
    const moved = fc.features.filter((f) => f.properties.historic_coordinates).length;
    note.hidden = !historical || !moved;
    note.textContent =
      `${moved} localities are shown at the position the historical sources record, ` +
      `which differs from their present-day centre.`;
  }
}

/** Earliest year for which any stage evidence exists across all extents. */
function computeEarliestYear() {
  let earliest = null;
  for (const key of Object.keys(EXTENT_STYLE)) {
    for (const f of state.data[key].features) {
      for (const ev of f.properties.stage_history || []) {
        if (!ev.valid_from) continue;
        const y = Number(ev.valid_from.slice(0, 4));
        if (earliest === null || y < earliest) earliest = y;
      }
    }
  }
  return earliest;
}

// --------------------------------------------------------------------------
// Layers
// --------------------------------------------------------------------------

function addHistoricalDataLayers(map) {
  // Mandatory Palestine — the denominator. Without a stated whole, every
  // "share of the land" figure is an assertion.
  map.addSource("mandate", { type: "geojson", data: state.data.mandate });
  map.addLayer({
    id: "mandate-line",
    type: "line",
    source: "mandate",
    layout: { visibility: "none" },
    paint: {
      "line-color": MANDATE_COLOUR,
      "line-width": 2,
      "line-dasharray": [6, 3],
      "line-opacity": 0.85,
    },
  });

  // One locality source, two views of it. The OCHA and Palestine Open Maps sets
  // were previously drawn as separate layers and produced visible double dots;
  // they are now reconciled in the ETL, so a place appears once and clicking it
  // cannot report a neighbour's name.
  map.addSource("localities", { type: "geojson", data: state.data.localities });

  // Depopulated localities, styled apart from settlements on purpose — a
  // different mechanism with a different legal character and evidence base.
  map.addLayer({
    id: "localities-depopulated",
    type: "circle",
    source: "localities",
    filter: ["==", ["get", "depopulated_1948"], true],
    layout: { visibility: "none" },
    paint: {
      // Scaled by the displaced Palestinian population so the map reads as loss
      // of people rather than dots. Prefers the Palestinian figure over the
      // total, which in mixed cities would badly overstate displacement.
      "circle-radius": [
        "interpolate", ["linear"], ["zoom"],
        7, ["interpolate", ["linear"],
            ["coalesce", ["get", "pop_1945_palestinian"], ["get", "pop_1945_total"], 0],
            0, 2, 5000, 7],
        13, ["interpolate", ["linear"],
            ["coalesce", ["get", "pop_1945_palestinian"], ["get", "pop_1945_total"], 0],
            0, 4, 5000, 18],
      ],
      "circle-color": MECHANISM_STYLE.depopulation_1948.colour,
      "circle-stroke-color": "#4a044e",
      "circle-stroke-width": 1,
      "circle-opacity": 0.72,
    },
  });

  // Localities still standing, for contrast with what was lost.
  map.addLayer({
    id: "localities-standing",
    type: "circle",
    source: "localities",
    filter: ["!=", ["get", "depopulated_1948"], true],
    layout: { visibility: "none" },
    paint: {
      "circle-radius": ["interpolate", ["linear"], ["zoom"], 7, 1.6, 13, 5],
      "circle-color": "#34d399",
      "circle-stroke-color": "#052e16",
      "circle-stroke-width": 0.8,
      "circle-opacity": 0.7,
    },
  });

  // Testimony is concentrated in Galilee and Haifa — depopulated 1948 villages
  // inside Israel — so almost none fall in the West Bank. Without a way to see
  // where they are, a reader looking at the West Bank would conclude there were
  // none at all.
  map.addLayer({
    id: "localities-testimony",
    type: "circle",
    source: "localities",
    filter: [">", ["coalesce", ["get", "oral_history_count"], 0], 0],
    layout: { visibility: "none" },
    paint: {
      "circle-radius": ["interpolate", ["linear"], ["zoom"], 6, 4, 13, 11],
      "circle-color": "#fbbf24",
      "circle-stroke-color": "#451a03",
      "circle-stroke-width": 1.5,
      "circle-opacity": 0.85,
    },
  });

  map.addLayer({
    id: "localities-label",
    type: "symbol",
    source: "localities",
    minzoom: 11,
    layout: {
      visibility: "none",
      // Naming policy: the Palestinian/Arabic name alongside the
      // transliteration wherever the merged record carries both.
      "text-field": [
        "case",
        ["all", ["has", "names"], ["!=", ["get", "arabic", ["get", "names"]], null]],
        ["concat", ["get", "name"], "\n", ["get", "arabic", ["get", "names"]]],
        ["get", "name"],
      ],
      "text-size": 10.5,
      "text-offset": [0, 1.1],
      "text-anchor": "top",
      "text-allow-overlap": false,
    },
    paint: {
      "text-color": "#a7f3d0",
      "text-halo-color": "#04120c",
      "text-halo-width": 1.4,
    },
  });
}

function addFiringZoneLayers(map) {
  // A closure order removes access to land as surely as a settlement does, and
  // every one of these polygons carries the date its order was signed — so this
  // is a mechanism of loss in its own right, not background context.
  map.addSource("firing", { type: "geojson", data: state.data.firing });
  map.addLayer({
    id: "firing-fill",
    type: "fill",
    source: "firing",
    layout: { visibility: "none" },
    paint: { "fill-color": "#f97316", "fill-opacity": 0.16 },
  });
  map.addLayer({
    id: "firing-line",
    type: "line",
    source: "firing",
    layout: { visibility: "none" },
    paint: {
      "line-color": "#f97316",
      "line-width": 1.2,
      "line-dasharray": [2, 2],
      "line-opacity": 0.8,
    },
  });

  map.addSource("villages", { type: "geojson", data: state.data.villages });
  map.addLayer({
    id: "villages-fill",
    type: "fill",
    source: "villages",
    layout: { visibility: "none" },
    paint: { "fill-color": "#34d399", "fill-opacity": 0.1 },
  });
  map.addLayer({
    id: "villages-line",
    type: "line",
    source: "villages",
    layout: { visibility: "none" },
    paint: { "line-color": "#34d399", "line-width": 0.8, "line-opacity": 0.6 },
  });
}

function addResourceLayers(map) {
  map.addSource("resource", { type: "geojson", data: state.data.resource });
  map.addLayer({
    id: "resource-point",
    type: "circle",
    source: "resource",
    layout: { visibility: "none" },
    paint: {
      "circle-radius": [
        "interpolate", ["linear"], ["zoom"],
        8, ["interpolate", ["linear"], ["get", "record_count"], 0, 3, 400, 14],
        13, ["interpolate", ["linear"], ["get", "record_count"], 0, 6, 400, 30],
      ],
      "circle-color": "#22d3ee",
      "circle-stroke-color": "#083344",
      "circle-stroke-width": 1.5,
      "circle-opacity": 0.6,
    },
  });
}

/** Hide the basemap's own place names while we are drawing our own. */
function setBasemapPlaceLabels(map, visible) {
  for (const id of BASEMAP_PLACE_LABELS) {
    if (map.getLayer(id)) {
      map.setLayoutProperty(id, "visibility", visible ? "visible" : "none");
    }
  }
}

function addContextLayers(map) {
  map.addSource("oslo", { type: "geojson", data: state.data.oslo });
  map.addLayer({
    id: "oslo-fill",
    type: "fill",
    source: "oslo",
    layout: { visibility: "none" },
    paint: {
      "fill-color": [
        "match", ["get", "oslo_class"],
        ...Object.entries(OSLO_COLOURS).flat(),
        "#64748b",
      ],
      "fill-opacity": 0.18,
    },
  });
  map.addLayer({
    id: "oslo-line",
    type: "line",
    source: "oslo",
    layout: { visibility: "none" },
    paint: {
      "line-color": [
        "match", ["get", "oslo_class"],
        ...Object.entries(OSLO_COLOURS).flat(),
        "#64748b",
      ],
      "line-width": 1,
      "line-opacity": 0.7,
    },
  });

  map.addSource("barrier", { type: "geojson", data: state.data.barrier });
  map.addLayer({
    id: "barrier-line",
    type: "line",
    source: "barrier",
    layout: { visibility: "none", "line-cap": "round" },
    paint: {
      "line-color": "#e879f9",
      "line-width": ["interpolate", ["linear"], ["zoom"], 8, 1, 14, 3],
      "line-dasharray": [3, 1.5],
    },
  });

}

function addSettlementLayers(map) {
  for (const [key, style] of Object.entries(EXTENT_STYLE)) {
    const src = `settlements-${key}`;
    map.addSource(src, { type: "geojson", data: state.data[key] });

    // Built-up is coloured by pipeline stage; the jurisdiction layers are a
    // single colour because a jurisdiction boundary has no stage of its own.
    const fillColour =
      key === "built_up"
        ? [
            "case",
            ["==", ["get", "entity_type"], "outpost"], OUTPOST_COLOUR,
            [
              "match", ["to-string", ["get", "stage_at"]],
              ...Object.entries(STAGE_COLOURS).flatMap(([k, v]) => [k, v]),
              style.colour,
            ],
          ]
        : style.colour;

    map.addLayer({
      id: `${src}-fill`,
      type: "fill",
      source: src,
      layout: { visibility: key === "built_up" ? "visible" : "none" },
      paint: {
        "fill-color": fillColour,
        "fill-opacity": key === "built_up" ? 0.62 : 0.22,
      },
    });
    map.addLayer({
      id: `${src}-line`,
      type: "line",
      source: src,
      layout: { visibility: key === "built_up" ? "visible" : "none" },
      paint: {
        "line-color": fillColour,
        "line-width": key === "built_up" ? 1 : 1.6,
        "line-opacity": 0.95,
        // Outposts get a dashed edge: unauthorised even under Israeli law.
        "line-dasharray": key === "built_up" ? [1, 0] : [4, 2],
      },
    });
  }

  map.addSource("incidents", { type: "geojson", data: state.data.incidents });
  map.addLayer({
    id: "incidents-point",
    type: "circle",
    source: "incidents",
    paint: {
      "circle-radius": ["interpolate", ["linear"], ["zoom"], 8, 4, 14, 8],
      "circle-color": "#38bdf8",
      "circle-stroke-color": "#082f49",
      "circle-stroke-width": 1.5,
      "circle-opacity": 0.85,
    },
  });
}

// --------------------------------------------------------------------------
// Historical underlay: overlay mode (one map) and swipe mode (two maps)
// --------------------------------------------------------------------------

let historicalMap = null;

function ensureOverlayLayer(map) {
  if (map.getSource("historical")) return;
  const layer = state.historicalLayer;
  map.addSource("historical", {
    type: "raster",
    tiles: [layer.tiles],
    tileSize: 256,
    maxzoom: layer.maxzoom,
    attribution: layer.attribution,
  });
  // Beneath the data layers so settlement geometry reads on top of the survey.
  const firstData = map.getLayer("settlements-built_up-fill")
    ? "settlements-built_up-fill"
    : undefined;
  map.addLayer(
    {
      id: "historical-raster",
      type: "raster",
      source: "historical",
      layout: { visibility: "none" },
      paint: { "raster-opacity": state.historicalOpacity },
    },
    firstData
  );
}

function ensureSwipeMap(map) {
  if (historicalMap) return historicalMap;

  const container = document.createElement("div");
  container.id = "map-historical";
  Object.assign(container.style, {
    position: "absolute", inset: "0", zIndex: "3", pointerEvents: "none",
  });
  $("#map").parentNode.insertBefore(container, $("#swipe"));

  historicalMap = new maplibregl.Map({
    container,
    style: {
      version: 8,
      sources: {
        hist: {
          type: "raster",
          tiles: [state.historicalLayer.tiles],
          tileSize: 256,
          maxzoom: state.historicalLayer.maxzoom,
          attribution: state.historicalLayer.attribution,
        },
      },
      layers: [
        { id: "bg", type: "background", paint: { "background-color": "#efe8d8" } },
        { id: "hist", type: "raster", source: "hist" },
      ],
    },
    center: map.getCenter(),
    zoom: map.getZoom(),
    bearing: map.getBearing(),
    pitch: map.getPitch(),
    interactive: false,
    attributionControl: false,
  });

  // Keep the two viewports locked together.
  map.on("move", () => {
    historicalMap.jumpTo({
      center: map.getCenter(),
      zoom: map.getZoom(),
      bearing: map.getBearing(),
      pitch: map.getPitch(),
    });
  });

  return historicalMap;
}

/** Repoint both historical renderers at the currently selected survey. */
function swapHistoricalTiles(map) {
  const layer = state.historicalLayer;

  const overlay = map.getSource("historical");
  if (overlay) {
    // setTiles avoids tearing down and rebuilding the layer.
    overlay.setTiles([layer.tiles]);
  }

  if (historicalMap) {
    const src = historicalMap.getSource("hist");
    if (src) src.setTiles([layer.tiles]);
  }
}

/** Usable width for the curtain. Zero while the pane/tab is not laid out. */
function viewportWidth() {
  const el = document.getElementById("map");
  return (el && el.clientWidth) || window.innerWidth || 0;
}

// If the swipe is switched on before the container has a width — a hidden tab,
// a display:none ancestor, a device rotation mid-init — a naive centre puts the
// handle at 0 and clips the historical map away entirely, which looks like the
// layer simply failed. Defer instead, and centre once a real width exists.
let swipeNeedsCentring = false;

function setSwipePosition(x) {
  const w = viewportWidth();
  if (!w) {
    swipeNeedsCentring = true;
    return;
  }
  swipeNeedsCentring = false;
  const clamped = Math.max(0, Math.min(w, x));
  $("#swipe-handle").style.left = `${clamped}px`;
  if (historicalMap) {
    historicalMap.getContainer().style.clipPath = `inset(0 ${w - clamped}px 0 0)`;
  }
}

function centreSwipe() {
  setSwipePosition(viewportWidth() / 2);
}

/** Re-centre as soon as the map container gains a width. */
function watchForLayout() {
  const el = document.getElementById("map");
  if (!el || typeof ResizeObserver === "undefined") return;
  const ro = new ResizeObserver(() => {
    if (swipeNeedsCentring && viewportWidth() > 0) centreSwipe();
  });
  ro.observe(el);
}

function initSwipeDrag() {
  const handle = $("#swipe-handle");
  let dragging = false;
  const move = (e) => {
    if (!dragging) return;
    setSwipePosition((e.touches ? e.touches[0].clientX : e.clientX));
  };
  handle.addEventListener("mousedown", () => { dragging = true; });
  handle.addEventListener("touchstart", () => { dragging = true; }, { passive: true });
  window.addEventListener("mousemove", move);
  window.addEventListener("touchmove", move, { passive: true });
  window.addEventListener("mouseup", () => { dragging = false; });
  window.addEventListener("touchend", () => { dragging = false; });
  handle.addEventListener("keydown", (e) => {
    const cur = handle.style.left
      ? parseFloat(handle.style.left)
      : viewportWidth() / 2;
    if (e.key === "ArrowLeft") setSwipePosition(cur - 24);
    if (e.key === "ArrowRight") setSwipePosition(cur + 24);
  });
  window.addEventListener("resize", centreSwipe);
  watchForLayout();
}

function setHistoricalMode(map, mode) {
  state.historicalMode = mode;
  ensureOverlayLayer(map);

  const overlayOn = mode === "overlay";
  map.setLayoutProperty("historical-raster", "visibility", overlayOn ? "visible" : "none");

  applyLocalityPositions(map);

  const swipeOn = mode === "swipe";
  $("#swipe").hidden = !swipeOn;
  if (swipeOn) {
    ensureSwipeMap(map);
    historicalMap.getContainer().style.display = "";
    centreSwipe();
    // The second canvas needs a resize once it becomes visible.
    setTimeout(() => historicalMap.resize(), 0);
  } else if (historicalMap) {
    historicalMap.getContainer().style.display = "none";
  }
}

// --------------------------------------------------------------------------
// UI wiring
// --------------------------------------------------------------------------

function toggleRow({ id, colour, label, definition, checked, disabled, note }) {
  const wrap = document.createElement("label");
  wrap.className = "toggle" + (disabled ? " disabled" : "");
  wrap.innerHTML = `
    <input type="checkbox" ${checked ? "checked" : ""} ${disabled ? "disabled" : ""}>
    ${colour ? `<span class="swatch" style="background:${colour}"></span>` : ""}
    <span class="label">${label}</span>
    ${note ? `<span class="badge-empty">${note}</span>` : ""}
    ${definition ? `<span class="def">${definition}</span>` : ""}`;
  wrap.dataset.id = id;
  return wrap;
}

function measureFor(id) {
  return ((state.meta.stats || {}).land_measures || []).find((m) => m.id === id) || {};
}

/** "520 km² · 9.2% of the West Bank" — the figure that makes the point. */
function figureFor(id) {
  const m = measureFor(id);
  if (!m.km2) return "";
  const pct = m.pct_west_bank ? ` · ${m.pct_west_bank}% of the West Bank` : "";
  return `<span class="measure-figure">${m.km2.toLocaleString()} km²${pct}</span>`;
}

/** The overlap-aware total for whatever is currently ticked. */
function updateLandTotal() {
  const el = $("#land-total");
  if (!el) return;
  const coverage = (state.meta.stats || {}).coverage || {};
  const selected = [...document.querySelectorAll("#extent-toggles input:checked")]
    .map((i) => i.closest(".toggle").dataset.id)
    .map((id) => (id === "firing" ? "closed_military_area" : id))
    .filter((id) => (coverage.combinations || {})[id] !== undefined || id !== "regional_council");

  const key = selected.slice().sort().join("+");
  const hit = (coverage.combinations || {})[key];

  // Away from "Today" the figure is the one measured at that date, and it covers
  // only the measures carrying dates. Saying so matters: built-up footprints
  // have no construction history, so a total that silently folded them into a
  // 1993 figure would be a fabrication.
  const epoch = state.epoch;
  if (epoch && epoch.dated_only) {
    const dated = new Set(["municipal", "closed_military_area"]);
    if (!selected.some((id) => dated.has(id))) {
      el.innerHTML = `<span class="lt-lead">No dated evidence for this selection at ${epoch.label}.</span>
        <span class="lt-note">Only municipal boundaries and closed military areas
        carry dates. Built-up footprints have just the date they were observed,
        which is not when they were built.</span>`;
      return;
    }
    el.innerHTML =
      `<span class="lt-figure">${epoch.pct}%</span>
       <span class="lt-lead">of the West Bank by ${epoch.label} — ${epoch.km2.toLocaleString()} km²</span>
       <span class="lt-note">${epoch.note}. Counts municipal jurisdiction and
       closed military areas, the only measures with dated evidence.</span>`;
    return;
  }

  if (!selected.length) {
    el.innerHTML = `<span class="lt-lead">Nothing selected.</span>
      <span class="lt-note">Tick a measure to see how much of the West Bank it covers.</span>`;
    return;
  }
  if (!hit) {
    el.innerHTML = `<span class="lt-note">No combined figure for this selection.</span>`;
    return;
  }
  const overlapping = selected.length > 1;
  el.innerHTML =
    `<span class="lt-figure">${hit.pct}%</span>
     <span class="lt-lead">of the West Bank — ${hit.km2.toLocaleString()} km²</span>
     <span class="lt-note">${
       overlapping
         ? "Counted once where the measures overlap, so this is the ground covered, not the measures added up."
         : "Of a West Bank of " + Math.round(coverage.denominator_km2).toLocaleString() + " km², measured from the Oslo areas on this map."
     }</span>`;
}

function buildExtentToggles(map) {
  const host = $("#extent-toggles");

  for (const [key, style] of Object.entries(EXTENT_STYLE)) {
    const count = state.data[key].features.length;
    const definition = (state.meta.extent_definitions || {})[key] || "";
    const row = toggleRow({
      id: key,
      colour: style.colour,
      label: style.label,
      definition: definition + figureFor(key),
      checked: key === "built_up" && count > 0,
      disabled: count === 0,
      note: count === 0 ? "no data yet" : `${count}`,
    });
    row.querySelector("input").addEventListener("change", (e) => {
      const vis = e.target.checked ? "visible" : "none";
      map.setLayoutProperty(`settlements-${key}-fill`, "visibility", vis);
      map.setLayoutProperty(`settlements-${key}-line`, "visibility", vis);
      updateLandTotal();
    });
    host.appendChild(row);
  }

  // Closed military areas belong with the measures rather than with context: a
  // closure order removes access to land, and at 18% of the West Bank this is
  // the largest single measure on the map.
  const firingMeta = state.data.firing.metadata || {};
  const firingRow = toggleRow({
    id: "firing",
    colour: "#f97316",
    label: "Closed military areas",
    definition:
      "Israeli firing zones — land closed to Palestinian access. Each polygon " +
      "carries the date its closure order was signed." +
      figureFor("closed_military_area"),
    checked: false,
    note: `${firingMeta.count ?? state.data.firing.features.length}`,
  });
  firingRow.querySelector("input").addEventListener("change", (e) => {
    const vis = e.target.checked ? "visible" : "none";
    ["firing-fill", "firing-line"].forEach(
      (l) => map.getLayer(l) && map.setLayoutProperty(l, "visibility", vis)
    );
    updateLandTotal();
  });
  host.appendChild(firingRow);
  updateLandTotal();
}

function buildMechanismToggles(map) {
  const host = $("#mechanism-toggles");
  const meta = state.data.localities.metadata || {};
  const resourceMeta = state.data.resource.metadata || {};

  const rows = [
    {
      id: "depopulated",
      colour: MECHANISM_STYLE.depopulation_1948.colour,
      label: MECHANISM_STYLE.depopulation_1948.label,
      definition:
        "Localities depopulated during and after the 1948 war, sized by their " +
        "1945 Palestinian population — not the locality total, which in mixed " +
        "cities overstates displacement by more than twice.",
      layers: ["localities-depopulated"],
      note: `${meta.depopulated_1948 ?? 0}`,
    },
    {
      id: "standing",
      colour: "#34d399",
      label: "Palestinian localities (present day)",
      definition:
        "Localities still standing, for contrast with what was lost. OCHA and " +
        "Palestine Open Maps records are reconciled into one point per place.",
      layers: ["localities-standing", "localities-label"],
      note: "",
    },
    {
      id: "resource",
      colour: "#22d3ee",
      label: "Destruction of resource access",
      definition:
        `Water, farmland, livestock, homes and property. ` +
        `${resourceMeta.total_records ?? 0} verified OCHA records. ` +
        `<strong>Masafer Yatta only, 2025 only</strong> — absence elsewhere means ` +
        `not monitored, not that nothing happened.`,
      layers: ["resource-point"],
      note: `${resourceMeta.localities_plotted ?? 0}`,
    },
  ];

  for (const r of rows) {
    const row = toggleRow({
      id: r.id, colour: r.colour, label: r.label,
      definition: r.definition, checked: false, note: r.note,
    });
    row.querySelector("input").addEventListener("change", (e) => {
      const vis = e.target.checked ? "visible" : "none";
      r.layers.forEach((l) => map.getLayer(l) && map.setLayoutProperty(l, "visibility", vis));
      if (r.layers.includes("localities-label")) {
        setBasemapPlaceLabels(map, !e.target.checked);
      }
    });
    host.appendChild(row);
  }
}

function buildContextToggles(map) {
  const host = $("#context-toggles");
  const rows = [
    { id: "oslo", label: "Oslo areas (A / B / C, H1, H2)", layers: ["oslo-fill", "oslo-line"],
      colour: "#64748b",
      definition: "The classification the West Bank area on this map is computed from." },
    { id: "barrier", label: "Separation Barrier (Jan 2018)", layers: ["barrier-line"],
      colour: "#e879f9" },
    { id: "villages", label: "Palestinian village boundaries",
      layers: ["villages-fill", "villages-line"], colour: "#34d399",
      definition: "Areal extent of Palestinian villages, rather than a single point." },
    { id: "mandate", label: "Mandatory Palestine (1920)", layers: ["mandate-line"],
      colour: MANDATE_COLOUR,
      definition: "Generalised boundary — indicative extent, and deliberately not used for any percentage here." },
  ];
  for (const r of rows) {
    const empty = r.id === "barrier" && state.data.barrier.features.length === 0;
    const row = toggleRow({
      id: r.id, colour: r.colour, label: r.label, definition: r.definition,
      checked: false, disabled: empty, note: empty ? "no data" : "",
    });
    row.querySelector("input").addEventListener("change", (e) => {
      const vis = e.target.checked ? "visible" : "none";
      r.layers.forEach((l) => map.getLayer(l) && map.setLayoutProperty(l, "visibility", vis));
    });
    host.appendChild(row);
  }
}

function buildHistoricalToggles(map) {
  const host = $("#historical-toggles");

  // Which historical survey to show.
  const picker = document.createElement("select");
  picker.id = "historical-layer";
  picker.style.cssText =
    "width:100%;margin-bottom:8px;background:var(--surface-2);color:var(--ink);" +
    "border:1px solid var(--line);border-radius:6px;padding:6px 8px;font-size:12px";
  for (const layer of HISTORICAL_LAYERS) {
    const opt = document.createElement("option");
    opt.value = layer.id;
    opt.textContent = `${layer.label} — ${layer.detail}`;
    if (layer.id === state.historicalLayer.id) opt.selected = true;
    picker.appendChild(opt);
  }
  picker.addEventListener("change", (e) => {
    state.historicalLayer =
      HISTORICAL_LAYERS.find((l) => l.id === e.target.value) || HISTORICAL;
    $("#historical-note").textContent =
      `${state.historicalLayer.label} · ${state.historicalLayer.detail}. Via Palestine Open Maps.`;
    swapHistoricalTiles(map);
  });
  host.appendChild(picker);

  const modes = [
    ["off", "Off"],
    ["overlay", "Overlay (adjustable opacity)"],
    ["swipe", "Swipe comparison"],
  ];
  for (const [value, label] of modes) {
    const row = document.createElement("label");
    row.className = "toggle";
    row.innerHTML =
      `<input type="radio" name="hist" value="${value}" ${value === "off" ? "checked" : ""}>` +
      `<span class="label">${label}</span>`;
    row.querySelector("input").addEventListener("change", () => {
      setHistoricalMode(map, value);
      opacity.style.display = value === "overlay" ? "" : "none";
    });
    host.appendChild(row);
  }

  const opacity = document.createElement("input");
  Object.assign(opacity, { type: "range", min: 0, max: 1, step: 0.05, value: state.historicalOpacity });
  opacity.style.cssText = "width:100%;margin-top:6px;accent-color:var(--accent);display:none";
  opacity.addEventListener("input", (e) => {
    state.historicalOpacity = Number(e.target.value);
    if (map.getLayer("historical-raster")) {
      map.setPaintProperty("historical-raster", "raster-opacity", state.historicalOpacity);
    }
  });
  host.appendChild(opacity);
}

function buildIncidentToggles(map) {
  const host = $("#incident-toggles");
  const meta = state.data.incidents.metadata || {};
  const row = toggleRow({
    id: "incidents",
    colour: "#38bdf8",
    label: "Al-Haq documented incidents",
    checked: true,
    note: `${meta.rendered ?? state.data.incidents.features.length}`,
  });
  row.querySelector("input").addEventListener("change", (e) => {
    map.setLayoutProperty("incidents-point", "visibility", e.target.checked ? "visible" : "none");
  });
  host.appendChild(row);

  const oralCount = Object.keys((state.oralHistories || {}).localities || {}).length;
  if (oralCount) {
    const oralRow = toggleRow({
      id: "testimony",
      colour: "#fbbf24",
      label: "Localities with recorded testimony",
      definition:
        "Palestinian Oral History Archive interviews, held by AUB Libraries. " +
        "Mostly depopulated villages in Galilee and Haifa, so few fall in the " +
        "West Bank. Click a locality to list its interviews.",
      checked: false,
      note: `${oralCount}`,
    });
    oralRow.querySelector("input").addEventListener("change", (e) => {
      map.setLayoutProperty(
        "localities-testimony", "visibility", e.target.checked ? "visible" : "none"
      );
    });
    host.appendChild(oralRow);
  }

  // Surfacing the withheld count is the point: the gap is visible rather than
  // being papered over with plausible-looking pins.
  const withheld = meta.withheld ?? 0;
  const total = meta.total_records ?? 0;
  $("#incident-coverage").innerHTML =
    `${meta.rendered ?? 0} of ${total} Al-Haq records are placed on the map. ` +
    `${withheld} are withheld because their location could not be resolved to a ` +
    `single locality, or because they are territory-wide periodic reports. ` +
    `Nothing is plotted on a guess.`;
}

function buildStageLegend() {
  const host = $("#stage-legend");
  for (const s of state.meta.stages) {
    const li = document.createElement("li");
    li.innerHTML =
      `<span class="num">${s.id}</span>` +
      `<span class="dot" style="background:${STAGE_COLOURS[s.id]}"></span>` +
      `<span>${s.label}</span>`;
    host.appendChild(li);
  }
  const li = document.createElement("li");
  li.innerHTML =
    `<span class="num">—</span>` +
    `<span class="dot" style="background:${OUTPOST_COLOUR}"></span>` +
    `<span>Outpost (parallel track)</span>`;
  host.appendChild(li);
}

function initInteraction(map) {
  const clickable = [
    "settlements-built_up-fill",
    "settlements-municipal-fill",
    "settlements-regional_council-fill",
    "incidents-point",
    "localities-depopulated",
    "localities-standing",
    "firing-fill",
    "resource-point",
    "localities-testimony",
  ];

  map.on("click", (e) => {
    const hits = map.queryRenderedFeatures(e.point, {
      layers: clickable.filter((l) => map.getLayer(l)),
    });
    if (!hits.length) return;
    renderDetail(hits[0], state.meta, state.oralHistories);
  });

  for (const layer of clickable) {
    map.on("mouseenter", layer, () => { map.getCanvas().style.cursor = "pointer"; });
    map.on("mouseleave", layer, () => { map.getCanvas().style.cursor = ""; });
  }

  $("#detail-close").addEventListener("click", () => { $("#detail").hidden = true; });
}

function initTimeline(map) {
  const slider = $("#time-slider");
  const epochs = (state.meta.stats || {}).timeline || [];

  // A continuous year slider implied a precision the sources do not have, and
  // most of its range moved nothing at all. These marks are historically
  // meaningful *and* each one changes the figure — a mark that moves nothing is
  // decoration.
  if (!epochs.length) {
    slider.min = TIME.min;
    slider.max = TIME.max;
    slider.value = TIME.max;
  } else {
    slider.min = 0;
    slider.max = epochs.length - 1;
    slider.step = 1;
    slider.value = epochs.length - 1;
    const marks = $("#time-marks");
    if (marks) marks.innerHTML = epochs.map((e) => `<span>${e.label}</span>`).join("");
  }

  const apply = () => {
    const epoch = epochs[Number(slider.value)] || null;
    state.epoch = epoch;
    state.year = epoch ? epoch.year : Number(slider.value);
    applyTime(map);
    updateLandTotal();
  };

  slider.addEventListener("input", apply);
  $("#time-reset").addEventListener("click", () => {
    slider.value = epochs.length ? epochs.length - 1 : TIME.max;
    apply();
  });
  apply();
}

// --------------------------------------------------------------------------


/** Find the loaded feature behind a search result, so the panel can open. */
function featureById(id) {
  for (const f of state.data.localities.features) {
    if (f.properties.locality_id === id) return f;
  }
  for (const key of Object.keys(EXTENT_STYLE)) {
    for (const f of state.data[key].features) {
      if (f.properties.entity_id === id) return f;
    }
  }
  return null;
}

function initSearch(map) {
  const input = $("#search-input");
  const host = $("#search-results");
  let token = 0;

  const run = async () => {
    const query = input.value;
    const mine = ++token;
    const results = await search(query);
    if (mine !== token) return;   // a later keystroke already won
    host.innerHTML = resultsMarkup(results, query);
  };

  input.addEventListener("input", run);

  host.addEventListener("click", (e) => {
    const button = e.target.closest("button[data-id]");
    if (!button) return;
    map.flyTo({
      center: [Number(button.dataset.lon), Number(button.dataset.lat)],
      zoom: Math.max(map.getZoom(), 13),
      speed: 1.4,
    });
    const feature = featureById(button.dataset.id);
    if (feature) renderDetail(feature, state.meta, state.oralHistories);
  });
}

async function init() {
  await loadAll();

  const view = state.meta.view || { center: [35.231, 31.78], zoom: 11 };
  const map = new maplibregl.Map({
    container: "map",
    style: BASEMAP,
    center: view.center,
    zoom: view.zoom,
    maxZoom: 17,
    attributionControl: { compact: true },
  });
  map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "bottom-right");
  map.addControl(new maplibregl.ScaleControl({ maxWidth: 120, unit: "metric" }), "bottom-right");

  // Layer setup runs on every style load, because swapping the style discards
  // all sources and layers. UI construction runs once.
  let uiBuilt = false;

  const onStyleReady = () => {
    if (map.getLayer("settlements-built_up-fill")) return; // already applied
    addContextLayers(map);
    addFiringZoneLayers(map);
    addResourceLayers(map);
    addHistoricalDataLayers(map);
    addSettlementLayers(map);

    if (!uiBuilt) {
      buildExtentToggles(map);
      buildMechanismToggles(map);
      buildContextToggles(map);
      buildHistoricalToggles(map);
      buildIncidentToggles(map);
      buildStageLegend();
      initInteraction(map);
      initTimeline(map);
      initSwipeDrag();
    initSearch(map);
      state.earliestYear = computeEarliestYear();
      uiBuilt = true;
    }

    applyTime(map);
    $("#loading").classList.add("done");
  };

  map.on("style.load", onStyleReady);

  // The basemap is a third-party dependency and must not be able to brick the
  // application. If the remote style has not arrived in time, fall back to a
  // bare local style so the data layers still render.
  let fellBack = false;
  const fallBack = (why) => {
    if (fellBack || map.isStyleLoaded()) return;
    fellBack = true;
    console.warn(`basemap unavailable (${why}); using fallback style`);
    $("#basemap-warning").hidden = false;
    map.setStyle(FALLBACK_STYLE);
  };

  const watchdog = setTimeout(() => fallBack("timeout"), STYLE_TIMEOUT_MS);
  map.on("style.load", () => clearTimeout(watchdog));

  map.on("error", (e) => {
    const msg = String(e?.error?.message || "");
    console.error("map error", e && e.error);
    // A failed style fetch surfaces here before any style.load event.
    if (!map.isStyleLoaded() && /style|fetch|load/i.test(msg)) fallBack(msg);
  });

  renderAbout(state.meta, state.data);
  const about = $("#about");
  $("#about-open").addEventListener("click", () => about.showModal());
  $("#about-close").addEventListener("click", () => about.close());
  // Clicking the backdrop closes it. The dialog element reports clicks on its
  // own padding box, so compare against the content rectangle rather than
  // relying on the target, which is the dialog either way.
  about.addEventListener("click", (e) => {
    const r = about.getBoundingClientRect();
    const outside =
      e.clientX < r.left || e.clientX > r.right ||
      e.clientY < r.top || e.clientY > r.bottom;
    if (outside) about.close();
  });
}

init().catch((err) => {
  console.error(err);
  $("#loading").textContent = `Failed to load: ${err.message}. Run "python -m etl.build all" first.`;
});
