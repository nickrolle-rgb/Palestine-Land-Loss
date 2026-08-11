"""Search index across every name a place is known by.

A locality on this map may carry four names: an English transliteration from
OCHA, a second transliteration from Palestine Open Maps, an Arabic name and a
Hebrew one. Someone looking for a village will type whichever they know, and
none of them match each other as strings.

So the index is built here rather than in the browser: one implementation of the
normalisation, applied to the data at build time, with the client only having to
normalise the query. The alternative — matching raw strings in JavaScript —
fails on the first search anyone actually tries.

Each script needs its own treatment:

  * **Arabic** — strip the tashkeel that appears in OCHA's names but not in
    ordinary typing (`خِرْبِة` is typed `خربة`), fold the alef forms
    (أ إ آ ٱ → ا), ta marbuta to ha, alef maqsura to ya, and drop tatweel.
    Without this, an Arabic search matches almost nothing, because the source
    names are vocalised and keyboards are not.
  * **Hebrew** — strip niqqud for the same reason.
  * **Latin** — reuse the transliteration folding already built for merging, so
    "Bayt" finds "Beit" and "Dayr" finds "Deir".
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Iterable

from .adapters.alhaq import normalise as normalise_latin
from .merge import _fold_transliteration
from .schema import Entity, Locality

# Tashkeel (harakat), superscript alef, and tatweel — decoration and elongation
# that appear in vocalised source names but almost never in typed queries.
_ARABIC_MARKS = re.compile(r"[ً-ٰٟـ]")
# Niqqud and cantillation.
_HEBREW_MARKS = re.compile(r"[֑-ׇ]")
_WS = re.compile(r"\s+")


def normalise_arabic(text: str) -> str:
    if not text:
        return ""
    t = _ARABIC_MARKS.sub("", text)
    for src, dst in (
        ("أ", "ا"), ("إ", "ا"), ("آ", "ا"), ("ٱ", "ا"),
        ("ة", "ه"), ("ى", "ي"), ("ؤ", "و"), ("ئ", "ي"),
    ):
        t = t.replace(src, dst)
    t = t.replace("ال", " ال")  # so "القدس" also matches a search for "قدس"
    return _WS.sub(" ", t).strip()


def normalise_hebrew(text: str) -> str:
    if not text:
        return ""
    return _WS.sub(" ", _HEBREW_MARKS.sub("", text)).strip()


def _keys(name: str | None) -> list[str]:
    """Every normalised form a name should be findable by."""
    if not name:
        return []
    out: list[str] = []
    stripped = "".join(
        c for c in unicodedata.normalize("NFKD", name) if not unicodedata.combining(c)
    )
    if any("؀" <= c <= "ۿ" for c in name):
        out.append(normalise_arabic(name))
    elif any("֐" <= c <= "׿" for c in name):
        out.append(normalise_hebrew(name))
    else:
        latin = normalise_latin(name)
        out.append(latin)
        folded = _fold_transliteration(latin)
        if folded != latin:
            out.append(folded)
        # Also keep the plain lowercase form so an exact spelling always hits,
        # even where normalisation is aggressive.
        out.append(stripped.lower().strip())
    return [k for k in out if k]


def _entry(
    ident: str,
    display: str,
    kind: str,
    coordinates: list[float],
    *,
    arabic: str | None = None,
    hebrew: str | None = None,
    district: str | None = None,
    variants: Iterable[str] = (),
    depopulated: bool = False,
) -> dict[str, Any]:
    keys: list[str] = []
    for name in (display, arabic, hebrew, *variants):
        keys.extend(_keys(name))

    entry = {
        "i": ident,
        "n": display,
        "k": " | ".join(dict.fromkeys(keys)),   # deduplicated, order preserved
        "c": [round(coordinates[0], 5), round(coordinates[1], 5)],
        "t": kind,
    }
    if arabic:
        entry["a"] = arabic
    if hebrew:
        entry["h"] = hebrew
    if district:
        entry["d"] = district
    if depopulated:
        entry["x"] = 1
    return entry


def _near(a: list[float], b: list[float], metres: float = 2500) -> bool:
    import math
    return math.hypot(
        (a[0] - b[0]) * math.cos(math.radians(31.9)) * 111_320,
        (a[1] - b[1]) * 111_320,
    ) <= metres


def _centroid(geometry: dict[str, Any]) -> list[float]:
    if geometry["type"] == "Point":
        return list(geometry["coordinates"])
    polys = (
        [geometry["coordinates"]]
        if geometry["type"] == "Polygon"
        else geometry["coordinates"]
    )
    ring = max(
        (rings[0] for rings in polys if rings),
        key=lambda r: (
            (max(p[0] for p in r) - min(p[0] for p in r))
            * (max(p[1] for p in r) - min(p[1] for p in r))
        ),
    )
    return [
        sum(p[0] for p in ring) / len(ring),
        sum(p[1] for p in ring) / len(ring),
    ]


def build_index(
    localities: list[Locality], entities: list[Entity]
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []

    for loc in localities:
        out.append(
            _entry(
                loc.locality_id,
                loc.names.primary,
                "locality",
                list(loc.geometry["coordinates"]),
                arabic=loc.names.arabic,
                hebrew=loc.names.hebrew,
                district=loc.district,
                variants=loc.names.transliterations,
                depopulated=loc.depopulated_1948,
            )
        )

    # OCHA and B'Tselem both describe the same settlements, so Ariel would
    # otherwise appear twice in the results, 800 m apart, indistinguishable to a
    # reader. Collapse those — but only between settlements. Susiya is a
    # Palestinian village AND an Israeli settlement 1.2 km apart, and folding
    # those together would erase the distinction this map exists to draw.
    settlement_keys: dict[str, list[float]] = {}
    seen: set[str] = set()

    for e in entities:
        if e.entity_id in seen or not e.extents:
            continue
        seen.add(e.entity_id)
        name = e.names.primary
        if name.startswith("Unidentified"):
            continue  # nothing to search for, and nothing to claim

        centre = _centroid(e.extents[0].geometry)
        key = _fold_transliteration(normalise_latin(name))
        existing = settlement_keys.get(key)
        if existing and _near(existing, centre):
            continue
        settlement_keys[key] = centre

        out.append(
            _entry(
                e.entity_id,
                name,
                e.entity_type.value,
                centre,
                hebrew=e.names.hebrew,
                district=e.district,
                variants=e.names.transliterations,
            )
        )

    return out
