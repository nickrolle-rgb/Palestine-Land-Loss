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
| **Post-1967 settlement** | Unlawful under international law as a sourced finding — UNSC 2334 (2016), ICJ advisory opinion 19 July 2024 | 160 settlements, built-up extent |
| **1948 depopulation** | Documented historical event; property vested in the state under the Absentees' Property Law 1950 | 467 localities depopulated 1947–50 |
| Mandate-era land transfer | Modelled, not populated | — |
| Closed military areas | Modelled, not populated | — |
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

- **Three ways to measure land taken.** Built-up footprint, municipal
  jurisdiction and regional council jurisdiction differ by an order of
  magnitude. All three are separate toggles with their definitions in the legend.
  Two are currently empty, and say so.
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
- **Mandatory Palestine boundary** as the stated denominator — without a defined
  whole, every "share of the land" figure is an assertion.
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
