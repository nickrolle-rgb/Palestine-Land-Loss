# Palestinian Land Loss

An interactive map of Palestinian land loss, drawn against the landscape that
preceded it, where every element resolves to a dated document.

**Current state:** working build covering historic Palestine, with an East
Jerusalem pilot for the settlement pipeline. Built entirely from openly licensed
or permission-pending data. See [Known gaps](#known-gaps) — several are
load-bearing.

## Mechanisms, kept apart

Land has been lost by more than one process, and those processes are not alike.
Collapsing them into one undifferentiated colour would misrepresent all of them,
so each carries its own styling, evidence and legal note:

| Mechanism | Status | In this build |
|---|---|---|
| **Post-1967 settlement** | Unlawful under international law as a sourced finding — UNSC 2334 (2016), ICJ advisory opinion 19 July 2024 | 160 built-up, 156 boundaries, 420 municipal areas |
| **Outposts** | Built without Israeli government authorisation; illegal under Israeli domestic law too, and often retroactively legalised | 127 outposts, 24.9 km² |
| **1948 depopulation** | Documented historical event; property vested in the state under the Absentees' Property Law 1950 | 467 localities depopulated 1947–50 |
| **Closed military areas** | Israeli firing zones; land closed to Palestinian access, each with the date its closure order was signed | 58 zones, 1,024 km² — 18.1% of the West Bank |
| **Destruction of resource access** | Water, farmland, livestock, homes and property, from OCHA field monitoring | 2,904 records, Masafer Yatta and 2025 only |
| Mandate-era land transfer | Modelled, not populated | — |
| Barrier severance | Modelled, not populated | — |

Keeping these distinct is not a softening. It is what stops a critic dismissing
the whole map by attacking its weakest join.

## Quick start

```bash
pip install -r requirements.txt
```

```bash
python -m etl.build all
```

```bash
python -m http.server -d web 8000
```

Tests assert the rules the project's credibility rests on — every feature cites
resolvable evidence, no ambiguous incident is plotted, periodic reports are never
pinned, coordinates fall inside historic Palestine, a declared CRS that disagrees
with the `.prj` raises, and no source appears in output while disabled in the
registry:

```bash
python -m unittest discover tests -v
```

Then open <http://localhost:8000>.

`etl.build` takes `base` (OCHA layers only, no crawl), `incidents` (Al-Haq only)
or `all`. The Al-Haq crawl is throttled to one request every 1.5s and takes a
few minutes.

## Deployment

Statically hosted, no build step on the server. `vercel.json` sets
`outputDirectory` to `web`, so the site root is `web/` and data resolves at
`/public/data/…` exactly as it does locally.

The generated GeoJSON in `web/public/data/` **is committed**, because there is no
server-side build to produce it. Re-run `python -m etl.build all` and commit the
result to refresh the deployed map.

## What it does

- **Five measures of the same territory**, and the spread is the point:

  | Measure | Area | % of West Bank |
  |---|---|---|
  | Built-up footprint | 70.9 km² | 1.25% |
  | Settlement boundary | 179.0 km² | 3.16% |
  | Municipal jurisdiction | 520.0 km² | 9.20% |
  | Closed military areas | 1,024.3 km² | 18.11% |
  | Regional council | — | no data yet |

  A 7× spread between built-up and municipal, and 14× to the firing zones. Each
  is a separate toggle with its definition stated; the unsourced one ships
  visibly empty rather than hidden.

  The denominator is computed from the Oslo polygons on the map, not quoted, and
  comes to 5,655 km² — the canonical West Bank figure, which is a standing check
  that the geometry and reprojection are sound.

- **A running total that counts overlapping ground once.** Built-up land inside a
  municipal boundary is the same ground, so selecting both reads 9.53%, not
  10.43%. Firing zones largely fall outside both, so they genuinely do add:
  everything together comes to 28.0% of the West Bank. Computed as a real union
  by rasterising each measure onto a 100 m grid at build time, since the ETL has
  no geometry library — see `etl/coverage.py`.

- **Search in English, Arabic and Hebrew**, including variant transliterations,
  so `Bayt Mirsim` finds `Beit Mirsim` and `القدس` finds Jerusalem. Arabic source
  names are vocalised and keyboards are not, so tashkeel is stripped and alef
  forms folded; Hebrew loses its niqqud.

- **Oral history.** 726 recorded interviews across 133 villages from the
  Palestinian Oral History Archive at AUB Libraries, joined on Palestine Open
  Maps' own slug. Listed and linked, never reproduced — CC BY-NC-ND.
- **The real seven-stage planning pipeline**, not a simplified four. Outposts run
  on a parallel track because they are frequently authorised retroactively and
  skip stages 2–4.
- **Time slider** resolving stage history, not a polygon-per-year.
- **Five historical surveys** via Palestine Open Maps, selectable in swipe or
  overlay: PEF Survey of Western Palestine (surveyed 1871–77), Survey of
  Palestine 1:20,000 (1940–45), Palestine 1:250,000 (1946), Palestine 1:100,000
  (1950s) and Israel 1:250,000 (1951) — before and after the Nakba in the same
  control.
- **Depopulated localities sized by displaced population**, using the Palestinian
  figure rather than the total where the source records the split. Jerusalem's
  1945 total is 157,080; its Palestinian population was 60,080. Using the total
  would inflate the symbol 2.6×.
- **Mandatory Palestine boundary** as context. It is *not* used as a denominator:
  the source polygon is generalised and computes to 31,114 km² against a
  published ~26,320, so percentages use the West Bank area measured from the
  Oslo polygons instead.
- **Every feature cites a dated document**, with the date retrieved.
- **Al-Haq incident records** matched to localities by name, with unplaceable
  records withheld rather than guessed.

## Architecture

```
sources → ETL adapters → canonical model → GeoJSON → MapLibre (static hosting)
```

Deliberately no GDAL, no tippecanoe, no Docker: the ETL runs on `pyshp` +
`pyproj` wheels so it works on a bare machine. At pilot volumes GeoJSON is
smaller than the tooling required to tile it; the PMTiles step is designed for
but not yet needed. See [docs/architecture.md](docs/architecture.md).

| Path | What |
|---|---|
| `etl/schema.py` | Canonical model — entities, extents, stage history, evidence |
| `etl/sources.py` | Source registry with licence and currency per source |
| `etl/geo.py` | Shapefile reading, CRS verification, reprojection to EPSG:4326 |
| `etl/adapters/ocha.py` | OCHA/HDX base geography and settlements |
| `etl/adapters/alhaq.py` | Al-Haq crawl, gazetteer matching, confidence scoring |
| `etl/adapters/historical.py` | Palestine Open Maps localities, Mandate boundary |
| `etl/adapters/btselem.py` | Settlement boundaries, municipal areas, outpost inventory |
| `etl/adapters/poha.py` | Palestinian Oral History Archive index |
| `etl/merge.py` | Reconciles the two locality sources into one place per dot |
| `etl/coverage.py` | Overlap-aware land totals, rasterised to a 100 m grid |
| `etl/search.py` | Cross-script name index |
| `tests/test_invariants.py` | The rules the project's credibility rests on |
| `web/` | Static MapLibre client |
| `docs/` | Pipeline, naming policy, data gaps, corrections, permission drafts |

## Data and licensing

Every source carries its licence in `etl/sources.py`, and a test fails the build
if anything ships with an unknown one.

| Source | Position |
|---|---|
| OCHA oPt / HDX | CC BY and CC BY-IGO |
| Peace Now, via OCHA on HDX | CC BY-IGO — their built-up layer, republished by OCHA |
| **B'Tselem** | **Granted 2026-08-11**, non-commercial licence; four GeoJSON files supplied directly |
| **Palestine Open Maps** | **Granted 2026-08-11** for tiles and the locality database, with conditions carried and asserted by tests |
| Palestinian Oral History Archive | CC BY-NC-ND — metadata and links only |
| Wikidata | CC0 |
| Al-Haq | All rights reserved; no licence relied on, metadata and links only |
| historical-basemaps | GPL-3.0 — **still unresolved**, used only for the Mandate boundary |
| Peace Now direct | Not yet granted; adapter disabled |

Correspondence and conditions are in [docs/permissions/](docs/permissions/).

One wrinkle worth knowing: OCHA's "State of Palestine Settlements" layer on HDX
*is* Peace Now's built-up settlement data, republished under CC BY-IGO. Using it
via HDX is already permitted with attribution to both. That is not the same as
scraping Peace Now directly.

## Keeping it current

A GitHub Action rebuilds from source every Monday and commits only if the data
changed — and only if `tests/test_invariants.py` still passes. An automated
commit must not be able to bypass the rules the project rests on, so a source
that changes shape and breaks one fails the run instead of publishing.

Currency is a property of the pipeline, not the data. OCHA refresh demolition
records within 48 hours of an incident; the limit on how fresh this map can be
is what they publish as data, not how often it is built.

## Scope

This map documents **land**. Detention — theft of freedom rather than land — was
researched and deliberately kept out: it has no locality-level geodata, so it
could only be a table, and folding it into a land map would blur both arguments.
It is scoped as a sibling project in
[docs/sibling-project-detention.md](docs/sibling-project-detention.md), which
this map should link to rather than absorb.

## Known gaps

These are real and they limit what the map can currently claim:

1. **Planning stages 1–5 are not populated.** OCHA publishes geography, not
   planning records. Every settlement is currently asserted at the *minimum*
   stage its evidence supports — a built-up footprint observed on 2021-06-03
   proves construction began by then and nothing earlier. This makes the time
   slider a cliff at 2021; the UI says so rather than looking broken.
2. **Municipal and regional council jurisdiction have no open source.** The
   layers exist and render; they are empty and labelled "no data yet".
3. **Outposts are not separately inventoried** in the open data.
4. **11 settlement polygons remain unnamed** in the source dataset. Thirteen
   were identified against Wikidata by requiring an item's coordinate fall
   *inside* the polygon, taking East Jerusalem from 2 of 20 named to 14 of 20.
   The rest are shown as unidentified, never guessed — including the largest
   unnamed polygon, where size and position make a guess tempting.
5. **Base layers are old** — settlements 2021, Oslo areas 2019, Barrier
   January 2018. Labelled with the data's date, not the build date.
6. **No pre-Mandate administrative boundaries.** Late-Ottoman Palestine was split
   between the Mutasarrifiyya of Jerusalem (independent, reporting directly to
   Constantinople from 1872) and the sanjaks of Nablus and Acre under the Vilayet
   of Beirut. No GIS dataset of those boundaries could be located —
   historical-basemaps and OpenHistoricalMap both stop at empire level. They are
   **not drawn**; the PEF Survey (1871–77) stands in as the period's cartographic
   record.
7. **Two licences need resolving before publication.** Palestine Open Maps'
   `pom-data` declares no licence at all, and historical-basemaps is GPL-3.0,
   which is copyleft and may impose obligations on a derived database. Both are
   flagged in `etl/sources.py` and `docs/permissions/`.

## Legal footing

Settlement illegality is cited, not asserted: UN Security Council Resolution
2334 (23 December 2016); the ICJ advisory opinion of 19 July 2024 on the legal
consequences of Israel's policies in the occupied Palestinian territory; and
Australia's stated position that settlements are inconsistent with international
law.

The project maps localities, parcels, plans and infrastructure. It does not map
individuals — no settler names, no addresses of specific homes.
