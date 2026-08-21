# Architecture

```
sources → ETL adapters → canonical model → GeoJSON → MapLibre (static hosting)
                                              │
                                              └→ (future) tippecanoe → PMTiles
```

## Why wheels only, and where GDAL fits after all

None of GDAL, tippecanoe or Docker were available on the target machine and all
three are awkward to install on Windows without WSL. The constraint that
followed is **everything installs from a wheel**: the whole pipeline runs after
`pip install -r requirements.txt`, on a bare box, with no system geo libraries.

That constraint was recorded for a while as "no GDAL", which is a different and
stricter claim than the reasoning supports — `pyproj` has always been a Python
wrapper around PROJ, a C library, shipped as a wheel. The standard was never
purity; it was installability.

So `pyogrio` is now a dependency. UNOSAT publish their Gaza damage assessment
only as an Esri File Geodatabase, `pyshp` cannot read one, and pyogrio's wheel
bundles GDAL and the OpenFileGDB driver — no system install, no WSL. The
alternative was hand-writing a binary FileGDB parser, which would have honoured
the letter of the old rule while being far worse for data integrity: silently
mis-parsed geometry is the worst failure this project could have.

It is **confined to `etl/adapters/unosat.py`**, asserted by
`tests/test_invariants.py::GdalStaysInItsBox`. `pyshp` still reads every
shapefile, and every measurement — ring reassembly, simplification, area,
rasterisation — remains readable Python in `etl/geo.py`. A reader who wants to
check our arithmetic can still do it without trusting a binary.

Consequence: shapefile polygon reassembly is done by hand in `etl/geo.py`.
Shapefiles encode outer rings and holes by **winding order** rather than
nesting, so a clockwise ring opens a new polygon and an anticlockwise ring is a
hole in the current one. This is handled in `shape_to_geojson`.

## Why GeoJSON and not PMTiles yet

PMTiles + MapLibre is the right end state — single-file tile archives on object
storage with HTTP range requests, no tile server, no running costs. GeoJSON is
the pragmatic pilot choice, but the current payload is already less comfortable
than expected:

| File | Size |
|---|---|
| `localities.geojson` | 1.70 MB |
| `village_boundaries.geojson` | 1.03 MB |
| `settlements_municipal.geojson` | 1.02 MB |
| `oslo_areas.geojson` | 594 KB |
| `search_index.json` | 500 KB |
| `settlements_settlement_boundary.geojson` | 354 KB |
| `settlements_built_up.geojson` | 336 KB |
| `oral_histories.json` | 217 KB |
| others | ~330 KB |
| **Total** | **~6.0 MB** |

About 5.5 MB of that loads at startup: the search index is fetched on first
search and the oral histories on first click, so neither costs a reader who
never uses them.

Simplification is already applied and is why these numbers are not far worse.
Two tolerances, deliberately different:

- **Context layers** (Oslo, Barrier, villages) simplify at ~10 m. Oslo alone
  went from 142,671 vertices to 27,804 — 3.0 MB to 594 KB.
- **Measurement layers** (the extents) simplify at ~5 m, below the accuracy of
  the source boundaries and sub-pixel until zoom 18. Municipal halved.

**Areas are never recomputed from simplified geometry.** They are measured from
the source polygons before simplification runs and stored on the feature, so
what is drawn can be cheaper than what is reported without the reported figure
drifting.

Move to PMTiles when the regional council layer lands and the payload grows again. Nothing in the client assumes GeoJSON beyond the source declarations
in `main.js` — swapping means changing source types and adding `source-layer`
names.

## CRS handling

This is the first thing critics test. Getting Palestine Grid 1923 (EPSG:28193),
Israeli TM Grid (EPSG:2039) or UTM 36N transforms subtly wrong shifts features
by tens of metres.

Rules enforced in `etl/geo.py`:

- The source CRS is read from the `.prj` and **recorded on every output feature**
  (visible in the detail panel).
- A `source_crs` declared in `etl/sources.py` is treated as an assertion and
  checked against the `.prj`. A mismatch raises `CrsMismatch` rather than
  silently proceeding.
- Everything is reprojected to EPSG:4326 exactly once, at ingest.
- Coordinates are rounded to 6 decimal places (~0.1 m at this latitude).

Grids encountered so far: settlements are UTM 36N (`EPSG:32636`); Oslo areas,
communities and the Barrier are already WGS84 geographic.

## Client structure

| File | Responsibility |
|---|---|
| `web/src/config.js` | Colours, tile URLs, stage palette — visual language only |
| `web/src/main.js` | Map setup, layers, time resolution, UI wiring |
| `web/src/panels.js` | Detail and About panels |
| `web/src/search.js` | Query normalisation and result rendering |

**Time filtering happens in JavaScript, not in MapLibre filter expressions.**
Stage history is an array of objects per feature, which expressions cannot index
usefully. With 160 entities, recomputing derived properties and calling
`setData` on slider input is instant and far simpler than flattening the history
into filterable scalars. Revisit if entity count reaches five figures.

**The swipe uses two synced map instances.** MapLibre cannot clip a single layer,
so the historical raster lives in a second, non-interactive map stacked above the
main one, clipped with `clip-path` and kept in sync via the main map's `move`
event. Overlay mode is different: there the raster is a normal layer inside the
main map with an opacity control, sitting beneath the settlement geometry.

## Hosting

Fully static. Any object store or GitHub Pages will serve it. The basemap
currently points at CARTO's keyless style and the historical tiles at Palestine
Open Maps — both third-party free tiers. Self-host the basemap style before any
public launch; relying on someone else's free tier is not a hosting strategy.


## Computing a union without a geometry library

Selecting built-up and municipal jurisdiction together must not add 70.9 km² to
520 km²: the built-up area sits inside the municipal boundary and it is the same
ground. Closed military areas largely fall outside both, so they do add. A
running total therefore needs a real union.

There is no geometry library here, so `etl/coverage.py` rasterises each measure
onto a 100 m grid and counts covered cells, precomputing all fifteen
combinations at build time. The client looks the answer up; the browser never
unions a polygon.

Three details make it trustworthy rather than approximate:

1. **Cells are sampled at their centres**, not by rounding spans outward. The
   first attempt rounded outward and inflated built-up by 35% — up to two extra
   cells per row is nothing for a large polygon and enormous for a small one.
2. **Cell area is computed per row**, since a degree of longitude shortens going
   north.
3. **The result is checked against known figures.** Rasterised singles match the
   polygon-computed areas within 0.3%, and the rasterised West Bank comes to
   5,672 km² against 5,655 km² measured from polygons. Four tests assert the
   union never exceeds the sum of its parts, never falls below its largest part,
   and that the denominator agrees within 2%.

Percentages use the rasterised denominator so numerator and denominator are
measured the same way.

## Reconciling overlapping sources

`etl/merge.py` exists because OCHA and Palestine Open Maps both record
Palestinian localities, and drawing both produced doubled dots and panels that
named the wrong place. Candidates are found by proximity and confirmed by name —
the reverse of the obvious order, because keying on exact names meant
"Beituniya" and "Beitunya" never met to have their distance compared.

Merged localities keep **both coordinates**: Palestine Open Maps marks the 1945
village, OCHA the present-day centre, and at Beituniya those differ by 1,175 m.
The client uses the historical position whenever a historical sheet is showing,
so a dot does not float away from the village it names.


## Caching, and why it is versioned rather than revalidated

Vercel counts a 304 as an edge request, exactly like a 200. So
`max-age=0, must-revalidate` — which an earlier fix applied to every data file
to stop stale GeoJSON being served after a deploy — meant **every visit
re-requested all eighteen data files**, with no browser caching benefit and full
billing cost. On a free tier capped at a million edge requests, that is the
difference between a site that stays up and one that pauses.

The fix is the standard one, and it solves both problems at once:

- `etl.build` stamps `meta.json` with a `build_id`: a short hash over the size
  and content of every published data file.
- The client requests everything except `meta.json` with `?v=<build_id>`.
- `vercel.json` serves `/public/data/*` as `max-age=31536000, immutable`, and
  `meta.json` alone as `must-revalidate`.

A repeat visitor therefore makes **one** conditional request — for `meta.json` —
and serves every data file from cache. When the data genuinely changes the hash
changes, the URLs change, and the browser fetches the new files. Correctness and
frugality stop being in tension, which is what the first attempt got wrong.
