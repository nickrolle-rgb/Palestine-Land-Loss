"""Reconciling the two locality datasets into one.

The map carried two overlapping sets of Palestinian localities and drew both:

  * OCHA's Palestinian Communities layer — 850 present-day West Bank communities,
    authoritative for what exists now, with PCODEs.
  * Palestine Open Maps' locality database — 2,527 localities across historic
    Palestine, with 1922/1931/1945 populations and depopulation status.

Drawn together they produced visible double dots — Kobar twice, Burham twice,
Abu Shukheidim twice — and clicking landed on whichever layer happened to be on
top, so the panel could name a different place from the one under the cursor.

Three distinct problems, handled differently.

**Duplication.** 472 pairs are merged into one locality carrying both sources'
attributes and both citations. Candidates are found by proximity and then
confirmed by name, not the other way round: keying on exact normalised names
missed real pairs, because "Beituniya" and "Beitunya" never landed in the same
bucket to have their distance compared at all.

**Position.** The two sources place the same town differently — Palestine Open
Maps marks the 1945 village, OCHA the present-day administrative centre. Usually
the gap is small (median 149 m) but it reaches 1.2 km at Beituniya, enough that a
dot drawn at the modern centre floats away from the village it names on a 1940s
survey sheet. Merged localities therefore keep both coordinates, and the client
uses the historical one whenever a historical sheet is showing.

**Coordinate conflicts.** 16 records sit on *exactly* the coordinates of a
differently-named locality — al-Zaytouneh on Abu Shukheidim's position, while
POM's own Abu Shukheidim is 200 m away. Both cannot be right, and a point we have
positive reason to believe is misplaced is not plotted. They are withheld,
counted and logged.

A locality depopulated in 1948 is never merged into one OCHA lists as inhabited
today. That rule caught a real error: POM's Jerusalem record, covering
neighbourhoods depopulated in 1948, was merging into OCHA's present-day East
Jerusalem community.
"""

from __future__ import annotations

import math
import re
from collections import defaultdict
from difflib import SequenceMatcher
from typing import Any

from .adapters.alhaq import normalise
from .schema import Locality, Names

# Merge two same-named localities within this distance. See the module docstring
# for why this number and not another.
MERGE_RADIUS_M = 600

# Beyond the confident radius but still one place. Same-name offsets cluster
# tightly — median 149 m, 95th percentile 826 m — and the next population of
# same-name pairs sits beyond 5 km, genuinely different villages. So a match out
# to 2.5 km is safe, and it is where a town's 1945 core and its modern
# administrative centre diverge: Beituniya's two records are 1,175 m apart.
# These merge, and are listed so the wider matches stay reviewable.
AMBIGUOUS_RADIUS_M = 2500

# Grid cell for candidate lookup, in degrees (~3 km).
_CELL = 0.03


def _cell(point: tuple[float, float]) -> tuple[int, int]:
    return (int(point[0] / _CELL), int(point[1] / _CELL))


# Two records at literally identical coordinates are describing the same point.
# The only question is whether they are the same *place*, and transliteration
# alone should not decide it: "Khirbat Tawil al-Shih" and "Khirbet Tawil ash
# Shih" are one village spelled two ways, while "al-Zaytouneh" and "Abu
# Shukheidim" are two villages with one coordinate between them. Normalisation
# collapses articles and diacritics but not vowel choices (Dayr/Deir,
# Khirbat/Khirbet), so a similarity ratio does the rest.
NAME_SIMILARITY = 0.82


# Known Arabic-to-Latin transliteration equivalences. These are systematic, not
# fuzzy: the same word rendered by two conventions. Folding them explicitly is
# safer than loosening the similarity threshold, which would start merging
# genuinely different places. "bayt mirsim" vs "beit mirsim" scores 0.818 —
# just under the threshold — and appears over and over in this data.
#
# Applied only here, deliberately: the shared `normalise()` also drives Al-Haq
# incident matching, where widening the net has a different risk profile.
TRANSLITERATIONS = {
    "bayt": "beit", "bet": "beit",
    "dayr": "deir", "der": "deir",
    "ayn": "ein", "ain": "ein",
    "khirbat": "khirbet", "kharbat": "khirbet", "khurbat": "khirbet",
    "shaykh": "sheikh", "shikh": "sheikh",
    "om": "umm", "um": "umm",
    "qaryat": "qariat",
    "nazlat": "nazlet",
    "jabal": "jabel",
}


def _fold_transliteration(normalised: str) -> str:
    return " ".join(TRANSLITERATIONS.get(t, t) for t in normalised.split())


# Some records carry a clan or tribe in brackets — "Khashem Adaraj
# (al-Hathaleen)" against OCHA's "Khashem ad Daraj". The qualifier identifies
# who lives there, not a different place, so it is set aside when comparing.
_PARENTHETICAL = re.compile(r"\([^)]*\)")


def _compare_key(name: str) -> str:
    return _fold_transliteration(normalise(_PARENTHETICAL.sub(" ", name)))


def _same_place(a: str, b: str) -> bool:
    na, nb = _compare_key(a), _compare_key(b)
    if not na or not nb:
        return False
    if na == nb:
        return True
    # One name containing the other catches "Bani Zeid" vs "Bani Zeid al-Sharqiya".
    if na in nb or nb in na:
        return True
    return SequenceMatcher(None, na, nb).ratio() >= NAME_SIMILARITY


def _metres(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(
        (a[0] - b[0]) * math.cos(math.radians(31.9)) * 111_320,
        (a[1] - b[1]) * 111_320,
    )


def _point(loc: Locality) -> tuple[float, float]:
    return tuple(loc.geometry["coordinates"])  # type: ignore[return-value]


def _merge_population(*series: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Union of population records, keyed by (year, group)."""
    seen: dict[tuple[Any, Any], dict[str, Any]] = {}
    for s in series:
        for entry in s or []:
            key = (entry.get("year"), entry.get("group"))
            seen.setdefault(key, entry)
    return sorted(seen.values(), key=lambda e: (e.get("year") or 0, e.get("group") or ""))


def _merge_pair(current: Locality, historic: Locality) -> Locality:
    """Combine an OCHA record with its Palestine Open Maps counterpart.

    OCHA supplies the identity — it is the present-day authority and carries the
    PCODE. Palestine Open Maps supplies the history. Names from both are kept:
    the transliterations differ often enough that discarding either would lose
    the variant a reader might be searching for.
    """
    variants = list(current.names.transliterations)
    if historic.names.primary and normalise(historic.names.primary) != normalise(
        current.names.primary
    ):
        variants.append(historic.names.primary)

    return Locality(
        locality_id=current.locality_id,
        names=Names(
            primary=current.names.primary,
            arabic=current.names.arabic or historic.names.arabic,
            hebrew=current.names.hebrew or historic.names.hebrew,
            pre_1948=current.names.pre_1948 or historic.names.pre_1948,
            transliterations=variants,
        ),
        geometry=current.geometry,
        district=current.district or historic.district,
        subdistrict=current.subdistrict or historic.subdistrict,
        in_east_jerusalem=current.in_east_jerusalem,
        population=_merge_population(current.population, historic.population),
        oslo_area=current.oslo_area,
        depopulated_1948=historic.depopulated_1948,
        depopulated_date=historic.depopulated_date,
        status_now=historic.status_now,
        group_1945=historic.group_1945,
        group_now=historic.group_now,
        mechanism=historic.mechanism,
        slug=historic.slug or current.slug,
        oral_histories=historic.oral_histories or current.oral_histories,
        references={**historic.references, **current.references},
        # The two sources place the same town differently: Palestine Open Maps
        # marks the 1945 village, OCHA the present-day administrative centre.
        # Both are kept so a locality can sit where it belongs on whichever
        # basemap is showing, instead of floating away from the historical sheet.
        historic_point=(
            list(historic.geometry["coordinates"])
            if historic.geometry["coordinates"] != current.geometry["coordinates"]
            else None
        ),
        evidence=current.evidence + historic.evidence,
    )


def _drop_coordinate_conflicts(
    localities: list[Locality],
) -> tuple[list[Locality], list[dict[str, str]], list[str]]:
    """Remove localities that share a position with a differently-named one.

    Two places cannot occupy the same point. When they appear to, at least one
    coordinate is wrong and we usually cannot tell which — so the map does not
    draw a position it has reason to doubt.

    Where the collision is between sources of unequal standing, the more
    authoritative record survives: OCHA's communities layer carries PCODEs and
    is the present-day authority, so it outranks a Palestine Open Maps record
    (this is the al-Zaytouneh / Abu Shukheidim case). Where neither outranks the
    other — two Palestine Open Maps records with copied coordinates — both are
    withheld, because keeping an arbitrary one would be a coin toss presented as
    a fact.
    """
    grouped: dict[tuple[float, float], list[Locality]] = defaultdict(list)
    for loc in localities:
        grouped[_point(loc)].append(loc)

    keep: list[Locality] = []
    dropped: list[dict[str, str]] = []
    coincident: list[str] = []

    for point, group in grouped.items():
        if len(group) == 1:
            keep.append(group[0])
            continue

        # If every record at this point plausibly names the same place, it is a
        # duplicate rather than a conflict: merge instead of withholding.
        first = group[0]
        if all(_same_place(first.names.primary, l.names.primary) for l in group[1:]):
            survivor = next(
                (l for l in group if not l.locality_id.startswith("pom-")), first
            )
            for other in group:
                if other is not survivor:
                    survivor = _merge_pair(survivor, other)
            keep.append(survivor)
            coincident.append(survivor.names.primary)
            continue

        authoritative = [l for l in group if not l.locality_id.startswith("pom-")]
        if len(authoritative) == 1:
            survivor = authoritative[0]
            keep.append(survivor)
            for l in group:
                if l is survivor:
                    continue
                dropped.append(
                    {
                        "withheld": l.names.primary,
                        "shares_coordinates_with": survivor.names.primary,
                        "coordinates": f"{point[0]:.5f}, {point[1]:.5f}",
                        "reason": "collides with a more authoritative record",
                    }
                )
        else:
            others = ", ".join(sorted(l.names.primary for l in group))
            for l in group:
                dropped.append(
                    {
                        "withheld": l.names.primary,
                        "shares_coordinates_with": others,
                        "coordinates": f"{point[0]:.5f}, {point[1]:.5f}",
                        "reason": "identical coordinates, neither record outranks the other",
                    }
                )

    return keep, dropped, coincident


def merge_localities(
    current: list[Locality], historic: list[Locality]
) -> tuple[list[Locality], dict[str, Any]]:
    """Return (merged localities, stats). Conflicted records are omitted."""
    by_point: dict[tuple[float, float], Locality] = {}
    by_name: dict[str, list[Locality]] = defaultdict(list)
    for loc in current:
        by_point[_point(loc)] = loc
        by_name[normalise(loc.names.primary)].append(loc)

    # Candidates are found by proximity first, then confirmed by name. Keying on
    # exact normalised names missed real pairs: "Beituniya" and "Beitunya" are
    # one town spelled two ways 1.2 km apart, and never landed in the same
    # bucket to have their distance checked at all.
    grid: dict[tuple[int, int], list[Locality]] = defaultdict(list)
    for loc in current:
        grid[_cell(_point(loc))].append(loc)

    merged_into: dict[str, Locality] = {}
    standalone: list[Locality] = []
    conflicts: list[dict[str, str]] = []
    ambiguous: list[str] = []

    for h in historic:
        hp = _point(h)
        cx, cy = _cell(hp)
        nearby = [
            c
            for dx in (-1, 0, 1)
            for dy in (-1, 0, 1)
            for c in grid.get((cx + dx, cy + dy), ())
        ]
        candidates = [
            (c, _metres(hp, _point(c)))
            for c in nearby
            if _same_place(h.names.primary, c.names.primary)
            # A locality OCHA lists as inhabited today cannot also be one
            # depopulated in 1948, and merging the two produces a record that
            # asserts both. It caught a real error: POM's Jerusalem record, for
            # the neighbourhoods depopulated in 1948, was merging into OCHA's
            # present-day "East Jerusalem" community — different places, and on
            # this map a consequential difference.
            and not h.depopulated_1948
        ]

        if candidates:
            nearest, distance = min(candidates, key=lambda pair: pair[1])
            if distance <= MERGE_RADIUS_M:
                key = nearest.locality_id
                merged_into[key] = _merge_pair(merged_into.get(key, nearest), h)
                continue
            if distance <= AMBIGUOUS_RADIUS_M:
                ambiguous.append(
                    f"{h.names.primary} / {nearest.names.primary} ({distance:,.0f} m apart)"
                )
                key = nearest.locality_id
                merged_into[key] = _merge_pair(merged_into.get(key, nearest), h)
                continue

        standalone.append(h)

    out = [merged_into.get(loc.locality_id, loc) for loc in current] + standalone
    out, conflicts, coincident = _drop_coordinate_conflicts(out)

    stats = {
        "current_records": len(current),
        "historic_records": len(historic),
        "merged_pairs": len(merged_into),
        "output_localities": len(out),
        "withheld_coordinate_conflicts": len(conflicts),
        "conflict_detail": conflicts,
        "merged_on_shared_coordinates": len(coincident),
        "same_name_but_too_far_to_merge": len(ambiguous),
        "ambiguous_detail": ambiguous[:20],
    }
    return out, stats
