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
// Wording suggested by Palestine Open Maps when they granted permission.
const POM_ATTRIBUTION =
  'Survey of Palestine / <a href="https://palopenmaps.org">Palestine Open Maps</a>';

export const HISTORICAL_LAYERS = [
  {
    id: "pal63k-1880",
    label: "PEF Survey of Western Palestine",
    detail: "Surveyed 1871–77 · pre-Mandate baseline",
    tiles: "https://palopenmaps.org/tiles/pal63k-1880/{z}/{x}/{y}@2x.jpg",
    attribution: `${POM_ATTRIBUTION} — PEF Survey of Western Palestine, 1871–77`,
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

// The basemap labels populated places from OpenStreetMap, so with our own
// locality labels on, every village was named twice — "Abu Shukhaidem" from
// CARTO beside "Abu Shukheidim" from OCHA, with different transliterations.
// Ours carry the Arabic name alongside the transliteration as the naming policy
// requires, so ours win and these are hidden while the locality layer is on.
// Country, state and continent labels are deliberately not in this list.
export const BASEMAP_PLACE_LABELS = [
  "place_hamlet",
  "place_suburbs",
  "place_villages",
  "place_town",
  "place_city_r6",
  "place_city_r5",
  "place_city_dot_r7",
  "place_city_dot_r4",
  "place_city_dot_r2",
  "place_city_dot_z7",
  "place_capital_dot_z7",
];

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

// Four measures of "how much land", deliberately distinct. Built-up is ~1% of
// the West Bank and municipal ~9% — a 9x spread that a single colour would hide.
export const EXTENT_STYLE = {
  built_up: { colour: "#dc2626", label: "Built-up footprint" },
  settlement_boundary: { colour: "#fb923c", label: "Settlement boundary" },
  municipal: { colour: "#f59e0b", label: "Municipal jurisdiction" },
  regional_council: { colour: "#a16207", label: "Regional council jurisdiction" },
};

// The Oslo classes, with what each one actually means for control on the
// ground. The classification is the most misread thing on this map: "40% of the
// West Bank is Palestinian" is Areas A and B added together, but B is civil
// control with Israeli security control, which is a different thing from A. The
// legend states the distinction rather than leaving it to the colour.
//
// A and B are deliberately far apart in hue. They were near-identical greens
// while our data wrongly labelled both 'A' (docs/corrections.md); now that they
// are distinct in the data, the difference has to survive being looked at.
export const OSLO_CLASSES = [
  { id: "A", colour: "#10b981",
    meaning: "Palestinian civil and security control" },
  // Amber rather than a second green. Area B reads at a glance as a qualified
  // version of A when the two share a hue, and "qualified" is the opposite of
  // what Israeli security control means for the people living under it.
  { id: "B", colour: "#eab308",
    meaning: "Palestinian civil control; Israeli security control" },
  { id: "C", colour: "#64748b",
    meaning: "Israeli civil and security control" },
  { id: "H1", colour: "#22c55e",
    meaning: "Hebron — Palestinian control (1997 Protocol)" },
  { id: "H2", colour: "#f97316",
    meaning: "Hebron — Israeli security control" },
  { id: "Nature Reserve", colour: "#4d7c0f",
    meaning: "Declared reserve; a separate class in the source" },
  { id: "Israeli Declared East Jerusalem", colour: "#7c3aed",
    meaning: "Unilaterally annexed 1980; annexation held void by UNSC 478" },
  { id: "No Man's Land", colour: "#475569",
    meaning: "Unallocated under the 1949 armistice" },
];

export const OSLO_COLOURS = Object.fromEntries(
  OSLO_CLASSES.map((c) => [c.id, c.colour]),
);

export const TIME = { min: 1945, max: 2026 };
