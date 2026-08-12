"""How much land is taken *in total*, when the measures overlap.

Selecting built-up and municipal jurisdiction together must not add 70.9 km² to
520 km²: the built-up area sits inside its municipal boundary, and it is the
same ground. But closed military areas largely fall outside both, so they do add
territory. A running total therefore needs a real union, not a sum.

There is no geometry library here — the ETL is deliberately GDAL-free — so the
union is computed by rasterising each measure onto a 100 m grid and counting the
cells covered by the selected combination. That is exact to the grid, which at
100 m is far finer than the accuracy of the source boundaries, and the
resolution is stated in the output so nobody mistakes it for an exact
computation.

Cell area is computed per row rather than assumed constant, since a degree of
longitude shortens as you go north. Summing the covered cells of the Oslo
polygons reproduces 5,655 km², which is the check that the rasteriser is sound.

Every combination is precomputed at build time — with four populated measures
there are only fifteen — so the client looks the answer up instead of trying to
union polygons in a browser.
"""

from __future__ import annotations

import math
from itertools import combinations
from typing import Any, Iterable

# Grid resolution in metres. Finer costs build time and buys nothing: the source
# boundaries are not accurate to 100 m in the first place.
CELL_M = 100

_LAT_M = 111_320.0


def _polygons(geometry: dict[str, Any]) -> list[list[list[list[float]]]]:
    if not geometry:
        return []
    if geometry["type"] == "Polygon":
        return [geometry["coordinates"]]
    if geometry["type"] == "MultiPolygon":
        return geometry["coordinates"]
    return []


class Grid:
    """A bitmask per cell recording which measures cover it."""

    def __init__(self, bbox: tuple[float, float, float, float]):
        self.min_lon, self.min_lat, self.max_lon, self.max_lat = bbox
        mid_lat = (self.min_lat + self.max_lat) / 2
        self.lat_step = CELL_M / _LAT_M
        self.lon_step = CELL_M / (_LAT_M * math.cos(math.radians(mid_lat)))
        self.rows = int((self.max_lat - self.min_lat) / self.lat_step) + 1
        self.cols = int((self.max_lon - self.min_lon) / self.lon_step) + 1
        self.cells = bytearray(self.rows * self.cols)

    def row_area_m2(self, row: int) -> float:
        """Cell area at this row's latitude — longitude shortens going north."""
        lat = self.min_lat + (row + 0.5) * self.lat_step
        return (self.lat_step * _LAT_M) * (
            self.lon_step * _LAT_M * math.cos(math.radians(lat))
        )

    def burn(self, features: Iterable[dict[str, Any]], bit: int) -> None:
        """Scanline-fill each polygon, setting `bit` on every covered cell.

        Rings are filled with the even-odd rule across all rings of a polygon at
        once, which handles holes without treating them specially.
        """
        flag = 1 << bit
        for feature in features:
            for rings in _polygons(feature.get("geometry")):
                self._burn_polygon(rings, flag)

    def _burn_polygon(self, rings: list[list[list[float]]], flag: int) -> None:
        ys = [p[1] for ring in rings for p in ring]
        if not ys:
            return
        first = max(0, int((min(ys) - self.min_lat) / self.lat_step))
        last = min(self.rows - 1, int((max(ys) - self.min_lat) / self.lat_step))

        for row in range(first, last + 1):
            y = self.min_lat + (row + 0.5) * self.lat_step
            crossings: list[float] = []
            for ring in rings:
                for i in range(len(ring) - 1):
                    x1, y1 = ring[i]
                    x2, y2 = ring[i + 1]
                    if (y1 > y) == (y2 > y):
                        continue
                    crossings.append(x1 + (y - y1) * (x2 - x1) / (y2 - y1))
            if len(crossings) < 2:
                continue
            crossings.sort()
            base = row * self.cols
            for i in range(0, len(crossings) - 1, 2):
                # A cell counts when its *centre* falls inside the span. Rounding
                # the span outward instead adds up to two cells per row, which is
                # negligible for a large polygon and enormous for a small one —
                # it inflated the built-up total by 35%.
                start = max(
                    0,
                    math.ceil((crossings[i] - self.min_lon) / self.lon_step - 0.5),
                )
                end = min(
                    self.cols - 1,
                    math.floor(
                        (crossings[i + 1] - self.min_lon) / self.lon_step - 0.5
                    ),
                )
                for col in range(start, end + 1):
                    self.cells[base + col] |= flag

    def area_by_mask(self) -> list[dict[int, int]]:
        """Per row, how many cells carry each mask value."""
        out = []
        for row in range(self.rows):
            counts: dict[int, int] = {}
            base = row * self.cols
            for col in range(self.cols):
                mask = self.cells[base + col]
                if mask:
                    counts[mask] = counts.get(mask, 0) + 1
            out.append(counts)
        return out


def feature_date(feature: dict[str, Any]) -> str | None:
    """The date a feature's evidence establishes, wherever the source put it."""
    props = feature.get("properties") or {}
    for key in ("signed_date", "declared_date", "depopulated_date"):
        if props.get(key):
            return props[key][:10]
    dates = [
        s["valid_from"][:10]
        for s in (props.get("stage_history") or [])
        if s.get("valid_from")
    ]
    return min(dates) if dates else None


def as_of(features: list[dict[str, Any]], year: int | None) -> list[dict[str, Any]]:
    """Features whose evidence dates on or before the end of `year`."""
    if year is None:
        return features
    out = []
    for f in features:
        d = feature_date(f)
        if d and int(d[:4]) <= year:
            out.append(f)
    return out


def compute_coverage(
    layers: list[tuple[str, list[dict[str, Any]]]],
    extent: list[dict[str, Any]],
) -> dict[str, Any]:
    """Union area for every combination of the given layers.

    `extent` supplies the denominator — the Oslo polygons, whose rasterised area
    is used rather than a quoted figure so numerator and denominator are
    measured the same way.
    """
    xs: list[float] = []
    ys: list[float] = []
    for feature in extent:
        for rings in _polygons(feature.get("geometry")):
            for ring in rings:
                for p in ring:
                    xs.append(p[0])
                    ys.append(p[1])
    grid = Grid((min(xs), min(ys), max(xs), max(ys)))

    # Bit 0 is the denominator; the measures follow.
    grid.burn(extent, 0)
    for i, (_, features) in enumerate(layers):
        grid.burn(features, i + 1)

    per_row = grid.area_by_mask()

    def area_of(mask_wanted: int) -> float:
        total = 0.0
        for row, counts in enumerate(per_row):
            cell = grid.row_area_m2(row)
            for mask, n in counts.items():
                if mask & mask_wanted:
                    total += n * cell
        return total / 1e6

    denominator = area_of(1)
    results: dict[str, Any] = {
        "cell_metres": CELL_M,
        "denominator_km2": round(denominator, 1),
        "combinations": {},
    }

    ids = [name for name, _ in layers]
    for size in range(1, len(ids) + 1):
        for combo in combinations(range(len(ids)), size):
            mask = 0
            for i in combo:
                mask |= 1 << (i + 1)
            km2 = area_of(mask)
            key = "+".join(sorted(ids[i] for i in combo))
            results["combinations"][key] = {
                "km2": round(km2, 1),
                "pct": round(km2 / denominator * 100, 2) if denominator else None,
            }

    return results
