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

## Palestine Open Maps
- Requested: 2026-08-10
- Replied: —
- Outcome: awaiting reply
- Asked for: licence position on the `pom-data` locality database (currently
  redistributed by this build), separately from tile display; ODbL implications
  given OpenStreetMap is among their sources.
- **Current exposure:** `pom_localities` is `enabled=True` and shipping. This is
  a recorded, deliberate risk, not an oversight — see docs/data-gaps.md §8. If
  the answer is no, pull the locality layer.

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
