# Working notes for Claude

## What this project is

**Palestinian Land Loss** — an interactive evidence map. Read `SCOPE.md` for the
original scoping (written when it was narrower, "Settlement Encroachment Map")
and `docs/data-gaps.md` for what is missing. The settlement-pipeline pilot area
is **East Jerusalem**; the historical layers cover all of historic Palestine.

## Non-negotiables

These are the rules that make the project credible. Breaking one to make the map
look better is the worst possible trade.

1. **Never assert a stage, date or location the sources do not support.** The ETL
   records the *minimum* stage the evidence proves. If that makes the time slider
   look empty, the UI explains why — it does not backfill plausible dates.
2. **Never plot a guessed location.** Al-Haq records that don't resolve to
   exactly one gazetteer locality are withheld and counted, not placed at a
   best-guess point. The withheld count is displayed.
3. **Never conflate the extent definitions.** Built-up footprint, settlement
   boundary, municipal jurisdiction and regional council jurisdiction differ by
   an order of magnitude and ship as separate layers with definitions stated.
   Empty layers render as "no data yet" rather than being hidden. A fourth
   definition was added rather than folding B'Tselem's settlement outline into
   an existing one — that folding is exactly what this rule forbids.
4. **Never enable a disabled source** in `etl/sources.py` without a recorded
   written permission in `docs/permissions/RESPONSES.md`.
5. **Never reproduce Al-Haq's report text.** Title, date, URL and matched
   locality only; link out for the content.
6. **Never map individuals.** No settler names, no addresses of specific homes.
   Localities, parcels, plans and infrastructure only.
7. **Never guess a settlement's identity** from size and position. Unnamed
   polygons stay unnamed until identified from a citable reference, logged in
   `docs/corrections.md`. Curated identifications live in
   `etl/identifications.json` and are accepted only on **containment** — a
   source coordinate falling inside the polygon — never proximity. The anchor is
   re-verified every build; a moved polygon refuses the name.
8. **Never conflate mechanisms of land loss.** Post-1967 settlement is unlawful
   under international law as a sourced finding (UNSC 2334; ICJ 19 July 2024).
   The 1948 depopulation is a documented event of different legal character.
   Both are land loss; they get different styling, evidence and legal notes.
   Flattening them weakens the settlement case rather than strengthening the
   1948 one.
9. **Never size a symbol by a misleading total.** Depopulation symbols use the
   Palestinian 1945 population, not the locality total — in mixed cities the
   total overstates displacement by more than 2×.
10. **Never hand-draw a historical boundary.** No GIS exists for late-Ottoman
    sanjaks; that is recorded as a gap, not filled in by eye.
11. **Never treat destruction as dispossession.** A destroyed building is not
    land taken. Tent camps stand among the rubble across Gaza and people are
    living on that ground — labelling it prohibited, lost or stolen would
    misdescribe their situation and erase the fact that they are still there.
    Destruction, access restriction and territorial control are three separate
    mechanisms measured three different ways, and their headline figures
    (roughly 69%, 64.9% and 70%) are close enough to invite exactly this
    mistake. Destruction data ships as its own layer, in its own styling, and
    is never summed into a land-loss total.


## Conventions

- Every output feature carries `evidence` with source, document date and
  retrieval date. A feature without evidence is a bug.
- Source CRS is read from the `.prj`, verified against the registry's assertion,
  and recorded on the feature. A mismatch raises rather than proceeding.
- Reproject to EPSG:4326 once, at ingest.
- Source-data quirks are normalised at ingest and logged in
  `docs/corrections.md`, not propagated (e.g. OCHA's literal `West Bsnk` typo).
- British/Australian spelling in prose; the codebase uses `licence` for the noun.

## Automation

`.github/workflows/weekly-rebuild.yml` runs `etl.build all` every Monday, then
the test suite, then commits only if `web/public/data` changed. The ordering is
deliberate: **tests gate the commit**, so an automated run can never publish data
that breaks an invariant.

## Commands

```bash
python -m etl.build all
```

```bash
python -m http.server -d web 8000
```

`etl.build` also takes `base` (no network crawl), `incidents`, and
`refresh-urls` (re-resolve HDX URLs from the CKAN API).

## Gotchas

- **Al-Haq listing dates** use an Arabic comma (`،`, U+060C): `07، Aug 2026`.
- **Al-Haq listings** use two card classes: `list-12-item` (field stories) and
  `list-11-item` (PDF reports). Missing the second silently loses whole sections.
- **Periodic reports must never be plotted** — they cover the whole West Bank.
- **Settlement polygons are grouped by `GIS_ID`** to merge multi-part settlements
  and recover names from blank-named parts. 201 polygons → 160 entities.
- **Windows console encoding** mangles Arabic — use `PYTHONIOENCODING=utf-8`.
- **Everything installs from a wheel; nothing needs a system install.** That is
  the real constraint, and it was mis-stated for a while as "no GDAL". No
  tippecanoe, no Docker, no WSL, no system GDAL — but `pyogrio`, whose wheel
  bundles GDAL, is in, on the same terms `pyproj` has always been in with PROJ.
  It is **confined to `etl/adapters/unosat.py`** and a test enforces that:
  `pyshp` still reads every shapefile, and every measurement — ring reassembly,
  simplification, area, rasterisation — stays readable Python in `etl/geo.py`,
  because being auditable is worth more here than being convenient.
- **MapLibre style expressions can't index nested arrays.** Anything used for
  styling (e.g. `pop_1945_palestinian`) must be flattened in `schema.py`.
- **Swipe curtain must tolerate a zero-width container.** If the map has no
  width at init the curtain collapses and looks like a failed layer; positioning
  defers until a `ResizeObserver` reports real width.
- **B'Tselem files are checked in, not fetched** — `data/source/btselem/`. They
  arrived by email; there is no URL to re-fetch them from. Used under B'Tselem's
  non-commercial licence, which requires them to be named expressly.
- **Permission conditions are enforced by tests**, not goodwill. Palestine Open
  Maps require an accuracy caveat and acknowledgement of seven underlying
  sources; `tests/test_invariants.py::AttributionConditions` fails if either
  stops being published.
- **One unresolved licence remains**: historical-basemaps is GPL-3.0. Palestine
  Open Maps and B'Tselem both granted permission on 2026-08-11; POHA is
  CC BY-NC-ND, so metadata and links only.
- **Land shares come from `etl/coverage.py`, not from adding areas.** The
  measures overlap — built-up sits inside municipal — so a sum would be wrong.
  Coverage rasterises to a 100 m grid and precomputes all combinations. Sample
  cell *centres*: rounding spans outward inflated built-up by 35%.
- **The West Bank denominator is computed, never quoted.** Summing the Oslo
  polygons gives 5,655 km², which matches the canonical figure and is a standing
  check on the geometry. The Mandate polygon is generalised (31,114 km² against
  a published ~26,320) and must not be used as a denominator.
- **`vercel.json` takes no comments.** A `"//"` key inside a header object fails
  Vercel's schema and silently breaks every deploy; rationale goes in the repo.
- **Anything with no `stage_history` must not be time-filtered out.** Municipal
  boundaries carry none, and filtering them by stage emptied the layer while
  leaving its checkbox working — correct data, no error, blank map.
- **Search normalisation lives in Python** (`etl/search.py`); the client
  normalises only the query. Arabic source names are vocalised and keyboards are
  not, so tashkeel must be stripped or Arabic search matches nothing.
