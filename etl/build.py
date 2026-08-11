"""Build orchestrator.

    python -m etl.build all          # fetch + build everything
    python -m etl.build base         # OCHA layers only (no network crawl)
    python -m etl.build incidents    # Al-Haq crawl only
    python -m etl.build refresh-urls # re-resolve HDX resource URLs from CKAN

Outputs land in web/public/data/ as plain GeoJSON. PMTiles conversion is a
later step (see docs/architecture.md) — at pilot volumes, GeoJSON is smaller
than the tooling needed to tile it.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import date

from .adapters import alhaq as alhaq_adapter
from .adapters import btselem
from .adapters import historical
from .adapters import ocha
from .adapters import ocha_violence
from .adapters import poha as poha_adapter
from .fetch import PROCESSED, write_json
from .geo import bounds_of, count_vertices, simplify_geometry
from .merge import merge_localities
from .search import build_index
from .schema import (
    EXTENT_DEFINITIONS,
    MECHANISM_LABELS,
    MECHANISM_NOTES,
    Confidence,
    EntityType,
    ExtentType,
    LossMechanism,
    RecordType,
    Stage,
    feature,
    feature_collection,
    normalise_features,
)
from .sources import manifest

# Default map view: the East Jerusalem pilot area.
EJ_VIEW = {"center": [35.2310, 31.7800], "zoom": 11.2}

# Simplification tolerance in degrees, for context layers only. ~0.0001 deg is
# roughly 10 m at this latitude — invisible at the zooms these layers are read
# at, and the difference between a 3 MB Oslo layer and a usable one.
# Measurement layers (settlement extents) are never simplified, and areas are
# computed from source geometry before any simplification happens.
CONTEXT_TOLERANCE = 0.0001

# Extent layers are measurements, so they get a far finer tolerance — about 5 m,
# below the accuracy of the source boundaries themselves and sub-pixel until
# zoom 18. Reported areas are unaffected: they are computed from source geometry
# before this runs and stored on the feature, never recomputed from what is drawn.
MEASUREMENT_TOLERANCE = 0.00005

# Shared citation table, published once in meta.json rather than repeated on
# every feature. Populated as layers are written.
EVIDENCE_TABLE: dict[str, dict] = {}


def write_layer(name: str, feats: list[dict], **meta) -> None:
    """Normalise, then write. Every layer goes through here."""
    packed = normalise_features(feats, EVIDENCE_TABLE)
    write_json(PROCESSED / name, feature_collection(packed, **meta))


def _simplify_features(feats: list[dict], tol: float = CONTEXT_TOLERANCE) -> list[dict]:
    before = count_vertices(feats)
    out = [
        {**f, "geometry": simplify_geometry(f["geometry"], tol)} if f.get("geometry") else f
        for f in feats
    ]
    after = count_vertices(out)
    if before:
        print(f"       simplified {before:,} -> {after:,} vertices "
              f"({100 - after * 100 // before}% smaller)")
    return out


def build_base() -> dict:
    print("[base] Oslo areas")
    oslo = ocha.load_oslo_areas()
    ej_poly = ocha.east_jerusalem_polygon(oslo)
    print(f"       {len(oslo)} polygons; EJ polygon: {'found' if ej_poly else 'MISSING'}")

    print("[base] settlements (built-up)")
    entities = ocha.load_settlements(ej_poly)
    ej_count = sum(1 for e in entities if e.entity_type is EntityType.EJ_SETTLEMENT)
    print(f"       {len(entities)} settlements ({ej_count} in East Jerusalem)")

    print("[base] Palestinian localities")
    localities = ocha.load_localities(oslo)
    ej_locs = sum(1 for l in localities if l.in_east_jerusalem)
    print(f"       {len(localities)} localities ({ej_locs} in East Jerusalem)")

    print("[base] Barrier")
    barrier = ocha.load_barrier()
    print(f"       {len(barrier)} features")

    print("[base] firing zones (closed military areas)")
    firing = ocha.load_firing_zones()
    firing_km2 = sum(f["properties"]["area_m2"] or 0 for f in firing) / 1e6
    dated = sum(1 for f in firing if f["properties"]["signed_date"])
    print(f"       {len(firing)} zones, {firing_km2:,.0f} km2, {dated} with a signed order date")

    print("[base] village boundaries")
    villages = ocha.load_village_boundaries()
    print(f"       {len(villages)} polygons")

    print("[bts]  B'Tselem settlement boundaries and outposts")
    bts_entities, bts_stats = btselem.load_boundaries()
    print(f"       {bts_stats['total']} entities: "
          + ", ".join(f"{v} {k}" for k, v in bts_stats["by_type"].items() if v))
    if bts_stats["unknown_types"]:
        print(f"       unmapped Type values: {bts_stats['unknown_types']}")

    print("[bts]  B'Tselem municipal boundaries")
    municipal, muni_stats = btselem.load_municipal(entities + bts_entities)
    print(f"       {muni_stats['total']} polygons | {muni_stats['named']} named by "
          f"containment, {muni_stats['unnamed']} unnamed "
          f"({muni_stats['ambiguous']} ambiguous)")
    if muni_stats["implausible_dates_rejected"]:
        print(f"       rejected {muni_stats['implausible_dates_rejected']} implausible DATE_ values")

    # B'Tselem entities join the settlement inventory, carrying the outpost track.
    entities = entities + bts_entities

    # --- settlement extents, one FeatureCollection per extent definition ---
    extent_counts: dict[str, int] = {}
    for extent_type in ExtentType:
        feats = []
        if extent_type is ExtentType.MUNICIPAL:
            feats = [feature(m["geometry"], m["properties"]) for m in municipal]
        for e in entities:
            for ext in e.extents:
                if ext.extent_type is not extent_type:
                    continue
                props = e.properties()
                props["extent_type"] = extent_type.value
                props["area_m2"] = ext.area_m2
                props["source_crs"] = ext.source_crs
                props["in_east_jerusalem"] = e.entity_type is EntityType.EJ_SETTLEMENT
                feats.append(feature(ext.geometry, props))
        extent_counts[extent_type.value] = len(feats)
        write_layer(
            f"settlements_{extent_type.value}.geojson",
            _simplify_features(feats, MEASUREMENT_TOLERANCE) if feats else feats,
            extent_type=extent_type.value,
            definition=EXTENT_DEFINITIONS[extent_type],
            count=len(feats),
        )
        status = "EMPTY — source not yet available" if not feats else f"{len(feats)} features"
        print(f"       settlements_{extent_type.value}.geojson: {status}")

    # Localities are written after the historical set is loaded, so the two
    # overlapping sources can be reconciled into one layer. See the write below.

    print("[base] oslo_areas.geojson")
    write_layer(
        "oslo_areas.geojson",
        _simplify_features([feature(f["geometry"], f["properties"]) for f in oslo]),
    )
    if barrier:
        print("[base] barrier.geojson")
        write_layer(
            "barrier.geojson",
            _simplify_features([feature(f["geometry"], f["properties"]) for f in barrier]),
        )

    print("[base] firing_zones.geojson")
    write_layer(
        "firing_zones.geojson",
        _simplify_features([feature(f["geometry"], f["properties"]) for f in firing]),
        mechanism="closed_military_area",
        count=len(firing),
        total_km2=round(firing_km2, 1),
        note="Israeli firing zones (closed military areas). Each polygon "
             "carries the date its closure order was signed.",
    )

    print("[base] village_boundaries.geojson")
    write_layer(
        "village_boundaries.geojson",
        _simplify_features([feature(f["geometry"], f["properties"]) for f in villages]),
    )

    print("[base] resource destruction (Masafer Yatta)")
    from .adapters.alhaq import Gazetteer
    gaz = Gazetteer(localities)
    resource_feats, resource_stats = ocha_violence.load_resource_destruction(gaz)
    print(f"       {resource_stats['total_records']} records -> "
          f"{resource_stats['localities_plotted']} localities plotted, "
          f"{resource_stats['localities_withheld']} withheld "
          f"({resource_stats['records_withheld']} records)")
    write_layer(
        "resource_destruction.geojson",
        [feature(f["geometry"], f["properties"]) for f in resource_feats],
        source="OCHA field-based monitoring, Masafer Yatta",
        coverage="Masafer Yatta (South Hebron Hills) only, 2025 only",
        **{k: v for k, v in resource_stats.items() if k != "withheld_detail"},
        withheld_detail=resource_stats["withheld_detail"],
    )

    # --- historical: the "what was there before" side of land loss ---
    print("[hist] Palestine Open Maps localities")
    hist = historical.load_localities()
    print(f"       {len(hist)} historic localities loaded")

    print("[poha] Palestinian Oral History Archive")
    interviews = poha_adapter.load_oral_histories()
    attached = 0
    for loc in hist:
        found = interviews.get(loc.slug or "")
        if found:
            loc.oral_histories = found
            attached += 1
    print(f"       {sum(len(v) for v in interviews.values())} interviews across "
          f"{len(interviews)} villages; attached to {attached} localities")

    print("[merge] reconciling the two locality sources")
    localities, merge_stats = merge_localities(localities, hist)
    depop = [l for l in localities if l.depopulated_1948]
    print(f"        {merge_stats['current_records']} current + "
          f"{merge_stats['historic_records']} historic -> "
          f"{merge_stats['output_localities']} localities "
          f"({merge_stats['merged_pairs']} merged)")
    print(f"        withheld {merge_stats['withheld_coordinate_conflicts']} records "
          f"sharing coordinates with a differently-named locality")
    if merge_stats["same_name_but_too_far_to_merge"]:
        print(f"        {merge_stats['same_name_but_too_far_to_merge']} same-name pairs "
              f"too far apart to merge; left separate")
    print(f"        {len(depop)} depopulated 1947-50")

    write_layer(
        "localities.geojson",
        [feature(l.geometry, l.properties()) for l in localities],
        sources=["UN OCHA oPt", "Palestine Open Maps"],
        total=len(localities),
        merged_pairs=merge_stats["merged_pairs"],
        depopulated_1948=len(depop),
        withheld_coordinate_conflicts=merge_stats["withheld_coordinate_conflicts"],
        note=(
            "One locality per place. Where OCHA and Palestine Open Maps both "
            "recorded a locality, the records are merged and both are cited. "
            "Records whose coordinates collide with a differently-named locality "
            "are withheld rather than plotted."
        ),
    )
    print("[search] name index")
    index = build_index(localities, entities)
    write_json(PROCESSED / "search_index.json", index)
    scripts = {
        "arabic": sum(1 for e in index if e.get("a")),
        "hebrew": sum(1 for e in index if e.get("h")),
    }
    print(f"        {len(index)} entries | {scripts['arabic']} with Arabic, "
          f"{scripts['hebrew']} with Hebrew")

    write_json(
        PROCESSED / "oral_histories.json",
        {
            "source": "Palestinian Oral History Archive, American University of Beirut Libraries",
            "licence": "CC BY-NC-ND 4.0",
            "note": "Metadata and links only. The archive's descriptions and indexed "
                    "contents are not reproduced; each interview links to AUB Libraries.",
            "localities": {
                l.locality_id: l.oral_histories for l in localities if l.oral_histories
            },
        },
    )
    write_json(
        PROCESSED / "locality_conflicts.json",
        {
            "count": merge_stats["withheld_coordinate_conflicts"],
            "note": "Withheld: these sit on the exact coordinates of a "
                    "differently-named locality, so at least one position is wrong.",
            "records": merge_stats["conflict_detail"],
            "same_name_but_too_far_to_merge": merge_stats["ambiguous_detail"],
        },
    )

    print("[hist] Mandatory Palestine boundary")
    mandate = historical.load_mandate_boundary()
    if mandate:
        write_layer(
            "mandate_palestine.geojson",
            [feature(mandate["geometry"], mandate["properties"])],
        )
        print("       boundary written")
    else:
        print("       NOT FOUND in source — layer omitted")

    built = [f for f in (PROCESSED / "settlements_built_up.geojson",) if f.exists()]
    all_feats = json.loads(built[0].read_text(encoding="utf-8"))["features"] if built else []

    return {
        "localities": localities,
        "entity_count": len(entities),
        "ej_entity_count": ej_count,
        "locality_count": len(localities),
        "extent_counts": extent_counts,
        "barrier_features": len(barrier),
        "firing_zones": len(firing),
        "firing_zones_km2": round(firing_km2, 1),
        "village_boundaries": len(villages),
        "locality_merge": {k: v for k, v in merge_stats.items() if not k.endswith("_detail")},
        "depopulated_1948": len(depop),
        "mandate_boundary": bool(mandate),
        "btselem_entities": bts_stats,
        "municipal_stats": muni_stats,
        "bounds": bounds_of(all_feats),
    }


def build_incidents(localities) -> dict:
    print("[incidents] building gazetteer")
    gaz = alhaq_adapter.Gazetteer(localities)
    print(f"            {len(gaz.by_norm)} name variants indexed")

    incidents = alhaq_adapter.build_incidents(gaz)
    counts = Counter(i.confidence.value for i in incidents)
    type_counts = Counter(i.record_type.value for i in incidents)
    renderable = [i for i in incidents if i.renderable]
    periodic = [i for i in incidents if i.record_type is RecordType.PERIODIC_REPORT]

    write_json(
        PROCESSED / "documents.json",
        {
            "note": "Al-Haq periodic reports. Territory-wide coverage — listed "
                    "and linked, deliberately not plotted.",
            "count": len(periodic),
            "records": [
                {"title": i.title, "date": i.date, "url": i.url} for i in periodic
            ],
        },
    )

    write_layer(
        "incidents.geojson",
        [feature(i.geometry, i.properties()) for i in renderable],
        source="Al-Haq monitoring and documentation",
        total_records=len(incidents),
        rendered=len(renderable),
        withheld=len(incidents) - len(renderable),
        confidence_breakdown=dict(counts),
        note=(
            "Records that could not be resolved to exactly one locality are "
            "retained in incidents_unplaced.json but are not drawn on the map."
        ),
    )
    write_json(
        PROCESSED / "incidents_unplaced.json",
        {
            "count": len(incidents) - len(renderable),
            "records": [i.properties() for i in incidents if not i.renderable],
        },
    )

    print(f"            {len(incidents)} records; {len(renderable)} plotted, "
          f"{len(incidents) - len(renderable)} withheld")
    print(f"            confidence: {dict(counts)}")
    print(f"            types: {dict(type_counts)}")
    return {
        "incident_total": len(incidents),
        "incident_rendered": len(renderable),
        "incident_withheld": len(incidents) - len(renderable),
        "incident_confidence": dict(counts),
        "incident_types": dict(type_counts),
        "periodic_reports": len(periodic),
    }


def write_meta(stats: dict) -> None:
    write_json(
        PROCESSED / "meta.json",
        {
            "built": date.today().isoformat(),
            "project": "Palestinian Land Loss",
            "pilot_area": "East Jerusalem",
            "view": EJ_VIEW,
            "bounds": stats.get("bounds"),
            "stages": [
                {"id": int(s), "label": s.label} for s in Stage
            ],
            "extent_definitions": {
                k.value: v for k, v in EXTENT_DEFINITIONS.items()
            },
            "mechanisms": [
                {
                    "id": m.value,
                    "label": MECHANISM_LABELS[m],
                    "note": MECHANISM_NOTES.get(m),
                }
                for m in LossMechanism
            ],
            "entity_types": [t.value for t in EntityType],
            "confidence_levels": [c.value for c in Confidence],
            "stats": {k: v for k, v in stats.items() if k != "localities"},
            # Citations, deduplicated across every layer. Features carry
            # `evidence_ref` ids that resolve here.
            "evidence": EVIDENCE_TABLE,
            **manifest(),
        },
    )
    print(f"[meta] meta.json written ({len(EVIDENCE_TABLE)} distinct citations)")


def main(argv: list[str]) -> int:
    cmd = argv[1] if len(argv) > 1 else "all"
    stats: dict = {}

    if cmd in ("all", "base"):
        stats.update(build_base())

    if cmd in ("all", "incidents"):
        if "localities" not in stats:
            base = build_base()
            stats.update(base)
        stats.update(build_incidents(stats["localities"]))

    if cmd == "refresh-urls":
        return refresh_urls()

    write_meta(stats)
    print("\nDone. Serve with:  python -m http.server -d web 8000")
    return 0


def refresh_urls() -> int:
    """Re-resolve HDX download URLs from the CKAN API."""
    import requests

    from .fetch import USER_AGENT

    resp = requests.get(
        "https://data.humdata.org/api/3/action/package_search",
        params={"q": "organization:ocha-opt", "rows": 100},
        headers={"User-Agent": USER_AGENT},
        timeout=60,
    )
    resp.raise_for_status()
    for pkg in resp.json()["result"]["results"]:
        for res in pkg.get("resources", []):
            print(f"{pkg['name']:60s} {res['format']:12s} {res['url']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
