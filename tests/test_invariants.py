"""Tests for the non-negotiables in CLAUDE.md.

These are not unit tests in the usual sense. They assert the rules the project's
credibility rests on — the ones where a silent regression would not crash
anything, would not look wrong on screen, and would quietly turn an evidence map
into an assertion map.

Run against a completed build:

    python -m etl.build base
    python -m unittest discover tests -v

Uses stdlib unittest deliberately: the ETL has no test-framework dependency and
should not acquire one.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "web" / "public" / "data"


def load(name: str):
    path = DATA / name
    if not path.exists():
        raise unittest.SkipTest(f"{name} not built — run `python -m etl.build base`")
    return json.loads(path.read_text(encoding="utf-8"))


class EvidenceInvariants(unittest.TestCase):
    """Rule: a feature without evidence is a bug."""

    LAYERS = [
        "settlements_built_up.geojson",
        "localities.geojson",
        "firing_zones.geojson",
        "village_boundaries.geojson",
        "oslo_areas.geojson",
    ]

    def test_every_feature_cites_evidence(self):
        meta = load("meta.json")
        table = meta.get("evidence", {})
        self.assertTrue(table, "meta.json carries no evidence table")

        for layer in self.LAYERS:
            fc = load(layer)
            for i, f in enumerate(fc["features"]):
                refs = f["properties"].get("evidence_ref")
                with self.subTest(layer=layer, index=i):
                    self.assertTrue(refs, f"{layer}[{i}] has no evidence_ref")
                    for ref in refs:
                        self.assertIn(
                            ref, table,
                            f"{layer}[{i}] cites {ref}, which is not in the "
                            f"evidence table — a dangling citation is worse than none",
                        )

    def test_evidence_records_source_and_retrieval(self):
        table = load("meta.json").get("evidence", {})
        for eid, ev in table.items():
            with self.subTest(evidence=eid):
                self.assertTrue(ev.get("source_id"), f"{eid} has no source_id")
                self.assertTrue(ev.get("title"), f"{eid} has no title")


class NoGuessedLocations(unittest.TestCase):
    """Rule: never plot a guessed location."""

    def test_only_confident_incidents_are_plotted(self):
        fc = load("incidents.geojson")
        for f in fc["features"]:
            props = f["properties"]
            with self.subTest(incident=props.get("incident_id")):
                self.assertIn(
                    props.get("confidence"), ("exact", "matched"),
                    "an ambiguous or unresolved incident reached the map",
                )
                self.assertIsNotNone(f["geometry"], "plotted incident has no geometry")

    def test_periodic_reports_are_never_plotted(self):
        """A West Bank-wide report pinned to one village would be a fabrication."""
        fc = load("incidents.geojson")
        for f in fc["features"]:
            with self.subTest(incident=f["properties"].get("incident_id")):
                self.assertNotEqual(
                    f["properties"].get("record_type"), "periodic_report",
                    "a territory-wide periodic report was plotted at a point",
                )

    def test_withheld_records_are_counted_not_dropped(self):
        fc = load("incidents.geojson")
        meta = fc.get("metadata", {})
        unplaced = load("incidents_unplaced.json")
        self.assertEqual(
            meta.get("withheld"), unplaced.get("count"),
            "withheld count does not match the retained unplaced records",
        )
        self.assertEqual(
            meta.get("rendered", 0) + meta.get("withheld", 0),
            meta.get("total_records"),
            "records went missing between crawl and output",
        )


class LocalitiesAreReconciled(unittest.TestCase):
    """One place, one dot.

    OCHA and Palestine Open Maps both record Palestinian localities. Drawn as
    separate layers they produced visible double dots, and clicking could report
    a neighbour's name — al-Zaytouneh's panel appearing over Abu Shukheidim.
    """

    def test_no_two_localities_share_exact_coordinates(self):
        fc = load("localities.geojson")
        seen: dict[tuple, str] = {}
        for f in fc["features"]:
            key = tuple(f["geometry"]["coordinates"])
            name = f["properties"].get("name", "?")
            with self.subTest(name=name):
                self.assertNotIn(
                    key, seen,
                    f"'{name}' sits on the exact coordinates of '{seen.get(key)}' — "
                    f"a click cannot tell them apart",
                )
            seen[key] = name

    def test_conflicted_records_are_withheld_and_counted(self):
        fc = load("localities.geojson")
        conflicts = load("locality_conflicts.json")
        self.assertEqual(
            fc.get("metadata", {}).get("withheld_coordinate_conflicts"),
            conflicts.get("count"),
            "withheld count does not match the retained conflict records",
        )
        # Every withheld record must say what it collided with.
        for rec in conflicts.get("records", []):
            with self.subTest(record=rec.get("withheld")):
                self.assertTrue(rec.get("shares_coordinates_with"))

    def test_no_locality_is_both_depopulated_and_present_day(self):
        """A place cannot have been depopulated in 1948 and still be inhabited.

        Widening the merge produced exactly this: Palestine Open Maps' Jerusalem
        record, covering neighbourhoods depopulated in 1948, merged into OCHA's
        present-day East Jerusalem community. Different places, and on this map
        a consequential difference.
        """
        fc = load("localities.geojson")
        for f in fc["features"]:
            p = f["properties"]
            if p.get("depopulated_1948") and not p["locality_id"].startswith("pom-"):
                self.fail(
                    f"'{p.get('name')}' is listed by OCHA as a present-day community "
                    f"and marked depopulated in 1948"
                )

    def test_historical_positions_are_plausible(self):
        """A historical position must be near its present-day one, not anywhere."""
        import math

        fc = load("localities.geojson")
        for f in fc["features"]:
            hist = f["properties"].get("historic_coordinates")
            if not hist:
                continue
            lon, lat = f["geometry"]["coordinates"]
            d = math.hypot(
                (hist[0] - lon) * math.cos(math.radians(31.9)) * 111_320,
                (hist[1] - lat) * 111_320,
            )
            with self.subTest(name=f["properties"].get("name")):
                self.assertLess(
                    d, 2600,
                    "historical position is further from the present-day one than "
                    "the merge radius allows — the two records are not one place",
                )

    def test_merged_localities_cite_both_sources(self):
        """A merged record must keep both citations, not silently drop one."""
        fc = load("localities.geojson")
        merged = [
            f for f in fc["features"]
            if len(f["properties"].get("evidence_ref", [])) > 1
        ]
        self.assertTrue(merged, "no locality carries more than one citation")
        table = load("meta.json").get("evidence", {})
        for f in merged[:50]:
            sources = {
                table[r]["source_id"] for r in f["properties"]["evidence_ref"] if r in table
            }
            with self.subTest(name=f["properties"].get("name")):
                self.assertGreaterEqual(len(sources), 1)


class CoverageIsAUnion(unittest.TestCase):
    """Selecting two measures must count shared ground once, not twice."""

    def _coverage(self):
        cov = (load("meta.json").get("stats") or {}).get("coverage") or {}
        if not cov.get("combinations"):
            raise unittest.SkipTest("coverage not computed")
        return cov

    def test_combined_never_exceeds_the_sum(self):
        cov = self._coverage()
        combos = cov["combinations"]
        for key, value in combos.items():
            parts = key.split("+")
            if len(parts) < 2:
                continue
            naive = sum(combos[p]["km2"] for p in parts)
            with self.subTest(combination=key):
                self.assertLessEqual(
                    value["km2"], naive + 0.5,
                    "a union cannot be larger than the sum of its parts",
                )

    def test_combined_never_less_than_its_largest_part(self):
        cov = self._coverage()
        combos = cov["combinations"]
        for key, value in combos.items():
            parts = key.split("+")
            if len(parts) < 2:
                continue
            largest = max(combos[p]["km2"] for p in parts)
            with self.subTest(combination=key):
                self.assertGreaterEqual(
                    value["km2"], largest - 0.5,
                    "adding a measure cannot reduce the ground covered",
                )

    def test_built_up_sits_inside_municipal(self):
        """The containment the running total exists to handle."""
        combos = self._coverage()["combinations"]
        built = combos["built_up"]["km2"]
        muni = combos["municipal"]["km2"]
        both = combos["built_up+municipal"]["km2"]
        self.assertLess(
            both, built + muni,
            "built-up and municipal must overlap; if they did not, the running "
            "total would be a plain sum and this feature would be pointless",
        )

    def test_rasterised_denominator_matches_the_polygon_area(self):
        """The grid is only trustworthy if it reproduces a known figure."""
        cov = self._coverage()
        stats = load("meta.json")["stats"]
        self.assertAlmostEqual(
            cov["denominator_km2"] / stats["west_bank_km2"], 1.0, delta=0.02,
            msg="rasterised West Bank area diverges from the polygon area by "
                "more than 2% — the grid is not reliable",
        )


class TimelineIsHonest(unittest.TestCase):
    """The slider must not imply a history the sources cannot support."""

    def _timeline(self):
        t = (load("meta.json").get("stats") or {}).get("timeline") or []
        if not t:
            raise unittest.SkipTest("timeline not computed")
        return t

    def test_coverage_never_decreases_over_time(self):
        """Land taken does not un-take itself."""
        previous = -1.0
        for entry in self._timeline():
            with self.subTest(year=entry["label"]):
                self.assertGreaterEqual(
                    entry["km2"], previous - 0.5,
                    "cumulative coverage fell between marks",
                )
            previous = entry["km2"]

    def test_historical_marks_declare_they_are_dated_only(self):
        """Built-up has no construction history and must not be implied into one."""
        for entry in self._timeline():
            if entry["label"] != "Today":
                with self.subTest(year=entry["label"]):
                    self.assertTrue(
                        entry.get("dated_only"),
                        "a historical mark must state that it counts only measures "
                        "carrying dates",
                    )

    def test_every_mark_changes_the_figure(self):
        """A mark that moves nothing is decoration on an evidence map."""
        values = [e["km2"] for e in self._timeline()]
        self.assertEqual(
            len(values), len(set(values)),
            "two marks report the same area — one of them earns nothing",
        )


class NoInventedNames(unittest.TestCase):
    """Rule: never guess a settlement's identity from size and position."""

    def test_unnamed_settlements_are_marked_not_guessed(self):
        fc = load("settlements_built_up.geojson")
        for f in fc["features"]:
            name = f["properties"].get("name", "")
            if name.startswith("Unidentified settlement"):
                # Must be traceable back to a source polygon, not a made-up label.
                self.assertRegex(
                    name, r"^Unidentified settlement \((gid|orphan|name)-",
                    "unnamed settlements must carry their source key",
                )


class MinimumStageRule(unittest.TestCase):
    """Rule: assert only the minimum stage the evidence supports."""

    def test_no_stage_predates_its_evidence(self):
        fc = load("settlements_built_up.geojson")
        for f in fc["features"]:
            for step in f["properties"].get("stage_history", []):
                with self.subTest(entity=f["properties"].get("entity_id")):
                    self.assertTrue(
                        step.get("valid_from"),
                        "a stage was recorded with no date — that is a claim "
                        "without evidence",
                    )

    def test_no_stage_beyond_what_the_source_proves(self):
        """OCHA proves construction started; it does not prove occupancy."""
        fc = load("settlements_built_up.geojson")
        for f in fc["features"]:
            stages = [s["stage"] for s in f["properties"].get("stage_history", [])]
            with self.subTest(entity=f["properties"].get("entity_id")):
                self.assertNotIn(
                    7, stages,
                    "stage 7 (populated) asserted, but no population source is "
                    "integrated — see docs/data-gaps.md",
                )


class MechanismsStayDistinct(unittest.TestCase):
    """Rule: never conflate mechanisms of land loss."""

    def test_depopulation_is_confined_to_1947_50(self):
        fc = load("localities.geojson")
        for f in fc["features"]:
            props = f["properties"]
            if props.get("depopulated_1948"):
                date = props.get("depopulated_date", "")
                with self.subTest(locality=props.get("name")):
                    self.assertRegex(date, r"^(1947|1948|1949|1950)")

    def test_depopulation_sizing_prefers_palestinian_population(self):
        """In mixed cities the total overstates displacement by more than 2x."""
        fc = load("localities.geojson")
        mixed = [
            f["properties"] for f in fc["features"]
            if f["properties"].get("pop_1945_palestinian")
            and f["properties"].get("pop_1945_total")
        ]
        self.assertTrue(mixed, "no locality carries both figures — sizing cannot be checked")
        for p in mixed:
            with self.subTest(locality=p.get("name")):
                self.assertLessEqual(
                    p["pop_1945_palestinian"], p["pop_1945_total"],
                    "Palestinian population exceeds the locality total",
                )


class ExtentsStayDistinct(unittest.TestCase):
    """Rule: never conflate the three extent definitions."""

    def test_all_three_extents_ship_with_definitions(self):
        for extent in ("built_up", "municipal", "regional_council"):
            fc = load(f"settlements_{extent}.geojson")
            meta = fc.get("metadata", {})
            with self.subTest(extent=extent):
                self.assertEqual(meta.get("extent_type"), extent)
                self.assertTrue(
                    meta.get("definition"),
                    "an extent layer shipped without its definition",
                )

    def test_empty_extents_are_present_not_hidden(self):
        """Empty layers must exist so the UI can say 'no data yet'."""
        for extent in ("municipal", "regional_council"):
            fc = load(f"settlements_{extent}.geojson")
            self.assertEqual(fc["type"], "FeatureCollection")


class GeometryIntegrity(unittest.TestCase):
    def test_coordinates_fall_within_historic_palestine(self):
        """A CRS error shifts features by tens of metres — or continents."""
        for layer in ("settlements_built_up.geojson", "firing_zones.geojson",
                      "localities.geojson"):
            fc = load(layer)
            xs, ys = [], []

            def walk(c):
                if c and isinstance(c[0], (int, float)):
                    xs.append(c[0])
                    ys.append(c[1])
                    return
                for part in c:
                    walk(part)

            for f in fc["features"]:
                if f.get("geometry"):
                    walk(f["geometry"]["coordinates"])

            with self.subTest(layer=layer):
                self.assertGreater(min(xs), 33.9, f"{layer}: longitude out of range")
                self.assertLess(max(xs), 36.5, f"{layer}: longitude out of range")
                self.assertGreater(min(ys), 29.4, f"{layer}: latitude out of range")
                self.assertLess(max(ys), 33.5, f"{layer}: latitude out of range")

    def test_source_crs_is_recorded_on_measured_layers(self):
        fc = load("settlements_built_up.geojson")
        for f in fc["features"]:
            with self.subTest(entity=f["properties"].get("entity_id")):
                self.assertTrue(
                    f["properties"].get("source_crs"),
                    "source CRS not recorded — reprojection cannot be audited",
                )

    def test_polygon_rings_are_closed(self):
        for layer in ("settlements_built_up.geojson", "oslo_areas.geojson",
                      "firing_zones.geojson"):
            fc = load(layer)
            for f in fc["features"]:
                geom = f.get("geometry") or {}
                polys = (
                    [geom["coordinates"]] if geom.get("type") == "Polygon"
                    else geom.get("coordinates", []) if geom.get("type") == "MultiPolygon"
                    else []
                )
                for rings in polys:
                    for ring in rings:
                        with self.subTest(layer=layer):
                            self.assertGreaterEqual(len(ring), 4)
                            self.assertEqual(
                                ring[0], ring[-1],
                                f"{layer}: unclosed ring after simplification",
                            )


class CrsVerification(unittest.TestCase):
    """Rule: a declared CRS that disagrees with the .prj must raise."""

    def test_mismatched_crs_raises(self):
        from etl.geo import CrsMismatch, identify_crs

        wgs84_prj = (
            'GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",'
            '6378137.0,298.257223563]],PRIMEM["Greenwich",0.0],'
            'UNIT["Degree",0.0174532925199433]]'
        )
        with self.assertRaises(CrsMismatch):
            identify_crs(wgs84_prj, declared="EPSG:32636")

    def test_matching_crs_passes(self):
        from etl.geo import identify_crs

        wgs84_prj = (
            'GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",'
            '6378137.0,298.257223563]],PRIMEM["Greenwich",0.0],'
            'UNIT["Degree",0.0174532925199433]]'
        )
        _, resolved = identify_crs(wgs84_prj, declared="EPSG:4326")
        self.assertEqual(resolved, "EPSG:4326")


class SourceRegistryDiscipline(unittest.TestCase):
    """Rule: never enable a source without recorded permission."""

    def test_disabled_sources_produce_no_output(self):
        from etl.sources import SOURCES

        table = load("meta.json").get("evidence", {})
        used = {ev.get("source_id") for ev in table.values()}
        for source_id in used:
            with self.subTest(source=source_id):
                self.assertIn(source_id, SOURCES, "output cites an unregistered source")
                self.assertTrue(
                    SOURCES[source_id].enabled,
                    f"{source_id} is disabled in the registry but appears in output",
                )

    def test_no_enabled_source_has_an_unresolved_licence(self):
        """Anything shipping must have a licence position, not a question mark.

        This replaced a weaker test that merely asserted the *unresolved* status
        of two sources was recorded. Both Palestine Open Maps and B'Tselem have
        since granted permission, so the useful invariant is now the stronger
        one: nothing ships with an unknown licence.
        """
        from etl.sources import SOURCES

        for sid, source in SOURCES.items():
            if not source.enabled:
                continue
            with self.subTest(source=sid):
                licence = source.licence.lower()
                self.assertNotIn("unknown", licence, f"{sid} ships with an unknown licence")
                self.assertNotIn("undeclared", licence, f"{sid} ships with an undeclared licence")

    def test_remaining_licence_risks_stay_recorded(self):
        """historical-basemaps is GPL-3.0 and that is still unresolved."""
        from etl.sources import SOURCES

        self.assertIn("gpl", SOURCES["historical_basemaps"].licence.lower())


class AttributionConditions(unittest.TestCase):
    """Conditions attached to granted permissions must actually travel with the data."""

    def test_pom_conditions_are_published(self):
        attribution = load("meta.json").get("attribution", {})
        self.assertTrue(
            attribution.get("pom_accuracy_note"),
            "Palestine Open Maps asked that the accuracy caveat be stated; it is missing",
        )
        underlying = attribution.get("pom_underlying_sources") or []
        for required in (
            "Palestine Remembered",
            "Institute for Palestine Studies",
            "Palestine Lands Society",
            "Palestinian Central Bureau of Statistics",
            "Israeli Central Bureau of Statistics",
            "Zochrot",
            "B'Tselem",
        ):
            with self.subTest(source=required):
                self.assertIn(required, underlying)

    def test_btselem_is_credited(self):
        attribution = load("meta.json").get("attribution", {})
        self.assertIn(
            "B'Tselem", attribution.get("btselem_note", ""),
            "B'Tselem's licence requires them to be named expressly",
        )


if __name__ == "__main__":
    unittest.main()


class OsloClassesAreDisambiguated(unittest.TestCase):
    """Rule 3, applied to the Oslo split: never conflate two definitions.

    OCHA publish Area A and Area B under the same CLASS='A' label. Shipping
    that unchanged asserted 35.7% of the West Bank as Area A when the figure
    is 17.4%, which overstates Palestinian control by roughly two-fold.
    """

    def setUp(self):
        self.fc = load("oslo_areas.geojson")
        self.by = {}
        for f in self.fc["features"]:
            self.by.setdefault(f["properties"].get("oslo_class"), []).append(f)

    def test_area_a_and_b_are_separate_classes(self):
        self.assertIn("A", self.by, "Area A missing from the Oslo layer")
        self.assertIn("B", self.by, "Area B missing — the source relabel did not run")
        self.assertEqual(len(self.by["A"]), 1, "Area A must be exactly one polygon")

    def test_relabelled_features_say_so(self):
        for f in self.by.get("B", []):
            self.assertIn(
                "class_corrected", f["properties"],
                "a relabelled polygon must carry its correction note",
            )

    def test_shares_match_the_published_figures(self):
        # OCHA publish A 18%, B 22%, C 60%. This file breaks Nature Reserve,
        # East Jerusalem and No Man's Land out of those buckets, so B and C
        # read low; A is not affected and is the check that the split is the
        # right way round. A wrong assignment would put A near 18.3%/35%.
        from etl.geo import geometry_area_m2
        area = {k: sum(geometry_area_m2(f["geometry"]) for f in v)
                for k, v in self.by.items()}
        total = sum(area.values())
        pct = {k: 100 * v / total for k, v in area.items()}
        self.assertAlmostEqual(pct["A"], 18.0, delta=1.5,
                               msg=f"Area A at {pct['A']:.2f}% — split may be inverted")
        self.assertAlmostEqual(pct["C"], 60.0, delta=2.0,
                               msg=f"Area C at {pct['C']:.2f}%")
        self.assertGreater(pct["B"], pct["A"],
                           "Area B is the larger of the two in every published figure")
