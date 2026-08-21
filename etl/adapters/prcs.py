"""Palestine Red Crescent Society facilities, via OCHA on HDX.

PRCS is a different kind of source from anything else here. Everything else
records what was taken; this records what was built to respond — hospitals,
ambulance stations, clinics and branches, across 16 districts in both the West
Bank and Gaza.

It earns its place for two reasons. Medical infrastructure is protected under
international humanitarian law, so where it stands is a fact with legal weight.
And it is first-party: PRCS mapping PRCS, published by OCHA under CC BY.

Two limits, stated because they bound what the layer may claim:

  1. **Dated 2019-07-24.** These are the facilities as they stood before
     October 2023. The layer is not a claim that any of them still operates.
  2. **Locations, not incidents.** This says where PRCS infrastructure was. It
     says nothing about attacks on ambulances or crews — that needs PRCS
     directly or WHO's Surveillance System for Attacks on Health Care, and
     neither is in this pipeline yet (docs/data-gaps.md).

Source quirk: two records — the Abasan al Kabira and Qarara sub-stations, both
Khan Younis — carry `-DBL_MAX` in the shapefile and `nan` in the DBF, i.e. no
coordinates at all. They are withheld and counted rather than plotted, which is
non-negotiable 2. A point at -1.8e308 would render somewhere impossible, and a
point invented near its named town would be a guess.
"""

from __future__ import annotations

from typing import Any

from ..fetch import download, retrieved_date
from ..geo import read_zipped_shapefile
from ..schema import Evidence
from ..sources import SOURCES, resource

PRCS_CURRENCY = (
    "Facilities as at 2019-07-24. Predates October 2023; not a claim that a "
    "given facility still operates."
)


#: The source spells one category two ways, 9 times and once. Merged here so
#: the legend does not show a category twice; logged in docs/corrections.md.
TYPE_ALIASES = {"Sub Station": "Sub-Station"}


def _clean(v: Any) -> str | None:
    if v is None:
        return None
    t = str(v).strip()
    return t or None


def _usable(geometry: dict[str, Any] | None) -> bool:
    """Reject the shapefile null sentinel and anything off-planet."""
    if not geometry or geometry.get("type") != "Point":
        return False
    coords = geometry.get("coordinates") or []
    if len(coords) < 2:
        return False
    lon, lat = coords[0], coords[1]
    try:
        return abs(float(lon)) <= 180 and abs(float(lat)) <= 90
    except (TypeError, ValueError):
        return False


def load_facilities() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    r = resource("prcs_facilities")
    path = download(r.url, r.filename)
    records, crs = read_zipped_shapefile(str(path), r.shapefile_base, r.source_crs)
    ev = Evidence(
        source_id="ocha_opt",
        title="State of Palestine — PRCS (Palestine Red Crescent Society facilities)",
        url=SOURCES["ocha_opt"].url,
        document_date="2019-07-24",
        retrieved=retrieved_date(r.filename),
        note=PRCS_CURRENCY,
    )

    out: list[dict[str, Any]] = []
    withheld: list[str] = []
    by_type: dict[str, int] = {}

    for rec in records:
        props = rec["properties"]
        name = _clean(props.get("name")) or "Unnamed PRCS facility"
        if not _usable(rec["geometry"]):
            withheld.append(name)
            continue
        ftype = _clean(props.get("Type")) or "Unspecified"
        ftype = TYPE_ALIASES.get(ftype, ftype)
        by_type[ftype] = by_type.get(ftype, 0) + 1
        out.append(
            {
                "geometry": rec["geometry"],
                "properties": {
                    "name": name,
                    "facility_type": ftype,
                    "district": _clean(props.get("District")),
                    "operator": "Palestine Red Crescent Society",
                    "currency_note": PRCS_CURRENCY,
                    "source_crs": crs,
                    "evidence": [ev.to_dict()],
                },
            }
        )

    stats = {
        "total": len(records),
        "plotted": len(out),
        "withheld": len(withheld),
        "withheld_names": sorted(withheld),
        "by_type": dict(sorted(by_type.items(), key=lambda kv: -kv[1])),
    }
    return out, stats
