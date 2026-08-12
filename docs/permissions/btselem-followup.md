# Draft follow-up — B'Tselem

**Status:** not sent
**To:** Shirly Eran <Seran@btselem.org> (cc Mail@btselem.org)
**Subject:** Re: Permission request — settlement jurisdiction boundaries for an open, cited map

**Context:** Nick has already replied thanking Shirly and inviting her to follow
along. This is a follow-up with three specific asks, sent once there was
something worth showing.

**The three asks, in order of value:**
1. Regional council jurisdiction — the last empty layer, and probably the largest
   measure on the map.
2. Confirmation that the licence's "fair usage" covers republishing the four
   files as map layers, since it excludes "expansive use".
3. Which file corresponds to which of their own definitions — our mapping is
   inference from measured magnitude, not their statement.

---

Hi Shirly,

Your files are in and doing real work — thank you again. A short update, and
three questions if you have the time.

**What they made possible.** The municipal boundaries filled a layer that had
been shipping visibly empty since I started, and the `Type` field in the boundary
file gave me something no open source had: **127 outposts**, alongside 156
settlements and 18 industrial zones, typed by you rather than guessed by me.

Measured against each other, your three files also demonstrate the point the map
exists to make, from one consistent source rather than three mismatched ones:

| Measure | Area | Share of the West Bank |
|---|---|---|
| Built-up | 56 km² | 1.0% |
| Settlement boundary | 179 km² | 3.2% |
| Municipal jurisdiction | 520 km² | 9.2% |

A reader can now see that "how much land" has an answer that moves by nine times
depending on which definition you use — and that all three are true at once.
That's a much stronger argument than any single number.

**Question 1 — do you hold regional council jurisdiction?**

It's the one measure still empty, and I suspect the largest: regional councils
cover a far greater share of Area C than the 9.2% municipal figure. Its absence
means the map currently *understates* the total. If you have it in any form, it
would change the headline figure more than anything else I could add.

**Question 2 — a licence question I'd rather ask than assume.**

Your licence covers "fair usage" of individual materials and excludes "expansive
use", which needs express written consent. Ingesting four complete datasets and
republishing them as map layers is arguably the latter. I read your sending the
files in answer to a request that described exactly this use as consent — but I'd
rather have you say so than rely on my reading. One line is plenty.

**Question 3 — which file is which definition?**

I've mapped `settlements-muni-border` to municipal jurisdiction and
`settlements-border` to the settlement's own outline, based on their measured
sizes rather than on anything you've stated. If I have those the wrong way round,
or if `settlements-border-2024` supersedes `settlements-border` rather than
sitting alongside it, I'd like to correct it before more is built on top.

**A few things in the files you may want to know about.** All handled here
without altering your data, and logged publicly:

- `settlements-muni-border` has no usable join key — `GIS_ID` is 0 on all 420
  features, and the name column arrives as underscores (`____ ____`), with 1 of
  420 English names populated. I recover names by containment where exactly one
  named settlement falls inside a polygon; 88 of 420 are named that way and the
  rest are left unnamed rather than guessed.
- `DATE_` contains some impossible values — the range runs from `1000-01-01` to
  `2094-11-17`. I validate against 1967-to-today and reject 29 of them.
- `Type` has two spellings worth a look: `Ouptost` for `Outpost`, and one
  untranslated `התנחלות`.
- One feature in the boundary files is a `GeometryCollection` rather than a
  polygon.

Everything is credited to B'Tselem in the interface, on the About page and on
every individual feature, and the project is non-commercial with no advertising
or paywall, as your licence requires.

The map is live but unannounced while I wait on a couple of these answers:

https://palestine-land-loss.vercel.app/

Do have a look if you get a moment — and if anything about how B'Tselem's work
appears is wrong or unwelcome, tell me and I'll change it.

Cheers,

Nick Olle
0433321011
Nick.r.olle@gmail.com
