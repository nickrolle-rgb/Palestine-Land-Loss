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

## 2. Municipal and regional council jurisdiction have no source

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

## 3. Outposts are not separately inventoried

Outposts need their own track — built without Israeli government authorisation,
illegal under Israeli domestic law as well as international law, and frequently
authorised retroactively, jumping to stage 7 without passing through 2–4. The
schema supports this (`EntityType.OUTPOST`, `retroactive_authorisation_date`)
and the client styles it, but the open data does not distinguish outposts from
settlements.

**To close:** Peace Now and Kerem Navot both track outposts.

## 4. Unnamed settlement polygons

24 of the 201 source polygons have a blank `Name`. Ten were recovered by joining
on `GIS_ID` to a named part of the same settlement; grouping by `GIS_ID` also
correctly merged multi-part settlements, reducing 201 polygons to 160 entities.

The remaining unnamed polygons are shown as `Unidentified settlement (gid-NNN)`
with a warning in the detail panel. **18 of the 20 East Jerusalem settlements
are unnamed** — only Atarot and Ramot Allon carry names. This is not a bug in
the ETL; the Peace Now layer does not name East Jerusalem settlements, which is
consistent with Israel treating them as Jerusalem municipality neighbourhoods
rather than settlements.

Since East Jerusalem is the pilot area, this is the single largest quality
problem in the current build.

**To close:** manual identification against a named reference. The large unnamed
EJ polygons (2.0, 1.68, 1.01 km²) are almost certainly well-known settlements,
but they must be identified from a source, not inferred from size and position.
Log each identification in `corrections.md` with the reference used.

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

## 7. Al-Haq coverage

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
