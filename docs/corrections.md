# Corrections log

A visible corrections log is part of the project's credibility, not an
afterthought. Anything that turns out to be wrong gets an entry here, with the
date and what changed.

Format: `YYYY-MM-DD — what was wrong — what it is now — source for the change`.

## Open items

Known problems not yet fixed. These are also surfaced in the UI.

| Item | Detail | Blocked on |
|---|---|---|
| 18 unnamed East Jerusalem settlements | The Peace Now/OCHA layer names only Atarot and Ramot Allon among the 20 EJ settlements. The rest render as `Unidentified settlement (gid-NNN)`. | Manual identification against a named reference |
| 6 unnamed orphan polygons | Very small polygons (≤0.02 km²) with neither a name nor a usable `GIS_ID`. May be fragments rather than settlements. | Inspection |
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

**2026-08-11 — B'Tselem data ingested; four source quirks handled.**
B'Tselem supplied four GeoJSON files under their licence for non-commercial use.
They fill the municipal jurisdiction layer and supply the outpost inventory.

Measured against each other they demonstrate, rather than assert, the premise
the project is built on:

| Measure | Area | % of West Bank | vs built-up |
|---|---|---|---|
| Built-up | 56 km² | 1.0% | — |
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
