// Detail and About panels. Both exist to make the map arguable: every feature
// resolves to a dated document, and every definitional choice is stated.

import { EXTENT_STYLE, STAGE_COLOURS } from "./config.js";

const esc = (s) =>
  String(s ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
  );

const km2 = (m2) => (m2 ? `${(m2 / 1e6).toFixed(2)} km²` : "—");

function evidenceList(evidence = []) {
  if (!evidence.length) return `<p class="hint">No evidence attached — this is a bug.</p>`;
  return `<ul class="evidence">${evidence
    .map((e) => {
      const link = e.url
        ? `<a href="${esc(e.url)}" target="_blank" rel="noopener">${esc(e.title)}</a>`
        : esc(e.title);
      const bits = [
        e.document_date ? `dated ${esc(e.document_date)}` : null,
        e.retrieved ? `retrieved ${esc(e.retrieved)}` : null,
      ].filter(Boolean).join(" · ");
      return `<li>${link}<span class="meta">${bits}</span>${
        e.note ? `<span class="meta">${esc(e.note)}</span>` : ""
      }</li>`;
    })
    .join("")}</ul>`;
}

function stageHistoryBlock(history = []) {
  if (!history.length) return "";
  const rows = history
    .slice()
    .sort((a, b) => a.stage - b.stage)
    .map(
      (ev) => `
      <li>
        <span class="dot" style="display:inline-block;width:9px;height:9px;border-radius:50%;
              background:${STAGE_COLOURS[ev.stage] || "#888"};margin-right:6px"></span>
        <strong>${ev.stage}. ${esc(ev.stage_label)}</strong>
        <span class="meta">${
          ev.valid_from ? `from ${esc(ev.valid_from)}` : "date unknown"
        }${ev.valid_to ? ` to ${esc(ev.valid_to)}` : ""}</span>
        ${evidenceList(ev.evidence)}
      </li>`
    )
    .join("");
  return `<h4>Stage history</h4><ul class="evidence">${rows}</ul>`;
}

function namesBlock(names = {}) {
  const rows = [
    ["Arabic", names.arabic],
    ["Hebrew", names.hebrew],
    ["Pre-1948", names.pre_1948],
  ].filter(([, v]) => v);
  if (!rows.length) return "";
  return `<h4>Names</h4><dl>${rows
    .map(([k, v]) => `<dt>${k}</dt><dd>${esc(v)}</dd>`)
    .join("")}</dl>`;
}

export function renderDetail(feature, meta) {
  const p = feature.properties;
  const host = document.getElementById("detail-body");

  // GeoJSON sources return nested objects as JSON strings after a round trip
  // through the tile pipeline; parse defensively.
  const parse = (v) => {
    if (typeof v !== "string") return v;
    try { return JSON.parse(v); } catch { return v; }
  };
  const names = parse(p.names) || {};
  const evidence = parse(p.evidence) || [];
  const history = parse(p.stage_history) || [];
  const population = parse(p.population) || [];

  if (p.incident_id) {
    host.innerHTML = `
      <span class="kind">Documented incident · Al-Haq</span>
      <h3>${esc(p.title)}</h3>
      <dl>
        <dt>Date</dt><dd>${esc(p.date || "unknown")}</dd>
        <dt>Placed via</dt><dd>${esc(p.matched_from || "—")} match</dd>
        <dt>Confidence</dt><dd>${esc(p.confidence)}</dd>
        ${p.categories?.length ? `<dt>Categories</dt><dd>${esc([].concat(parse(p.categories)).join(", "))}</dd>` : ""}
      </dl>
      <p class="hint">${esc(p.match_note || "")}</p>
      <p><a href="${esc(p.url)}" target="_blank" rel="noopener">Read the record at Al-Haq →</a></p>
      <div class="warn">
        The pin marks the locality this record was matched to, not a precise
        address. Al-Haq's text is not reproduced here — follow the link.
      </div>`;
    document.getElementById("detail").hidden = false;
    return;
  }

  if (p.locality_id) {
    const pop = population.find((x) => x.value != null);
    host.innerHTML = `
      <span class="kind">Palestinian locality</span>
      <h3>${esc(p.name)}</h3>
      <dl>
        <dt>District</dt><dd>${esc(p.district || "—")}</dd>
        <dt>Oslo area</dt><dd>${esc(p.oslo_area || "—")}</dd>
        <dt>East Jerusalem</dt><dd>${p.in_east_jerusalem ? "Yes" : "No"}</dd>
        <dt>Population</dt><dd>${
          pop ? `${pop.value.toLocaleString()} (${pop.year})` : "not published"
        }</dd>
      </dl>
      ${namesBlock(names)}
      <h4>Sources</h4>${evidenceList(evidence)}`;
    document.getElementById("detail").hidden = false;
    return;
  }

  const extent = EXTENT_STYLE[p.extent_type];
  const unidentified = String(p.name || "").startsWith("Unidentified");
  host.innerHTML = `
    <span class="kind">${esc((p.entity_type || "").replace("_", " "))}</span>
    <h3>${esc(p.name)}</h3>
    <dl>
      <dt>Measured as</dt><dd>${esc(extent?.label || p.extent_type)}</dd>
      <dt>Area</dt><dd>${km2(p.area_m2)}</dd>
      <dt>District</dt><dd>${esc(p.district || "—")}</dd>
      <dt>Source CRS</dt><dd><code>${esc(p.source_crs || "—")}</code></dd>
      ${p.retroactive_authorisation_date
        ? `<dt>Retroactively authorised</dt><dd>${esc(p.retroactive_authorisation_date)}</dd>`
        : ""}
    </dl>
    <p class="hint">${esc(meta.extent_definitions?.[p.extent_type] || "")}</p>
    ${namesBlock(names)}
    ${stageHistoryBlock(history)}
    <h4>Sources</h4>${evidenceList(evidence)}
    ${unidentified ? `<div class="warn">
      This polygon has no name in the source dataset. It is shown because the
      geometry is real, but it has not yet been identified. See the corrections
      log.</div>` : ""}
    <div class="warn">
      Stage history is only as complete as the sources permit. The current build
      asserts the <em>minimum</em> stage the evidence supports — a built-up
      footprint observed on a date proves construction began by then, and nothing
      earlier. Stages 1–5 require Peace Now planning records, which are not yet
      integrated.
    </div>`;
  document.getElementById("detail").hidden = false;
}

// --------------------------------------------------------------------------

export function renderAbout(meta, data) {
  const stats = meta.stats || {};
  const inc = data.incidents?.metadata || {};
  const sources = meta.sources || [];

  const sourceRows = sources
    .map(
      (s) => `<tr>
        <td>${s.url ? `<a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.name)}</a>` : esc(s.name)}
          ${s.enabled ? "" : `<span class="badge-empty">not yet used</span>`}</td>
        <td>${esc(s.licence)}</td>
        <td>${esc(s.currency_note || "—")}</td>
      </tr>`
    )
    .join("");

  const extentRows = Object.entries(meta.extent_definitions || {})
    .map(
      ([k, v]) => `<tr>
        <td><span class="swatch" style="display:inline-block;width:10px;height:10px;
            border-radius:2px;margin-right:6px;background:${EXTENT_STYLE[k]?.colour}"></span>
          ${esc(EXTENT_STYLE[k]?.label || k)}</td>
        <td>${esc(v)}</td>
        <td>${stats.extent_counts?.[k] ?? 0} features</td>
      </tr>`
    )
    .join("");

  document.getElementById("about-body").innerHTML = `
    <h2>What this map shows</h2>
    <p>
      Israeli settlement development in the occupied Palestinian territory, drawn
      against the landscape that preceded it. This build is an
      <strong>East Jerusalem pilot</strong> on a West Bank-wide base layer, built
      on ${new Date(meta.built).toLocaleDateString("en-AU", { day: "numeric", month: "long", year: "numeric" })}.
    </p>

    <h2>The three ways to measure "how much land"</h2>
    <p>
      These differ by an order of magnitude. Choosing one silently would either
      understate the encroachment or overstate the daily footprint, so all three
      ship as separate toggles with their definitions stated.
    </p>
    <table><thead><tr><th>Layer</th><th>Definition</th><th>Coverage</th></tr></thead>
      <tbody>${extentRows}</tbody></table>
    <p class="hint">
      Municipal and regional council jurisdiction are not present in the openly
      licensed OCHA data. They are modelled and rendered but currently empty —
      shown as unavailable rather than quietly omitted.
    </p>

    <h2>The planning pipeline</h2>
    <p>
      Israeli settlement development follows a documented administrative pipeline
      and each step generates a dated public record: land declaration → plan
      deposited → plan approved → tenders published → ground works → construction
      start → populated. Outposts run on a parallel track: built without Israeli
      government authorisation, illegal under Israeli domestic law as well as
      international law, and frequently authorised retroactively — so they skip
      stages 2–4 rather than progressing through them.
    </p>
    <p class="hint">
      This build asserts only the minimum stage each source supports. It does not
      infer earlier stage dates it cannot cite.
    </p>

    <h2>Naming</h2>
    <p>
      Localities carry an Arabic name, an official name, a pre-1948 name and an
      OCHA transliteration, and these often disagree. The policy here is to show
      the Palestinian/Arabic name alongside the transliteration, and to list every
      known variant in the feature panel. Silently picking one scheme makes a map
      look partisan regardless of the quality of the data underneath it.
    </p>

    <h2>Legal position</h2>
    <p>
      That the settlements are unlawful is a sourced legal finding, not an
      editorial position of this project:
    </p>
    <ul>
      <li>UN Security Council Resolution 2334 (23 December 2016)</li>
      <li>International Court of Justice advisory opinion of 19 July 2024 on the
          legal consequences of Israel's policies and practices in the occupied
          Palestinian territory</li>
      <li>Australia's stated position that settlements are inconsistent with
          international law</li>
    </ul>

    <h2>Documented incidents</h2>
    <p>
      Incident records come from Al-Haq's monitoring and documentation. Al-Haq does
      not publish a geolocated database, so records are matched to localities by
      name. <strong>${inc.rendered ?? 0} of ${inc.total_records ?? 0}</strong>
      records are placed; ${inc.withheld ?? 0} are withheld because the location
      could not be resolved to exactly one locality, or because the record is a
      territory-wide periodic report. Nothing is plotted on a guess. Al-Haq's text
      is not reproduced — every record links back to them.
    </p>

    <h2>Sources and licensing</h2>
    <table><thead><tr><th>Source</th><th>Licence</th><th>Currency</th></tr></thead>
      <tbody>${sourceRows}</tbody></table>
    <p class="hint">
      Several OCHA layers have not been revised since 2018–2021. Where a layer is
      old, it is labelled with the date of the data, not the date of this build.
    </p>

    <h2>Known gaps</h2>
    <ul>
      <li>Planning stages 1–5 require Peace Now records, not yet integrated.</li>
      <li>Municipal and regional council jurisdiction boundaries are unsourced.</li>
      <li>Outposts are not present in the openly licensed data as a distinct class.</li>
      <li>24 settlement polygons carry no name in the source and are shown as
          unidentified rather than guessed.</li>
      <li>Per-settlement population time series (stage 7) requires Israeli CBS data.</li>
    </ul>

    <h2>Corrections</h2>
    <p>
      Errors are expected and tracked in the repository's corrections log. Every
      feature panel shows the source and the date it was retrieved, so any claim
      here can be checked against the document it came from.
    </p>`;
}
