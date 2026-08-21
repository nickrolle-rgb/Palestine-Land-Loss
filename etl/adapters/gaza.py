"""Gaza Strip base geography, from OCHA's CC BY layers.

What these can and cannot tell us, stated plainly because it governs what the
map may claim:

  CAN: the administrative shape of the Gaza Strip — 33 municipal boundaries and
       149 named neighbourhood points, with PCODEs that join to OCHA's other
       Palestinian datasets.

  CANNOT: anything about the present. Both layers are dated **2019-07-18**.
       They describe Gaza as it was administratively defined before October
       2023, not as it is. A municipal boundary is not a claim that the
       municipality still stands.

That gap is the point rather than an embarrassment: publishing a pre-war
administrative map *and saying so* is honest, and it is the frame a damage
assessment has to be read against. It is also why the layer carries its
currency caveat in the UI rather than in a footnote — a reader who takes these
outlines for current Gaza has been misled by us, not by the source.

Source quirk: the neighbourhoods shapefile spells its community field
`Communithy`, and leaves district and community blank on 111 of its 149 points.
Both are normalised at ingest and logged in docs/corrections.md; neither is
inferred.
"""

from __future__ import annotations

from typing import Any

from ..fetch import download, retrieved_date
from ..geo import read_zipped_shapefile
from ..schema import Evidence
from ..sources import SOURCES, resource

#: Every Gaza feature carries this. The date is the source's own.
GAZA_CURRENCY = (
    "Administrative geography as at 2019-07-18. Predates October 2023 and "
    "describes how Gaza was defined, not what still stands."
)


def _evidence(key: str, title: str) -> Evidence:
    r = resource(key)
    return Evidence(
        source_id="ocha_opt",
        title=title,
        url=SOURCES["ocha_opt"].url,
        document_date="2019-07-18",
        retrieved=retrieved_date(r.filename),
        note=GAZA_CURRENCY,
    )


def _clean(value: Any) -> str | None:
    """Blank strings become absent. An empty field is not a value."""
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def load_municipal_boundaries() -> list[dict[str, Any]]:
    r = resource("gaza_municipal")
    path = download(r.url, r.filename)
    records, crs = read_zipped_shapefile(str(path), r.shapefile_base, r.source_crs)
    ev = _evidence("gaza_municipal", "State of Palestine — Gaza Strip Municipal Boundaries")

    out = []
    for rec in records:
        props = rec["properties"]
        out.append(
            {
                "geometry": rec["geometry"],
                "properties": {
                    "name": _clean(props.get("NAME")) or "Unnamed municipality",
                    "named": _clean(props.get("NAME")) is not None,
                    "region": "gaza",
                    "currency_note": GAZA_CURRENCY,
                    "source_crs": crs,
                    "evidence": [ev.to_dict()],
                },
            }
        )
    return out


def load_neighbourhoods() -> tuple[list[dict[str, Any]], dict[str, int]]:
    r = resource("gaza_neighbourhoods")
    path = download(r.url, r.filename)
    records, crs = read_zipped_shapefile(str(path), r.shapefile_base, r.source_crs)
    ev = _evidence("gaza_neighbourhoods", "State of Palestine — Gaza Strip Neighbourhoods")

    out: list[dict[str, Any]] = []
    stats = {"total": 0, "with_district": 0, "with_community": 0, "with_arabic": 0}
    for rec in records:
        props = rec["properties"]
        stats["total"] += 1
        # `Communithy` is the source's spelling. Normalised here, never
        # propagated — see docs/corrections.md.
        district = _clean(props.get("DISTRICT"))
        community = _clean(props.get("Communithy"))
        arabic = _clean(props.get("NameARB"))
        stats["with_district"] += bool(district)
        stats["with_community"] += bool(community)
        stats["with_arabic"] += bool(arabic)

        out.append(
            {
                "geometry": rec["geometry"],
                "properties": {
                    "name": _clean(props.get("Neighbourh")) or "Unnamed neighbourhood",
                    "arabic": arabic,
                    "district": district,
                    "community": community,
                    "pcode": _clean(props.get("PCODE")),
                    "region": "gaza",
                    "currency_note": GAZA_CURRENCY,
                    "source_crs": crs,
                    "evidence": [ev.to_dict()],
                },
            }
        )
    return out, stats
