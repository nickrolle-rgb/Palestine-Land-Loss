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

## 11. Gaza — four usable layers, and the current ones are pre-war

`SCOPE.md` put Gaza out of scope. That is no longer the right call for a map
called Palestinian Land Loss.

**Correction, 2026-08-12.** An earlier version of this section said Gaza was
"almost entirely absent" from open data. That was wrong — it came from searching
HDX for damage and buffer keywords and missing OCHA's Gaza administrative set.
All four below were downloaded and parsed with the existing GDAL-free stack:

| Dataset | Licence | Parsed | Note |
|---|---|---|---|
| Gaza Strip Municipal Boundaries | CC BY | 33 features, **365 km²** | The Strip's canonical area — gives Gaza a *computed* denominator, the same self-check the Oslo polygons provide for the West Bank |
| Gaza Strip Buffer Area | CC BY | 3 features, **83 km²** | "Closed and access restricted areas". **22.7% of the Gaza Strip** |
| Gaza Strip Fishing Zone (2019) | CC BY | 1 feature, 964 km² | The maritime limit imposed by Israel — access restriction by sea |
| Gaza Strip Neighbourhoods | CC BY | points | Locality detail |

**But every one of them predates the current war**: the buffer area was last
updated 2023-10-19 and the rest 2019-07-18. They describe the Gaza of before
October 2023, and any layer built from them must say so on its face — the
failure mode here is a reader taking a 2019 fishing limit or a 2023 buffer for
the situation today.

**What the map currently holds for Gaza:** 152 localities and 10 depopulated
1948 records, inherited from Palestine Open Maps' historic-Palestine coverage.
**No area layer at all** — every polygon layer on the map (settlements,
municipal, firing zones, Oslo, villages) has zero vertices inside the Strip.

**Still not available as data — the Yellow Line and Orange Line.** The Yellow
Line is the demarcation from the ceasefire of 10 October 2025; the Orange Line
the wider restricted-access zone. OCHA reports the restricted area at **64.9% of
the Gaza Strip by June 2026, up from 53%**. Both appear in OCHA's published maps;
neither is on HDX in any geospatial format. Same failure as the demolition
database — published, drawn, not machine-readable. Requested in
`permissions/ocha-demolition-data.md`.

**Available with obstacles — UNOSAT damage assessments.** Buildings, cropland
with FAO, roads, greenhouses, the 1 km perimeter strip, 2023 to 2025. Two
problems: **CC BY-SA**, whose share-alike would attach to this project's derived
database, and mostly **Geodatabase**, which the GDAL-free ETL cannot read.

The denominator question is answered: Gaza's municipal boundaries sum to 365 km²,
so a Gaza percentage can be computed exactly as the West Bank's is, from geometry
on the map rather than a quoted figure.

## 12. Beyond the West Bank — what exists, researched 2026-08-12

The project is called Palestinian Land Loss but measures *area* in the West Bank
only. That is a real shortfall, not a presentational one. This records what is
available to close it.

### Displacement across all fields — available and verified

**UNRWA Palestine Refugees** (CC BY-IGO, XLSX, updated quarterly, last 2025 Q4)
was downloaded and parsed successfully. It is the consequence of the loss this
map documents, counted where the displaced ended up:

| Field | Registered refugees |
|---|---|
| Jordan | 2,398,179 |
| Gaza | 1,545,991 |
| West Bank | 938,589 |
| Syria | 357,985 |
| Lebanon | 228,274 |
| Unknown | 495,764 |
| **Total** | **5,964,782** |

Broken down by sex and age band, quarterly back through the series. Not
geolocated — it is field-level aggregate — so it belongs in a table or a
five-field choropleth, not as points.

Reading it needs `openpyxl`, a pure-Python addition with no system dependencies,
which is the first non-shapefile format the ETL would take on.

### Also available

| Dataset | Publisher | Licence | Note |
|---|---|---|---|
| State of Palestine — Subnational Population Statistics | PCBS via OCHA | CC BY-IGO | CSV; population by governorate |
| Escalations in Gaza — Killed & Injured Persons | OCHA | CC BY | XLSX |
| State of Palestine — Health Facilities | OCHA | CC BY | SHP — has geometry, covers Gaza |
| Palestinian Camp in Lebanon | — | CC BY | XLSX |

### Detention — moved to a sibling project, 2026-08-12

Detention was researched as a candidate layer and deliberately ruled out. It is
theft of freedom rather than land: a real continuity with what this map
documents, and a different claim resting on different evidence. It has no
locality-level geodata, so it could only ever be a table, and folding it into a
land map would have blurred both arguments.

Scoped separately in `sibling-project-detention.md`, including the sources
already found, the access obstacles, and the constraints any such project would
inherit. This map should link to it rather than absorb it.

### What would actually close this gap

In order of value:

1. **UNRWA registered refugees** — verified above. The largest single step from
   "West Bank areas" to Palestine-wide.
2. **The four Gaza layers** in §11 — gives Gaza its first measured area and its
   own computed denominator.
3. **Regional council jurisdiction** from B'Tselem — the missing West Bank
   measure, and probably the largest.

## 13. Worked example — two news events, 13 August 2026

Two articles were checked against the build to test a plain question: can this
map document what happened this week?

### Demolition at Ein el-Hilweh, northern Jordan Valley

Two homes of the Daraghmeh family demolished on 2 and 28 July 2026. The family
held an Israeli Supreme Court injunction; no formal demolition order was
presented.

- **The place is on the map.** `Ein al Hilwa` (Tubas), plus `Ein al Hilwa - Wadi
  al Faw` and `Ein al Hilwa - Um al Jmal`.
- **The event is not.** Our Al-Haq layer holds 31 plotted records and none from
  July 2026; the OCHA resource-destruction layer covers Masafer Yatta and 2025
  only, and the Jordan Valley is outside it.
- **OCHA does hold it.** The article cites OCHA for the aggregates — more than
  **907 Palestinian structures demolished in the West Bank this year**, and more
  than **6,200 Palestinians forcibly displaced since January 2023, including
  3,000 children**. OCHA's own page states demolitions usually appear there
  within 48 hours.

So the data exists, is current within two days, and is **published only as an
embedded Power BI dashboard**. This is the request already drafted in
`permissions/ocha-demolition-data.md`, and this is what it costs.

### Re-establishment of Ganim, northern West Bank

Around 30 settler families returned on 13 August 2026, following the December
2025 cabinet decision granting legal status to 19 settlements. Ganim was
evacuated under the 2005 disengagement, along with Kadim, Homesh and Sa-Nur.

The map handles this better than expected. Ganim, Homesh and Sa-Nur are **absent
from the settlement layers** — correctly, since B'Tselem's inventory records
settlements that exist — while Palestine Open Maps carries all three as
localities marked `status_now = "Abandoned"`, `group_now = "Jewish"`, with no
1945 population because they are post-1967 creations.

The map is therefore accurate as at 12 August 2026 and one day stale as at the
13th. Tracking that change is **settlement-approval data, which is Peace Now's**,
not OCHA's — the other outstanding request.

A detail worth keeping: `Sanur` (Jenin) is a Palestinian locality, status
`Remaining`, while `Sa-nur` (Samaria) is the abandoned settlement. Two places,
near-identical names. The type-aware handling built for Susiya keeps them apart.

### What "document when they happen" actually requires

Three things, none of them the map itself:

1. **The data published as data.** Both requests already cover this.
2. **A scheduled rebuild.** OCHA refreshes within 48 hours; this build runs when
   someone runs it. Currency is a pipeline property, not a data property.
3. **A rule for individual incidents.** Rule 6 forbids mapping individuals. A
   demolition is recorded at its locality with structure counts and displacement
   figures — never a named family or an address.

## 14. The WZO Settlement Division — a stage-1 actor with no public data

Since the early 1970s the Israeli government has allocated West Bank land
through the **Settlement Division of the World Zionist Organization**, a body it
finances and directs. Peace Now describe it as managing hundreds of thousands of
dunams on the State's behalf and transferring them to settlers without effective
supervision; the State Attorney's Office has put the grazing allocations alone at
roughly 80,000 dunams.

That makes it one of the largest single mechanisms of land transfer in the West
Bank, and it sits squarely at **stage 1** of our pipeline — the stage that is
already the least populated.

**Why it is a gap and not a task:** a 2015 law shields the Settlement Division
almost entirely from Israel's Freedom of Information Act. Kerem Navot, who have
done the most work on this, state plainly that they know allocations happened but
are blocked from the amounts, the recipients and the conditions, and have
contemplated litigation to force the database open. There is no dataset to
ingest, from them or anyone, because the State does not publish one.

**Status:** not drawn, not estimated, and not inferrable from settlement extents
— an allocation is not a building, and treating one as evidence of the other
would break non-negotiable 1. Recorded here so the absence is visible. If Kerem
Navot's petition ever succeeds this becomes the single highest-value ingest in
the project.

## 15. Gaza destruction — the data exists and we cannot read it

**UNOSAT** publish a Comprehensive Building Damage Assessment for the Gaza
Strip, updated roughly quarterly. The most recent is **11 October 2025** (5.0 MB,
published to HDX 2025-10-31). Their December 2024 assessment counted 170,812
damaged or destroyed structures, about 69% of all structures in the Strip.

**The licence is fine.** HDX records it as **CC BY-SA** — Attribution and
ShareAlike, with *no* NonCommercial clause. That is an open licence, and it is
less restrictive than the CC BY-NC-SA stated on UNOSAT's own hub page. The
ShareAlike condition binds *adaptations*, not works merely aggregated alongside
others, so publishing it as its own unmodified layer does not relicense the rest
of this database. It would bite if UNOSAT data ever fed a derived figure — a
`coverage.py` union or a combined percentage — so it must not.

**The format is the blocker.** Every current product ships only as an Esri File
Geodatabase (`.gdb`). This pipeline is deliberately GDAL-free (`pyshp` +
`pyproj`), and `pyshp` cannot read a geodatabase. The shapefile resources listed
against those HDX packages all resolve to `CE20140715PSE` — the **2014** Gaza
assessment, not the current one.

Third-party republications of the current data exist as ArcGIS feature services
under university and NGO accounts. They are not used: that would put an
unaccountable intermediary in the middle of the evidence chain for the single
most contested dataset in the project.

**Options, in the order I would try them:**

1. **Ask UNOSAT for a shapefile or GeoJSON export.** Their older products were
   shapefiles, they are a UN body, and this project already runs a permissions
   workflow. Costs nothing but time.
2. **Add `pyogrio`**, whose wheels bundle GDAL and need no system install. This
   reverses a documented design decision and is therefore not mine to make.
3. **Write a minimal OpenFileGDB reader.** Respects the constraint and is the
   riskiest path: silently mis-parsed binary geometry is worse than no layer.

**Currency, separately:** even UNOSAT's newest assessment is October 2025.

**And the framing it must carry when it lands** — see non-negotiable 11.
Destruction is not dispossession. People live in tent camps among the rubble;
that ground is not lost, prohibited or stolen, and the layer must never be
summed into a land-loss total.

## 16. Gaza access restrictions — no public geometry at all

OCHA report the restricted-access zone Israel calls the **"Yellow Line"** at
**64.9% of the Gaza Strip as at June 2026**, up from about 53% at the October
ceasefire. That figure is published in situation reports; **the polygon is not**.
Israel's military sent the maps to aid groups in mid-March 2026 and has not
released them publicly.

The only OCHA buffer geodata is **Gaza Strip Buffer Area** (CC BY), last updated
**2023-10-19** — the early-war perimeter buffer, not the current line.

So this is a gap no licensing decision can close. The percentage is citable
prose; the extent is not mappable from anything public. Recorded here rather
than approximated, because a hand-drawn line across Gaza would be
non-negotiable 2 at its worst.
