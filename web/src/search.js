// Search across every name a place is known by — English transliterations,
// Arabic, Hebrew, and the variant spellings the two locality sources disagree on.
//
// The index is built in Python (etl/search.py) with the normalisation applied
// there, so only the *query* is normalised here. The functions below mirror
// their Python counterparts; if one changes, change both.

const DATA = "public/data";

let index = null;
let loading = null;

/** 512 KB, and only useful once someone searches — so fetch it on first use. */
async function ensureIndex() {
  if (index) return index;
  if (!loading) {
    loading = fetch(`${DATA}/search_index.json`)
      .then((r) => (r.ok ? r.json() : []))
      .then((data) => (index = data))
      .catch(() => (index = []));
  }
  return loading;
}

// --- normalisation, mirroring etl/search.py -------------------------------

const ARABIC_MARKS = /[ً-ْٰـ]/g;
const HEBREW_MARKS = /[֑-ׇ]/g;
const ARABIC_FOLD = [
  [/[أإآٱ]/g, "ا"], // alef forms
  [/ة/g, "ه"],                     // ta marbuta -> ha
  [/ى/g, "ي"],                     // alef maqsura -> ya
  [/ؤ/g, "و"],
  [/ئ/g, "ي"],
];

// Arabic-to-Latin equivalences, matching etl/merge.py TRANSLITERATIONS.
const TRANSLITERATIONS = {
  bayt: "beit", bet: "beit",
  dayr: "deir", der: "deir",
  ayn: "ein", ain: "ein",
  khirbat: "khirbet", kharbat: "khirbet", khurbat: "khirbet",
  shaykh: "sheikh", shikh: "sheikh",
  om: "umm", um: "umm",
  qaryat: "qariat",
  nazlat: "nazlet",
  jabal: "jabel",
};

const isArabic = (s) => /[؀-ۿ]/.test(s);
const isHebrew = (s) => /[֐-׿]/.test(s);

function normaliseQuery(q) {
  const text = (q || "").trim();
  if (!text) return "";

  if (isArabic(text)) {
    let t = text.replace(ARABIC_MARKS, "");
    for (const [re, to] of ARABIC_FOLD) t = t.replace(re, to);
    return t.replace(/\s+/g, " ").trim();
  }
  if (isHebrew(text)) {
    return text.replace(HEBREW_MARKS, "").replace(/\s+/g, " ").trim();
  }

  // Latin: strip diacritics, drop the Arabic definite article in its assimilated
  // forms, then fold the known transliteration pairs.
  let t = text.normalize("NFKD").replace(/[̀-ͯ]/g, "");
  t = t.replace(/['’ʻʼ]/g, " ").toLowerCase();
  t = t.replace(/\b(?:al|el|as|ash|ad|at|az|ar|an|ain|ayn)[\s\-']+/g, " ");
  t = t.replace(/[^\w\s]/g, " ").replace(/\s+/g, " ").trim();
  t = t.replace(/yy/g, "y").replace(/ww/g, "w").replace(/ii/g, "i");
  return t
    .split(" ")
    .map((tok) => TRANSLITERATIONS[tok] || tok)
    .join(" ");
}

// --- matching -------------------------------------------------------------

const TYPE_LABEL = {
  locality: "Locality",
  settlement: "Settlement",
  ej_settlement: "Settlement · East Jerusalem",
  outpost: "Outpost",
  industrial_zone: "Industrial zone",
};

export async function search(query, limit = 25) {
  const key = normaliseQuery(query);
  if (key.length < 2) return [];
  const entries = await ensureIndex();

  const starts = [];
  const contains = [];
  for (const e of entries) {
    const pos = e.k.indexOf(key);
    if (pos === -1) continue;
    // A name beginning with the query is a better answer than one merely
    // containing it: "Beit" should offer Beit Jala before Khirbet Beit Zata.
    (pos === 0 || e.k[pos - 1] === " " || e.k[pos - 1] === "|" ? starts : contains).push(e);
    if (starts.length >= limit) break;
  }
  return [...starts, ...contains].slice(0, limit).map((e) => ({
    id: e.i,
    name: e.n,
    arabic: e.a || null,
    hebrew: e.h || null,
    district: e.d || null,
    type: e.t,
    typeLabel: TYPE_LABEL[e.t] || e.t,
    depopulated: e.x === 1,
    coordinates: e.c,
  }));
}

export function resultsMarkup(results, query) {
  if (!query || query.trim().length < 2) return "";
  if (!results.length) {
    return `<p class="hint">Nothing matches "${escapeHtml(query)}". Names are
      searchable in English, Arabic and Hebrew, including variant spellings.</p>`;
  }
  return `<ul class="search-results">${results
    .map((r) => {
      const scripts = [r.arabic, r.hebrew].filter(Boolean).join(" · ");
      const meta = [r.typeLabel, r.district].filter(Boolean).join(" · ");
      return `<li><button type="button" data-id="${escapeHtml(r.id)}"
          data-lon="${r.coordinates[0]}" data-lat="${r.coordinates[1]}">
          <span class="r-name">${escapeHtml(r.name)}${
            r.depopulated ? '<span class="r-tag">depopulated 1948</span>' : ""
          }</span>
          ${scripts ? `<span class="r-scripts">${escapeHtml(scripts)}</span>` : ""}
          <span class="r-meta">${escapeHtml(meta)}</span>
        </button></li>`;
    })
    .join("")}</ul>`;
}

function escapeHtml(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
  );
}
