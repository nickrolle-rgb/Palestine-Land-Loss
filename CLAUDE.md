# Working notes for Claude

## What this project is

An interactive map of Israeli settlement development in the occupied Palestinian
territory. Read `SCOPE.md` for the original scoping and `docs/data-gaps.md` for
what is currently missing. The pilot area is **East Jerusalem**.

## Non-negotiables

These are the rules that make the project credible. Breaking one to make the map
look better is the worst possible trade.

1. **Never assert a stage, date or location the sources do not support.** The ETL
   records the *minimum* stage the evidence proves. If that makes the time slider
   look empty, the UI explains why — it does not backfill plausible dates.
2. **Never plot a guessed location.** Al-Haq records that don't resolve to
   exactly one gazetteer locality are withheld and counted, not placed at a
   best-guess point. The withheld count is displayed.
3. **Never conflate the three extent definitions.** Built-up footprint,
   municipal jurisdiction and regional council jurisdiction differ by an order of
   magnitude and ship as separate layers with definitions in the legend. Empty
   layers render as "no data yet" rather than being hidden.
4. **Never enable a disabled source** in `etl/sources.py` without a recorded
   written permission in `docs/permissions/RESPONSES.md`.
5. **Never reproduce Al-Haq's report text.** Title, date, URL and matched
   locality only; link out for the content.
6. **Never map individuals.** No settler names, no addresses of specific homes.
   Localities, parcels, plans and infrastructure only.
7. **Never guess a settlement's identity** from size and position. Unnamed
   polygons stay unnamed until identified from a citable reference, logged in
   `docs/corrections.md`.

## Conventions

- Every output feature carries `evidence` with source, document date and
  retrieval date. A feature without evidence is a bug.
- Source CRS is read from the `.prj`, verified against the registry's assertion,
  and recorded on the feature. A mismatch raises rather than proceeding.
- Reproject to EPSG:4326 once, at ingest.
- Source-data quirks are normalised at ingest and logged in
  `docs/corrections.md`, not propagated (e.g. OCHA's literal `West Bsnk` typo).
- British/Australian spelling in prose; the codebase uses `licence` for the noun.

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
- **No GDAL/tippecanoe/Docker** on this machine, by design. Don't add them as
  prerequisites; `pyshp` + `pyproj` cover it.
