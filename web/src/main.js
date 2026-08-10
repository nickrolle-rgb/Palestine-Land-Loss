import {
  BASEMAP, DATA, EXTENT_STYLE, FALLBACK_STYLE, HISTORICAL, OSLO_COLOURS,
  OUTPOST_COLOUR, STAGE_COLOURS, STYLE_TIMEOUT_MS, TIME,
} from "./config.js";
import { renderAbout, renderDetail } from "./panels.js";

const $ = (sel) => document.querySelector(sel);

const state = {
  meta: null,
  data: {},          // layer id -> FeatureCollection (kept raw for time filtering)
  year: TIME.max,
  historicalMode: "off",
  historicalOpacity: 0.75,
};

// --------------------------------------------------------------------------
// Data loading
// --------------------------------------------------------------------------

async function loadJSON(name, { optional = false } = {}) {
  const res = await fetch(`${DATA}/${name}`);
  if (!res.ok) {
    if (optional) return null;
    throw new Error(`${name}: ${res.status}`);
  }
  return res.json();
}

const EMPTY = { type: "FeatureCollection", features: [] };

async function loadAll() {
  state.meta = await loadJSON("meta.json");
  const names = {
    built_up: "settlements_built_up.geojson",
    municipal: "settlements_municipal.geojson",
    regional_council: "settlements_regional_council.geojson",
    localities: "localities.geojson",
    oslo: "oslo_areas.geojson",
    barrier: "barrier.geojson",
    incidents: "incidents.geojson",
  };
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
  for (const key of ["built_up", "municipal", "regional_council"]) {
    const fc = state.data[key];
    const out = {
      type: "FeatureCollection",
      features: fc.features
        .map((f) => {
          const stage = stageAt(f.properties, state.year);
          return stage === null
            ? null
            : { ...f, properties: { ...f.properties, stage_at: stage } };
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

  $("#time-readout").textContent = state.year;
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

/** Earliest year for which any stage evidence exists across all extents. */
function computeEarliestYear() {
  let earliest = null;
  for (const key of ["built_up", "municipal", "regional_council"]) {
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

  map.addSource("localities", { type: "geojson", data: state.data.localities });
  map.addLayer({
    id: "localities-point",
    type: "circle",
    source: "localities",
    layout: { visibility: "none" },
    paint: {
      "circle-radius": ["interpolate", ["linear"], ["zoom"], 9, 2.5, 15, 6],
      "circle-color": "#34d399",
      "circle-stroke-color": "#052e16",
      "circle-stroke-width": 1,
      "circle-opacity": 0.9,
    },
  });
  map.addLayer({
    id: "localities-label",
    type: "symbol",
    source: "localities",
    minzoom: 11,
    layout: {
      visibility: "none",
      // Naming policy: Palestinian/Arabic name shown alongside the
      // transliteration wherever the source carries both.
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
  map.addSource("historical", {
    type: "raster",
    tiles: [HISTORICAL.tiles],
    tileSize: 256,
    maxzoom: HISTORICAL.maxzoom,
    attribution: HISTORICAL.attribution,
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
          tiles: [HISTORICAL.tiles],
          tileSize: 256,
          maxzoom: HISTORICAL.maxzoom,
          attribution: HISTORICAL.attribution,
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

function setSwipePosition(x) {
  const w = window.innerWidth;
  const clamped = Math.max(0, Math.min(w, x));
  $("#swipe-handle").style.left = `${clamped}px`;
  if (historicalMap) {
    historicalMap.getContainer().style.clipPath =
      `inset(0 ${w - clamped}px 0 0)`;
  }
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
    const cur = parseFloat(handle.style.left || window.innerWidth / 2);
    if (e.key === "ArrowLeft") setSwipePosition(cur - 24);
    if (e.key === "ArrowRight") setSwipePosition(cur + 24);
  });
  window.addEventListener("resize", () => setSwipePosition(window.innerWidth / 2));
}

function setHistoricalMode(map, mode) {
  state.historicalMode = mode;
  ensureOverlayLayer(map);

  const overlayOn = mode === "overlay";
  map.setLayoutProperty("historical-raster", "visibility", overlayOn ? "visible" : "none");

  const swipeOn = mode === "swipe";
  $("#swipe").hidden = !swipeOn;
  if (swipeOn) {
    ensureSwipeMap(map);
    historicalMap.getContainer().style.display = "";
    setSwipePosition(window.innerWidth / 2);
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

function buildExtentToggles(map) {
  const host = $("#extent-toggles");
  for (const [key, style] of Object.entries(EXTENT_STYLE)) {
    const count = state.data[key].features.length;
    const definition = state.meta.extent_definitions?.[key] || "";
    const row = toggleRow({
      id: key,
      colour: style.colour,
      label: style.label,
      definition,
      checked: key === "built_up" && count > 0,
      disabled: count === 0,
      note: count === 0 ? "no data yet" : `${count}`,
    });
    row.querySelector("input").addEventListener("change", (e) => {
      const vis = e.target.checked ? "visible" : "none";
      map.setLayoutProperty(`settlements-${key}-fill`, "visibility", vis);
      map.setLayoutProperty(`settlements-${key}-line`, "visibility", vis);
    });
    host.appendChild(row);
  }
}

function buildContextToggles(map) {
  const host = $("#context-toggles");
  const rows = [
    { id: "oslo", label: "Oslo areas (A / B / C, H1, H2)", layers: ["oslo-fill", "oslo-line"], colour: "#64748b" },
    { id: "barrier", label: "Separation Barrier (Jan 2018)", layers: ["barrier-line"], colour: "#e879f9" },
    { id: "localities", label: "Palestinian localities", layers: ["localities-point", "localities-label"], colour: "#34d399" },
  ];
  for (const r of rows) {
    const empty = r.id === "barrier" && state.data.barrier.features.length === 0;
    const row = toggleRow({
      id: r.id, colour: r.colour, label: r.label,
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
    "localities-point",
  ];

  map.on("click", (e) => {
    const hits = map.queryRenderedFeatures(e.point, {
      layers: clickable.filter((l) => map.getLayer(l)),
    });
    if (!hits.length) return;
    renderDetail(hits[0], state.meta);
  });

  for (const layer of clickable) {
    map.on("mouseenter", layer, () => { map.getCanvas().style.cursor = "pointer"; });
    map.on("mouseleave", layer, () => { map.getCanvas().style.cursor = ""; });
  }

  $("#detail-close").addEventListener("click", () => { $("#detail").hidden = true; });
}

function initTimeline(map) {
  const slider = $("#time-slider");
  slider.min = TIME.min;
  slider.max = TIME.max;
  slider.value = TIME.max;
  slider.addEventListener("input", (e) => {
    state.year = Number(e.target.value);
    applyTime(map);
  });
  $("#time-reset").addEventListener("click", () => {
    state.year = TIME.max;
    slider.value = TIME.max;
    applyTime(map);
  });
}

// --------------------------------------------------------------------------

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
    addSettlementLayers(map);

    if (!uiBuilt) {
      buildExtentToggles(map);
      buildContextToggles(map);
      buildHistoricalToggles(map);
      buildIncidentToggles(map);
      buildStageLegend();
      initInteraction(map);
      initTimeline(map);
      initSwipeDrag();
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
  $("#about-open").addEventListener("click", () => $("#about").showModal());
  $("#about-close").addEventListener("click", () => $("#about").close());
}

init().catch((err) => {
  console.error(err);
  $("#loading").textContent = `Failed to load: ${err.message}. Run "python -m etl.build all" first.`;
});
