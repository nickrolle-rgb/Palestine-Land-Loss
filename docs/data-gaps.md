# Data gaps

What the map cannot currently show, why, and what would close each gap. This
file is the honest counterweight to the map itself — if a gap here is not also
visible in the UI, that is a bug.

## 1. Planning stages 1–5 are unpopulated

**Status:** blocking the core premise.

The seven-stage pipeline is the intellectual core of the project, but OCHA
publishes *geography*, not *planning records*. Nothing in the openly licensed
data carries a land declaration date, a plan deposit date, an HPC approval date
or a tender date.

The ETL therefore asserts only the minimum stage each source supports: a
built-up footprint observed on 2021-06-03 proves construction had started by
then, and nothing earlier. No stage-1–5 dates are fabricated.

**Consequence:** the time slider drops to zero before 2021. The UI names this
explicitly rather than appearing broken.

**To close:** Peace Now Settlement Watch. Their planning-stage data is published
as reports and tables rather than clean GeoJSON, so this is extraction work, not
a download. Permission draft in `permissions/peace-now.md`.

## 2. Jurisdiction extents — municipal now sourced, regional council still not

**Status:** largely closed 2026-08-11.

B'Tselem granted permission and supplied the data. The map now ships four
measures: built-up (1.0% of the West Bank), settlement boundary (3.2%),
municipal jurisdiction (9.2%) and regional council (still empty). The
order-of-magnitude spread the project was designed around is now demonstrated
from a single consistent source rather than asserted.

**Still missing: regional council jurisdiction.** That layer continues to ship
visibly empty and labelled "no data yet". Regional councils cover a far larger
share of Area C than any measure currently shown, so its absence understates the
total. Worth asking B'Tselem whether they hold it.

### Original note

**Status:** blocking the project's defining honesty decision.

Built-up footprint, municipal jurisdiction and regional council jurisdiction
differ by an order of magnitude. Shipping only the built-up layer understates
encroachment; shipping only regional council jurisdiction overstates the daily
footprint. The schema models all three and the client renders all three, but
only built-up has data.

The two empty layers are rendered as disabled toggles labelled "no data yet"
rather than being hidden, so the absence is visible.

**To close:** B'Tselem is the primary candidate. Permission draft in
`permissions/btselem.md`.

## 3. Outposts — inventory now sourced, authorisation dates still missing

**Status:** largely closed 2026-08-11.

B'Tselem's boundary file types every feature, giving **127 outposts** covering
24.9 km², alongside 156 settlements and 18 industrial zones. The parallel track
the schema has modelled since the start finally has data in it.

**Still missing: `retroactive_authorisation_date`.** The field exists and is
rendered, but nothing populates it. Retroactive authorisation is the mechanism
that makes outposts distinctive — built without Israeli government
authorisation, illegal under Israeli domestic law as well as international law,
then legalised after the fact. Without dates, the map can show that a place is
an outpost but not when it was authorised.

**To close:** Peace Now tracks authorisation decisions; Kerem Navot covers the
land-use side.

## 4. Unnamed settlement polygons

24 of the 201 source polygons have a blank `Name`. Ten were recovered by joining
on `GIS_ID` to a named part of the same settlement; grouping by `GIS_ID` also
correctly merged multi-part settlements, reducing 201 polygons to 160 entities.

The Peace Now layer does not name East Jerusalem settlements at all, which is
consistent with Israel treating them as Jerusalem municipality neighbourhoods
rather than settlements. Originally only Atarot and Ramot Allon carried names —
2 of 20.

**Largely closed, 2026-08-10.** Thirteen polygons were identified against
Wikidata (CC0) by requiring that an item's coordinate fall *inside* the polygon.
East Jerusalem is now 14 of 20 named. The anchor is re-verified on every build,
so a source revision that moves the geometry causes the identification to be
refused rather than silently misattached. Full table in `corrections.md`.

**Eleven polygons remain unidentified**, including `gid-760` — at 2.0 km² the
largest unnamed polygon in the dataset. Its size and position in north-east
Jerusalem make a particular identification tempting; that inference is exactly
what the rules forbid, so it stays unidentified until a source supports a name.

**To close the remainder:** a named reference with geometry, most likely
B'Tselem (permission pending) or OpenStreetMap. Note that OSM is ODbL, so
deriving names from it would attach share-alike obligations to the derived
database — Wikidata's CC0 was chosen partly to avoid that.

## 5. Base layer currency

| Layer | Data date |
|---|---|
| Settlements (built-up) | 2021-06-03 |
| Oslo areas (A/B/C, H1, H2) | 2019-07-22 |
| Palestinian communities | 2019-07-17 |
| Separation Barrier | January 2018 |
| Village boundaries | 2019-07-24 |

Every layer is labelled with the date of the data, never the date of the build.

## 6. Population time series

Stage 7 ("populated") and any population-over-time view need Israeli CBS annual
locality data. Not integrated. The communities layer carries a single 2017
population figure, and that field is dirty — values include `NA` and
cross-references like `with Ar Ram`. Non-numeric values are preserved as notes
rather than being coerced or dropped.

## 7. Pre-Mandate administrative boundaries — not drawn

Late-Ottoman Palestine was not one administrative unit. The Mutasarrifiyya of
Jerusalem — an independent sanjak reporting directly to Constantinople from 1872
— covered the south; the sanjaks of Nablus and Acre sat under the Vilayet of
Beirut.

**No GIS dataset of those boundaries could be located.** Checked:

| Source | Result |
|---|---|
| `aourednik/historical-basemaps` | Ottoman Empire as a single polygon in `world_1900`; no sub-imperial divisions |
| OpenHistoricalMap (Overpass) | Ottoman entities at admin_level 2 only; level 4/6 boundaries begin 1953 |
| Academic/GIS repositories | Nothing published found |

Per the rule against guessed geometry, they are not drawn. The period is
represented instead by the **PEF Survey of Western Palestine (surveyed 1871–77)**,
which is genuine surveyed cartography, and by a textual account in the About
panel.

**To close:** the Institute for Palestine Studies' Ottoman Palestine project, or
digitisation from a published Ottoman administrative atlas. Any resulting
boundaries must be recorded as derived-by-georeferencing, with the source sheet
cited, not presented as survey-grade.

## 8. Licences unresolved on two historical sources

| Source | Problem |
|---|---|
| Palestine Open Maps `pom-data` | **No licence declared at all.** Consuming their raster tiles with attribution is a different question from redistributing their locality database, which this build does. |
| `aourednik/historical-basemaps` | **GPL-3.0** — copyleft, and its implications for a derived geospatial database are not obvious. Used only for the Mandatory Palestine boundary. |

Both must be resolved before publication. Neither is currently disabled, because
the alternative is shipping a land-loss map with no historical layer at all — but
this is a deliberate, recorded risk rather than an oversight.

## 9. Resource destruction — covered for one area only

The map shows destruction of resource access (water, farmland, livestock, homes,
property) from OCHA's field-based monitoring: 2,904 verified records for 2025.

**It covers Masafer Yatta only** — 27 localities in the South Hebron Hills — and
**2025 only**. Twenty-four localities are plotted; three are withheld because
they do not resolve to exactly one entry in OCHA's own communities gazetteer,
taking 385 records with them. The largest of those, **Umm Dhorit** (370 records),
is genuinely absent from the OCHA Palestinian Communities layer — a mismatch
between two OCHA datasets, worth reporting upstream.

The UI states the coverage limit wherever the layer appears. This matters more
than usual: on a map, an empty area reads as "nothing happened" unless it is
explicitly labelled "not monitored".

The source's agricultural category is "farmland, crops, or irrigation systems".
It does **not** distinguish olive groves or vineyards, and neither does this map.
Naming crops the source does not name would be an invention.

**To close:** OCHA's demolition and displacement database is the West Bank-wide
equivalent, running from 2009 and disaggregated by structure type. It is
published solely as an embedded Power BI dashboard with no CSV, API or HDX entry.
A data request is drafted at `permissions/ocha-demolition-data.md`. B'Tselem also
holds agricultural and olive-tree data (permission pending).

## 10. Al-Haq coverage

Al-Haq publishes narrative HTML, not a geolocated database. Of 71 crawled
records: 47 are locatable field stories and 24 are territory-wide periodic
reports. Of the 47 field stories, 31 resolved to exactly one locality (9 from
the title alone; body-text matching added 22), 5 were ambiguous and 11
unresolved.

Periodic reports are indexed and linked but never plotted — pinning an annual
West Bank-wide report to one locality because a place name appears in its title
would be a fabrication.

**To close:** better recall needs either Arabic-language matching against the
Arabic site, or manual curation. Neither should lower the bar for plotting.
