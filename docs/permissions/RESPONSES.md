# Permission responses

Record every reply here, including refusals. A source in `etl/sources.py` may
only be set `enabled=True` once its grant is recorded below with the scope
stated.

Template:

```
## <Organisation>
- Requested: YYYY-MM-DD
- Replied: YYYY-MM-DD
- Outcome: granted / granted with conditions / declined / no reply
- Scope granted: <exact wording of what was permitted>
- Conditions: <attribution wording, redistribution limits, review requests>
- Contact: <name, role>
- Source flag flipped: yes/no, on which commit
```

---

## Palestine Open Maps (Visualizing Palestine)
- Requested: 2026-08-10
- Replied: 2026-08-11
- Outcome: **granted with conditions**
- Contact: the VP team, admin@visualizingpalestine.org
- Scope granted:
  - Historical map tiles may be used directly from their tile server, including
    all five surveys, provided they are attributed to Palestine Open Maps.
  - The localities data may be used **and redistributed** as part of an openly
    licensed map.
- Conditions, all implemented:
  1. Attribute the tiles — they suggested "Survey of Palestine / Palestine Open
     Maps". Carried in `config.js` as the tile attribution string.
  2. State that the data is not guaranteed 100% accurate when republishing,
     along with its sources. Carried as `POM_ACCURACY_NOTE` and rendered in the
     About panel.
  3. Credit Palestine Open Maps and, where practical, acknowledge the underlying
     sources: Palestine Remembered, Institute for Palestine Studies, Palestine
     Lands Society, Palestinian Central Bureau of Statistics, Israeli Central
     Bureau of Statistics, Zochrot, B'Tselem. Carried as
     `POM_UNDERLYING_SOURCES`, published in `meta.json`, and asserted by
     `tests/test_invariants.py::AttributionConditions`.
- **ODbL question answered:** OpenStreetMap is used only for their present-day
  vector overlay and is *not* the source of the localities data, so no
  share-alike obligation flows to this project.
- Outstanding courtesy: they asked to see a preview before publication. The site
  went live at palestine-land-loss.vercel.app before that happened. Send them the
  link, say plainly that it is live but unannounced, and invite comment before
  any wider promotion.
- Source flag: `pom_localities` remains `enabled=True`, now with a settled
  licence position.

## B'Tselem
- Requested: 2026-08-10
- Replied: 2026-08-11
- Outcome: **granted**
- Contact: Shirly Eran, B'Tselem
- Scope granted: "You are welcome to use the information from our website in
  accordance with this license", plus four GeoJSON files supplied directly:
  `settlements.geojson`, `settlements-border.geojson`,
  `settlements-border-2024.geojson`, `settlements-muni-border.geojson`.
- Licence: B'Tselem's public licence for non-commercial use.
  Conditions carried by this project:
  1. Non-commercial use, without remuneration. ✔ — the project is non-commercial.
  2. No harm to the integrity of the materials, no distortion, no use out of
     context. ✔
  3. B'Tselem named **prominently and expressly**. ✔ — About panel attribution
     section, source registry, and every feature's citation.
  4. Where B'Tselem credits other parties, those must be stated explicitly. ✔ —
     no third-party credits appear in the supplied files; re-check on any update.
- **Open question to raise in the reply:** the licence covers "fair usage" of
  individual materials and excludes "expansive use", which requires express
  written consent. Ingesting four complete datasets and republishing them as map
  layers is arguably expansive. The files were supplied in direct answer to a
  request describing exactly this use, which reads as consent — but one
  confirming sentence would remove all doubt.
- Also worth asking: which file corresponds to which extent definition. Measured
  areas suggest `settlements` = built-up (56 km², 1.0% of the West Bank),
  `settlements-border` = settlement outline (179 km², 3.2%) and
  `settlements-muni-border` = municipal jurisdiction (520 km², 9.2%), but that is
  inference from magnitude, not their stated definition.
- Source flag: `btselem` flipped to `enabled=True` on this commit.

## Peace Now (Settlement Watch)
- Requested: 2026-08-10
- Replied: —
- Outcome: awaiting reply
- Asked for: planning stages 2–4, tenders, construction starts, outpost
  inventory with retroactive authorisation dates.
- Argument used: OCHA already redistributes their built-up layer on HDX under
  CC BY-IGO; request framed as extending terms already granted.
- Blocks: pipeline stages 1–5, and therefore the time slider before 2021.

## B'Tselem
- Requested: 2026-08-10
- Replied: —
- Outcome: awaiting reply
- Asked for: municipal jurisdiction and regional council jurisdiction boundaries.
- Blocks: two of the three extent layers, which currently ship visibly empty.

## Al-Haq
- Requested: 2026-08-10
- Replied: —
- Outcome: awaiting reply
- Nature: courtesy notice, not a permission request. Their site reserves all
  rights; the build stores only title, date, URL and matched locality, and links
  out. Also asked whether any place matching is wrong.
