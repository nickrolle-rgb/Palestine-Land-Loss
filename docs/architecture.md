# Architecture

```
sources → ETL adapters → canonical model → GeoJSON → MapLibre (static hosting)
                                              │
                                              └→ (future) tippecanoe → PMTiles
```

## Why no GDAL, tippecanoe or Docker

None were available on the target machine and all three are awkward to install
on Windows without WSL. Rather than make the toolchain a prerequisite, the ETL
uses `pyshp` (pure Python shapefile reader) and `pyproj` (wheels, no system
GDAL). The whole pipeline runs after `pip install -r requirements.txt`.

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
| `oslo_areas.geojson` | 3.0 MB |
| `barrier.geojson` | 524 KB |
| `settlements_built_up.geojson` | 513 KB |
| `localities.geojson` | 496 KB |
| `incidents.geojson` | 18 KB |
| **Total** | **~4.6 MB** |

Eight Oslo polygons account for two thirds of that — they are extremely
high-vertex boundaries. Two cheap wins before reaching for tiling: simplify the
Oslo geometry at build time (it is a context layer, not a measurement layer),
and gzip on the host, which typically takes GeoJSON to a fifth of its size.

Move to PMTiles when the full West Bank build lands with all three extent layers
populated. Nothing in the client assumes GeoJSON beyond the source declarations
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
