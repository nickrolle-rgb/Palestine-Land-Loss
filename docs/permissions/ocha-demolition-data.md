# Draft — OCHA oPt (demolition and displacement database)

**Status:** not sent
**To:** OCHA occupied Palestinian territory — via <https://www.ochaopt.org/contact>
**Subject:** Data request — machine-readable access to the demolition and displacement database

**Why this is needed:** OCHA's demolition and displacement database is the
authoritative West Bank-wide record of destroyed Palestinian structures —
residential, livelihood, service and infrastructure, including water pipes and
wells — from 2009 to the present. It is published **only as an embedded Power BI
dashboard** at <https://www.ochaopt.org/data/demolition>. There is no CSV, no API
and no HDX entry, so it cannot be used programmatically.

This is not a permission problem so much as a format one: OCHA already publishes
most of its oPt geodata openly on HDX under CC BY / CC BY-IGO, and this build
already uses six of those layers.

---

Dear OCHA oPt data team,

I maintain Palestinian Land Loss, a non-commercial, open-source evidence map
built substantially on your published data — the Oslo classification, the
Palestinian communities layer, village boundaries, the Barrier alignment, the
firing zones layer, and the Masafer Yatta violence monitoring dataset from HDX.
Every feature on the map cites its source with a document date and a retrieval
date.

**What I'm asking for**

A machine-readable export of the demolition and displacement database behind
<https://www.ochaopt.org/data/demolition> — CSV, or an HDX entry alongside your
other oPt datasets. The fields I'd need are the ones the dashboard already shows:
date, locality, structure type, number of structures, people displaced and people
otherwise affected.

If a full export isn't possible, even a periodic aggregate by locality and
structure type would be far more useful than the current situation, where the
data is visible but not usable.

**A second request, if I may: the Gaza access-restricted lines**

OCHA's maps show the restricted-access zone Israel calls the Yellow Line, and
the broader Orange Line between military positions and the surrounding danger
zones. OCHA's own reporting puts the restricted area at 64.9% of the Gaza Strip
by June 2026, up from 53% earlier in the year.

Those figures are exactly the kind of thing this map exists to show, and the
lines appear in your published graphics — but I can find no shapefile or GeoJSON
for either on HDX. Your *Gaza Strip Buffer Area* dataset is openly licensed and
usable, but it was last updated in October 2023 and so predates all of this.

If the Yellow and Orange lines could be published as geodata, or added to the
existing buffer dataset, they would be among the most useful layers available
for the Gaza Strip.

**Why it matters for this map**

I currently show destruction of resource access — water, farmland, livestock,
homes — using your Masafer Yatta dataset on HDX. That is 2,904 verified records,
but it covers 27 localities in the South Hebron Hills and the year 2025 only. The
map states that limitation explicitly wherever the layer appears, because
otherwise a reader would take absence elsewhere as evidence that nothing
happened. Your West Bank-wide database is what would fix that.

**How it would be used**

- Attributed to OCHA oPt on the layer, in the About page, and on every feature.
- Aggregated to locality level; the map does not identify individuals, and it
  would not publish anything more granular than your dashboard already shows.
- Records that cannot be resolved to exactly one locality in your own communities
  gazetteer are withheld from the map and counted publicly rather than plotted at
  a best guess. That is already how the Masafer Yatta layer behaves — three
  localities and 385 records are currently withheld on that basis.

One small thing you may want to know: your Masafer Yatta dataset names a locality,
**Umm Dhorit** (370 records in 2025), which does not appear in the OCHA
Palestinian Communities layer on HDX. I've withheld those records rather than
place them approximately, but the mismatch between the two datasets may be worth
a look at your end.

The work is open, including its gaps and errors:
https://github.com/nickrolle-rgb/Palestine-Land-Loss

With thanks,

[name]
[contact]
