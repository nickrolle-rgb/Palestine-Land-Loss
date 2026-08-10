# Draft — Peace Now (Settlement Watch)

**Status:** not sent
**To:** Settlement Watch, Peace Now
**Suggested address:** `hagit@peacenow.org.il` (Hagit Ofran, Settlement Watch) —
search-derived, verify before sending. Their contact form is an alternative.
**Subject:** Permission request — Settlement Watch planning data for an open, cited map

**Precedent this draft leans on:** OCHA already publishes your built-up settlement
layer on HDX under CC BY-IGO (`settlements_peacenow.zip`). Amnesty International's
June 2026 West Bank report used data provided directly by Peace Now. FMEP
republishes Peace Now maps and charts with attribution. The ask below is
deliberately framed as "the same terms you have already granted OCHA".

---

Dear Settlement Watch team,

I'm building a non-commercial, open-source map called Palestinian Land Loss. Its
purpose is to make the *planning pipeline* legible: rather than showing
settlements as static shapes, it shows each stage — land declaration, plan
deposited, plan approved, tenders published, ground works, construction start,
populated — as a dated, citable event, with a time slider and comparison against
historical surveys of Palestine.

Your Settlement Watch data is the only source that documents those stages
systematically, and I'd like to ask permission to use it.

**What I'm already using, and why I'm asking**

The map currently uses the built-up settlement footprints that OCHA publishes on
HDX under CC BY-IGO, which originate with Peace Now. That layer is credited to
both Peace Now and OCHA in the legend and on every feature.

Since you have already permitted OCHA to redistribute that layer openly, I'm
essentially asking whether the same terms could extend to the planning-stage
material, which isn't on HDX:

- planning stages (plans deposited and approved by the Higher Planning Committee)
- tenders published
- construction starts
- the outpost inventory, including retroactive authorisation dates

**How it would be used and credited**

- Every feature links back to the specific Peace Now publication it came from,
  with the publication date and the date I retrieved it.
- Peace Now is named in the layer legend, the About page, and each feature panel.
- Non-commercial, openly licensed, no paywall, no advertising.
- Outposts are modelled as a distinct category that can skip planning stages and
  be authorised retroactively, rather than being flattened into the same pipeline
  as authorised settlements.

**What the map does when it lacks your data — which is the honest part**

Right now it asserts only the *minimum* stage each source supports. A built-up
footprint observed on 2021-06-03 proves construction had started by then and
nothing earlier, so the time slider currently drops to zero before 2021 and the
interface says exactly why. I would rather ship a visibly incomplete map than
backfill plausible dates. Your data is what would make that slider mean something.

**One thing I'd value your view on**

The map renders built-up footprint, municipal jurisdiction and regional council
jurisdiction as three separately toggleable layers, because they differ by an
order of magnitude and picking one silently would misrepresent the situation in
one direction or the other. Currently only the built-up layer has data; the other
two ship visibly empty and labelled "no data yet". If you think that framing is
wrong, I'd genuinely like to hear it before I publish.

The work is open and you can inspect it, including everything it currently gets
wrong: https://github.com/nickrolle-rgb/Palestine-Land-Loss

I'm happy to remove or amend anything you're not comfortable with.

With thanks and respect for the work,

[name]
[contact]
