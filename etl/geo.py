"""Shapefile reading and CRS handling — no GDAL required.

CRS is the thing critics test first. Getting Palestine Grid / Israeli TM / UTM
transforms subtly wrong shifts features by tens of metres. So:

  * the source CRS is read from the .prj and recorded on every output feature;
  * a declared `source_crs` in the registry is treated as an assertion and
    checked against the .prj — a mismatch raises rather than silently proceeding;
  * everything is reprojected to EPSG:4326 exactly once, at ingest.
"""

from __future__ import annotations

import io
import zipfile
from typing import Any, Iterator

import shapefile  # pyshp
from pyproj import CRS, Transformer
from pyproj.exceptions import CRSError


# Grids you will actually meet in this project.
KNOWN_GRIDS = {
    "EPSG:28193": "Palestine Grid 1923",
    "EPSG:2039": "Israeli TM Grid (ITM)",
    "EPSG:32636": "WGS 84 / UTM zone 36N",
    "EPSG:4326": "WGS 84 (geographic)",
}

WGS84 = "EPSG:4326"


class CrsMismatch(RuntimeError):
    pass


def crs_from_prj(prj_text: str) -> CRS:
    try:
        return CRS.from_wkt(prj_text)
    except CRSError:
        return CRS.from_user_input(prj_text.strip())


def identify_crs(prj_text: str, declared: str | None = None) -> tuple[CRS, str]:
    """Return (crs, epsg_string). Verifies `declared` against the .prj if given."""
    crs = crs_from_prj(prj_text)
    epsg = crs.to_epsg()
    resolved = f"EPSG:{epsg}" if epsg else crs.to_string()

    if declared:
        declared_crs = CRS.from_user_input(declared)
        # Compare on the projection definition, not the string — ESRI WKT often
        # lacks an EPSG authority code even when it is definitionally identical.
        if not crs.equals(declared_crs, ignore_axis_order=True):
            raise CrsMismatch(
                f"registry declares {declared} ({KNOWN_GRIDS.get(declared, '?')}) but "
                f"the .prj says {resolved}. Refusing to guess — update etl/sources.py "
                f"after confirming which is right."
            )
        resolved = declared

    return crs, resolved


def make_transformer(source_crs: CRS) -> Transformer | None:
    """None means the data is already WGS84 geographic and needs no transform."""
    if source_crs.equals(CRS.from_user_input(WGS84), ignore_axis_order=True):
        return None
    return Transformer.from_crs(source_crs, CRS.from_user_input(WGS84), always_xy=True)


def _round(v: float, nd: int = 6) -> float:
    """~0.1 m at this latitude. Keeps payloads small without visible drift."""
    return round(v, nd)


def _transform_ring(ring, tf: Transformer | None) -> list[list[float]]:
    if tf is None:
        return [[_round(x), _round(y)] for x, y in ring]
    xs, ys = zip(*ring)
    lons, lats = tf.transform(xs, ys)
    return [[_round(x), _round(y)] for x, y in zip(lons, lats)]


def _ring_is_clockwise(ring: list[list[float]]) -> bool:
    """Shoelace sign. Shapefile outer rings are clockwise; holes anticlockwise."""
    total = 0.0
    for i in range(len(ring) - 1):
        x1, y1 = ring[i]
        x2, y2 = ring[i + 1]
        total += (x2 - x1) * (y2 + y1)
    return total > 0


def shape_to_geojson(shp: Any, tf: Transformer | None) -> dict[str, Any] | None:
    """Convert a pyshp shape to a GeoJSON geometry in EPSG:4326.

    Shapefile polygons encode outer rings and holes by winding order rather than
    by nesting, so multipart polygons have to be reassembled: a clockwise ring
    opens a new polygon, an anticlockwise ring is a hole in the current one.
    """
    kind = shp.shapeTypeName

    if kind == "NULL":
        return None

    if kind.startswith("POINT"):
        x, y = shp.points[0]
        if tf is not None:
            x, y = tf.transform(x, y)
        return {"type": "Point", "coordinates": [_round(x), _round(y)]}

    parts = list(shp.parts) + [len(shp.points)]
    rings = [
        _transform_ring(shp.points[parts[i]:parts[i + 1]], tf)
        for i in range(len(parts) - 1)
    ]
    rings = [r for r in rings if len(r) >= 4]
    if not rings:
        return None

    if kind.startswith("POLYLINE"):
        lines = [r for r in rings if len(r) >= 2]
        if len(lines) == 1:
            return {"type": "LineString", "coordinates": lines[0]}
        return {"type": "MultiLineString", "coordinates": lines}

    if kind.startswith("POLYGON"):
        polygons: list[list[list[list[float]]]] = []
        for ring in rings:
            if _ring_is_clockwise(ring) or not polygons:
                polygons.append([ring])
            else:
                polygons[-1].append(ring)
        if len(polygons) == 1:
            return {"type": "Polygon", "coordinates": polygons[0]}
        return {"type": "MultiPolygon", "coordinates": polygons}

    raise ValueError(f"unhandled shape type: {kind}")


def read_zipped_shapefile(
    zip_path: str,
    base: str,
    declared_crs: str | None = None,
) -> tuple[list[dict[str, Any]], str]:
    """Read a zipped shapefile into (records, resolved_crs).

    Each record is {"geometry": <GeoJSON, EPSG:4326>, "properties": {...}}.
    """
    with zipfile.ZipFile(zip_path) as zf:
        names = {n.split("/")[-1].lower(): n for n in zf.namelist()}

        def member(ext: str) -> bytes:
            key = f"{base.lower()}{ext}"
            if key not in names:
                raise FileNotFoundError(
                    f"{zip_path}: no member {base}{ext} (have: {sorted(names)})"
                )
            return zf.read(names[key])

        prj_text = member(".prj").decode("utf-8", "replace")
        crs, resolved = identify_crs(prj_text, declared_crs)
        tf = make_transformer(crs)

        reader = shapefile.Reader(
            shp=io.BytesIO(member(".shp")),
            dbf=io.BytesIO(member(".dbf")),
            shx=io.BytesIO(member(".shx")),
            encoding="utf-8",
            encodingErrors="replace",
        )

        out: list[dict[str, Any]] = []
        for sr in reader.iterShapeRecords():
            geom = shape_to_geojson(sr.shape, tf)
            if geom is None:
                continue
            out.append({"geometry": geom, "properties": sr.record.as_dict()})

    return out, resolved


# --- geometry helpers ------------------------------------------------------

def geometry_area_m2(geom: dict[str, Any]) -> float:
    """Approximate area via an equal-area projection. For display only."""
    if geom["type"] not in ("Polygon", "MultiPolygon"):
        return 0.0
    polys = (
        [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]
    )
    # Cylindrical equal-area centred on the West Bank.
    tf = Transformer.from_crs(
        WGS84, "+proj=cea +lat_ts=31.9 +lon_0=35.2 +datum=WGS84 +units=m", always_xy=True
    )
    total = 0.0
    for rings in polys:
        for i, ring in enumerate(rings):
            xs, ys = zip(*ring)
            px, py = tf.transform(xs, ys)
            a = 0.0
            for j in range(len(px) - 1):
                a += px[j] * py[j + 1] - px[j + 1] * py[j]
            a = abs(a) / 2.0
            total += a if i == 0 else -a
    return round(total, 1)


def bounds_of(features: list[dict[str, Any]]) -> list[float]:
    xs: list[float] = []
    ys: list[float] = []

    def walk(c: Any) -> None:
        if isinstance(c, (int, float)):
            return
        if c and isinstance(c[0], (int, float)):
            xs.append(c[0])
            ys.append(c[1])
            return
        for part in c:
            walk(part)

    for f in features:
        if f.get("geometry"):
            walk(f["geometry"]["coordinates"])
    return [min(xs), min(ys), max(xs), max(ys)] if xs else [34.2, 31.2, 35.6, 32.6]


def point_in_polygon(pt: tuple[float, float], geom: dict[str, Any]) -> bool:
    """Ray casting, honouring holes. Used to assign Oslo area to localities."""
    x, y = pt
    polys = (
        [geom["coordinates"]] if geom["type"] == "Polygon" else geom.get("coordinates", [])
    )
    inside = False
    for rings in polys:
        if not rings:
            continue
        if _ray_cast(x, y, rings[0]):
            in_hole = any(_ray_cast(x, y, h) for h in rings[1:])
            if not in_hole:
                inside = not inside
    return inside


def _ray_cast(x: float, y: float, ring: list[list[float]]) -> bool:
    inside = False
    n = len(ring)
    for i in range(n - 1):
        x1, y1 = ring[i]
        x2, y2 = ring[i + 1]
        if (y1 > y) != (y2 > y):
            xint = (x2 - x1) * (y - y1) / (y2 - y1) + x1
            if x < xint:
                inside = not inside
    return inside
