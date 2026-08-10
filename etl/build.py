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
from .adapters import historical
from .adapters import ocha
from .fetch import PROCESSED, write_json
from .geo import bounds_of
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
)
from .sources import manifest

# Default map view: the East Jerusalem pilot area.
EJ_VIEW = {"center": [35.2310, 31.7800], "zoom": 11.2}


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

    # --- settlement extents, one FeatureCollection per extent definition ---
    extent_counts: dict[str, int] = {}
    for extent_type in ExtentType:
        feats = []
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
        write_json(
            PROCESSED / f"settlements_{extent_type.value}.geojson",
            feature_collection(
                feats,
                extent_type=extent_type.value,
                definition=EXTENT_DEFINITIONS[extent_type],
                count=len(feats),
            ),
        )
        status = "EMPTY — source not yet available" if not feats else f"{len(feats)} features"
        print(f"       settlements_{extent_type.value}.geojson: {status}")

    write_json(
        PROCESSED / "localities.geojson",
        feature_collection([feature(l.geometry, l.properties()) for l in localities]),
    )
    write_json(
        PROCESSED / "oslo_areas.geojson",
        feature_collection([feature(f["geometry"], f["properties"]) for f in oslo]),
    )
    if barrier:
        write_json(
            PROCESSED / "barrier.geojson",
            feature_collection([feature(f["geometry"], f["properties"]) for f in barrier]),
        )

    # --- historical: the "what was there before" side of land loss ---
    print("[hist] Palestine Open Maps localities")
    hist = historical.load_localities()
    depop = [l for l in hist if l.depopulated_1948]
    print(f"       {len(hist)} historic localities; {len(depop)} depopulated 1947-50")
    write_json(
        PROCESSED / "historic_localities.geojson",
        feature_collection(
            [feature(l.geometry, l.properties()) for l in hist],
            source="Palestine Open Maps",
            total=len(hist),
            depopulated_1948=len(depop),
            licence_note="Publisher declares no licence; permission request pending.",
        ),
    )

    print("[hist] Mandatory Palestine boundary")
    mandate = historical.load_mandate_boundary()
    if mandate:
        write_json(
            PROCESSED / "mandate_palestine.geojson",
            feature_collection([feature(mandate["geometry"], mandate["properties"])]),
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
        "historic_localities": len(hist),
        "depopulated_1948": len(depop),
        "mandate_boundary": bool(mandate),
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

    write_json(
        PROCESSED / "incidents.geojson",
        feature_collection(
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
            **manifest(),
        },
    )
    print("[meta] meta.json written")


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
