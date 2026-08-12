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

## Precedent — what these organisations have already allowed

Researched 2026-08-10. Useful because a permission request that cites a
comparable grant is far stronger than one that asks in the abstract.

| Organisation | Precedent found | Strength |
|---|---|---|
| Peace Now | OCHA publishes their built-up settlement layer on HDX as `settlements_peacenow.zip` under **CC BY-IGO** | Strong — they have already permitted open redistribution by a third party |
| Peace Now | Amnesty International's June 2026 West Bank report used data **provided directly by Peace Now** | Moderate — shows willingness to supply data on request |
| Peace Now | FMEP republishes Peace Now maps and charts with hyperlink attribution | Moderate — established reuse practice |
| Al-Haq | Site footer states **"All Rights Reserved ©2026"** | Negative — no implied permission; metadata-and-link-out is the correct posture |
| B'Tselem | **Unknown.** btselem.org returned HTTP 429 to every automated request; terms not retrieved | Unverified — check before sending |
| Palestine Open Maps | No licence declared. Their `sources.csv` credits David Rumsey, National Libraries of Australia and Israel, Hebrew University, ESRI and OpenStreetMap | Mixed provenance likely explains the silence — ask narrowly |

One counter-signal worth knowing: CAMERA, a group critical of Peace Now, has
alleged they decline to release all underlying data. Treat as contested, but it
suggests a narrowly scoped request will land better than a broad one.

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

| File | Recipient | Asking for | Priority |
|---|---|---|---|
| `palestine-open-maps.md` | Palestine Open Maps | Licence for the locality database already in use | **Highest — we are redistributing it now** |
| `peace-now.md` | Peace Now (Settlement Watch) | Planning-stage, tender, construction-start and outpost data | High — unblocks stages 1–5 |
| `btselem.md` | B'Tselem | Municipal and regional council jurisdiction boundaries | High — unblocks two empty layers |
| `alhaq.md` | Al-Haq | Courtesy notice + confirmation the link-out approach is acceptable | Medium |
| `ocha-demolition-data.md` | OCHA oPt | Machine-readable export of the demolition database, plus the Gaza Yellow/Orange lines | Medium — format request, not permission |
| `pom-reply.md` | Palestine Open Maps | Reply confirming conditions met; answers the preview request; reports two coordinate errors back | Ready to send |
| `btselem-followup.md` | B'Tselem | Regional council boundaries; licence scope; which file is which definition | Ready to send |

These are **drafts for you to review and send**. Nothing has been sent.

Each still needs `[name]` and `[contact]` filled in. Addresses for Peace Now and
B'Tselem are search-derived and unverified — both sites block automated requests
— so confirm them before sending.
