"""OCHA/HDX adapter — base geography, settlements, localities.

What this source can and cannot tell us, stated plainly because it determines
what the map is allowed to claim:

  CAN: built-up settlement footprints; Oslo area classification; Palestinian
       communities with Arabic names, districts and 2017 population; the
       Barrier alignment; firing zones.

  CANNOT: planning-pipeline stages 1-5, tender dates, construction-start dates,
       per-settlement population time series, outpost inventory, or municipal /
       regional-council jurisdiction boundaries.

So we assign each settlement the *minimum* stage its evidence supports —
a built-up footprint observed on date D proves construction started by D, and
nothing more. We do not backfill dates we do not have. Everything above that
minimum waits on Peace Now / CBS (see docs/data-gaps.md).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from ..fetch import download, retrieved_date
from ..geo import (
    bounds_of,
    geometry_area_m2,
    point_in_polygon,
    read_zipped_shapefile,
)
from ..schema import (
    Confidence,
    Entity,
    EntityType,
    Evidence,
    Extent,
    ExtentType,
    Locality,
    Names,
    Stage,
    StageEvent,
)
from ..sources import SOURCES, resource

# The HDX record's own last-modified date. Used as the observation date for the
# built-up extents, NOT as a construction date.
SETTLEMENTS_OBSERVED = "2021-06-03"

EJ_OSLO_CLASS = "Israeli Declared East Jerusalem"

# Curated identifications for polygons the source leaves unnamed. Each entry
# names a Wikidata item whose coordinate falls *inside* the polygon — not merely
# near it — so the identification is a checkable relationship rather than an
# inference from size and position, which the project's rules forbid.
#
# The stored anchor is re-verified against the polygon on every build. If a
# source revision moves the geometry so the anchor no longer falls inside, the
# override is refused and the polygon reverts to unidentified. A silently
# misattached name would be worse than no name.
IDENTIFICATIONS_PATH = Path(__file__).resolve().parent.parent / "identifications.json"


def load_identifications() -> dict[str, dict[str, Any]]:
    if not IDENTIFICATIONS_PATH.exists():
        return {}
    return json.loads(IDENTIFICATIONS_PATH.read_text(encoding="utf-8"))


def _slug(text: str) -> str:
    keep = [c.lower() if c.isalnum() else "-" for c in text.strip()]
    out = "".join(keep)
    while "--" in out:
        out = out.replace("--", "-")
    return out.strip("-") or "unnamed"


def _centroid(geom: dict[str, Any]) -> tuple[float, float]:
    """Area-weighted centroid of the largest ring. Good enough for containment."""
    polys = (
        [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]
    )
    best: list[list[float]] | None = None
    best_span = -1.0
    for rings in polys:
        ring = rings[0]
        xs = [p[0] for p in ring]
        ys = [p[1] for p in ring]
        span = (max(xs) - min(xs)) * (max(ys) - min(ys))
        if span > best_span:
            best_span, best = span, ring
    assert best is not None
    return (
        sum(p[0] for p in best) / len(best),
        sum(p[1] for p in best) / len(best),
    )


# --------------------------------------------------------------------------

#: Oslo II (Interim Agreement, 28 September 1995) placed these city centres
#: under full Palestinian control — the definition of Area A. They are used
#: here only as containment probes to tell OCHA's two identically-labelled
#: polygons apart, never published as data.
AREA_A_ANCHORS = {
    "Ramallah": (35.2042, 31.8996),
    "Nablus": (35.2544, 32.2211),
    "Jenin": (35.3027, 32.4597),
    "Tulkarm": (35.0286, 32.3104),
    "Jericho": (35.4444, 31.8569),
    "Bethlehem": (35.2094, 31.7054),
    "Qalqilya": (34.9706, 32.1896),
}


def _split_mislabelled_area_b(out: list[dict[str, Any]]) -> None:
    """OCHA's Oslo file labels Area B as 'A'. Separate them by containment.

    The published shapefile carries CLASS='A' on two disjoint polygons. One is
    Area A, the other is Area B, and nothing in the attribute table says which.
    Leaving it produced a map asserting that 35.7% of the West Bank is Area A
    when the real figure is 17.4% — a factor-of-two overstatement of Palestinian
    civil *and* security control, and exactly the kind of error a hostile reader
    would find first.

    The Oslo II city centres are Area A by definition, so the polygon that
    contains them is Area A and the other is Area B. This is the containment
    standard used for settlement identification (non-negotiable 7), for the same
    reason: proximity would be a guess, containment is a fact about the geometry.
    It is re-run every build, so a source that fixes its own labelling, or
    reshapes a polygon, cannot silently leave a stale relabel behind.
    """
    candidates = [f for f in out if f["properties"]["oslo_class"] == "A"]
    if len(candidates) < 2:
        return  # source corrected upstream, or a shape we do not recognise

    def anchors_inside(feature):
        return {n for n, c in AREA_A_ANCHORS.items()
                if point_in_polygon(c, feature["geometry"])}

    hits = {id(f): anchors_inside(f) for f in candidates}
    with_cities = [f for f in candidates if hits[id(f)]]
    without = [f for f in candidates if not hits[id(f)]]

    # Refuse to guess. Area A must be exactly one polygon holding every anchor.
    if len(with_cities) != 1 or len(without) != len(candidates) - 1:
        raise ValueError(
            "Oslo A/B disambiguation is ambiguous — "
            f"{[sorted(hits[id(f)]) for f in candidates]}. Refusing to relabel."
        )
    missing = set(AREA_A_ANCHORS) - hits[id(with_cities[0])]
    if missing:
        raise ValueError(
            f"Oslo Area A polygon does not contain {sorted(missing)}. "
            "The source geometry has changed; re-verify before relabelling."
        )

    for f in without:
        f["properties"]["oslo_class"] = "B"
        f["properties"]["class_corrected"] = (
            "Source labelled this polygon 'A'. Reassigned to Area B: it contains "
            "none of the Oslo II Area A city centres, which all fall inside the "
            "other 'A' polygon. See docs/corrections.md."
        )


def load_oslo_areas() -> list[dict[str, Any]]:
    r = resource("oslo_areas")
    path = download(r.url, r.filename)
    records, crs = read_zipped_shapefile(str(path), r.shapefile_base, r.source_crs)
    ev = Evidence(
        source_id="ocha_opt",
        title="State of Palestine - Oslo Agreement in the West Bank",
        url=SOURCES["ocha_opt"].url,
        document_date="2019-07-22",
        retrieved=retrieved_date(r.filename),
    )
    out = []
    for rec in records:
        cls = str(rec["properties"].get("CLASS", "")).strip()
        out.append(
            {
                "geometry": rec["geometry"],
                "properties": {
                    "oslo_class": cls,
                    "source_crs": crs,
                    "evidence": [ev.to_dict()],
                },
            }
        )
    _split_mislabelled_area_b(out)
    return out


def east_jerusalem_polygon(oslo: list[dict[str, Any]]) -> dict[str, Any] | None:
    for f in oslo:
        if f["properties"]["oslo_class"] == EJ_OSLO_CLASS:
            return f["geometry"]
    return None


def load_settlements(ej_polygon: dict[str, Any] | None) -> list[Entity]:
    r = resource("settlements_builtup")
    path = download(r.url, r.filename)
    records, crs = read_zipped_shapefile(str(path), r.shapefile_base, r.source_crs)

    ev = Evidence(
        source_id="peacenow_via_hdx",
        title="State of Palestine Settlements (built-up areas)",
        url=SOURCES["peacenow_via_hdx"].url,
        document_date=SETTLEMENTS_OBSERVED,
        retrieved=retrieved_date(r.filename),
        note="Built-up footprint only. Municipal and regional council extents "
             "are not present in this dataset.",
    )

    # 24 of the 201 polygons have a blank Name. Ten of those share a GIS_ID with
    # a named polygon — they are additional parts of the same settlement, not
    # separate places. So group by GIS_ID and merge parts into one multipart
    # entity, recovering the name from whichever part carries it. Polygons with
    # neither a name nor a resolvable GIS_ID stay unnamed and are flagged for
    # manual identification rather than being dropped or invented.
    names_by_gid: dict[float, str] = {}
    for rec in records:
        gid = rec["properties"].get("GIS_ID")
        nm = str(rec["properties"].get("Name") or "").strip()
        if nm and gid not in (None, 0, 0.0):
            names_by_gid.setdefault(gid, nm)

    groups: dict[str, list[dict[str, Any]]] = {}
    for idx, rec in enumerate(records):
        props = rec["properties"]
        gid = props.get("GIS_ID")
        name = str(props.get("Name") or "").strip() or names_by_gid.get(gid, "")
        if gid not in (None, 0, 0.0):
            key = f"gid-{int(gid)}"
        elif name:
            key = f"name-{_slug(name)}"
        else:
            key = f"orphan-{idx}"
        groups.setdefault(key, []).append({**rec, "_name": name})

    entities: list[Entity] = []
    used_ids: set[str] = set()
    identifications = load_identifications()
    applied: list[str] = []
    refused: list[str] = []

    for key, parts in groups.items():
        name = next((p["_name"] for p in parts if p["_name"]), "")
        unnamed = not name
        display_name = name or f"Unidentified settlement ({key})"
        identification: dict[str, Any] | None = None

        entity_id = _slug(name) if name else key
        while entity_id in used_ids:
            entity_id = f"{entity_id}-2"
        used_ids.add(entity_id)

        polys: list[Any] = []
        for p in parts:
            g = p["geometry"]
            if g["type"] == "Polygon":
                polys.append(g["coordinates"])
            else:
                polys.extend(g["coordinates"])
        geom: dict[str, Any] = (
            {"type": "Polygon", "coordinates": polys[0]}
            if len(polys) == 1
            else {"type": "MultiPolygon", "coordinates": polys}
        )

        # Apply a curated identification only if its anchor still falls inside
        # this polygon. Verifying rather than trusting is the whole point.
        if unnamed and key in identifications:
            candidate = identifications[key]
            anchor = tuple(candidate["anchor"])
            if point_in_polygon(anchor, geom):
                identification = candidate
                display_name = candidate["name"]
                unnamed = False
                applied.append(f"{key} -> {candidate['name']}")
            else:
                refused.append(
                    f"{key} ({candidate['name']}): anchor no longer inside the polygon"
                )

        in_ej = bool(ej_polygon) and point_in_polygon(_centroid(geom), ej_polygon)

        # Geometry always cites OCHA. An identified name adds a second
        # citation rather than replacing the first — they are different claims
        # from different sources.
        part_ev = ev
        name_ev: Evidence | None = None
        if identification:
            name_ev = Evidence(
                source_id="wikidata",
                title=f"{identification['name']} (Wikidata {identification['wikidata']})",
                url=identification["wikidata_url"],
                document_date=identification.get("identified"),
                retrieved=identification.get("identified"),
                note=(
                    "Name not present in the OCHA/Peace Now source. "
                    f"{identification['method']}. Logged in docs/corrections.md."
                ),
            )
        elif unnamed:
            part_ev = Evidence(
                source_id=ev.source_id,
                title=ev.title,
                url=ev.url,
                document_date=ev.document_date,
                retrieved=ev.retrieved,
                note="Name field blank in the source dataset; requires manual "
                     "identification. Logged in docs/corrections.md.",
            )

        entities.append(
            Entity(
                entity_id=entity_id,
                entity_type=EntityType.EJ_SETTLEMENT if in_ej else EntityType.SETTLEMENT,
                names=Names(primary=display_name),
                extents=[
                    Extent(
                        extent_type=ExtentType.BUILT_UP,
                        geometry=geom,
                        source_crs=crs,
                        area_m2=geometry_area_m2(geom),
                        evidence=[part_ev],
                    )
                ],
                # Minimum defensible stage: a built-up footprint observed on this
                # date proves construction had started by then. No earlier stage
                # dates are asserted because this source does not carry them.
                stage_history=[
                    StageEvent(
                        stage=Stage.CONSTRUCTION_START,
                        valid_from=SETTLEMENTS_OBSERVED,
                        evidence=[part_ev],
                    )
                ],
                evidence=[part_ev] + ([name_ev] if name_ev else []),
            )
        )

    if applied:
        print(f"       applied {len(applied)} curated identifications")
    for r in refused:
        print(f"       REFUSED identification: {r}")

    return entities


def load_localities(oslo: list[dict[str, Any]]) -> list[Locality]:
    r = resource("communities")
    path = download(r.url, r.filename)
    records, crs = read_zipped_shapefile(str(path), r.shapefile_base, r.source_crs)

    ev = Evidence(
        source_id="ocha_opt",
        title="State of Palestine - Palestinian Communities in the West Bank and the Gaza Strip",
        url=SOURCES["ocha_opt"].url,
        document_date="2019-07-17",
        retrieved=retrieved_date(r.filename),
    )

    localities: list[Locality] = []
    for rec in records:
        p = rec["properties"]
        # Source data has "West Bsnk" as a literal typo — normalise, don't
        # propagate. Gaza is explicitly out of scope for this project.
        region = str(p.get("Region") or "").strip()
        if region.lower().startswith("gaza"):
            continue

        name = str(p.get("PCBS_NAME") or "").strip() or "Unnamed locality"
        arabic = str(p.get("NAME_ARB") or "").strip() or None
        pcode = str(p.get("PCODE") or "").strip()

        pops: list[dict[str, Any]] = []
        raw_pop = str(p.get("pop2017") or "").strip()
        # pop2017 is dirty: "NA", "with Ar Ram", "17230". Only keep real numbers,
        # but preserve the raw string so the panel can explain a missing value.
        if raw_pop.isdigit():
            pops.append({"year": 2017, "value": int(raw_pop), "source_id": "ocha_opt"})
        elif raw_pop and raw_pop.upper() != "NA":
            pops.append({"year": 2017, "value": None, "note": raw_pop, "source_id": "ocha_opt"})

        geom = rec["geometry"]
        oslo_area = None
        for f in oslo:
            if point_in_polygon(tuple(geom["coordinates"]), f["geometry"]):
                oslo_area = f["properties"]["oslo_class"]
                break

        localities.append(
            Locality(
                locality_id=pcode or _slug(name),
                names=Names(primary=name, arabic=arabic),
                geometry=geom,
                district=str(p.get("District") or "").strip() or None,
                in_east_jerusalem=str(p.get("EJ")).strip() == "1",
                population=pops,
                oslo_area=oslo_area or str(p.get("Oslo_Areas") or "").strip() or None,
                evidence=[ev],
            )
        )

    return localities


def _clean_label(value: Any) -> str | None:
    """Firing-zone names come through as mangled Hebrew or numeric codes.

    The shapefile's DBF is not UTF-8 and the codepage is unreliable, so names
    arrive as things like "309�'". A garbled label is worse than none — it
    looks like a data error to a reader and invites doubt about everything
    else — so anything containing replacement characters is dropped and the
    zone falls back to being identified by its signing date.
    """
    text = str(value or "").strip()
    if not text or "�" in text:
        return None
    if not any(c.isalnum() for c in text):
        return None
    return text


def load_firing_zones() -> list[dict[str, Any]]:
    """Israeli firing zones — closed military areas, ~18% of the West Bank.

    Every polygon carries the date its closure order was signed, which makes
    this the only OCHA layer besides the settlements that supports a dated
    claim. Treated as a mechanism of land loss in its own right rather than
    context, because a closure order removes access to land as surely as a
    settlement does.
    """
    r = resource("firing_zones")
    path = download(r.url, r.filename)
    records, crs = read_zipped_shapefile(str(path), r.shapefile_base, r.source_crs)

    out = []
    for rec in records:
        props = rec["properties"]
        # pyshp returns DBF dates as datetime.date, which json cannot serialise.
        signed = props.get("SIGN_DATE")
        signed_iso = signed.isoformat() if hasattr(signed, "isoformat") else None
        name = _clean_label(props.get("FIRE_NAME"))

        ev = Evidence(
            source_id="ocha_opt",
            title="State of Palestine - Israeli Firing Zones (Closed Military Areas)",
            url=SOURCES["ocha_opt"].url,
            document_date=signed_iso,
            retrieved=retrieved_date(r.filename),
            note="Date is the date the closure order was signed.",
        )
        out.append(
            {
                "geometry": rec["geometry"],
                "properties": {
                    "zone_name": name,
                    "name": f"Firing zone {name}" if name else "Firing zone (unnumbered)",
                    "signed_date": signed_iso,
                    "mechanism": "closed_military_area",
                    "area_m2": geometry_area_m2(rec["geometry"]),
                    "source_crs": crs,
                    "evidence": [ev.to_dict()],
                },
            }
        )
    return out


def load_village_boundaries() -> list[dict[str, Any]]:
    """Palestinian village boundaries — areal extent, not just a point."""
    r = resource("village_boundaries")
    path = download(r.url, r.filename)
    records, crs = read_zipped_shapefile(str(path), r.shapefile_base, r.source_crs)

    ev = Evidence(
        source_id="ocha_opt",
        title="State of Palestine - Village boundary in the West Bank",
        url=SOURCES["ocha_opt"].url,
        document_date="2019-07-24",
        retrieved=retrieved_date(r.filename),
    )
    return [
        {
            "geometry": rec["geometry"],
            "properties": {
                "name": _clean_label(rec["properties"].get("VNAME")) or "Unnamed village",
                "area_m2": geometry_area_m2(rec["geometry"]),
                "source_crs": crs,
                "evidence": [ev.to_dict()],
            },
        }
        for rec in records
    ]


def load_barrier() -> list[dict[str, Any]]:
    r = resource("barrier")
    path = download(r.url, r.filename)
    try:
        records, crs = read_zipped_shapefile(str(path), r.shapefile_base, r.source_crs)
    except FileNotFoundError:
        # Barrier archives have shifted member names between HDX revisions.
        return []
    ev = Evidence(
        source_id="ocha_opt",
        title="West Bank Separation Barrier (January 2018 alignment)",
        url=SOURCES["ocha_opt"].url,
        document_date="2018-01-01",
        retrieved=retrieved_date(r.filename),
    )
    return [
        {
            "geometry": rec["geometry"],
            "properties": {**rec["properties"], "source_crs": crs, "evidence": [ev.to_dict()]},
        }
        for rec in records
    ]
