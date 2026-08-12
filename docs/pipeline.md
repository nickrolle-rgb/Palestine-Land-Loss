# The settlement planning pipeline

"Concept / planning / clearing / settlement" is the right instinct but too
coarse. Israeli settlement development follows a documented administrative
pipeline, and each step generates a **dated public record**. Modelling the real
stages is what lets every pixel on the map cite a document.

| # | Stage | What happens | Evidence source | Integrated? |
|---|---|---|---|---|
| 1 | Land declaration / seizure | Land declared "state land", military seizure order, or survey | Civil Administration records, Kerem Navot, Peace Now | No |
| 2 | Plan deposited | Plan lodged with the Higher Planning Committee | Peace Now Settlement Watch | No |
| 3 | Plan approved | HPC validation | Peace Now | No |
| 4 | Tenders published | Ministry of Housing tenders units | Peace Now, Israeli govt tender publications | No |
| 5 | Ground works | Roads, infrastructure, site clearing | Satellite, Peace Now aerial surveys | No |
| 6 | Construction started | Foundations, units under construction | Peace Now, Israeli CBS | **Partial** |
| 7 | Populated | Residents present, population reported | Israeli CBS, municipal data | No |

Only stage 6 currently has data, and only as a floor — see below.

**The outpost inventory is no longer missing.** B'Tselem supplied it on
2026-08-11: 127 outposts covering 24.9 km², alongside 156 settlements and 18
industrial zones, each typed by them rather than inferred by us. What is still
missing is the `retroactive_authorisation_date` — the field exists and renders,
but nothing populates it, so the map can show that a place is an outpost and not
when it was legalised. That remains with Peace Now.

## Outposts are a parallel track, not a stage

Outposts are settlements built **without** Israeli government authorisation —
illegal under Israeli domestic law as well as international law. Many are later
*retroactively authorised*, jumping straight to stage 7 without ever passing
through stages 2–4.

Forcing outposts through the linear pipeline produces a wrong map. They are
modelled as a distinct `EntityType` with a `retroactive_authorisation_date`, and
styled distinctly (purple, dashed edge).

## The minimum-stage rule

The ETL never asserts a stage it cannot cite. Where a source proves only that
some stage was reached by a date, that stage is recorded with that date and
nothing earlier is inferred.

Concretely: OCHA's built-up footprint layer, last modified 2021-06-03, proves
that construction had started on each of those settlements **by** 2021-06-03. It
does not tell us when the land was declared, when the plan was deposited, or
whether the settlement is populated today. So each entity gets exactly one
`StageEvent`:

```python
StageEvent(stage=Stage.CONSTRUCTION_START, valid_from="2021-06-03", evidence=[...])
```

This is why the time slider is a cliff: there is genuinely no evidence in the
current sources for any date before 2021. The alternative — backfilling
plausible founding dates from secondary reading — would make the slider look
good and the map dishonest.

## Time model

Features are stored **once** with a stage history, not once per year:

```
(entity_id, stage, valid_from, valid_to, evidence_ref)
```

The client resolves "what stage was this on date D" at query time by taking the
highest stage whose `valid_from` is on or before D. This keeps the dataset small,
makes every stage transition individually citable, and means adding a newly
discovered tender date is a one-row change rather than a re-cut of every year.
