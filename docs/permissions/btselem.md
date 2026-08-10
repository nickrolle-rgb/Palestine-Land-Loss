# Draft — B'Tselem

**Status:** not sent
**Suggested address:** `mail@btselem.org` — search-derived and corroborated
across sources, but **not verified directly**: btselem.org rate-limited every
automated request, so confirm before sending. Their contact form is an alternative.
**Subject:** Permission request — settlement jurisdiction boundaries for an open, cited map

**Note on precedent:** B'Tselem's own terms of use could not be retrieved (site
returned HTTP 429 to every attempt), so this draft makes no assumption about
their existing licensing posture. If you can load their site, check for a terms
or copyright page before sending and adjust accordingly.

---

Dear B'Tselem,

I'm building a non-commercial, open-source map called Palestinian Land Loss, and
I'd like to ask permission to use your land-control data.

**The specific problem I'm trying to solve**

There are three completely different ways to draw "how much land is taken", and
they differ by an order of magnitude:

- the built-up footprint — the actual buildings and roads
- the settlement's municipal jurisdiction — usually far larger than what is built
- regional council jurisdiction — vast, covering a large share of Area C

Publishing only the first understates the encroachment. Publishing only the third
overstates the daily footprint. Either way the map is fairly dismissed as
misleading. So it renders all three as independently toggleable layers with the
definition of each stated in the legend.

I have openly licensed data for the built-up footprint via OCHA on HDX. I have no
source for the other two, and your land-control analysis is the clearest public
treatment of the distinction I've found.

**What I'm asking for**

Permission to derive map layers from B'Tselem's published data on settlement
municipal jurisdiction boundaries and regional council jurisdiction.

**How it would be used and credited**

- Every feature links back to the B'Tselem publication it came from, with the
  publication date and the date retrieved.
- B'Tselem credited in the layer legend, the About page, and each feature panel.
- Non-commercial, openly licensed, no paywall, no advertising.
- The map cites UNSC Resolution 2334 and the ICJ advisory opinion of 19 July 2024
  for the legal position, rather than asserting it editorially.
- It maps localities, plans, parcels and infrastructure only. It does not map
  individuals — no settler names, no addresses of specific homes.
- Mechanisms of land loss are kept visually and legally distinct: post-1967
  settlement is presented as unlawful per the sourced findings above, while the
  1948 depopulation is presented as a documented historical event of different
  legal character. They are not flattened into one colour.

**Until I hear from you**

The two jurisdiction layers ship visibly empty, labelled "no data yet", so the
gap is stated rather than hidden. That is the current live behaviour, not a
promise.

The work is open and you can inspect it, including its known errors and gaps:
https://github.com/nickrolle-rgb/Palestine-Land-Loss

I'm happy to remove or amend anything you're not comfortable with.

With thanks,

[name]
[contact]
