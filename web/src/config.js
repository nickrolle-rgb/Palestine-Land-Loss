// Rendering configuration. Kept separate from behaviour so the visual language
// can be argued about without touching map logic.

export const DATA = "public/data";

// Keyless vector basemap. Swap for a self-hosted style before any public launch —
// relying on a third party's free tier is not a hosting strategy.
export const BASEMAP =
  "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json";

// If the remote basemap cannot be reached, the map still has to work: the
// settlement geometry, Oslo areas and incidents are the point, and the basemap
// is context. This bare style keeps the whole application functional offline
// rather than leaving it stuck on a loading screen.
export const FALLBACK_STYLE = {
  version: 8,
  sources: {},
  layers: [
    { id: "bg", type: "background", paint: { "background-color": "#14120f" } },
  ],
};

// How long to wait for the remote style before falling back.
export const STYLE_TIMEOUT_MS = 6000;

// Palestine Open Maps — already georeferenced, do not rebuild.
// Ordered oldest first: the PEF sheets predate essentially all Zionist land
// purchase, so they are the closest thing to a pre-transfer baseline that
// exists as surveyed cartography.
const POM_ATTRIBUTION =
  '<a href="https://palopenmaps.org">Palestine Open Maps</a>';

export const HISTORICAL_LAYERS = [
  {
    id: "pal63k-1880",
    label: "PEF Survey of Western Palestine",
    detail: "Surveyed 1871–77 · pre-Mandate baseline",
    tiles: "https://palopenmaps.org/tiles/pal63k-1880/{z}/{x}/{y}@2x.jpg",
    attribution: `${POM_ATTRIBUTION} — PEF Survey of Western Palestine, surveyed 1871–77`,
    maxzoom: 15,
  },
  {
    id: "pal20k-1940s",
    label: "Survey of Palestine 1:20,000",
    detail: "Surveyed 1940–1945",
    tiles: "https://palopenmaps.org/tiles/pal20k-1940s/{z}/{x}/{y}.jpg",
    attribution: `${POM_ATTRIBUTION} — Survey of Palestine, surveyed 1940–1945`,
    maxzoom: 16,
  },
  {
    id: "pal250k-1946",
    label: "Palestine 1:250,000",
    detail: "1946 · immediately pre-Nakba",
    tiles: "https://palopenmaps.org/tiles/pal250k-1946/{z}/{x}/{y}.jpg",
    attribution: `${POM_ATTRIBUTION} — Palestine 1:250,000, 1946`,
    maxzoom: 14,
  },
  {
    id: "pal100k-1950s",
    label: "Palestine 1:100,000",
    detail: "1950s · immediately post-Nakba",
    tiles: "https://palopenmaps.org/tiles/pal100k-1950s/{z}/{x}/{y}.jpg",
    attribution: `${POM_ATTRIBUTION} — Palestine 1:100,000, 1950s`,
    maxzoom: 15,
  },
  {
    id: "isr250k-1951",
    label: "Israel 1:250,000",
    detail: "1951 · renamed landscape",
    tiles: "https://palopenmaps.org/tiles/isr250k-1951/{z}/{x}/{y}@2x.jpg",
    attribution: `${POM_ATTRIBUTION} — Israel 1:250,000, 1951`,
    maxzoom: 14,
  },
];

// Default historical layer for the swipe.
export const HISTORICAL = HISTORICAL_LAYERS[1];

// Mechanisms of land loss are styled apart on purpose. Post-1967 settlement is
// unlawful as a sourced legal finding; the 1948 depopulation is a documented
// historical event of different legal character. Same map, different marks.
export const MECHANISM_STYLE = {
  depopulation_1948: { colour: "#f472b6", label: "Depopulated in 1948" },
  settlement_post_1967: { colour: "#dc2626", label: "Israeli settlement (post-1967)" },
};

export const MANDATE_COLOUR = "#fbbf24";

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
