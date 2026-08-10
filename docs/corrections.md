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
