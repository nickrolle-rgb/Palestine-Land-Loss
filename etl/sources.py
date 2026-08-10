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
        name="B'Tselem settlement and land-control data",
        publisher="B'Tselem",
        licence="UNKNOWN — permission not yet sought",
        url="https://www.btselem.org/map",
        enabled=False,
        notes="Primary candidate source for municipal / regional council jurisdiction extents.",
    ),
    "alhaq": Source(
        source_id="alhaq",
        name="Al-Haq monitoring and documentation",
        publisher="Al-Haq",
        licence="UNKNOWN — permission not yet sought; ingest is link-out only",
        url="https://www.alhaq.org/monitoring-documentation",
        enabled=True,
        attribution="Al-Haq — Defending Human Rights in Palestine since 1979",
        notes=(
            "Not a structured/geolocated database — narrative HTML reports under "
            "numeric IDs. We store title, date, URL and a matched locality only, "
            "and link out to Al-Haq for the content itself. We do not republish "
            "their report text."
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
