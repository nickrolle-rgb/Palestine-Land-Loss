# INSS — permission to reuse the Yellow Line polygon

**Status:** drafted 2026-08-23, not sent. Source registered **disabled** in
`etl/sources.py` until a reply is recorded in `RESPONSES.md` (non-negotiable 4).

## What we found

INSS publish an ArcGIS Experience app, *Post-War Gaza*
(`experience.arcgis.com/experience/beea7b2bc2c2420884e0b3adf9072136`), whose
web map carries a layer titled **"Israeli Military Presence"**, served from
`services-eu1.arcgis.com/.../GazaYellowLine/FeatureServer/0`.

It is a **single polygon, 232 vertices**. Measured with `etl/geo.py` it comes to
**197.6 km²**, which is **54.1%** of the 364.9 km² our OCHA municipal layer
gives for the Strip — consistent with the roughly 53% widely reported for the
Yellow Line at the October 2025 ceasefire.

Its `Shape__Area` field reads 271,902,533 m². That is Web Mercator and inflates
area by about 37% at this latitude; it must not be quoted. Our own measurement
is the figure above.

The item states **"Free to be used by the public."** — but on the *parent
Experience app*, not on the feature layer, and it is not a named licence. For
the most contested line on this map, that gap is worth one email.

## Draft

Subject: Reuse of the Yellow Line polygon from your Post-War Gaza map

Dear INSS GIS team,

I maintain *Palestinian Land Loss* (https://palestine-land-loss.vercel.app), a
free, non-commercial, openly published evidence map where every element resolves
to a dated document and nothing is drawn that cannot be sourced.

Access restrictions inside Gaza are something we have so far been unable to show
at all. OCHA describe the Yellow Line in their situation reports but publish no
geometry, and a search of all 254 Palestine-tagged datasets on the Humanitarian
Data Exchange found no access-restriction boundary as open data. Drawing one by
eye is not something we are willing to do.

Your *Post-War Gaza* map is the only vector depiction of that line we have been
able to find from a named, accountable publisher. The item notes it is "free to
be used by the public", but as that appears on the Experience app rather than on
the layer, I would rather ask than assume.

May we publish the "Israeli Military Presence" polygon as a layer on our map,
attributed to INSS and linked back to your publication? We would state the
November 2025 date, note that the boundary is your depiction rather than an
official demarcation, and remove or update it on request.

Two questions that would improve the record either way:

1. What date does the polygon represent? The feature carries no date field, so
   we would otherwise cite the publication month.
2. What is it derived from — official maps, satellite imagery, or your own
   analysis? We would like to describe its provenance accurately rather than
   vaguely.

For context on how it would be presented: we measure it at 197.6 km², 54.1% of
the Strip. It would sit in its own layer, styled apart from everything else,
and would not be added into any other figure.

With thanks,

Nick Olle
0433321011
Nick.r.olle@gmail.com
