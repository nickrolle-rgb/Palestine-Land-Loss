# Permissions

Current posture: **OCHA/HDX-licensed data only.** Peace Now and B'Tselem
adapters exist in `etl/sources.py` but are `enabled=False`.

## Rules

1. Do not flip `enabled` on a source without a written reply recorded in
   `RESPONSES.md`.
2. Record the exact scope granted. "Yes go ahead" in an email is not the same as
   permission to redistribute a derived database.
3. If a source declines or restricts, note that too — a documented refusal is
   useful and prevents someone re-asking in six months.

## What is already permitted

OCHA's "State of Palestine Settlements" layer on HDX **is** Peace Now's built-up
settlement data, republished by OCHA under CC BY-IGO. Using it via HDX is
already permitted with attribution to both Peace Now and OCHA. The permission
request below is for their *planning-stage* data, which is not on HDX.

## Watch for

- **OpenStreetMap.** If OSM data is ever incorporated, ODbL share-alike attaches
  to the derived database. Currently not used — the basemap is rendered by
  CARTO, not derived into our data.
- **Palestine Open Maps.** Historical tiles are consumed as a tile layer with
  attribution, not redistributed. Verify their terms before mirroring tiles.
- **Al-Haq.** The ingest stores title, date, URL and a matched locality, and
  links out. Their report text is not reproduced. A courtesy notice is drafted
  in `alhaq.md`.

## Drafts

| File | Recipient | Asking for |
|---|---|---|
| `peace-now.md` | Peace Now (Settlement Watch) | Planning-stage, tender, construction-start and outpost data |
| `btselem.md` | B'Tselem | Municipal and regional council jurisdiction boundaries |
| `alhaq.md` | Al-Haq | Courtesy notice + confirmation the link-out approach is acceptable |

These are **drafts for you to review and send**. Nothing has been sent.
