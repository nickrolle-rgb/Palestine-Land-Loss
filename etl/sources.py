"""Source registry.

Every source carries its licence and an `enabled` flag. The current posture is
**OCHA/HDX-licensed data only**; Peace Now and B'Tselem direct adapters are
scaffolded but disabled pending written permission (see
docs/permissions/). Do not flip `enabled` without recording the permission in
docs/permissions/RESPONSES.md.

Note the licensing wrinkle worth understanding: OCHA's "State of Palestine
Settlements" layer on HDX *is* Peace Now's built-up settlement data, republished
by OCHA under CC BY-IGO. Using it via HDX is therefore already permitted, with
attribution to both. That is not the same as scraping Peace Now's own site.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Source:
    source_id: str
    name: str
    publisher: str
    licence: str
    url: str
    enabled: bool = True
    attribution: str = ""
    # Currency matters: several OCHA oPt layers have not been revised in years.
    # This string is rendered in the UI next to any layer built from the source.
    currency_note: str = ""
    notes: str = ""


@dataclass(frozen=True)
class HdxResource:
    """A concrete downloadable, resolved from the registry by the fetcher."""

    key: str
    source_id: str
    url: str
    filename: str
    shapefile_base: str | None = None
    source_crs: str | None = None       # None = read from the .prj
    description: str = ""


SOURCES: dict[str, Source] = {
    "ocha_opt": Source(
        source_id="ocha_opt",
        name="OCHA occupied Palestinian territory data",
        publisher="UN OCHA oPt",
        licence="CC BY-IGO 3.0 / CC BY 4.0 (varies by dataset)",
        url="https://www.ochaopt.org/page/datasets-and-mapping-tools",
        attribution="United Nations Office for the Coordination of Humanitarian Affairs — occupied Palestinian territory",
        currency_note="Base geography reference year 2019–2021; see per-layer dates.",
    ),
    "peacenow_via_hdx": Source(
        source_id="peacenow_via_hdx",
        name="Peace Now settlement built-up areas (republished via OCHA/HDX)",
        publisher="Peace Now (Settlement Watch), republished by UN OCHA",
        licence="CC BY-IGO 3.0 (as published on HDX)",
        url="https://data.humdata.org/dataset/state-of-palestine-settlements",
        attribution="Peace Now (Settlement Watch), via UN OCHA oPt on HDX",
        currency_note="HDX record last modified 2021-06-03. Built-up footprints only.",
        notes=(
            "This is the built-up extent ONLY. Municipal and regional council "
            "jurisdiction boundaries are NOT in this dataset and must be sourced "
            "separately — see docs/data-gaps.md."
        ),
    ),
    "peacenow_direct": Source(
        source_id="peacenow_direct",
        name="Peace Now Settlement Watch (direct)",
        publisher="Peace Now",
        licence="UNKNOWN — permission not yet sought",
        url="https://peacenow.org.il/en/settlements-watch",
        enabled=False,
        notes=(
            "THE source for planning stages 2-4, construction starts and outpost "
            "tracking. Published as reports/tables, not clean GeoJSON. Adapter "
            "scaffolded but disabled pending permission."
        ),
    ),
    "btselem": Source(
        source_id="btselem",
        name="B'Tselem settlement, boundary and municipal data",
        publisher="B'Tselem — The Israeli Information Center for Human Rights in the Occupied Territories",
        licence=(
            "B'Tselem public licence for non-commercial use — "
            "https://www.btselem.org/license"
        ),
        url="https://www.btselem.org",
        enabled=True,
        attribution=(
            "Data from the B'Tselem website, supplied by B'Tselem and used under "
            "its licence for non-commercial use"
        ),
        currency_note="Supplied 2026-08-11; includes a 2024-vintage boundary file.",
        notes=(
            "Granted 2026-08-11 by Shirly Eran, with four GeoJSON files supplied "
            "directly. See docs/permissions/RESPONSES.md.\n\n"
            "Licence conditions carried by this project: non-commercial use only; "
            "no distortion or use out of context; B'Tselem named prominently and "
            "expressly; any third parties B'Tselem credits must be named too.\n\n"
            "OPEN QUESTION: the licence covers 'fair usage' of individual materials "
            "and excludes 'expansive use', which needs express written consent. The "
            "files were supplied in direct answer to a request describing this exact "
            "use, which reads as consent — confirmation has been sought to remove "
            "any doubt."
        ),
    ),
    "alhaq": Source(
        source_id="alhaq",
        name="Al-Haq monitoring and documentation",
        publisher="Al-Haq",
        licence=(
            "All rights reserved by Al-Haq. No licence is relied on: this project "
            "stores only bibliographic metadata and links out."
        ),
        url="https://www.alhaq.org/monitoring-documentation",
        enabled=True,
        attribution="Al-Haq — Defending Human Rights in Palestine since 1979",
        currency_note="Crawled from their published listings; alhaq.org states 'All Rights Reserved'.",
        notes=(
            "Not a structured/geolocated database — narrative HTML reports under "
            "numeric IDs. We store title, date, URL and a matched locality only, "
            "and link out to Al-Haq for the content itself. We do not republish "
            "their report text, so no copyright licence is required for what is "
            "stored. A courtesy notice was sent 2026-08-10 describing exactly this "
            "and inviting them to object; no reply yet."
        ),
    ),
    "palestine_open_maps": Source(
        source_id="palestine_open_maps",
        name="Palestine Open Maps — Survey of Palestine 1:20,000",
        publisher="Visualizing Palestine / Palestine Open Maps",
        licence="See palopenmaps.org — verify before redistribution",
        url="https://palopenmaps.org",
        attribution="Palestine Open Maps — georeferenced Survey of Palestine, surveyed 1940–1945",
        currency_note="Historical underlay: Survey of Palestine 1:20,000, surveyed 1940–1945.",
        notes="Already georeferenced. Consume as tiles; do not rebuild.",
    ),
    "pom_localities": Source(
        source_id="pom_localities",
        name="Palestine Open Maps — locality database",
        publisher="Palestine Open Maps / Visualizing Palestine",
        licence="Permission granted 2026-08-11 for use and redistribution in an openly licensed map",
        url="https://github.com/palopenmaps/pom-data",
        enabled=True,
        attribution="Palestine Open Maps",
        currency_note="Locality records span 1922–2016; repository last updated 2025.",
        notes=(
            "Granted 2026-08-11 by the Visualizing Palestine team. Conditions "
            "carried by this project: credit Palestine Open Maps; acknowledge the "
            "underlying sources where practical (see POM_UNDERLYING_SOURCES); and "
            "state that the data is not guaranteed to be 100% accurate.\n\n"
            "They confirmed OpenStreetMap is used only for their present-day vector "
            "overlay and is NOT the source of the localities data, so no ODbL "
            "share-alike obligation flows to this project from it."
        ),
    ),
    "wikidata": Source(
        source_id="wikidata",
        name="Wikidata",
        publisher="Wikimedia Foundation",
        licence="CC0 1.0 (public domain dedication)",
        url="https://www.wikidata.org",
        enabled=True,
        attribution="Wikidata contributors, CC0",
        notes=(
            "Used only to identify settlement polygons the OCHA/Peace Now source "
            "leaves unnamed. An identification is accepted only where a Wikidata "
            "item's coordinate falls inside the polygon — containment, not "
            "proximity — and the anchor is re-verified on every build. See "
            "etl/identifications.json and docs/corrections.md. CC0 means no "
            "attribution obligation, but it is credited anyway."
        ),
    ),
    "poha": Source(
        source_id="poha",
        name="Palestinian Oral History Archive",
        publisher="American University of Beirut Libraries",
        licence="CC BY-NC-ND 4.0 — attribution, non-commercial, no derivatives",
        url="https://libraries.aub.edu.lb/poha/",
        enabled=True,
        attribution="Palestinian Oral History Archive, American University of Beirut Libraries",
        currency_note="Interviews recorded from 2002 onwards; indexed via Palestine Open Maps.",
        notes=(
            "726 recorded interviews across 133 villages, joined to localities on "
            "Palestine Open Maps' slug — an exact key, so no name matching or "
            "proximity guessing is involved. "
            "NoDerivatives governs what we may store: title, year, duration, "
            "language and record URL only. The archive's own descriptions and its "
            "indexed contents are its editorial work and are not reproduced; every "
            "interview links back to AUB Libraries."
        ),
    ),
    "historical_basemaps": Source(
        source_id="historical_basemaps",
        name="Historical Basemaps — world boundaries by year",
        publisher="André Ourednik",
        licence="GPL-3.0 — copyleft; see docs/permissions/README.md",
        url="https://github.com/aourednik/historical-basemaps",
        enabled=True,
        attribution="Historical Basemaps (aourednik), GPL-3.0",
        currency_note="Mandatory Palestine boundary as at 1920. BORDERPRECISION 3.",
        notes=(
            "Used for the Mandatory Palestine boundary, which is the territorial "
            "denominator for any land-loss measure. GPL-3.0 is a copyleft licence "
            "and may impose obligations on a derived database — this needs a "
            "decision before publication, logged as an open question."
        ),
    ),
    "israeli_cbs": Source(
        source_id="israeli_cbs",
        name="Israeli Central Bureau of Statistics",
        publisher="Israeli CBS",
        licence="Public statistics",
        url="https://www.cbs.gov.il/en/Pages/default.aspx",
        enabled=False,
        notes="Annual population per locality — for stage 7 and the time slider.",
    ),
}


# --- Concrete HDX downloadables -------------------------------------------
# URLs resolved from the HDX CKAN API; pinned here so builds are reproducible.
# Re-resolve with: python -m etl.build refresh-urls

HDX_RESOURCES: list[HdxResource] = [
    HdxResource(
        key="settlements_builtup",
        source_id="peacenow_via_hdx",
        url="https://data.humdata.org/dataset/0d6d3717-afc1-4f6b-a003-c7e458298928/resource/05d6421b-e796-4940-ae9e-a55858e96664/download/settlements_peacenow.zip",
        filename="settlements_peacenow.zip",
        shapefile_base="Settlements_Buildup_PeaceNow",
        source_crs="EPSG:32636",  # WGS_1984_UTM_Zone_36N per .prj
        description="Israeli settlement built-up areas (201 polygons).",
    ),
    HdxResource(
        key="oslo_areas",
        source_id="ocha_opt",
        url="https://data.humdata.org/dataset/d3a843df-a640-4e9d-b867-8ca974c2aa74/resource/86f2707a-dc64-46af-bd41-b31e95611b45/download/osloagreement.zip",
        filename="osloagreement.zip",
        shapefile_base="OsloAgreement",
        source_crs="EPSG:4326",
        description="Oslo classification: Area A, C, H1, H2, Nature Reserve, "
                    "Israeli Declared East Jerusalem, No Man's Land.",
    ),
    # --- Gaza -------------------------------------------------------------
    # Both are dated 2019-07-18 and describe Gaza as it was administratively
    # defined before October 2023. They are not a picture of Gaza now, and the
    # UI says so on the layer rather than in a footnote. Damage assessment is a
    # separate question needing a separate source.
    HdxResource(
        key="gaza_municipal",
        source_id="ocha_opt",
        url="https://data.humdata.org/dataset/6b79f7ab-9e13-48e5-9f58-dc45b4a9222c/resource/f131956a-8cc6-424c-a831-5b8b0d6956b9/download/gazastrip_municipalboundaries.zip",
        filename="gazastrip_municipalboundaries.zip",
        shapefile_base="GazaStrip_MunicipalBoundaries",
        source_crs="EPSG:4326",
        description="33 Gaza Strip municipal boundaries (CC BY, dated 2019-07-18).",
    ),
    HdxResource(
        key="gaza_neighbourhoods",
        source_id="ocha_opt",
        url="https://data.humdata.org/dataset/0e62a5ad-372f-4f99-96b8-54785201211f/resource/098d8e9f-3ae2-4ed9-b6f7-29ab429106f3/download/gazastrip_neighbourhoods_points.zip",
        filename="gazastrip_neighbourhoods_points.zip",
        shapefile_base="GazaStrip_Neighbourhoods_points",
        source_crs="EPSG:4326",
        description="149 Gaza neighbourhood points (CC BY, dated 2019-07-18). "
                    "111 of them carry no district or community value in the "
                    "source; those fields are omitted rather than inferred.",
    ),
    HdxResource(
        key="communities",
        source_id="ocha_opt",
        url="https://data.humdata.org/dataset/c7e2f4b3-6a74-4b98-b064-1e9c2d066242/resource/1936b09f-74a8-4d4d-b92b-2ee75abb21f1/download/palestiniancommunities_wb_gs.zip",
        filename="palestiniancommunities_wb_gs.zip",
        shapefile_base="PalestinianCommunities_WB_GS",
        source_crs="EPSG:4326",
        description="893 Palestinian communities with Arabic names, PCODE, district, "
                    "East Jerusalem flag and 2017 population. Doubles as the "
                    "geocoding gazetteer for Al-Haq incidents.",
    ),
    HdxResource(
        key="village_boundaries",
        source_id="ocha_opt",
        url="https://data.humdata.org/dataset/8e88b6e5-c8e8-45b3-afa1-268530aadae1/resource/70c36308-91ed-4e21-9a25-e0aefb4e756f/download/villageboundary.zip",
        filename="villageboundary.zip",
        shapefile_base="VillageBoundary",
        description="Palestinian village boundaries in the West Bank.",
    ),
    HdxResource(
        key="barrier",
        source_id="ocha_opt",
        url="https://data.humdata.org/dataset/e782d4c9-d0ce-412c-ad1e-6771be2969b0/resource/95470fef-0d9d-4967-bbd6-cf247b80d578/download/barrier_jan2018.zip",
        filename="barrier_jan2018.zip",
        shapefile_base="Barrier_Jan2018",
        description="West Bank Separation Barrier, January 2018 alignment.",
    ),
    HdxResource(
        key="firing_zones",
        source_id="ocha_opt",
        url="https://data.humdata.org/dataset/95c86a40-d870-430e-bc04-8eff594c6532/resource/22a81f4b-7a34-4fc6-b3aa-6a8e1a6f57e2/download/israelifiringzomes.zip",
        filename="israelifiringzomes.zip",
        shapefile_base="IsraeliFiringZomes",  # sic — source filename is misspelled
        description="Israeli firing zones (closed military areas) in the West Bank.",
    ),
]


# Palestine Open Maps asked that the sources underlying their locality database
# be acknowledged where practical. Rendered in the About panel and shipped in
# meta.json so the credit travels with the data rather than living only in prose.
POM_UNDERLYING_SOURCES = [
    "Palestine Remembered",
    "Institute for Palestine Studies",
    "Palestine Lands Society",
    "Palestinian Central Bureau of Statistics",
    "Israeli Central Bureau of Statistics",
    "Zochrot",
    "B'Tselem",
]

# Their requested accuracy note, carried verbatim in substance.
POM_ACCURACY_NOTE = (
    "Palestine Open Maps do not guarantee that all of this data is 100% accurate. "
    "It is republished here with their permission, together with its underlying "
    "sources."
)

# Attribution wording they suggested for the historical tiles.
POM_TILE_ATTRIBUTION = "Survey of Palestine / Palestine Open Maps"


def enabled_sources() -> dict[str, Source]:
    return {k: v for k, v in SOURCES.items() if v.enabled}


def resource(key: str) -> HdxResource:
    for r in HDX_RESOURCES:
        if r.key == key:
            return r
    raise KeyError(f"unknown HDX resource: {key}")


def manifest() -> dict[str, Any]:
    """Source manifest shipped to the client for the About page and legend."""
    return {
        "attribution": {
            "pom_underlying_sources": POM_UNDERLYING_SOURCES,
            "pom_accuracy_note": POM_ACCURACY_NOTE,
            "pom_tile_attribution": POM_TILE_ATTRIBUTION,
            "btselem_note": (
                "Settlement boundary and municipal boundary data from the B'Tselem "
                "website, supplied by B'Tselem and used under its licence for "
                "non-commercial use."
            ),
        },
        "sources": [
            {
                "source_id": s.source_id,
                "name": s.name,
                "publisher": s.publisher,
                "licence": s.licence,
                "url": s.url,
                "attribution": s.attribution,
                "currency_note": s.currency_note,
                "enabled": s.enabled,
            }
            for s in SOURCES.values()
        ]
    }
