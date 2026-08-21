"""UNOSAT Gaza building damage, aggregated onto the municipal boundaries.

**Non-negotiable 11 governs this whole module.** A destroyed building is not
land taken. Tent camps stand among the rubble and people are living on that
ground; calling it lost, prohibited or stolen would misdescribe their situation
and erase the fact that they are still there. This layer therefore ships as its
own mechanism, in its own styling, and is **never** summed into a land-loss
total or fed to `etl/coverage.py`.

What the source is: 198,308 individually assessed damage sites from satellite
imagery, each carrying up to fourteen dated assessment rounds, published by
UNITAR/UNOSAT under CC BY-SA. Assessment date 11 October 2025.

Why it is aggregated rather than plotted point by point: 198,308 points is
around 20 MB of GeoJSON against a current total payload of six. Counts per
municipality answer the question a reader actually has — *how much of this place
was destroyed* — at a thousandth of the weight.

**Aggregation is an adaptation**, so the derived layer carries CC BY-SA. The
rest of the database is unaffected: share-alike binds adaptations, not works
merely published alongside.

Assignment is by **containment** — each site is counted in the municipal polygon
it falls inside — not by matching UNOSAT's municipality names against OCHA's.
Name matching is where this project has been burned before, and containment is a
fact about coordinates rather than a judgement about spelling. UNOSAT's own
`Municipality` attribute is then used as an independent check on that assignment,
and the agreement rate is published rather than assumed.

This is the only module permitted to import `pyogrio`, because it is the only
place a File Geodatabase is read. `tests/test_invariants.py::GdalStaysInItsBox`
enforces that.
"""

from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Any

from ..fetch import download, retrieved_date
from ..schema import Evidence
from ..sources import SOURCES, resource

ASSESSMENT_DATE = "2025-10-11"
PUBLISHED_DATE = "2025-10-31"

DAMAGE_NOTE = (
    "Buildings assessed as damaged or destroyed from satellite imagery, counted "
    "per municipality. Destruction is not dispossession: people live among this "
    "rubble, and these counts are never added to any land-loss total."
)


def _open_layer() -> tuple[list[tuple[float, float]], list[str | None]]:
    """Read site coordinates and UNOSAT's own municipality label.

    GDAL reads inside a zip through its /vsizip/ virtual filesystem, so the
    geodatabase never has to be unpacked to disk.
    """
    import pyogrio  # noqa: PLC0415 — deliberately local; see module docstring
    from pyogrio.raw import read as ogr_read

    r = resource("unosat_gaza_damage")
    path = download(r.url, r.filename)

    with zipfile.ZipFile(path) as zf:
        gdb_names = {n.split("/")[0] for n in zf.namelist() if ".gdb/" in n}
    if not gdb_names:
        raise ValueError(f"no .gdb directory inside {path}")
    vsi = f"/vsizip/{Path(path).as_posix()}/{sorted(gdb_names)[0]}"

    layers = [n for n, _ in pyogrio.list_layers(vsi) if n.startswith("Damage_Sites")]
    if not layers:
        raise ValueError(f"no Damage_Sites layer in {vsi}")

    meta, _, geometry, fields = ogr_read(
        vsi, layer=layers[0], columns=["Municipality"], read_geometry=True
    )
    labels = list(dict(zip(meta["fields"], fields)).get("Municipality", []))

    # Geometry comes back as WKB. Points are cheap to unpack by hand, and doing
    # so keeps the dependency to reading rather than to geometry handling.
    import struct

    coords: list[tuple[float, float]] = []
    for wkb in geometry:
        if wkb is None:
            coords.append((float("nan"), float("nan")))
            continue
        buf = bytes(wkb)
        little = buf[0] == 1
        endian = "<" if little else ">"
        x, y = struct.unpack_from(f"{endian}dd", buf, 5)
        coords.append((x, y))
    return coords, labels


#: The assessment carries fourteen rounds. Each has a sensor date and, per
#: site, a damage class where the site was classified in that round.
ROUNDS = range(1, 15)


def _round_columns() -> list[str]:
    cols = ["Main_Damage_Site_Class", "SensorDate"]
    for i in ROUNDS:
        if i == 1:
            continue
        cols += [f"Main_Damage_Site_Class_{i}", f"SensorDate_{i}"]
    return cols


def damage_timeline() -> tuple[list[dict[str, Any]], dict]:
    """Cumulative assessed damage at each of UNOSAT's fourteen sensor dates.

    What this counts, exactly: the number of sites carrying a damage class in
    round *n*. Those totals rise monotonically across the rounds, which is what
    a cumulative record of assessed damage looks like.

    What it deliberately does **not** do is interpret `Damage_Status`, whose
    values (0, 1, 3) are not decoded anywhere in the file. Building a timeline
    on guessed status codes would be inventing a finding, and the round dates
    and damage classes are unambiguous without them.

    Each point is therefore "sites assessed as damaged as at this date", not
    "buildings destroyed on this date". The distinction is stated in the UI.
    """
    import collections

    import pyogrio  # noqa: PLC0415
    from pyogrio.raw import read as ogr_read

    r = resource("unosat_gaza_damage")
    path = download(r.url, r.filename)
    with zipfile.ZipFile(path) as zf:
        gdb = sorted({n.split("/")[0] for n in zf.namelist() if ".gdb/" in n})[0]
    vsi = f"/vsizip/{Path(path).as_posix()}/{gdb}"
    layer = [n for n, _ in pyogrio.list_layers(vsi) if n.startswith("Damage_Sites")][0]

    meta, _, _, fields = ogr_read(
        vsi, layer=layer, columns=_round_columns(), read_geometry=False
    )
    data = dict(zip(meta["fields"], fields))

    points = []
    ambiguous_dates = 0
    for i in ROUNDS:
        cls_col = "Main_Damage_Site_Class" if i == 1 else f"Main_Damage_Site_Class_{i}"
        date_col = "SensorDate" if i == 1 else f"SensorDate_{i}"
        if cls_col not in data or date_col not in data:
            continue
        classes = data[cls_col]
        dates = [str(d)[:10] for d in data[date_col]]

        assessed = sum(1 for c in classes if str(c) not in ("nan", "None", ""))
        # One sensor date can span a couple of days of imagery. The modal date
        # is the round's date; anything else is noted rather than hidden.
        real = collections.Counter(d for d in dates if d and d != "NaT")
        if not real:
            continue
        date, _ = real.most_common(1)[0]
        if len(real) > 1:
            ambiguous_dates += 1
        points.append({"round": i, "date": date, "sites_assessed": assessed})

    points.sort(key=lambda p: p["date"])
    stats = {
        "rounds": len(points),
        "first_date": points[0]["date"] if points else None,
        "last_date": points[-1]["date"] if points else None,
        "rounds_with_mixed_dates": ambiguous_dates,
    }
    return points, stats


def damage_by_municipality(municipal: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict]:
    """Count assessed damage sites inside each municipal polygon."""
    from ..geo import bounds_of, point_in_polygon

    coords, labels = _open_layer()

    boxes = []
    for feat in municipal:
        minx, miny, maxx, maxy = bounds_of([feat])
        boxes.append((minx, miny, maxx, maxy))

    counts = [0] * len(municipal)
    unplaced = 0
    agree = 0
    checked = 0

    for (x, y), label in zip(coords, labels):
        if x != x or y != y:          # NaN
            unplaced += 1
            continue
        hit = -1
        for i, (minx, miny, maxx, maxy) in enumerate(boxes):
            if minx <= x <= maxx and miny <= y <= maxy:
                if point_in_polygon((x, y), municipal[i]["geometry"]):
                    hit = i
                    break
        if hit < 0:
            unplaced += 1
            continue
        counts[hit] += 1
        # Independent check: does our containment result agree with UNOSAT's
        # own label? Published, never used to override the geometry.
        if label:
            checked += 1
            ours = (municipal[hit]["properties"].get("name") or "").casefold()
            theirs = str(label).casefold()
            if ours and (ours in theirs or theirs in ours):
                agree += 1

    ev = Evidence(
        source_id="unosat",
        title="UNOSAT Gaza Strip Comprehensive Building Damage Assessment — 11 October 2025",
        url=SOURCES["unosat"].url,
        document_date=ASSESSMENT_DATE,
        retrieved=retrieved_date(resource("unosat_gaza_damage").filename),
        note=DAMAGE_NOTE,
    )

    out = []
    for feat, n in zip(municipal, counts):
        out.append(
            {
                "geometry": feat["geometry"],
                "properties": {
                    "name": feat["properties"].get("name"),
                    "damage_sites": n,
                    "assessment_date": ASSESSMENT_DATE,
                    "mechanism": "destruction",
                    "currency_note": DAMAGE_NOTE,
                    "licence": "CC BY-SA 4.0 — this aggregate is an adaptation of "
                               "UNOSAT's assessment and carries their terms.",
                    "evidence": [ev.to_dict()],
                },
            }
        )

    stats = {
        "sites_total": len(coords),
        "sites_placed": sum(counts),
        "sites_unplaced": unplaced,
        "municipalities": len(out),
        "label_checked": checked,
        "label_agreement": agree,
        "label_agreement_pct": round(100 * agree / checked, 1) if checked else None,
        "assessment_date": ASSESSMENT_DATE,
    }
    return out, stats
