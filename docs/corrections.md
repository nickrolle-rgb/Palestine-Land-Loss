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

*(none yet — the project has not been published)*
