"""Territory occupied by Israel beyond Palestine.

This layer exists because the mechanism is adjacent and the people are not.
The Golan Heights is occupied **Syrian** territory and Shebaa Farms is claimed
by **Lebanon**; Syrians and Lebanese are not Palestinians, and folding their
land into a Palestinian total would be the same error non-negotiable 8 already
forbids between 1948 and post-1967, and non-negotiable 11 forbids between
destruction and dispossession.

So it ships as its own layer, in its own styling, with every feature naming who
administers it and who claims it — and a test asserts it never reaches the land
figures.

Three features, from Natural Earth's public-domain disputed-areas set:

  * **Golan Heights** — "Admin. By Israel; Claimed by Syria". Occupied in 1967,
    annexed by Israel's Golan Heights Law in 1981. UN Security Council
    Resolution 497 (17 December 1981) held that annexation "null and void and
    without international legal effect" — the same finding, in the same words,
    that Resolution 478 (1980) made about East Jerusalem.
  * **Shebaa Farms** — "Admin. By Israel; Claimed by Lebanon".
  * **UNDOF Zone** — the UN-patrolled area of separation established by the
    1974 Disengagement Agreement. Included as context, not as occupied land:
    it is a ceasefire arrangement, not a claim.

The boundaries are generalised at 1:10m. That is fine for showing *that* a
territory is occupied and roughly where; it is not a survey boundary, the
features say so, and no area figure computed from them is published.
"""

from __future__ import annotations

import json
from typing import Any

from ..fetch import download, retrieved_date
from ..schema import Evidence
from ..sources import SOURCES, resource

WANTED = {
    "Golan Heights": {
        "administered_by": "Israel",
        "claimed_by": "Syria",
        "occupied_since": "1967",
        "status": "occupied",
        "legal_note": "Occupied 1967; annexed by Israel's Golan Heights Law 1981. "
                      "UN Security Council Resolution 497 (17 December 1981) held "
                      "the annexation null and void and without international "
                      "legal effect.",
    },
    "Shebaa Farms": {
        "administered_by": "Israel",
        "claimed_by": "Lebanon",
        "occupied_since": "1967",
        "status": "occupied",
        "legal_note": "Administered by Israel and claimed by Lebanon. Its status "
                      "was left unresolved by the UN's confirmation of Israeli "
                      "withdrawal from Lebanon in 2000.",
    },
    "UNDOF Zone": {
        "administered_by": "United Nations (UNDOF)",
        "claimed_by": None,
        "occupied_since": None,
        "status": "ceasefire_zone",
        "legal_note": "UN-patrolled area of separation under the 1974 "
                      "Disengagement Agreement. Context, not occupied land — a "
                      "ceasefire arrangement rather than a claim.",
    },
}

GENERALISED = (
    "Boundary generalised at 1:10m — indicative extent, not a survey line. No "
    "area figure is computed from it."
)

NOT_PALESTINIAN = (
    "Not Palestinian territory. Shown because the mechanism is adjacent, and "
    "never counted in any Palestinian land-loss figure."
)


def load() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    r = resource("ne_disputed_areas")
    path = download(r.url, r.filename)
    doc = json.loads(path.read_text(encoding="utf-8"))

    ev = Evidence(
        source_id="natural_earth",
        title="Natural Earth 1:10m — Admin 0 disputed areas",
        url=SOURCES["natural_earth"].url,
        document_date=None,
        retrieved=retrieved_date(r.filename),
        note=GENERALISED,
    )

    out, found = [], []
    for f in doc.get("features", []):
        name = (f.get("properties") or {}).get("NAME")
        if name not in WANTED:
            continue
        meta = WANTED[name]
        found.append(name)
        out.append(
            {
                "geometry": f["geometry"],
                "properties": {
                    "name": name,
                    **{k: v for k, v in meta.items() if v is not None},
                    "source_note": (f.get("properties") or {}).get("NOTE_BRK"),
                    "not_palestinian": True,
                    "disclaimer": NOT_PALESTINIAN,
                    "generalised": GENERALISED,
                    "source_crs": "EPSG:4326",
                    "evidence": [ev.to_dict()],
                },
            }
        )

    missing = sorted(set(WANTED) - set(found))
    if missing:
        raise ValueError(
            f"Natural Earth no longer carries {missing}; re-verify before shipping."
        )
    return out, {"features": len(out), "names": sorted(found)}
