"""B'Tselem adapter — settlement boundaries, municipal boundaries, outposts.

Supplied directly by B'Tselem on 2026-08-11 in response to a permission request,
and used under their licence for non-commercial use. These are checked-in source
files rather than fetched ones, because they arrived by email and there is no
public URL to re-fetch them from.

Two things this data unlocks that nothing else did:

1. **The municipal jurisdiction layer**, which shipped visibly empty until now.
2. **The outpost inventory** — 127 outposts, typed by B'Tselem. Outposts are the
   parallel track the schema has modelled since the start with nothing to put in
   it: built without Israeli government authorisation, illegal under Israeli
   domestic law as well as international law, and frequently authorised
   retroactively.

Measured against each other, these files demonstrate rather than assert the
premise the whole project rests on:

    built-up            56 km2   1.0% of the West Bank
    settlement boundary 179 km2   3.2%   (2.8x built-up)
    municipal          520 km2   9.2%   (7.0x built-up)

Source quirks handled here, all logged in docs/corrections.md:

  * The municipal file has **no usable join key** — GIS_ID is 0 on all 420
    features and the Hebrew name column is mangled to underscores. Names are
    recovered by containment: a municipal polygon that contains exactly one
    named settlement takes that settlement's name, and takes none otherwise.
  * `DATE_` contains impossible values (1000-01-01, 2094-11-17). Validated
    against a plausible range rather than trusted.
  * `Type` contains source typos — "Ouptost" for "Outpost", and one untranslated
    Hebrew value.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from ..geo import geometry_area_m2, point_in_polygon
from ..schema import (
    Entity,
    EntityType,
    Evidence,
    Extent,
    ExtentType,
    Names,
    Stage,
    StageEvent,
)

SOURCE_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "source" / "btselem"
SUPPLIED = "2026-08-11"

# B'Tselem's Type vocabulary, with the source's own typos mapped. "Ouptost" is
# a misspelling in the file; the Hebrew value means "settlement".
TYPE_MAP = {
    "settlement": EntityType.SETTLEMENT,
    "outpost": EntityType.OUTPOST,
    "ouptost": EntityType.OUTPOST,          # sic — source typo
    "התנחלות": EntityType.SETTLEMENT,        # sic — untranslated in source
    "industrial area": EntityType.INDUSTRIAL_ZONE,
    "tourism": EntityType.INDUSTRIAL_ZONE,
    "touristic site": EntityType.INDUSTRIAL_ZONE,
    "planned": EntityType.SETTLEMENT,
    "other": EntityType.SETTLEMENT,
}

# Dates outside this range are source errors, not history.
PLAUSIBLE_FROM = date(1967, 1, 1)
PLAUSIBLE_TO = date.today()


def _evidence(title: str, note: str | None = None) -> Evidence:
    return Evidence(
        source_id="btselem",
        title=title,
        url="https://www.btselem.org",
        document_date=SUPPLIED,
        retrieved=SUPPLIED,
        note=note or (
            "Supplied directly by B'Tselem under their licence for non-commercial "
            "use. B'Tselem is named expressly as required by that licence."
        ),
    )


def _load(name: str) -> list[dict[str, Any]]:
    path = SOURCE_DIR / name
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8-sig", errors="replace"))
    return [f for f in data.get("features", []) if f.get("geometry")]


def _clean(value: Any) -> str | None:
    """Reject mangled text. The municipal file's names arrive as underscores."""
    text = str(value or "").strip()
    if not text or text.strip("_") == "" or "�" in text:
        return None
    return text


def _centroid(geom: dict[str, Any]) -> tuple[float, float]:
    polys = [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]
    best, best_span = None, -1.0
    for rings in polys:
        ring = rings[0]
        xs = [p[0] for p in ring]
        ys = [p[1] for p in ring]
        span = (max(xs) - min(xs)) * (max(ys) - min(ys))
        if span > best_span:
            best_span, best = span, ring
    assert best is not None
    return (sum(p[0] for p in best) / len(best), sum(p[1] for p in best) / len(best))


def _valid_date(value: Any) -> str | None:
    text = str(value or "").strip()[:10]
    try:
        parsed = date.fromisoformat(text)
    except ValueError:
        return None
    return text if PLAUSIBLE_FROM <= parsed <= PLAUSIBLE_TO else None


# --------------------------------------------------------------------------

def load_boundaries() -> tuple[list[Entity], dict[str, Any]]:
    """Settlement outlines, typed — this is where the outposts come from."""
    feats = [f for f in _load("settlements-border.geojson")
             if f["geometry"]["type"] != "GeometryCollection"]
    ev = _evidence("B'Tselem settlement boundaries")

    entities: list[Entity] = []
    unknown_types: set[str] = set()
    used: set[str] = set()

    for f in feats:
        p = f["properties"]
        name_en = _clean(p.get("NameEng"))
        name_he = _clean(p.get("Name"))
        raw_type = str(p.get("Type") or "").strip()
        entity_type = TYPE_MAP.get(raw_type.lower())
        if entity_type is None:
            unknown_types.add(raw_type)
            entity_type = EntityType.SETTLEMENT

        display = name_en or name_he or "Unnamed"
        base = "".join(c.lower() if c.isalnum() else "-" for c in display).strip("-") or "unnamed"
        entity_id = f"bts-{base}"
        while entity_id in used:
            entity_id += "-2"
        used.add(entity_id)

        geom = f["geometry"]
        entities.append(
            Entity(
                entity_id=entity_id,
                entity_type=entity_type,
                names=Names(primary=display, hebrew=name_he),
                extents=[
                    Extent(
                        extent_type=ExtentType.SETTLEMENT_BOUNDARY,
                        geometry=geom,
                        source_crs="EPSG:4326",
                        area_m2=geometry_area_m2(geom),
                        evidence=[ev],
                    )
                ],
                # B'Tselem mapping the outline establishes the place existed by
                # the date they supplied it, and nothing earlier. No founding
                # dates are invented.
                stage_history=[
                    StageEvent(
                        stage=Stage.CONSTRUCTION_START,
                        valid_from=SUPPLIED,
                        evidence=[ev],
                    )
                ],
                evidence=[ev],
            )
        )

    stats = {
        "total": len(entities),
        "by_type": {
            t.value: sum(1 for e in entities if e.entity_type is t)
            for t in EntityType
        },
        "unknown_types": sorted(unknown_types),
    }
    return entities, stats


def load_municipal(named_reference: list[Entity]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Municipal boundaries, named by containment because no join key exists.

    `named_reference` supplies named settlements whose centroids are tested
    against each municipal polygon. Exactly one hit names the polygon; zero or
    more than one leaves it unnamed rather than guessing.
    """
    feats = _load("settlements-muni-border.geojson")
    ev = _evidence("B'Tselem settlement municipal boundaries")

    anchors: list[tuple[str, tuple[float, float]]] = []
    for e in named_reference:
        if e.names.primary and e.names.primary != "Unnamed":
            for ext in e.extents:
                anchors.append((e.names.primary, _centroid(ext.geometry)))
                break

    out: list[dict[str, Any]] = []
    named = ambiguous = 0
    bad_dates = 0

    for f in feats:
        p = f["properties"]
        geom = f["geometry"]
        # Deduplicate by name: the same settlement appears in both the OCHA
        # built-up inventory and the B'Tselem boundary file, and counting it
        # twice would read as ambiguity where there is none.
        hits = {n for n, c in anchors if point_in_polygon(c, geom)}

        name = None
        if len(hits) == 1:
            name = next(iter(hits))
            named += 1
        elif len(hits) > 1:
            ambiguous += 1

        declared = _valid_date(p.get("DATE_"))
        if p.get("DATE_") and not declared:
            bad_dates += 1

        note = None
        if name is None:
            note = (
                "Municipal polygon: the source carries no usable name (the name "
                "column is mangled and GIS_ID is zero throughout) and no single "
                "named settlement falls inside it, so it is left unnamed."
            )

        out.append(
            {
                "geometry": geom,
                "properties": {
                    "name": name or "Unnamed municipal area",
                    "named_by": "containment of a named settlement" if name else None,
                    "extent_type": ExtentType.MUNICIPAL.value,
                    "declared_date": declared,
                    "area_m2": geometry_area_m2(geom),
                    "source_crs": "EPSG:4326",
                    "evidence": [(_evidence("B'Tselem settlement municipal boundaries", note)
                                  if note else ev).to_dict()],
                },
            }
        )

    stats = {
        "total": len(out),
        "named": named,
        "ambiguous": ambiguous,
        "unnamed": len(out) - named,
        "implausible_dates_rejected": bad_dates,
    }
    return out, stats
