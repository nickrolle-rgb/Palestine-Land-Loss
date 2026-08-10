// Rendering configuration. Kept separate from behaviour so the visual language
// can be argued about without touching map logic.

export const DATA = "public/data";

// Keyless vector basemap. Swap for a self-hosted style before any public launch —
// relying on a third party's free tier is not a hosting strategy.
export const BASEMAP =
  "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json";

// Palestine Open Maps — already georeferenced, do not rebuild.
export const HISTORICAL = {
  id: "pal20k-1940s",
  label: "Survey of Palestine 1:20,000",
  detail: "Surveyed 1940–1945",
  tiles: "https://palopenmaps.org/tiles/pal20k-1940s/{z}/{x}/{y}.jpg",
  attribution:
    '<a href="https://palopenmaps.org">Palestine Open Maps</a> — Survey of Palestine, surveyed 1940–1945',
  maxzoom: 16,
};

// The seven-stage pipeline. Colour ramps from "paper" to "built".
export const STAGE_COLOURS = {
  1: "#fde68a",
  2: "#fcd34d",
  3: "#fbbf24",
  4: "#f59e0b",
  5: "#ea580c",
  6: "#dc2626",
  7: "#991b1b",
};

export const OUTPOST_COLOUR = "#a855f7";

export const EXTENT_STYLE = {
  built_up: { colour: "#dc2626", label: "Built-up footprint" },
  municipal: { colour: "#f59e0b", label: "Municipal jurisdiction" },
  regional_council: { colour: "#a16207", label: "Regional council jurisdiction" },
};

export const OSLO_COLOURS = {
  A: "#10b981",
  B: "#14b8a6",
  C: "#64748b",
  H1: "#22c55e",
  H2: "#f97316",
  "Nature Reserve": "#4d7c0f",
  "Israeli Declared East Jerusalem": "#7c3aed",
  "No Man's Land": "#475569",
};

export const TIME = { min: 1945, max: 2026 };
