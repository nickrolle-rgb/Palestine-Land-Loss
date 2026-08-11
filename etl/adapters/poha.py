"""Palestinian Oral History Archive — testimony linked to depopulated villages.

POHA is held by the American University of Beirut Libraries and indexed by
Palestine Open Maps, whose repository carries one file per village keyed by the
same slug their locality database uses. That makes the join exact rather than
fuzzy: no name matching, no proximity, no guessing.

What this adds is the thing a dot on a map cannot carry. A depopulated locality
becomes a place where named people, born there before 1948, recorded what it was
like — and the map links out to them in their own voice.

**Licence discipline.** POHA is CC BY-NC-ND 4.0: attribution, non-commercial, no
derivatives. This project stores an interview's title, year, duration, language
and record URL, and nothing else. The archive's descriptions and its indexed
contents are its own editorial work and are not reproduced here; every interview
links back to AUB Libraries.
"""

from __future__ import annotations

import json
from typing import Any

from ..fetch import RAW, get, write_json

LISTING = "https://api.github.com/repos/palopenmaps/pom-data/contents/raw-data/poha"
RAW_BASE = "https://raw.githubusercontent.com/palopenmaps/pom-data/main/raw-data/poha"
RECORD_URL = "https://libraries.aub.edu.lb/poha/Record/{interview_id}"

CACHE = RAW / "poha.json"


def _fetch_all() -> dict[str, list[dict[str, Any]]]:
    """One request per village file. Cached, because it is 133 of them."""
    listing = get(LISTING, throttle=False).json()
    slugs = [
        entry["name"][:-5]
        for entry in listing
        if entry["type"] == "file" and entry["name"].endswith(".json")
    ]

    out: dict[str, list[dict[str, Any]]] = {}
    for i, slug in enumerate(slugs, 1):
        try:
            # GitHub's raw CDN, not a small publisher's server, so no throttle.
            records = get(f"{RAW_BASE}/{slug}.json", throttle=False).json()
        except Exception as exc:  # noqa: BLE001
            print(f"       ! {slug}: {exc}")
            continue
        out[slug] = records
        if i % 40 == 0:
            print(f"       {i}/{len(slugs)} village files")
    return out


def load_oral_histories(*, refresh: bool = False) -> dict[str, list[dict[str, Any]]]:
    """Return slug -> list of interview metadata. Metadata only, never content."""
    if CACHE.exists() and not refresh:
        raw = json.loads(CACHE.read_text(encoding="utf-8"))
    else:
        raw = _fetch_all()
        write_json(CACHE, raw)

    indexed: dict[str, list[dict[str, Any]]] = {}
    for slug, records in raw.items():
        interviews = []
        for r in records:
            interview_id = r.get("interview_id")
            if not interview_id:
                continue
            interviews.append(
                {
                    "title": (r.get("name_en") or "").strip() or "Untitled interview",
                    "title_ar": (r.get("name_ar") or "").strip() or None,
                    "year": r.get("year"),
                    "duration": r.get("duration"),
                    "language": r.get("language"),
                    "format": r.get("format"),
                    "collection": r.get("collection"),
                    "url": RECORD_URL.format(interview_id=interview_id),
                }
            )
        if interviews:
            indexed[slug] = interviews
    return indexed
