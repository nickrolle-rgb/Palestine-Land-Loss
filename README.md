# Settlement Encroachment Map

An interactive map of Israeli settlement development in the occupied Palestinian
territory, showing each stage of the planning pipeline over time, against the
landscape that preceded it.

**Current state:** working East Jerusalem pilot on a West Bank-wide base layer,
built entirely from openly licensed data. See [Known gaps](#known-gaps) — several
are load-bearing.

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

Then open <http://localhost:8000>.

`etl.build` takes `base` (OCHA layers only, no crawl), `incidents` (Al-Haq only)
or `all`. The Al-Haq crawl is throttled to one request every 1.5s and takes a
few minutes.

## What it does

- **Three ways to measure land taken.** Built-up footprint, municipal
  jurisdiction and regional council jurisdiction differ by an order of
  magnitude. All three are separate toggles with their definitions in the legend.
  Two are currently empty, and say so.
- **The real seven-stage planning pipeline**, not a simplified four. Outposts run
  on a parallel track because they are frequently authorised retroactively and
  skip stages 2–4.
- **Time slider** resolving stage history, not a polygon-per-year.
- **Swipe comparison** against the Survey of Palestine 1:20,000 (surveyed
  1940–1945) via Palestine Open Maps.
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
| `web/` | Static MapLibre client |
| `docs/` | Pipeline, naming policy, data gaps, corrections, permission drafts |

## Data and licensing

Current posture is **OCHA/HDX-licensed data only**. Peace Now and B'Tselem
adapters are scaffolded but disabled pending written permission; drafts are in
[docs/permissions/](docs/permissions/).

One wrinkle worth knowing: OCHA's "State of Palestine Settlements" layer on HDX
*is* Peace Now's built-up settlement data, republished under CC BY-IGO. Using it
via HDX is already permitted with attribution to both. That is not the same as
scraping Peace Now directly.

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
4. **24 settlement polygons have no name** in the source dataset, including 18
   of the 20 in East Jerusalem. They are shown as unidentified, never guessed.
5. **Base layers are old** — settlements 2021, Oslo areas 2019, Barrier
   January 2018. Labelled with the data's date, not the build date.

## Legal footing

Settlement illegality is cited, not asserted: UN Security Council Resolution
2334 (23 December 2016); the ICJ advisory opinion of 19 July 2024 on the legal
consequences of Israel's policies in the occupied Palestinian territory; and
Australia's stated position that settlements are inconsistent with international
law.

The project maps localities, parcels, plans and infrastructure. It does not map
individuals — no settler names, no addresses of specific homes.
