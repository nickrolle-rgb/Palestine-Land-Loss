# Corrections log

A visible corrections log is part of the project's credibility, not an
afterthought. Anything that turns out to be wrong gets an entry here, with the
date and what changed.

Format: `YYYY-MM-DD — what was wrong — what it is now — source for the change`.

## Open items

Known problems not yet fixed. These are also surfaced in the UI.

| Item | Detail | Blocked on |
|---|---|---|
| 6 unnamed East Jerusalem settlements | Was 18; 13 identified from Wikidata by containment (see below). `gid-760`, at 2.0 km² the largest unnamed polygon, is among those remaining. | A named reference with geometry — B'Tselem or OSM |
| 6 unnamed orphan polygons | Very small polygons (≤0.02 km²) with neither a name nor a usable `GIS_ID`. May be fragments rather than settlements. | Inspection |
| 16 withheld locality coordinate conflicts | Records sitting on the exact coordinates of a differently-named locality. Mostly Bedouin communities recorded at a neighbouring village's position. | Reporting upstream to OCHA and Palestine Open Maps |
| 332 unnamed municipal polygons | B'Tselem's municipal file carries no usable join key; 88 of 420 named by containment. | Asking B'Tselem for a keyed version |
| `Region` field typo in source | OCHA's communities layer contains the literal value `West Bsnk`. Normalised at ingest, not propagated. | Upstream — worth reporting to OCHA |
| Dirty `pop2017` values | Values include `NA` and cross-references such as `with Ar Ram`. Non-numeric values are preserved as notes rather than coerced. | Upstream |
| Barrier alignment is January 2018 | Latest openly published OCHA alignment. Labelled with its own date. | Newer OCHA release |

## Identification protocol for unnamed polygons

Do **not** infer a settlement's identity from its size and position, however
obvious it seems. Each identification needs a citable reference. Record here as:

```
2026-08-10 — gid-760 shown as "Unidentified settlement (gid-760)" —
identified as <name> — source: <reference, URL, date retrieved>
```

Then add the mapping to a curated overrides file so the ETL applies it on the
next build, and note in the entity's evidence that the name came from the
override source rather than from OCHA.

## Changes

**2026-08-12 — the municipal jurisdiction layer was populated but never drawn.**
Its checkbox did nothing. The 420 polygons were in the file and loaded fine, but
`applyTime()` drops any feature whose planning stage resolves to null, and a
municipal boundary has no stage history — it is a jurisdiction, not a settlement
moving through a pipeline. Every polygon was silently filtered out on each
render. Features without a stage history are now shown regardless of the slider,
honouring `declared_date` where the source provides one.

Worth noting how this hid: the data was correct, the layer existed, the toggle
worked, and nothing errored. Only the map was empty.

**2026-08-12 — Palestinian Oral History Archive linked from localities.** 726
recorded interviews across 133 villages, held by the American University of
Beirut Libraries and indexed by Palestine Open Maps. The join is exact — POM
files them under the same slug their locality database uses — so no name
matching or proximity is involved.

Licence is CC BY-NC-ND 4.0, so the same discipline as Al-Haq applies: title,
year, duration, language and record URL only. The archive's descriptions and its
indexed contents are its own editorial work and are not reproduced. Interview
metadata lives in `oral_histories.json` and is looked up on click rather than
carried on every map feature.

**2026-08-12 — payload cut from 6.5 MB to 5.5 MB.** Extent layers are now
simplified at about 5 m, below the accuracy of the source boundaries and
sub-pixel until zoom 18. Municipal halved, from 2,116 KB to 1,019 KB. Reported
areas are unaffected: they are computed from source geometry before
simplification and stored on the feature, never recomputed from what is drawn.


**2026-08-12 — localities carry a historical position as well as a present-day
one.** Points sat away from the villages they name on the historical sheets.
Palestine Open Maps records the 1945 village; OCHA records the present-day
administrative centre. Usually the gap is small (median 149 m) but it reaches
1,175 m at Beituniya. Merged localities now keep both coordinates, and the map
uses the historical one whenever a historical sheet is showing — 354 localities
move, and a note says so.

Palestine Open Maps was checked for vector data digitised from the survey sheets
that might align better. It does not exist: their `places.json` is 2,490 points
with the same coordinates as the CSV already ingested, and their only other
vector data is present-day OpenStreetMap tiles. Their `raw-data/poha/` directory
is the Palestinian Oral History Archive — interviews keyed to villages, not
geometry, and worth linking from depopulated localities later.

Two matching faults surfaced while investigating:

1. **Candidates were keyed on exact normalised names**, so `Beituniya` and
   `Beitunya` never landed in the same bucket to have their distance compared.
   Matching is now proximity-first, name-confirmed, which took merged pairs from
   311 to 472.
2. **Merging more widely created a contradiction.** Palestine Open Maps'
   Jerusalem record — the neighbourhoods depopulated in 1948 — merged into
   OCHA's present-day East Jerusalem community, producing one record asserting a
   place was both depopulated and inhabited. A locality depopulated in 1948 is
   now never merged into one OCHA lists as inhabited today. A test asserts it.

**2026-08-12 — the basemap was naming every village a second time.** The
reconciled data draws one dot per place, but CARTO labels the same villages from
OpenStreetMap, so places appeared twice in two transliterations (`Abu Shukhaidem`
beside `Abu Shukheidim`). Our labels carry the Arabic name alongside the
transliteration as the naming policy requires, so the basemap's populated-place
labels are hidden while the locality layer is on.

**2026-08-12 — deployed data could lag deployed code by an hour.** `vercel.json`
set `max-age=3600` on the data directory, so a browser held old GeoJSON while
HTML and JavaScript updated immediately. The interface reported counts from data
it was no longer using — "Depopulated in 1948: 0" against a file containing 467.
Correct data looked like missing data, which on this map is a claim in itself.
The browser now always revalidates; the CDN still caches until a deploy purges.


**2026-08-11 — the two locality datasets reconciled into one.** OCHA's
communities layer and Palestine Open Maps' locality database both record
Palestinian localities. Drawn as separate map layers they produced visible
double dots — Kobar, Burham, Deir Nidham and Abu Shukheidim each appearing
twice — and a click landed on whichever layer was on top, so the detail panel
could name a different place from the one under the cursor.

Now merged in the ETL: 850 current + 2,527 historic records resolve to **3,024
localities**, with **311 pairs merged**. A merged locality keeps OCHA's identity
and PCODE, Palestine Open Maps' history, both name variants and **both
citations**.

Merging requires the same name within **600 m**. That radius is not arbitrary:
same-name distances are sharply bimodal — half within 165 m, three quarters
within 376 m, then a gap, then a cluster beyond 5 km that is genuinely different
places sharing a name (Palestine has several localities called Zayta). 600 m
sits in the empty band. 25 same-name pairs fall between 600 m and 1,500 m and
are left separate rather than merged on a hunch.

**16 records are withheld for coordinate conflicts.** These sit on the exact
coordinates of a differently-named locality, so at least one position is wrong.
Where one source outranks the other, the authoritative record survives — this is
the reported `al-Zaytouneh` / `Abu Shukheidim` case, where Palestine Open Maps
gave al-Zaytouneh the coordinates of Abu Shukheidim while its own Abu Shukheidim
sat 200 m away. Where neither outranks the other — `Aqada` and `al-Bayada`, two
Palestine Open Maps records with adjacent ids and identical coordinates — both
are withheld, because keeping an arbitrary one would be a coin toss presented as
a fact.

Most of the remainder are Bedouin communities recorded at a neighbouring
village's coordinates (`Arab al-Jahalin` at Abu Dis, `al-Ka'abina` at Anata).
Worth reporting to both publishers.

Distinguishing a duplicate from a conflict needed more than exact name matching.
Transliteration varies systematically between the two sources — Bayt/Beit,
Dayr/Deir, Ayn/Ein, Khirbat/Khirbet — and `bayt mirsim` against `beit mirsim`
scores 0.818 on a similarity ratio, just under the 0.82 threshold. Those
equivalences are folded explicitly rather than by loosening the threshold, which
would have started merging genuinely different places. Clan qualifiers in
brackets are set aside for comparison too. Explicit folding took the withheld
count from 42 to 16, all real.


**2026-08-11 — B'Tselem data ingested; four source quirks handled.**
B'Tselem supplied four GeoJSON files under their licence for non-commercial use.
They fill the municipal jurisdiction layer and supply the outpost inventory.

Measured against each other they demonstrate, rather than assert, the premise
the project is built on:

These are B'Tselem's own three files measured against each other. Note the
built-up figure below is **B'Tselem's** `settlements.geojson`; the layer this map
ships as built-up is OCHA/Peace Now's, which measures 70.9 km² (1.25%). Both are
built-up footprints from different surveys, and the map uses the OCHA one.

| Measure | Area | % of West Bank | vs built-up |
|---|---|---|---|
| Built-up (B'Tselem) | 56 km² | 1.0% | — |
| Settlement boundary | 179 km² | 3.2% | 2.8× |
| Municipal jurisdiction | 520 km² | 9.2% | 7.0× |

Quirks handled at ingest, not propagated:

1. **The municipal file has no usable join key.** `GIS_ID` is 0 on all 420
   features and the Hebrew name column arrives mangled to underscores
   (`____ ____`), with 1 of 420 English names populated. Names are recovered by
   containment: a municipal polygon containing exactly one named settlement takes
   that name. 88 of 420 are named this way; 332 stay unnamed, of which 58 contain
   more than one settlement and are therefore ambiguous. None are guessed.
2. **`DATE_` contains impossible values** — the range runs from `1000-01-01` to
   `2094-11-17`. Validated against 1967-to-today; **29 values rejected**, 376
   retained.
3. **`Type` contains source typos** — `Ouptost` for `Outpost`, and one
   untranslated Hebrew value `התנחלות`. Mapped explicitly rather than
   normalised by guesswork.
4. **A `GeometryCollection` feature** in the boundary files, which the extent
   layers skip rather than mis-render.

**2026-08-11 — a fourth extent definition added.** B'Tselem's settlement outline
sits between built-up and municipal at 2.8× built-up. Rather than fold it into an
existing definition — the exact conflation the extent model exists to prevent —
it ships as `settlement_boundary` with its own stated definition. Which B'Tselem
file corresponds to which of their own definitions is inference from magnitude,
and confirmation has been sought.

**2026-08-10 — 13 unnamed settlement polygons identified from Wikidata.** East
Jerusalem went from 2 of 20 settlements named to 14 of 20.

Method: a Wikidata item's coordinate must fall **inside** the polygon.
Containment, not proximity — a nearest-neighbour match would be exactly the
"guess from size and position" the rules forbid. Each identification records the
QID, the anchor coordinate and the query tier that produced it, in
`etl/identifications.json`. **The anchor is re-verified on every build**: if a
source revision moves the geometry so the anchor no longer falls inside, the
identification is refused and the polygon reverts to unidentified. Wikidata is
CC0, so there is no attribution obligation; it is credited regardless.

| Source key | Identified as | Wikidata |
|---|---|---|
| gid-840 | Gilo | [Q1524664](https://www.wikidata.org/wiki/Q1524664) |
| gid-750 | Neve Yaakov | [Q2918013](https://www.wikidata.org/wiki/Q2918013) |
| gid-852 | Har Homa | [Q1584365](https://www.wikidata.org/wiki/Q1584365) |
| gid-830 | East Talpiot | [Q2920377](https://www.wikidata.org/wiki/Q2920377) |
| gid-115 | Ramat Shlomo | [Q951590](https://www.wikidata.org/wiki/Q951590) |
| gid-771 | French Hill | [Q1455257](https://www.wikidata.org/wiki/Q1455257) |
| gid-111 | Givat HaMivtar | [Q2919853](https://www.wikidata.org/wiki/Q2919853) |
| gid-112 | Ma'alot Dafna | [Q2900311](https://www.wikidata.org/wiki/Q2900311) |
| gid-113 | Ramat Eshkol | [Q2778124](https://www.wikidata.org/wiki/Q2778124) |
| gid-631 | Jewish Quarter | [Q1186403](https://www.wikidata.org/wiki/Q1186403) |
| gid-851 | Givat HaMatos | [Q2903335](https://www.wikidata.org/wiki/Q2903335) |
| orphan-187 | Ma'ale David | [Q6856202](https://www.wikidata.org/wiki/Q6856202) |
| orphan-189 | Nof Zion | [Q7047394](https://www.wikidata.org/wiki/Q7047394) |

**Eleven polygons remain unidentified and stay that way**, including `gid-760`
— at 2.0 km² the largest unnamed polygon in the dataset, in north-east
Jerusalem. No Wikidata item's coordinate falls inside it. Its location and size
make a particular identification tempting; that is precisely the inference the
rules prohibit, so it remains unidentified until a source supports a name.

Two ambiguous cases were resolved by re-running the containment test against a
narrower, settlement-typed candidate set: `gid-112` (which also contained the
coordinate for the *Battle* of Ammunition Hill, an event rather than a place)
and `gid-631` (which sits inside the Old City and so contained several nested
entities).

**2026-08-10 — 12 Sinai localities excluded.** Palestine Open Maps' locality
database includes Israeli settlements built in occupied Sinai between 1967 and
1982 and evacuated under the Egypt–Israel peace treaty (Ofira, Neviot, Di Zahav
and others, `district_1945 = Sinai`). They are real records, but Sinai is
Egyptian territory and outside the scope of a map about Palestinian land loss.
Excluded at ingest by district name rather than by a bounding box, so the
exclusion is explicit and reviewable. Found by
`tests/test_invariants.py::GeometryIntegrity`, which flagged a locality at
27.87°N — well south of historic Palestine.

**2026-08-10 — Duyuk population figures are internally inconsistent.** The source
records a 1945 Palestinian population of 730 against a locality total of 130.
One of the two is wrong and there is no basis in the data for deciding which, so
neither is silently corrected: the contradictory group figure is withheld, symbol
sizing falls back to the total (the choice that cannot overstate the claim), and
the feature's evidence note records the conflict. Worth reporting upstream to
Palestine Open Maps. Found by
`tests/test_invariants.py::MechanismsStayDistinct`.

**2026-08-10 — firing zone names withheld where unreadable.** The firing zones
shapefile's DBF uses an unreliable codepage and `FIRE_NAME` arrives as mangled
Hebrew (e.g. `309à'`). Garbled labels are dropped rather than displayed — a
visible encoding error invites doubt about everything else on the map — and those
zones are identified by their signing date instead.

## OCHA labels Area B as Area A

**Source:** `osloagreement.zip`, State of Palestine — Oslo Agreement in the West
Bank, document date 2019-07-22.

**The quirk:** the shapefile has eight polygons and its `CLASS` field carries
`'A'` on **two** of them — 1,034.7 km² and 982.3 km². Nothing in the attribute
table distinguishes them. Taken at face value the file asserts that 35.66% of
the West Bank is Area A, against OCHA's own published figure of 18%.

**Why it mattered:** Area A is full Palestinian civil *and* security control;
Area B is Palestinian civil control with Israeli security control. Merging them
doubles the apparent extent of Palestinian authority — the single most
load-bearing number on a map about land control, and an error that flatters the
occupier. It is the Oslo-split instance of non-negotiable 3.

**The fix:** `etl/adapters/ocha.py::_split_mislabelled_area_b`. Oslo II
(28 September 1995) placed Jenin, Nablus, Tulkarm, Qalqilya, Ramallah,
Bethlehem and Jericho under full Palestinian control, so those city centres are
Area A by definition. The polygon containing all seven is Area A; the other is
relabelled Area B and carries a `class_corrected` note stating why.

Assignment is by **containment**, never proximity — the same standard
non-negotiable 7 sets for settlement identification. It re-runs every build and
**raises rather than guessing** if the anchors do not fall cleanly inside
exactly one polygon, so a reshaped or upstream-corrected source cannot leave a
stale relabel in place.

**Result:** A 17.37%, B 18.30%, C 58.84%, against OCHA's published 18/22/60.
B and C read low because this file breaks Nature Reserve (2.95%), Israeli
Declared East Jerusalem (1.22%) and No Man's Land (0.88%) out into their own
classes rather than folding them in — which is the correct behaviour under
non-negotiable 3, and they are **not** folded back to make the totals match.
Asserted by `tests/test_invariants.py::OsloClassesAreDisambiguated`.

## OCHA's Gaza neighbourhoods file spells its community field `Communithy`

**Source:** `gazastrip_neighbourhoods_points.zip`, State of Palestine — Gaza
Strip Neighbourhoods, document date 2019-07-18.

**The quirk:** the attribute is `Communithy`, not `Community`. Normalised at
ingest in `etl/adapters/gaza.py` and never propagated — the same treatment as
OCHA's literal `West Bsnk` typo.

**Also:** 111 of the 149 points carry an empty `DISTRICT` and an empty
`Communithy`, and 18 carry no Arabic name. Blank strings are dropped rather
than shipped, so a missing district is *absent* from the feature instead of
rendering as an empty value in the detail panel. Nothing is inferred from
neighbouring points, and `tests/test_invariants.py::GazaLayersStateTheirAge`
fails the build if an empty string ever ships.

**Currency, which matters more than either:** both Gaza layers are dated
2019-07-18. They describe how the Strip was administratively divided before
October 2023, not what still stands. Every feature carries that caveat, the
panel section states it, and a test asserts the caveat and the evidence date
agree. Publishing pre-war geography is useful; publishing it silently would
mislead, and that would be our fault rather than the source's.
