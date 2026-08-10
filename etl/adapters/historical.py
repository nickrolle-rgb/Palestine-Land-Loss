"""Historical layers — the "what was there before" side of land loss.

Two things come from here:

1. **The locality record**, from Palestine Open Maps: 2,543 localities across
   historic Palestine with trilingual names, population for 1922, 1931 and 1945
   split Palestinian/Jewish, depopulation dates, and what stands there now. This
   is the evidence base for depicting the 1948 depopulation, and it covers
   territory inside the 1949 armistice lines as well as the West Bank and Gaza.

2. **The Mandatory Palestine boundary**, which matters because every "share of
   the land" claim needs a stated denominator. Without it, percentages are
   assertions.

On the pre-Mandate division: late-Ottoman Palestine was not one unit. The
Mutasarrifiyya (independent sanjak) of Jerusalem covered the south and reported
directly to Constantinople from 1872; the sanjaks of Nablus and Acre sat under
the Vilayet of Beirut. **No GIS dataset of those boundaries could be found** —
historical-basemaps and OpenHistoricalMap both stop at empire level. Per the
project's rule against guessed geometry, they are not drawn. The PEF Survey of
Western Palestine (surveyed 1871–77) ships as the period's cartographic record
instead, and the gap is logged in docs/data-gaps.md.
"""

from __future__ import annotations

import csv
import io
import json
from typing import Any

from ..fetch import RAW, download, retrieved_date
from ..schema import (
    Confidence,
    Evidence,
    Locality,
    LossMechanism,
    Names,
)
from ..sources import SOURCES

POM_LOCALITIES_URL = (
    "https://raw.githubusercontent.com/palopenmaps/pom-data/main/raw-data/localities.csv"
)
MANDATE_URL = (
    "https://raw.githubusercontent.com/aourednik/historical-basemaps/master/"
    "geojson/world_1920.geojson"
)

# Values of change_2016 that mean the locality no longer exists as a Palestinian
# place. Taken verbatim from the source vocabulary rather than reinterpreted.
DEPOPULATED_STATES = {
    "Depopulated",
    "Depopulated & built over",
    "Depopulated & appropriated",
    "Abandoned",
}


def _int(v: str) -> int | None:
    v = (v or "").strip().replace(",", "")
    return int(v) if v.isdigit() else None


# POM's dataset includes Israeli settlements built in occupied Sinai between 1967
# and 1982 and evacuated under the Egypt-Israel peace treaty. They are real, but
# Sinai is Egyptian territory and outside the scope of a map about Palestinian
# land loss. Excluded by name rather than by a bounding box, so the exclusion is
# explicit and reviewable instead of a silent geographic filter.
SINAI_DISTRICT = "sinai"


def load_localities() -> list[Locality]:
    path = download(POM_LOCALITIES_URL, "pom_localities.csv")
    ev = Evidence(
        source_id="pom_localities",
        title="Palestine Open Maps — locality database",
        url=SOURCES["pom_localities"].url,
        retrieved=retrieved_date("pom_localities.csv"),
        note="Licence undeclared by the publisher; permission request pending.",
    )

    rows = list(csv.DictReader(io.StringIO(path.read_text(encoding="utf-8", errors="replace"))))
    out: list[Locality] = []
    skipped_sinai = 0
    inconsistent: list[str] = []

    for r in rows:
        if (r.get("district_1945") or "").strip().lower() == SINAI_DISTRICT:
            skipped_sinai += 1
            continue

        try:
            lat, lng = float(r["lat"]), float(r["lng"])
        except (TypeError, ValueError):
            continue  # no coordinates — not plotted, consistent with the no-guess rule

        status = (r.get("change_2016") or "").strip()
        depopulated = status in DEPOPULATED_STATES
        end = (r.get("end") or "").strip()

        pops = []
        for year, key in ((1922, "pop_1922"), (1931, "pop_1931"), (1945, "pop_1945")):
            v = _int(r.get(key, ""))
            if v is not None:
                pops.append({"year": year, "value": v, "source_id": "pom_localities"})
        # 1945 split by group, where the source records it.
        total_1945 = _int(r.get("pop_1945", ""))
        pal_1945 = _int(r.get("pal_1945", ""))

        # One record (Duyuk) has a Palestinian figure larger than the locality
        # total. We cannot know which number is wrong, so we do not pick a
        # winner: the contradictory group figure is dropped, symbol sizing falls
        # back to the total, and the conflict is flagged on the feature and
        # logged in docs/corrections.md. Taking the smaller figure is the choice
        # that cannot overstate the claim.
        conflict = (
            total_1945 is not None and pal_1945 is not None and pal_1945 > total_1945
        )
        if conflict:
            inconsistent.append(f"{r.get('name_en')} (Palestinian {pal_1945} > total {total_1945})")

        for key, label in (("pal_1945", "Palestinian"), ("jsh_1945", "Jewish")):
            v = _int(r.get(key, ""))
            if v is None:
                continue
            if conflict and key == "pal_1945":
                continue
            pops.append(
                {"year": 1945, "value": v, "group": label, "source_id": "pom_localities"}
            )
        v = _int(r.get("pop_2016", ""))
        if v is not None:
            pops.append({"year": 2016, "value": v, "source_id": "pom_localities"})

        refs = {}
        if r.get("url_pr"):
            refs["palestine_remembered"] = (
                f"https://www.palestineremembered.com/{r['url_pr']}/index.html"
            )
        if r.get("id_zo"):
            refs["zochrot"] = f"https://www.zochrot.org/villages/view/{r['id_zo']}/en"

        # Only 1948-era depopulation is attributed to that mechanism. Later
        # abandonments exist in the data and are not relabelled to fit.
        mechanism = None
        if depopulated and end[:4].isdigit() and 1947 <= int(end[:4]) <= 1950:
            mechanism = LossMechanism.DEPOPULATION_1948

        out.append(
            Locality(
                locality_id=f"pom-{r['id']}",
                names=Names(
                    primary=(r.get("name_en") or "").strip() or "Unnamed locality",
                    arabic=(r.get("name_ar") or "").strip() or None,
                    hebrew=(r.get("name_he") or "").strip() or None,
                ),
                geometry={"type": "Point", "coordinates": [round(lng, 6), round(lat, 6)]},
                district=(r.get("district_1945") or "").strip() or None,
                subdistrict=(r.get("subdistrict_1945") or "").strip() or None,
                population=pops,
                depopulated_1948=mechanism is LossMechanism.DEPOPULATION_1948,
                depopulated_date=end or None,
                status_now=status or None,
                group_1945=(r.get("grp_1945") or "").strip() or None,
                group_now=(r.get("grp_2016") or "").strip() or None,
                mechanism=mechanism,
                references=refs,
                evidence=[
                    ev if not conflict else Evidence(
                        source_id=ev.source_id,
                        title=ev.title,
                        url=ev.url,
                        retrieved=ev.retrieved,
                        note="Source population figures are internally "
                             "inconsistent for this locality; the contradictory "
                             "group figure is withheld. See docs/corrections.md.",
                    )
                ],
            )
        )

    if skipped_sinai:
        print(f"       skipped {skipped_sinai} Sinai localities (outside historic Palestine)")
    if inconsistent:
        print(f"       {len(inconsistent)} locality with inconsistent population: "
              f"{'; '.join(inconsistent)}")

    return out


def load_mandate_boundary() -> dict[str, Any] | None:
    """Mandatory Palestine, 1920 — the denominator for any land-share claim."""
    path = download(MANDATE_URL, "world_1920.geojson")
    data = json.loads(path.read_text(encoding="utf-8", errors="replace"))

    for f in data.get("features", []):
        name = str(f.get("properties", {}).get("NAME", ""))
        if "Mandatory Palestine" in name:
            ev = Evidence(
                source_id="historical_basemaps",
                title="Mandatory Palestine boundary, 1920",
                url=SOURCES["historical_basemaps"].url,
                document_date="1920-01-01",
                retrieved=retrieved_date("world_1920.geojson"),
                note="Generalised boundary (source BORDERPRECISION 3). Indicative "
                     "extent, not a survey-grade delimitation.",
            )
            return {
                "geometry": f["geometry"],
                "properties": {
                    "name": "Mandatory Palestine",
                    "year": 1920,
                    "precision_note": "Generalised — indicative extent only.",
                    "evidence": [ev.to_dict()],
                },
            }
    return None
