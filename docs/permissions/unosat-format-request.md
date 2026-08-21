# UNOSAT — request for a vector export of the Gaza damage assessment

**Status:** drafted 2026-08-21, not sent.
**To:** UNOSAT / UNITAR — via <unosat@unitar.org> or the Gaza Data Hub contact.
**Why this is not a permissions request:** the licence is already settled. HDX
publishes the assessment as **CC BY-SA 4.0**, which permits what we are doing.
This asks only for a different file format, and is worth sending because a
vector export would let us drop a dependency we added solely to read theirs.

---

Subject: Gaza Comprehensive Damage Assessment — shapefile or GeoJSON export?

Dear UNOSAT team,

I maintain *Palestinian Land Loss* (https://palestine-land-loss.vercel.app), a
free, non-commercial, open evidence map where every element resolves to a dated
document. I have just added your **Gaza Strip Comprehensive Building Damage
Assessment (11 October 2025)**, used under CC BY-SA with attribution to
UNITAR/UNOSAT, and the share-alike terms carried on the derived layer.

The 198,308 assessed sites are aggregated to the 33 OCHA municipal boundaries by
point-in-polygon containment, so the map shows damage counts per municipality
rather than individual buildings. Your fourteen assessment rounds also drive a
timeline showing assessed damage rising from 15,601 sites in October 2023 to
198,308 two years later.

One request. The assessment is distributed only as an Esri File Geodatabase. Our
pipeline is otherwise built to run on a bare machine with no system geospatial
libraries, so reading the `.gdb` meant taking on a GDAL-backed dependency purely
for that one file. **If a shapefile or GeoJSON export could be published
alongside the geodatabase, we would drop that dependency entirely** — and I
suspect we are not the only small project in that position. Your older Gaza
products were distributed as shapefiles, so I hope this is a modest ask.

Two smaller questions, if anyone has a moment:

1. Is there a codebook for the per-round `Damage_Status` values (0, 1, 3)? We
   deliberately do not interpret them — our timeline counts sites carrying a
   damage class in each round, which needs no assumption about those codes — but
   we would use them correctly if their meaning were documented.
2. Are the `Main_Damage_Site_Class` values (1–4) the standard destroyed /
   severe / moderate / possible scale? We have not asserted this either.

Happy to correct the attribution wording if it does not match your preferred
form.

With thanks and respect for the work,

Nick Olle
0433321011
Nick.r.olle@gmail.com
