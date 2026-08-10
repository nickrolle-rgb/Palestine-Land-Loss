# Draft — Palestine Open Maps

**Status:** not sent
**To:** Palestine Open Maps / Visualizing Palestine — via palopenmaps.org, or an
issue on `github.com/palopenmaps/pom-data`
**Subject:** Licence question — reuse of the POM locality database

**Why this is the most urgent of the four:** the `pom-data` repository declares
**no licence at all**, and the current build already redistributes their locality
database (2,537 records) rather than merely displaying their tiles. Their own
`sources.csv` credits David Rumsey, the National Libraries of Australia and
Israel, the Hebrew University, ESRI and OpenStreetMap — mixed provenance that
probably explains why no blanket licence is stated. So the ask below is
deliberately narrow and specific rather than "may I use your data".

---

Dear Palestine Open Maps team,

I'm building a non-commercial, open-source map called Palestinian Land Loss,
which uses your work in two ways. I want to check both are acceptable, because
your repository doesn't state a licence and I'd rather ask than assume.

**1. Your historical map tiles — displayed, not copied**

The map offers five of your georeferenced surveys as switchable underlays, in a
swipe and overlay comparison: the PEF Survey of Western Palestine (1871–77), the
Survey of Palestine 1:20,000 (1940–45), Palestine 1:250,000 (1946), Palestine
1:100,000 (1950s) and Israel 1:250,000 (1951). These are requested from your tile
server at display time and attributed to Palestine Open Maps on the map canvas.
Nothing is mirrored or cached.

If you would prefer I not hotlink your tiles, or would like a different rate,
attribution wording, or referrer, please say and I'll change it immediately.

**2. Your locality database — this is the one I actually need permission for**

The build ingests `raw-data/localities.csv` and republishes it as a map layer:
2,537 localities with names in English, Arabic and Hebrew, populations for 1922,
1931 and 1945, depopulation dates, and your cross-references to Zochrot and
Palestine Remembered. It is the evidence base for depicting the 1948
depopulation — 467 localities in the current build.

Because your repository states no licence, I have no basis to assume this is
permitted. Specifically I'd like to know:

- May I redistribute this data as part of an openly licensed map?
- If so, what attribution would you like, and under what licence?
- Are there records or fields you'd rather I did not republish?
- Given your sources include OpenStreetMap, are there ODbL obligations I should
  be carrying through?

**How it's used**

Symbols are sized by the *Palestinian* 1945 population rather than the locality
total, because in mixed cities the total badly overstates displacement —
Jerusalem's 1945 total was 157,080 against a Palestinian population of 60,080.
Records without coordinates are omitted rather than placed approximately. Each
locality links back to your cross-referenced sources.

I've credited Palestine Open Maps throughout and flagged the undeclared licence
publicly in the project's own data-gaps documentation, so nobody is misled about
its status while I wait to hear from you:
https://github.com/nickrolle-rgb/Palestine-Land-Loss

If the answer is no, or not yet, I'll pull the locality layer.

With thanks for building the thing that made this possible,

[name]
[contact]
