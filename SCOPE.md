# Settlement Encroachment Map — Scoping

**Concept:** An interactive map of Israeli settlement expansion in the occupied Palestinian
territory, showing every stage of development from plan to populated settlement, with a time
dimension, overlaid on what existed on that land before.

**Verdict:** The strongest of the three concepts. The data mostly exists, is openly licensed,
and nobody has assembled it into one time-sliderable map with a pre-1948/pre-occupation underlay.
Legal exposure is far lower than the Money Tracker because you're mapping state planning records
and geography, not making allegations about named private parties. Narrow v1: 4–6 weeks.
Credible full v1: 3–4 months.

---

## 1. Your four stages are too coarse — use the real pipeline

"Concept / planning / clearing / settlement" is the right instinct, but Israeli settlement
development follows a documented administrative pipeline, and each step generates a *dated public
record*. Using the real stages means every pixel on your map is citable:

| Stage | What happens | Evidence source |
|---|---|---|
| 1. Land declaration/seizure | Land declared "state land", military seizure order, or survey | Civil Administration records, Kerem Navot, Peace Now |
| 2. Plan deposited | Plan lodged with the Higher Planning Committee | Peace Now Settlement Watch |
| 3. Plan approved/validated | HPC validation | Peace Now |
| 4. Tenders published | Ministry of Housing tenders units | Peace Now, Israeli govt tender publications |
| 5. Ground works | Roads, infrastructure, site clearing, bulldozing | Satellite (Sentinel-2/Landsat), Peace Now aerial surveys |
| 6. Construction starts | Foundations, units under construction | Peace Now construction-start counts, Israeli CBS |
| 7. Populated | Residents present, population reported annually | Israeli CBS, settlement municipal data |

**Plus a parallel track you must model separately: outposts.** Outposts are settlements built
without Israeli government authorisation — illegal under Israeli domestic law as well as
international law — and many are later *retroactively authorised*, jumping straight to stage 7.
If you force outposts through the same linear pipeline your map will be wrong. Model them as a
distinct entity type with a `retroactive_authorisation_date`.

This taxonomy is the intellectual core of the project. It's what makes it more than a prettier
version of maps that already exist.

---

## 2. The honesty decision that defines the project

There are three completely different ways to draw "how much land is taken", and they differ by an
order of magnitude:

- **Built-up footprint** — the actual buildings and roads. Small (low single-digit % of the West Bank).
- **Municipal jurisdiction** — the settlement's declared boundary, usually far larger than what's built.
- **Regional council jurisdiction** — vast; covers a large share of Area C.

Pick one and you're either understating the encroachment or overstating the daily footprint, and
either way someone will (fairly) call it misleading. **Render all three as independently
toggleable layers with the definition stated in the legend.** This costs you maybe two days of
work and it's the difference between a tool that survives scrutiny and one that gets dismissed.

Same principle for the "what was there before" underlay: label precisely what the historical layer
*is* (e.g. "Survey of Palestine 1:20,000, surveyed 1940–1945"), not a vague "before".

---

## 3. Data sources

**Geography & settlements**
- **OCHA oPt / HDX** — settlement outlines, outposts, Area A/B/C, the Barrier, checkpoints,
  admin boundaries (COD-AB, 2023 reference year). Shapefiles + geodatabase, humanitarian licence.
  `data.humdata.org` and `ochaopt.org/page/datasets-and-mapping-tools`. This is your base layer.
- **B'Tselem** — settlement map and land-control analysis; the source for the built-up vs
  jurisdiction distinction above.
- **Peace Now (Settlement Watch)** — *the* source for planning stages, construction starts,
  tenders and outpost tracking. Largely published as reports/tables rather than clean GeoJSON,
  so expect real extraction work.
- **Kerem Navot** — land-use and agricultural-takeover research; strongest on stages 1 and 5.
- **Israeli CBS** — annual population per locality, for stage 7 and the time slider.

**Historical underlay**
- **Palestine Open Maps** (`palopenmaps.org`) — georeferenced British Mandate Survey of Palestine
  1:20,000 sheets plus digitised villages, roads and features. This is exactly the "towns and
  roads that were previously there" layer you described, and the georeferencing is already done.
  Don't rebuild it.
- **Village Statistics 1945** and Abu Sitta's *Atlas of Palestine* — for locality attributes and
  depopulated villages.
- **Historical aerial/satellite:** declassified CORONA imagery (1960s–70s) and Landsat (1972→)
  for the pre-settlement baseline.

**Change detection (stage 5)**
- **Sentinel-2** via Copernicus — 10m, ~5-day revisit, free. Bare-soil/NDVI differencing detects
  clearing and new roads reasonably well.
- Treat this as an optional research module, not MVP. Automated clearing detection is its own
  multi-week project with a real false-positive problem (agriculture, quarrying, fire scars).

---

## 4. Architecture

```
sources → ETL (per-source adapters) → canonical GeoPackage/PostGIS
                                            │
                                            ├→ tippecanoe → PMTiles (vector tiles)
                                            └→ historical rasters → PMTiles (raster)
                                                     │
                                            MapLibre GL client (static hosting)
```

- **PMTiles + MapLibre** is the right stack. Single-file tile archives served from object storage
  (or even GitHub Pages / R2) with HTTP range requests — no tile server, no running costs, and it
  handles both the vector settlement layers and the georeferenced historical raster sheets.
- **Time model:** don't store "one polygon per year". Store each feature once with a **stage
  history**: `(feature_id, stage, valid_from, valid_to, evidence_ref)`. The time slider then
  resolves "what stage was this on date D". This is also what makes every element on the map
  clickable through to a source.
- **Projections:** you'll meet Palestine Grid 1923 (EPSG:28193), Israeli TM Grid (EPSG:2039) and
  WGS84. Reproject everything to EPSG:4326 at ingest and record the source CRS. Getting this
  subtly wrong shifts features by tens of metres and will be the first thing critics test.
- **Comparison UI:** swipe/curtain between historical and current, plus per-layer opacity. Swipe
  is more legible than blend for this kind of before/after.

**Naming policy — decide it up front and document it.** Every locality potentially has an Arabic
name, a Hebrew name, a pre-1948 name and an OCHA transliteration. Recommendation: show the
Palestinian/Arabic name and the current official name together, with all known variants in the
feature detail panel, and state the policy in an "About the data" page. Silently picking one
naming scheme is the fastest way to make the whole map look partisan regardless of the underlying
data quality.

---

## 5. Terminology and legal footing

The illegality framing is well-supported and you should state it with citations rather than as
assertion: UN Security Council Resolution 2334 (2016), and the International Court of Justice
advisory opinion of July 2024 on the legal consequences of Israel's policies in the occupied
Palestinian territory. Australia's stated position is also that settlements are inconsistent with
international law. Cite these on an "About" page and the framing is a sourced legal finding, not
your editorial voice.

Risk profile here is genuinely low — you're mapping places and published state planning decisions,
not accusing identifiable private people of anything. The real risks are:

- **Licensing.** Check terms for OCHA/HDX (usually permissive), B'Tselem and Peace Now (may
  require permission for derived works — just ask, they generally want the reach). If you touch
  OpenStreetMap data, ODbL share-alike attaches to your derived database.
- **Accuracy.** A visible corrections log and a per-feature "source + date retrieved" panel.
- **Don't map individuals.** No settler names, no addresses of specific homes. Localities,
  parcels, plans and infrastructure only.

---

## 6. MVP scope

**Narrow v1 (4–6 weeks)** — prove the concept on one governorate, don't boil the ocean:
- One area (Bethlehem or Salfit governorate — dense, well-documented settlement growth)
- OCHA base layers + Palestine Open Maps historical underlay
- Settlements and outposts with the 7-stage model, hand-curated from Peace Now for that area
- Time slider across a handful of discrete dates (e.g. 1945, 1967, 1993, 2000, 2010, 2025)
- Swipe comparison, click-through to sources
- Static hosting, PMTiles

**Full v1 (3–4 months):** all of the West Bank incl. East Jerusalem, automated ETL refresh,
built-up/municipal/regional-council layer toggles, per-settlement population time series,
depopulated-village layer, export/embed.

**Out of scope for both:** automated satellite change detection, Gaza (different data situation
and a different story), any live/real-time component.

---

## 7. Relationship to the Money Tracker

These two share a layer. The Money Tracker needs to answer "is this recipient project located
beyond the Green Line, and in which settlement?" — that's exactly the entity+geography registry
this project builds. **Build this one first.** It's more tractable, lower risk, produces something
visually compelling on its own, and becomes the geographic backbone if you later pursue the
funding work.

## 8. Open questions

1. West Bank only, or include East Jerusalem (different legal/administrative regime, better data,
   more contested)? Recommend including it but modelling it separately.
2. How far back does "previously" go — 1967 (start of occupation, cleanest legal framing) or
   1948/Mandate-era (much stronger emotionally, more data work, broader claim)?
3. Are you willing to seek permission from Peace Now / B'Tselem for derived use, or do you need to
   restrict to OCHA/HDX-licensed data only?

**Sources:** [OCHA oPt datasets](https://www.ochaopt.org/page/datasets-and-mapping-tools) · [OCHA oPt on HDX](https://data.humdata.org/organization/1fddc052-2031-4365-8342-49b18f0e3307) · [B'Tselem interactive map](https://www.btselem.org/map)
