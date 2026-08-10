"""Canonical data model.

Two modelling decisions carry the whole project:

1. **Geometry is separated from entity.** A settlement is not "a polygon". It is an
   entity that has up to three *different* spatial extents — built-up footprint,
   municipal jurisdiction, regional council jurisdiction — which differ by an order
   of magnitude. Storing them as separate `Extent` rows keyed to the same entity is
   what makes the three-way legend toggle honest instead of a rendering trick.

2. **Time is a stage history, not a polygon per year.** Each entity carries a list of
   `StageEvent(stage, valid_from, valid_to, evidence)`. The time slider resolves
   "what stage was this entity on date D" at query time. This is also why every
   element on the map can cite a dated document.

Everything that reaches the client carries provenance. A feature with no `evidence`
is a bug, not a feature.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Literal


# --------------------------------------------------------------------------
# Stages — the real Israeli planning pipeline, not a simplified four-step
# --------------------------------------------------------------------------

class Stage(int, Enum):
    """Each step generates a dated public record. See docs/pipeline.md."""

    LAND_DECLARATION = 1   # declared "state land" / military seizure order / survey
    PLAN_DEPOSITED = 2     # plan lodged with the Higher Planning Committee
    PLAN_APPROVED = 3      # HPC validation
    TENDERS_PUBLISHED = 4  # Ministry of Housing tenders units
    GROUND_WORKS = 5       # roads, infrastructure, site clearing
    CONSTRUCTION_START = 6 # foundations, units under construction
    POPULATED = 7          # residents present

    @property
    def label(self) -> str:
        return _STAGE_LABELS[self]


_STAGE_LABELS = {
    Stage.LAND_DECLARATION: "Land declared / seized",
    Stage.PLAN_DEPOSITED: "Plan deposited",
    Stage.PLAN_APPROVED: "Plan approved",
    Stage.TENDERS_PUBLISHED: "Tenders published",
    Stage.GROUND_WORKS: "Ground works",
    Stage.CONSTRUCTION_START: "Construction started",
    Stage.POPULATED: "Populated",
}


class EntityType(str, Enum):
    """Outposts are a parallel track, not a pipeline stage.

    Outposts are built without Israeli government authorisation — illegal under
    Israeli domestic law as well as international law — and are frequently
    *retroactively authorised*, jumping straight to STAGE 7 without passing
    through 2-4. Forcing them through the linear pipeline produces a wrong map,
    so they get their own type and a `retroactive_authorisation_date`.
    """

    SETTLEMENT = "settlement"
    OUTPOST = "outpost"
    # East Jerusalem is administered under a different legal regime (Israeli law
    # applied following the 1967 annexation, which is not internationally
    # recognised). Modelled separately so its planning pipeline is not silently
    # conflated with Area C settlements.
    EJ_SETTLEMENT = "ej_settlement"
    INDUSTRIAL_ZONE = "industrial_zone"


class LossMechanism(str, Enum):
    """How land was lost. Kept distinct because the mechanisms are not alike.

    The project's credibility depends on not flattening these together. Post-1967
    settlement is unlawful under international law as a sourced finding (UNSC
    2334; ICJ advisory opinion, 19 July 2024). The 1948 depopulation is a
    documented historical event with a different legal character and a different
    evidence base. Both are Palestinian land loss; rendering them in identical
    visual language would misrepresent both, and would weaken the settlement case
    by association rather than strengthen the 1948 one.

    Each mechanism carries its own styling, its own evidence and its own legal
    note in the UI.
    """

    DEPOPULATION_1948 = "depopulation_1948"
    SETTLEMENT_POST_1967 = "settlement_post_1967"
    # Modelled, not yet populated — see docs/data-gaps.md
    LAND_TRANSFER_MANDATE = "land_transfer_mandate"
    CLOSED_MILITARY_AREA = "closed_military_area"
    BARRIER_SEVERANCE = "barrier_severance"


MECHANISM_LABELS = {
    LossMechanism.DEPOPULATION_1948: "Depopulated in 1948",
    LossMechanism.SETTLEMENT_POST_1967: "Israeli settlement (post-1967)",
    LossMechanism.LAND_TRANSFER_MANDATE: "Mandate-era land transfer",
    LossMechanism.CLOSED_MILITARY_AREA: "Closed military area",
    LossMechanism.BARRIER_SEVERANCE: "Severed by the Barrier",
}

MECHANISM_NOTES = {
    LossMechanism.DEPOPULATION_1948: (
        "Localities depopulated during and after the 1948 war. Around 750,000 "
        "Palestinians were displaced. Property was subsequently vested in the "
        "state under the Absentees' Property Law 1950. This is a documented "
        "historical event; it is not the same legal category as the settlements."
    ),
    LossMechanism.SETTLEMENT_POST_1967: (
        "Israeli settlements in territory occupied since 1967. Unlawful under "
        "international law per UN Security Council Resolution 2334 (2016) and the "
        "ICJ advisory opinion of 19 July 2024."
    ),
}


class ExtentType(str, Enum):
    """The three ways to draw "how much land is taken". All three ship."""

    BUILT_UP = "built_up"                  # actual buildings and roads
    MUNICIPAL = "municipal"                # declared settlement boundary
    REGIONAL_COUNCIL = "regional_council"  # regional council jurisdiction


EXTENT_DEFINITIONS = {
    ExtentType.BUILT_UP: (
        "The physically developed area — buildings, roads and immediate curtilage. "
        "The smallest of the three measures."
    ),
    ExtentType.MUNICIPAL: (
        "The settlement's declared municipal boundary, within which it may plan and "
        "build. Typically several times larger than the built-up area."
    ),
    ExtentType.REGIONAL_COUNCIL: (
        "The jurisdiction of the regional council the settlement belongs to. Covers "
        "a large share of Area C, including land not built on and land cultivated by "
        "Palestinians."
    ),
}


class Confidence(str, Enum):
    """Applies to any derived/inferred value, especially geocoded incidents."""

    EXACT = "exact"        # coordinates given in the source
    MATCHED = "matched"    # unambiguous match to a gazetteer locality
    AMBIGUOUS = "ambiguous"  # multiple candidate localities — NOT rendered on map
    UNRESOLVED = "unresolved"  # no location recoverable — NOT rendered on map


RENDERABLE_CONFIDENCE = {Confidence.EXACT, Confidence.MATCHED}


class RecordType(str, Enum):
    """Not every document describes a locatable event.

    Al-Haq's periodic output (monthly/annual/fieldwork reports) aggregates
    violations across the whole West Bank. Pinning such a report to one locality
    because a place name appears in its title would be a fabrication. Those
    records are listed and linked, never plotted.
    """

    FIELD_STORY = "field_story"          # a specific, locatable documented event
    PERIODIC_REPORT = "periodic_report"  # aggregate coverage — listed, not plotted


# --------------------------------------------------------------------------
# Provenance
# --------------------------------------------------------------------------

@dataclass
class Evidence:
    """Every dated claim points at one of these. No evidence, no render."""

    source_id: str            # key into etl/sources.py SOURCES
    title: str
    url: str | None = None
    document_date: str | None = None  # ISO date the document itself is dated
    retrieved: str | None = None      # ISO date we fetched it
    note: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class StageEvent:
    """`valid_to = None` means "still in this stage as far as we know"."""

    stage: Stage
    valid_from: str | None            # ISO date; None = date unknown
    valid_to: str | None = None
    evidence: list[Evidence] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage": int(self.stage),
            "stage_label": self.stage.label,
            "valid_from": self.valid_from,
            "valid_to": self.valid_to,
            "evidence": [e.to_dict() for e in self.evidence],
        }


@dataclass
class Extent:
    """One spatial extent of one entity, under one definition."""

    extent_type: ExtentType
    geometry: dict[str, Any]          # GeoJSON geometry, EPSG:4326
    source_crs: str                   # e.g. "EPSG:32636" — recorded, never guessed
    area_m2: float | None = None
    evidence: list[Evidence] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "extent_type": self.extent_type.value,
            "definition": EXTENT_DEFINITIONS[self.extent_type],
            "source_crs": self.source_crs,
            "area_m2": self.area_m2,
            "evidence": [e.to_dict() for e in self.evidence],
        }


# --------------------------------------------------------------------------
# Naming — see docs/naming-policy.md
# --------------------------------------------------------------------------

@dataclass
class Names:
    """Show the Palestinian/Arabic name and the current official name together.

    Silently picking one naming scheme is the fastest way to make the map look
    partisan regardless of data quality. All known variants are carried through
    to the feature detail panel.
    """

    primary: str                       # what the label renders
    arabic: str | None = None
    hebrew: str | None = None
    pre_1948: str | None = None
    transliterations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = {k: v for k, v in asdict(self).items() if v}
        return d


# --------------------------------------------------------------------------
# Entities
# --------------------------------------------------------------------------

@dataclass
class Entity:
    """A settlement, outpost, industrial zone or EJ settlement."""

    entity_id: str
    entity_type: EntityType
    names: Names
    extents: list[Extent] = field(default_factory=list)
    stage_history: list[StageEvent] = field(default_factory=list)
    retroactive_authorisation_date: str | None = None  # outposts only
    district: str | None = None
    population: list[dict[str, Any]] = field(default_factory=list)  # {year, value, source_id}
    evidence: list[Evidence] = field(default_factory=list)

    def current_stage(self, on_date: str | None = None) -> Stage | None:
        """Resolve the stage as at `on_date` (ISO). Highest stage reached wins."""
        reached = [
            ev.stage for ev in self.stage_history
            if ev.valid_from and (on_date is None or ev.valid_from <= on_date)
        ]
        return max(reached) if reached else None

    def properties(self) -> dict[str, Any]:
        """Flattened, client-facing properties. Geometry attaches per-extent."""
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type.value,
            "name": self.names.primary,
            "names": self.names.to_dict(),
            "district": self.district,
            "retroactive_authorisation_date": self.retroactive_authorisation_date,
            "stage_history": [s.to_dict() for s in self.stage_history],
            "population": self.population,
            "evidence": [e.to_dict() for e in self.evidence],
        }


@dataclass
class Locality:
    """A Palestinian community — the "what was there / what is there" counterpart."""

    locality_id: str
    names: Names
    geometry: dict[str, Any]
    district: str | None = None
    subdistrict: str | None = None
    in_east_jerusalem: bool = False
    population: list[dict[str, Any]] = field(default_factory=list)
    oslo_area: str | None = None
    depopulated_1948: bool = False
    depopulated_date: str | None = None
    status_now: str | None = None       # e.g. "Depopulated & built over"
    group_1945: str | None = None       # Palestinian / Jewish / Mixed
    group_now: str | None = None
    mechanism: LossMechanism | None = None
    references: dict[str, str] = field(default_factory=dict)  # external cross-refs
    evidence: list[Evidence] = field(default_factory=list)

    def properties(self) -> dict[str, Any]:
        # Flattened for MapLibre: style expressions cannot index the nested
        # population array, and circle radius is scaled by 1945 population so
        # the depopulation layer reads as loss of people rather than dots.
        pop_1945 = next(
            (p["value"] for p in self.population
             if p.get("year") == 1945 and not p.get("group") and p.get("value")),
            None,
        )
        # In mixed cities the total badly overstates displacement — Jerusalem's
        # 1945 total is ~157,000, which is not the number of Palestinians
        # displaced from it. Symbol size uses the Palestinian figure where the
        # source records the split, and falls back to the total only when it
        # does not.
        pop_1945_pal = next(
            (p["value"] for p in self.population
             if p.get("year") == 1945 and p.get("group") == "Palestinian" and p.get("value")),
            None,
        )
        return {
            "locality_id": self.locality_id,
            "name": self.names.primary,
            "names": self.names.to_dict(),
            "district": self.district,
            "subdistrict": self.subdistrict,
            "pop_1945_total": pop_1945,
            "pop_1945_palestinian": pop_1945_pal,
            "in_east_jerusalem": self.in_east_jerusalem,
            "oslo_area": self.oslo_area,
            "population": self.population,
            "depopulated_1948": self.depopulated_1948,
            "depopulated_date": self.depopulated_date,
            "status_now": self.status_now,
            "group_1945": self.group_1945,
            "group_now": self.group_now,
            "mechanism": self.mechanism.value if self.mechanism else None,
            "references": self.references,
            "evidence": [e.to_dict() for e in self.evidence],
        }


@dataclass
class Incident:
    """A documented violation, geolocated to a locality.

    Records that cannot be confidently placed are retained in the dataset with
    `confidence` of AMBIGUOUS/UNRESOLVED but are *not* rendered on the map. The
    count of unrendered records is surfaced in the UI so the gap is visible
    rather than hidden.
    """

    incident_id: str
    title: str
    date: str | None
    url: str
    source_id: str
    record_type: RecordType = RecordType.FIELD_STORY
    summary: str | None = None
    categories: list[str] = field(default_factory=list)
    location_text: str | None = None       # the raw free-text we matched on
    matched_locality_id: str | None = None
    matched_from: str | None = None        # "title" or "body"
    geometry: dict[str, Any] | None = None
    confidence: Confidence = Confidence.UNRESOLVED
    match_note: str | None = None

    @property
    def renderable(self) -> bool:
        return (
            self.record_type is RecordType.FIELD_STORY
            and self.confidence in RENDERABLE_CONFIDENCE
            and self.geometry is not None
        )

    def properties(self) -> dict[str, Any]:
        return {
            "incident_id": self.incident_id,
            "title": self.title,
            "date": self.date,
            "url": self.url,
            "source_id": self.source_id,
            "record_type": self.record_type.value,
            "summary": self.summary,
            "categories": self.categories,
            "location_text": self.location_text,
            "matched_locality_id": self.matched_locality_id,
            "matched_from": self.matched_from,
            "confidence": self.confidence.value,
            "match_note": self.match_note,
        }


def feature(geometry: dict[str, Any], properties: dict[str, Any]) -> dict[str, Any]:
    return {"type": "Feature", "geometry": geometry, "properties": properties}


# --------------------------------------------------------------------------
# Payload normalisation
# --------------------------------------------------------------------------

_EMPTY = (None, "", [], {})


def _evidence_id(ev: dict[str, Any]) -> str:
    """Stable content hash, so the same citation always gets the same id."""
    import hashlib
    import json as _json

    canonical = _json.dumps(ev, sort_keys=True, ensure_ascii=False)
    return hashlib.sha1(canonical.encode("utf-8")).hexdigest()[:10]


def normalise_features(
    features: list[dict[str, Any]], evidence_table: dict[str, Any]
) -> list[dict[str, Any]]:
    """Hoist repeated evidence into a shared table and drop empty properties.

    The rule that every feature must carry evidence is unchanged — this only
    stops us shipping 2,537 byte-identical copies of the same citation, which
    was 38% of one layer's payload. Features carry `evidence_ref`, a list of ids
    into the table published in meta.json. A feature whose refs do not resolve
    is still a bug, and the test suite asserts exactly that.

    Empty values are removed rather than serialised: `oslo_area` was null on
    every one of those 2,537 features.
    """
    out = []
    for f in features:
        props = dict(f.get("properties") or {})

        refs: list[str] = []
        for ev in props.pop("evidence", []) or []:
            eid = _evidence_id(ev)
            evidence_table.setdefault(eid, ev)
            refs.append(eid)

        # Nested stage history carries its own evidence; normalise it too.
        history = props.get("stage_history")
        if history:
            new_history = []
            for step in history:
                step = dict(step)
                step_refs = []
                for ev in step.pop("evidence", []) or []:
                    eid = _evidence_id(ev)
                    evidence_table.setdefault(eid, ev)
                    step_refs.append(eid)
                if step_refs:
                    step["evidence_ref"] = step_refs
                new_history.append({k: v for k, v in step.items() if v not in _EMPTY})
            props["stage_history"] = new_history

        props = {k: v for k, v in props.items() if v not in _EMPTY}
        if refs:
            props["evidence_ref"] = refs

        out.append({**f, "properties": props})
    return out


def feature_collection(features: list[dict[str, Any]], **meta: Any) -> dict[str, Any]:
    fc: dict[str, Any] = {"type": "FeatureCollection", "features": features}
    if meta:
        fc["metadata"] = meta
    return fc
