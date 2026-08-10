// Detail and About panels. Both exist to make the map arguable: every feature
// resolves to a dated document, and every definitional choice is stated.

import { EXTENT_STYLE, STAGE_COLOURS } from "./config.js";

const esc = (s) =>
  String(s ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
  );

const km2 = (m2) => (m2 ? `${(m2 / 1e6).toFixed(2)} km²` : "—");

// Citations are deduplicated into meta.evidence at build time; features carry
// `evidence_ref` ids. Older inline `evidence` arrays still resolve, so a stale
// cached payload degrades rather than breaking.
function resolveEvidence(props, meta) {
  const table = (meta && meta.evidence) || {};
  const refs = props.evidence_ref;
  if (Array.isArray(refs)) {
    return refs.map((id) => table[id]).filter(Boolean);
  }
  return Array.isArray(props.evidence) ? props.evidence : [];
}

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

function stageHistoryBlock(history = [], meta) {
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
        ${evidenceList(resolveEvidence(ev, meta))}
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
  const evidence = resolveEvidence(
    { ...p, evidence_ref: parse(p.evidence_ref), evidence: parse(p.evidence) },
    meta
  );
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
    const refs = parse(p.references) || {};
    // Population trajectory is the point for depopulated places: it shows what
    // was lost, not merely that something was.
    const series = population
      .filter((x) => x.value != null && !x.group)
      .sort((a, b) => a.year - b.year)
      .map((x) => `<dt>${x.year}</dt><dd>${x.value.toLocaleString()}</dd>`)
      .join("");
    const split = population.filter((x) => x.group && x.value != null);
    const refLinks = Object.entries(refs)
      .map(([k, v]) =>
        `<li><a href="${esc(v)}" target="_blank" rel="noopener">${esc(
          k.replace(/_/g, " ")
        )}</a></li>`
      )
      .join("");

    host.innerHTML = `
      <span class="kind">${
        p.depopulated_1948 ? "Depopulated locality · 1948" : "Palestinian locality"
      }</span>
      <h3>${esc(p.name)}</h3>
      <dl>
        <dt>District</dt><dd>${esc(p.district || "—")}</dd>
        ${p.subdistrict ? `<dt>Subdistrict</dt><dd>${esc(p.subdistrict)}</dd>` : ""}
        ${p.oslo_area ? `<dt>Oslo area</dt><dd>${esc(p.oslo_area)}</dd>` : ""}
        ${p.status_now ? `<dt>Status</dt><dd>${esc(p.status_now)}</dd>` : ""}
        ${p.depopulated_date ? `<dt>Depopulated</dt><dd>${esc(p.depopulated_date)}</dd>` : ""}
        ${p.group_1945 ? `<dt>Community 1945</dt><dd>${esc(p.group_1945)}</dd>` : ""}
      </dl>
      ${series ? `<h4>Population</h4><dl>${series}</dl>` : ""}
      ${split.length
        ? `<p class="hint">1945 split: ${split
            .map((x) => `${esc(x.group)} ${x.value.toLocaleString()}`)
            .join(" · ")}</p>`
        : ""}
      ${namesBlock(names)}
      ${refLinks ? `<h4>Further documentation</h4><ul class="evidence">${refLinks}</ul>` : ""}
      <h4>Sources</h4>${evidenceList(evidence)}
      ${p.depopulated_1948 ? `<div class="warn">
        Depopulation is a distinct mechanism from post-1967 settlement, with a
        different legal character and evidence base. It is styled apart for that
        reason, not to rank one above the other.
      </div>` : ""}`;
    document.getElementById("detail").hidden = false;
    return;
  }

  if (p.mechanism === "closed_military_area") {
    host.innerHTML = `
      <span class="kind">Closed military area</span>
      <h3>${esc(p.name)}</h3>
      <dl>
        <dt>Order signed</dt><dd>${esc(p.signed_date || "date not recorded")}</dd>
        <dt>Area</dt><dd>${km2(p.area_m2)}</dd>
        <dt>Source CRS</dt><dd><code>${esc(p.source_crs || "—")}</code></dd>
      </dl>
      <p class="hint">
        Land inside a firing zone is closed to Palestinian access. Firing zones
        cover roughly 18% of the West Bank.
      </p>
      <h4>Sources</h4>${evidenceList(evidence)}
      ${!p.zone_name ? `<div class="warn">
        This zone's name field was unreadable in the source dataset (the DBF
        encoding is unreliable). It is identified by its signing date rather than
        by a possibly garbled label.
      </div>` : ""}`;
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
    ${stageHistoryBlock(history, meta)}
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
      Palestinian land loss, drawn against the landscape that preceded it, with
      every element resolving to a dated document. Built on
      ${new Date(meta.built).toLocaleDateString("en-AU", { day: "numeric", month: "long", year: "numeric" })}.
    </p>

    <h2>Mechanisms, kept apart</h2>
    <p>
      Land has been lost by more than one process, and those processes are not
      alike. Rendering them in a single undifferentiated colour would misrepresent
      all of them, so each has its own styling, evidence and legal note:
    </p>
    <ul>
      <li><strong>Post-1967 settlement</strong> — unlawful under international law
        as a sourced finding (UNSC 2334; ICJ advisory opinion, 19 July 2024).</li>
      <li><strong>1948 depopulation</strong> — around 750,000 Palestinians
        displaced and ${stats.depopulated_1948 ?? 0} localities depopulated in the
        data shown here, with property subsequently vested in the state under the
        Absentees' Property Law 1950. A documented historical event, and a
        different legal category from the settlements.</li>
    </ul>
    <p class="hint">
      Keeping these distinct is not a softening. It is what stops a critic
      dismissing the whole map by attacking the weakest join in it.
    </p>

    <h2>Before the Mandate</h2>
    <p>
      Late-Ottoman Palestine was not a single administrative unit. The
      Mutasarrifiyya of Jerusalem — an independent sanjak reporting directly to
      Constantinople from 1872 — covered the south, while the sanjaks of Nablus
      and Acre sat under the Vilayet of Beirut.
    </p>
    <p class="hint">
      <strong>Those boundaries are not drawn on this map.</strong> No GIS dataset
      of late-Ottoman sanjak boundaries could be located — historical-basemaps and
      OpenHistoricalMap both stop at empire level. Rather than hand-draw them, the
      period is represented by the PEF Survey of Western Palestine (surveyed
      1871–77), which is actual surveyed cartography of the time, and the gap is
      recorded in the corrections log.
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
