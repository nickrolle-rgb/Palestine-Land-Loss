# Sibling project — detention

**Status:** scoped, not started. Deliberately **not** part of Palestinian Land
Loss.

## The decision, and why

Detention was researched as a candidate layer for this map on 2026-08-12 and
ruled out the same day. It belongs in a separate project that links to this one.

The framing that settles it: detention is **theft of freedom rather than land**.
That is a real continuity with what this map documents, and it is also a
different claim, resting on different evidence, answerable by different
objections. The rule that keeps the 1948 depopulation visually and legally apart
from post-1967 settlement applies here with more force, not less — a fifth
colour on the land layer would have blurred both.

Three practical constraints pointed the same way:

1. **No geolocation.** The figures are published as national aggregates. There is
   no locality-level breakdown, so placing detainees on a map would mean
   inventing geography — the one thing this project will not do.
2. **Rule 6 forbids mapping individuals.** Aggregate counts only. That matches
   how these organisations publish, so it costs nothing.
3. **Sources disagree.** Counts differ between organisations and between dates.
   Each figure must carry its own source and as-at date rather than being
   reconciled into a single number.

## Sources, as researched 2026-08-12

| Source | Holds | Access |
|---|---|---|
| **B'Tselem** | Statistics on administrative detention and on Palestinians in Israeli custody | **We already hold their licence** for non-commercial use. Their site returns HTTP 429 to every automated request, so retrieval must be manual or by direct ask — and there is an open thread with Shirly Eran |
| **HaMoked** | Prisoner charts obtained from the Israel Prison Service by freedom-of-information request, current to August 2026 | HTTP 403 to automated fetching |
| **Addameer** | Monthly updates on Palestinian political detainees | Published as news posts |
| **Israel Prison Service** | Primary figures | Stopped supplying B'Tselem on request at the end of 2020; now publishes some data quarterly itself |

Scale, to indicate the order of magnitude rather than to be quoted:
approximately **3,198 administrative detainees** held without charge or trial as
at August 2026, against 3,532 in April 2026 and 3,474 at the end of September
2025. Total Palestinian prisoners reported above 9,600.

Categories worth modelling: administrative detention (held without charge or
trial), sentenced, awaiting trial, "unlawful combatants", minors, and Gaza
residents held under separate legal frameworks. Detention duration and judicial
status are the fields that make the argument, and are the least consistently
published.

## What it should reuse from this project

The discipline, not the code:

- Every figure carries its source and the date it was retrieved.
- Anything unresolvable is withheld and counted, never estimated.
- Sources that disagree are shown disagreeing, not averaged.
- A licence position is recorded for every source before anything ships.
- Gaps are published as prominently as findings.

## The link

Palestinian Land Loss should link out to it, and it back, each stating plainly
what it does and does not cover. Neither should absorb the other.
