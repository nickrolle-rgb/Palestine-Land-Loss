"""IDF forced displacement orders, archived by Gaza Maps.

Every entry here begins as a post by the Israeli military's own spokesman
ordering people out of numbered blocks. Gaza Maps archive the post, reconstruct
the order against the IDF's published "Swords of Iron" map, and compute the area
in WGS84 — publishing their method rather than asserting a result. That is a
derivation from a primary record, and it is why this source is here and a
commercial aggregator's map is not.

**The one thing that must never be done with this data is add it up.** The 154
orders sum to about 3,056 km² against a Gaza Strip of roughly 365 km². Orders
overlap, repeat over the same blocks, and are reissued; the sum is a measure of
how often people have been ordered to move, not of how much land exists. A
displacement order is also not a transfer of ownership — non-negotiable 11's
logic again. Nothing here enters any land-loss figure, and a test enforces it.

What it does give, honestly: a dated chronology of how often and how widely
people have been ordered to leave, with every entry resolving to the order that
caused it.

No geometry. The orders identify numbered population blocks, not polygons, and
this project does not own a block gazetteer — so nothing is plotted.
"""

from __future__ import annotations

import json
from typing import Any

from ..fetch import download, retrieved_date
from ..schema import Evidence
from ..sources import SOURCES, resource


def _f(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def load_orders() -> tuple[dict[str, Any], dict[str, Any]]:
    r = resource("displacement_orders")
    path = download(r.url, r.filename)
    records = json.loads(path.read_text(encoding="utf-8"))

    ev = Evidence(
        source_id="databases_for_palestine",
        title="Gaza Maps — IDF forced displacement orders",
        url="https://gazamaps.com/methodology",
        document_date=None,
        retrieved=retrieved_date(r.filename),
        note="Each order links to the IDF post that issued it. Areas are per "
             "order and overlap; they are never summed.",
    )

    by_month: dict[str, dict[str, float]] = {}
    orders = []
    for rec in records:
        date = str(rec.get("date") or "")[:10]
        if not date:
            continue
        area = _f(rec.get("area_sq_km_displacement"))
        month = date[:7]
        bucket = by_month.setdefault(month, {"orders": 0, "largest_km2": 0.0})
        bucket["orders"] += 1
        bucket["largest_km2"] = max(bucket["largest_km2"], area)
        orders.append({
            "date": date,
            "area_km2": round(area, 2),
            "idf_post": rec.get("source") or None,
            "archive": rec.get("link") or None,
        })

    orders.sort(key=lambda o: o["date"])
    payload = {
        "orders_total": len(orders),
        "first_date": orders[0]["date"] if orders else None,
        "last_date": orders[-1]["date"] if orders else None,
        "largest_single_order_km2": round(max((o["area_km2"] for o in orders), default=0), 2),
        "by_month": {m: {"orders": v["orders"],
                         "largest_km2": round(v["largest_km2"], 2)}
                     for m, v in sorted(by_month.items())},
        "orders": orders,
        "never_sum": (
            "Order areas overlap and repeat. They sum to far more than the Gaza "
            "Strip exists, because the figure counts how often people were ordered "
            "to move, not how much land there is."
        ),
        "evidence": [ev.to_dict()],
    }
    stats = {
        "orders": len(orders),
        "first_date": payload["first_date"],
        "last_date": payload["last_date"],
        "largest_single_order_km2": payload["largest_single_order_km2"],
    }
    return payload, stats
