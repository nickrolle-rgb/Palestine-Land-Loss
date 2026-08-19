# From report to evidence

## The problem

Land loss is usually *announced* before it is *visible*. A tender is published,
a plan is validated, a seizure order is signed — and none of it shows up in the
geodata this map is built from until construction is already on the ground. OCHA
publishes geography, not planning records, which is why Known Gap 1 exists and
why the time slider is a cliff at 2021.

Press reporting fills that window. It is also the weakest kind of source we
could use: secondary, often paywalled, usually copyrighted, and written to a
deadline. Non-negotiable 1 forbids asserting a stage the sources do not support,
so the temptation to plot a newspaper headline has to be designed out rather
than resisted case by case.

The resolution is that **a report is a lead, not a record.** It tells us a
primary document exists. The primary document is the evidence.

## Three tiers

| Tier | Name | What it means | On the map |
|---|---|---|---|
| 1 | `alleged` | A press or NGO report alleges an action. No primary record located. | **Never.** Ledger only. |
| 2 | `verified` | The primary record is identified and cited — tender number, plan number, decision date. Geometry unknown or unsourced. | Listed, with its citation. **Not drawn.** |
| 3 | `mapped` | Primary record *and* a sourced geometry. | Drawn, as a normal stage event with evidence. |

The tiers are a **provenance** axis and are independent of `Confidence`, which
records how well a location resolved. A record can be provenance-`verified` and
still have no location at all; that is the normal state for a plan that has been
approved but never surveyed into any public dataset.

Nothing promotes itself. An `alleged` entry becomes `verified` only when someone puts
the primary reference in the ledger, and `mapped` only when a geometry arrives
from a source in `etl/sources.py`. `alleged` entries are counted and displayed as a
count — the same treatment as withheld Al-Haq records — so the map says "four
reported actions we could not yet verify" instead of silently omitting them.

## Why not reuse the vocabulary from Millpond

The sibling project in `Projects/OrbitWatch` — Millpond — already runs a
three-tier confidence discipline, and its scope document is emphatic that an
inferred position must never render like a confirmed one. Its tiers are
`reported` (an authority said so) / `observed` (seen in sensor data) /
`inferred` (produced by correlation logic).

Those are a **mode-of-knowledge** axis: *how did this reach us*. Ours is a
**strength-of-provenance** axis: *how well is this sourced*. They are genuinely
different questions, and the word `reported` means close to opposite things in
the two systems — for Millpond it denotes an authority's own statement, near the
top of its hierarchy, while here it would denote an unverified press allegation
at the bottom. Sharing the token across two projects that may one day be read
side by side would be worse than having two vocabularies. Tier 1 is therefore
`alleged`.

## Collapsing the cascade before counting corroboration

Millpond's rumour-intake design names the dominant failure mode in open-source
reporting: **circular reporting** — forty accounts repeating one origin, which
reads as forty confirmations. Its rule is to cluster restatements, timestamp
first appearance, collapse the cluster to a single claim carrying its origin's
credibility, and record the repetition count **as metadata, never as evidence**.

That rule applies here unchanged, and it corrects something in the E1 entry
below. Three outlets carrying "1,234 units" is not three independent
observations of the tender; it is very likely three readings of the same
document, or of each other. The count of outlets is recorded, and it counts for
nothing. This is not a weakness of the tiering — it is the reason tier 2 exists
and why promotion to `mapped` requires the primary record rather than a
sufficient weight of repetition.

## Unrefuted is not confirmed

Also from Millpond, and worth stating in the project's own words: verification
can only reduce false belief, never manufacture true belief. A claim that
survives every check we can apply is **unrefuted**, not confirmed. Where the
distinction matters the record and the UI should say "no source contradicts
this" rather than implying corroboration nobody actually supplied.

## Why the press citation is kept even at `mapped`

Not as evidence — as provenance. It records how we came to look, which is the
part of an evidence chain that is normally invisible and the first thing a
hostile reader will probe. It carries `role: "lead"` and never appears in the
evidence block that a feature cites.

## Copyright

`alleged` entries store **headline, outlet, byline, publication date, URL and
retrieval date**. Never the body text, and never a paraphrase dense enough to
substitute for it. This is the Al-Haq rule (non-negotiable 5) applied to a
different kind of publisher, for the same reason.

## Worked example — E1, August 2026

The case the tiers were designed against.

**`alleged` — the lead.** Haaretz, 18 August 2026, Liza Rozovsky: Israel's Housing
Ministry issued a tender for about 1,200 housing units in E1. Paywalled after
the first paragraph, so the accessible text is the headline, deck and lede.

**`verified` — the primary record.** Corroborating reports name the documents:

- **Tender no. 186/2026**, issued 18 August 2026, bids closing 19 October 2026,
  covering seven complexes in the southern part of E1 — 1,234 units, reported by
  WAFA citing the Palestinian Wall and Settlement Resistance Commission.
- **Detailed plan no. 420/4/7**, the approved plan the tender executes.
- **Tender no. 460/2025**, 10 December 2025, for the full 3,401 units, per Peace
  Now.

Both tender numbers and the plan number are checkable against the Israel Land
Authority's published tenders and the national planning portal (MAVAT). Until
someone does that check against the issuing body, this stays `verified` no matter
how many outlets repeat it.

**Numbers that disagree, and why that is fine.** Three outlets carry these
figures and they are *not* three confirmations — see the cascade rule above. The
plausible common origin for all of them is the tender document itself, which is
the argument for checking it rather than counting them. Haaretz says
"about 1,200"; WAFA says 1,234. That is rounding, not conflict, and the record carries 1,234
with Haaretz's figure noted — the specific figure and the general one come from
different distances to the source. The 1,234 is *part of* the 3,401 already
approved, not additional to it: roughly the first phase. That relationship is
sourced, not inferred, which matters because inferring it the other way would
have double-counted the plan.

**A real stage history.** E1 is the first entity in this project that could
carry more than one documented stage, because each step generated a dated public
record:

| Stage | Date | Record |
|---|---|---|
| 2 — Plan deposited | shortly before Feb 2020 | approved for deposit |
| 3 — Plan approved | August 2025 | Higher Planning Committee validation |
| 4 — Tenders published | 10 Dec 2025 | tender 460/2025, 3,401 units |
| 4 — Tenders published | 18 Aug 2026 | tender 186/2026, 1,234 units, plan 420/4/7 |

Stage 5 is **not** asserted. No source says ground works have begun, and a
tender is an invitation to bid, not a bulldozer. Recording stage 4 and stopping
is exactly what non-negotiable 1 requires, and it is the discipline that makes
the stage-4 claim worth believing.

**Why it still cannot be drawn.** E1 covers about 12 km², east of Jerusalem
towards Ma'ale Adumim. We have no polygon for it from any enabled source. Plan
420/4/7's boundary would be the correct geometry; Peace Now publish E1 maps but
that adapter is disabled pending permission (non-negotiable 4). Sketching a
12 km² block from a description would violate non-negotiable 2 for the single
most scrutinised parcel in the West Bank.

So E1 sits at `verified`: cited, dated, listed, undrawn. That is the honest state.

**Context that is real but is not ours to assert.** Haaretz notes the bid
deadline falls days before the 27 October 2026 elections; Ir Amim, Bimkom and
Peace Now say the State Attorney's Office had undertaken to notify petitioners
before any E1 tender and did not. Both are attributable statements by named
parties, and they belong in the record as such — quoted and attributed, never
restated in the project's own voice as motive.
