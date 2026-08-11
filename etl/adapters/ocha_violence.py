"""Destruction of resource access — OCHA's Masafer Yatta violence monitoring.

Answers "what was destroyed, where, when": water tanks, wells and pipes;
farmland, crops and irrigation; livestock and animal shelters; homes; and other
property. Every record comes from OCHA field-based monitoring.

**Read the coverage limits before quoting anything from this layer.**

  * It covers **Masafer Yatta only** — 27 localities in the South Hebron Hills —
    not the West Bank. Absence from this layer means "not monitored here", never
    "did not happen".
  * It covers **2025 only**.
  * The source has no olive-grove or vineyard category. Its agricultural class is
    "farmland, crops, or irrigation systems", and that is what this layer says.
    Naming crops the source does not name would be an invention.

The West Bank-wide equivalent is OCHA's demolition and displacement database,
which is published solely as an embedded Power BI dashboard with no CSV or API.
Getting at it means asking OCHA — see docs/permissions/.

Records are aggregated to one point per locality rather than plotted as 2,904
coincident dots, since 27 places cannot legibly carry that many marks. The full
per-incident breakdown travels in the feature's properties.
"""

from __future__ import annotations

import csv
import io
from collections import Counter, defaultdict
from datetime import datetime
from typing import Any

from ..fetch import download, retrieved_date
from ..schema import Confidence, Evidence, Locality
from ..sources import SOURCES

CSV_URL = (
    "https://data.humdata.org/dataset/2b26b394-ca7a-407c-9886-873b23939d21/"
    "resource/d49c68c3-2aaa-4d4e-8026-d5d3ffc0c1e3/download/"
    "israeli-violence-masafer-yatta-west-bank-2025.csv"
)

# Resource categories, matched against the source's own wording. Conservative on
# purpose: a record that matches nothing is counted as uncategorised rather than
# swept into a bucket it does not belong in.
RESOURCE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "water": (
        "water", "well", "wells", "cistern", "irrigation", "water tank",
        "water pipe", "spring",
    ),
    "agriculture": (
        "farmland", "crop", "irrigation", "harvest", "tree", "olive",
        "vineyard", "grove", "plough", "grazing", "pasture",
    ),
    "livestock": (
        "livestock", "animal shelter", "chicken", "coop", "sheep", "goat",
        "dairy", "herd",
    ),
    "home": ("home", "house", "residential", "dwelling", "toilet", "tent"),
    "property": (
        "car", "vehicle", "tractor", "camera", "fence", "wall", "gate",
        "household", "solar", "generator", "equipment", "smartphone",
    ),
}

RESOURCE_LABELS = {
    "water": "Water access (tanks, wells, pipes, irrigation)",
    "agriculture": "Farmland, crops and irrigation",
    "livestock": "Livestock and animal shelters",
    "home": "Homes and dwellings",
    "property": "Vehicles, equipment and other property",
}


def _categorise(*fields: str) -> list[str]:
    text = " ".join(f.lower() for f in fields if f)
    return [
        cat for cat, words in RESOURCE_KEYWORDS.items()
        if any(w in text for w in words)
    ]


def _iso(date_str: str) -> str | None:
    """Source dates are DD/MM/YYYY."""
    try:
        return datetime.strptime(date_str.strip(), "%d/%m/%Y").date().isoformat()
    except (ValueError, AttributeError):
        return None


def load_resource_destruction(gazetteer) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Return (features, stats). Unmatched localities are withheld, not guessed."""
    path = download(CSV_URL, "masafer_yatta_violence_2025.csv")
    rows = list(
        csv.DictReader(
            io.StringIO(path.read_text(encoding="utf-8-sig", errors="replace")),
            delimiter=";",
        )
    )

    ev = Evidence(
        source_id="ocha_opt",
        title="Palestine: Violence affecting Palestinians in Masafer Yatta, West Bank",
        url="https://data.humdata.org/dataset/violence-masafer-yatta-west-bank",
        document_date="2026-04-08",
        retrieved=retrieved_date("masafer_yatta_violence_2025.csv"),
        note="OCHA field-based monitoring. Covers Masafer Yatta only, 2025 only.",
    )

    by_village: dict[str, list[dict[str, str]]] = defaultdict(list)
    for r in rows:
        village = (r.get("village") or "").strip()
        if village:
            by_village[village].append(r)

    features: list[dict[str, Any]] = []
    withheld: list[dict[str, Any]] = []

    for village, records in sorted(by_village.items()):
        # A dedicated village column, so exact matching is safe here in a way it
        # is not when scanning prose.
        candidates = gazetteer.match_exact(village)
        if len(candidates) != 1:
            withheld.append(
                {
                    "village": village,
                    "records": len(records),
                    "reason": "no single gazetteer match" if not candidates
                              else f"matches {len(candidates)} localities",
                }
            )
            continue

        loc: Locality = candidates[0]
        resources = Counter()
        uncategorised = 0
        for r in records:
            cats = _categorise(r.get("violation_type", ""), r.get("property_damage_type", ""))
            if cats:
                resources.update(cats)
            else:
                uncategorised += 1

        violations = Counter(
            (r.get("violation_type") or "").strip() for r in records if r.get("violation_type")
        )
        dates = sorted(d for d in (_iso(r.get("date", "")) for r in records) if d)

        features.append(
            {
                "geometry": loc.geometry,
                "properties": {
                    "locality_id": loc.locality_id,
                    "name": loc.names.primary,
                    "names": loc.names.to_dict(),
                    "district": loc.district,
                    "record_count": len(records),
                    "resource_counts": dict(resources),
                    "resource_labels": {k: RESOURCE_LABELS[k] for k in resources},
                    "uncategorised": uncategorised,
                    "violation_counts": dict(violations.most_common()),
                    "first_recorded": dates[0] if dates else None,
                    "last_recorded": dates[-1] if dates else None,
                    "coverage_note": "Masafer Yatta monitoring, 2025 only. "
                                     "Absence elsewhere means not monitored, not absent.",
                    "evidence": [ev.to_dict()],
                },
            }
        )

    stats = {
        "total_records": len(rows),
        "localities_plotted": len(features),
        "localities_withheld": len(withheld),
        "records_withheld": sum(w["records"] for w in withheld),
        "withheld_detail": withheld,
    }
    return features, stats
