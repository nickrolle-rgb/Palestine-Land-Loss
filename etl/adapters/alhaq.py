"""Al-Haq automated ingest.

Al-Haq does not publish a geolocated incident API. What exists is paginated
listings of narrative HTML reports under numeric IDs. So "automated ingest"
here means: crawl the listings for structured (title, date, URL) triples, then
resolve a location by matching place names against the OCHA communities
gazetteer.

Two rules govern this module, and they exist because the alternative is a map
that quietly invents facts:

1. **Copyright.** We store title, date, URL and the matched locality. We do not
   republish Al-Haq's report text. Every incident links out to Al-Haq.

2. **No guessed pins.** A record whose location cannot be resolved to exactly
   one gazetteer locality is kept in the dataset with confidence AMBIGUOUS or
   UNRESOLVED and is *not* drawn on the map. The counts are reported in the
   build summary and surfaced in the UI, so the coverage gap is visible instead
   of being papered over with a plausible-looking dot.
"""

from __future__ import annotations

import re
import unicodedata
from datetime import datetime
from typing import Any, Iterable

from bs4 import BeautifulSoup

from ..fetch import get
from ..schema import Confidence, Incident, Locality, RecordType

BASE = "https://www.alhaq.org"

# Listing sections, each paginating with ?page=N, and what kind of record they
# produce. The periodic reports aggregate violations across the whole West Bank;
# they are indexed and linked but never plotted, because a single pin would
# misrepresent territory-wide coverage as a located event.
SECTIONS: dict[str, RecordType] = {
    "monitoring-documentation/FromtheField": RecordType.FIELD_STORY,
    "monitoring-documentation/fieldwork-reports": RecordType.PERIODIC_REPORT,
    "monitoring-documentation/monthly-reports": RecordType.PERIODIC_REPORT,
    "monitoring-documentation/annual-reports": RecordType.PERIODIC_REPORT,
}

MAX_PAGES_PER_SECTION = 40  # safety stop; crawl ends earlier when a page is empty

# Coarse categorisation from title keywords. Deliberately conservative — an
# unmatched title simply gets no category rather than a wrong one.
CATEGORY_KEYWORDS = {
    "demolition": ["demolition", "demolish", "razed", "bulldoz"],
    "forced_transfer": ["forced transfer", "forcible transfer", "displace", "eviction", "evict"],
    "settler_violence": ["settler attack", "settler violence", "settlers attack", "arson", "pogrom"],
    "land_confiscation": ["confiscat", "seizure", "seized", "expropriat", "land grab"],
    "settlement_expansion": ["settlement expansion", "outpost", "new settlement", "annexation"],
    "movement_restriction": ["checkpoint", "closure", "road block", "movement restriction"],
    "detention": ["arrest", "detention", "detainee", "administrative detention"],
    "killing": ["killed", "killing", "shot dead", "extrajudicial"],
    "property_damage": ["uprooted", "olive tree", "crops", "property damage", "vandal"],
    "water_access": ["water", "cistern", "well", "spring"],
}

MONTHS = {
    m.lower(): i
    for i, m in enumerate(
        ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        start=1,
    )
}


# --------------------------------------------------------------------------
# Place-name normalisation
# --------------------------------------------------------------------------

# Arabic definite-article prefixes as they appear in English transliteration.
_ARTICLE_RE = re.compile(
    r"\b(?:al|el|as|ash|ad|at|az|ar|an|ain|ayn)[\s\-']+", re.IGNORECASE
)
_PUNCT_RE = re.compile(r"[^\w\s]", re.UNICODE)
_WS_RE = re.compile(r"\s+")


def normalise(text: str) -> str:
    """Fold transliteration variance so 'Al-'Isawiya' == 'Isawiya' == 'al Isawiyya'.

    Deliberately lossy. It is used only to *propose* matches; ambiguity is
    resolved by rejecting the record, never by picking a favourite.
    """
    if not text:
        return ""
    t = unicodedata.normalize("NFKD", text)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.replace("'", " ").replace("’", " ").replace("ʻ", " ").replace("ʼ", " ")
    t = t.lower()
    t = _ARTICLE_RE.sub(" ", t)
    t = _PUNCT_RE.sub(" ", t)
    t = _WS_RE.sub(" ", t).strip()
    # Common transliteration doublings.
    for a, b in (("yy", "y"), ("ww", "w"), ("ii", "i"), ("kh", "kh")):
        t = t.replace(a, b)
    return t


def parse_listing_date(raw: str) -> str | None:
    """Al-Haq renders '07، Aug 2026' — note the Arabic comma U+060C."""
    if not raw:
        return None
    cleaned = raw.replace("،", " ").replace(",", " ")
    cleaned = _WS_RE.sub(" ", cleaned).strip()
    m = re.match(r"(\d{1,2})\s+([A-Za-z]{3,})\s+(\d{4})", cleaned)
    if not m:
        m2 = re.search(r"(\d{4})", cleaned)
        return f"{m2.group(1)}-01-01" if m2 else None
    day, mon, year = m.groups()
    month = MONTHS.get(mon[:3].lower())
    if not month:
        return f"{year}-01-01"
    try:
        return datetime(int(year), month, int(day)).date().isoformat()
    except ValueError:
        return f"{year}-{month:02d}-01"


# --------------------------------------------------------------------------
# Gazetteer
# --------------------------------------------------------------------------

class Gazetteer:
    """Locality name index built from the OCHA communities layer.

    Also carries settlement names so an incident naming a settlement can be
    associated with it, though only Palestinian localities are used for the pin
    location.
    """

    # Short or highly generic names produce false positives inside sentences
    # ('Nabi Samwil' is safe; 'Beit' or 'Deir' alone are not).
    MIN_TOKEN_LEN = 5
    STOPNAMES = {"gaza", "israel", "palestine", "west bank", "jerusalem", "area c", "area a"}

    def __init__(self, localities: Iterable[Locality]):
        self.by_norm: dict[str, list[Locality]] = {}
        self.localities = list(localities)
        for loc in self.localities:
            for variant in self._variants(loc):
                n = normalise(variant)
                if len(n) < self.MIN_TOKEN_LEN or n in self.STOPNAMES:
                    continue
                self.by_norm.setdefault(n, []).append(loc)

    @staticmethod
    def _variants(loc: Locality) -> list[str]:
        out = [loc.names.primary]
        if loc.names.arabic:
            out.append(loc.names.arabic)
        # OCHA composites like "Beit Hanina - Dahiyat Al Bareed" also match on
        # each side of the dash.
        for part in re.split(r"\s*[-–]\s*", loc.names.primary):
            if len(part.strip()) > 4:
                out.append(part.strip())
        return out

    def match(self, text: str) -> tuple[list[Locality], str | None]:
        """Return (candidates, matched_surface_form).

        Longest name wins, so 'Beit Hanina - Dahiyat Al Bareed' beats
        'Beit Hanina' when both appear.
        """
        hay = f" {normalise(text)} "
        hits: list[tuple[int, str, list[Locality]]] = []
        for norm_name, locs in self.by_norm.items():
            if f" {norm_name} " in hay:
                hits.append((len(norm_name), norm_name, locs))
        if not hits:
            return [], None
        hits.sort(key=lambda h: -h[0])
        best_len = hits[0][0]
        top = [h for h in hits if h[0] == best_len]
        # Deduplicate by locality_id — the same place reached via two variants
        # is one candidate, not two.
        seen: dict[str, Locality] = {}
        for _, _, locs in top:
            for loc in locs:
                seen[loc.locality_id] = loc
        return list(seen.values()), hits[0][1]


# --------------------------------------------------------------------------
# Crawl
# --------------------------------------------------------------------------

def _parse_listing_page(html: str) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "lxml")
    out = []
    # list-12-item: "From the Field" cards. list-11-item: PDF report rows.
    for a in soup.select("a.list-12-item, a.list-11-item, a.list-2-item, a.list-13-item"):
        href = a.get("href") or ""
        if not re.search(r"/\d+\.html$", href):
            continue
        title_el = a.select_one(
            ".list-12-item-title, .list-11-item-title, .list-2-item-title"
        )
        title = (title_el.get_text(strip=True) if title_el else a.get("title") or "").strip()
        date_el = a.select_one(
            ".list-2-item-date span, .list-12-item-date span, .list-11-item-date span"
        )
        date_raw = date_el.get_text(strip=True) if date_el else ""
        if not title:
            continue
        out.append({"url": href, "title": title, "date_raw": date_raw})
    return out


def crawl_section(section: str, max_pages: int = MAX_PAGES_PER_SECTION) -> list[dict[str, Any]]:
    seen_urls: set[str] = set()
    records: list[dict[str, Any]] = []

    for page in range(1, max_pages + 1):
        url = f"{BASE}/{section}" + (f"?page={page}" if page > 1 else "")
        try:
            resp = get(url)
        except Exception as exc:  # noqa: BLE001 — a dead page ends the section
            print(f"    ! {section} page {page}: {exc}")
            break

        items = _parse_listing_page(resp.text)
        fresh = [i for i in items if i["url"] not in seen_urls]
        if not fresh:
            break
        for i in fresh:
            seen_urls.add(i["url"])
            i["section"] = section
        records.extend(fresh)
        print(f"    {section} page {page}: +{len(fresh)} (total {len(records)})")

    return records


def categorise(title: str) -> list[str]:
    low = title.lower()
    return [cat for cat, kws in CATEGORY_KEYWORDS.items() if any(k in low for k in kws)]


def article_text(url: str, limit: int = 6000) -> str:
    """Fetch an article's visible text *for place-name matching only*.

    The text is used transiently to locate the record and is never stored or
    republished — only the resulting locality id survives into the dataset.
    """
    try:
        soup = BeautifulSoup(get(url).text, "lxml")
    except Exception as exc:  # noqa: BLE001
        print(f"    ! body fetch failed {url}: {exc}")
        return ""
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    node = soup.select_one(".page-1-content, article, .post-content") or soup
    return node.get_text(" ", strip=True)[:limit]


def build_incidents(
    gaz: Gazetteer,
    *,
    sections: dict[str, RecordType] | None = None,
    match_bodies: bool = True,
) -> list[Incident]:
    raw: list[dict[str, Any]] = []
    for section, record_type in (sections or SECTIONS).items():
        print(f"  crawling {section}")
        for rec in crawl_section(section):
            rec["record_type"] = record_type
            raw.append(rec)

    incidents: list[Incident] = []
    body_lookups = 0

    for rec in raw:
        incident_id = re.search(r"/(\d+)\.html$", rec["url"]).group(1)
        record_type: RecordType = rec["record_type"]

        candidates, surface = gaz.match(rec["title"])
        matched_from = "title" if candidates else None

        # Titles alone resolve poorly ("Special Focus: Demolition and Forced
        # Transfer in Silwan" works; many do not name a place). For locatable
        # field stories only, fall back to the article body. Periodic reports
        # are skipped entirely — matching them would only produce a wrong pin.
        if (
            match_bodies
            and not candidates
            and record_type is RecordType.FIELD_STORY
        ):
            body = article_text(rec["url"])
            body_lookups += 1
            if body:
                candidates, surface = gaz.match(body)
                matched_from = "body" if candidates else None

        if record_type is RecordType.PERIODIC_REPORT:
            confidence = Confidence.UNRESOLVED
            geometry = None
            matched_id: str | None = None
            note = (
                "Periodic report covering multiple locations; indexed and linked "
                "but deliberately not plotted."
            )
            surface = None
            matched_from = None
        elif len(candidates) == 1:
            loc = candidates[0]
            confidence = Confidence.MATCHED
            geometry = loc.geometry
            matched_id = loc.locality_id
            note = f"Matched '{surface}' in {matched_from} to gazetteer locality."
        elif len(candidates) > 1:
            confidence = Confidence.AMBIGUOUS
            geometry = None
            matched_id = None
            names = ", ".join(sorted(c.names.primary for c in candidates))[:200]
            note = f"'{surface}' matches multiple localities ({names}); not plotted."
        else:
            confidence = Confidence.UNRESOLVED
            geometry = None
            matched_id = None
            note = "No locality name recognised in title or body; not plotted."

        incidents.append(
            Incident(
                incident_id=f"alhaq-{incident_id}",
                title=rec["title"],
                date=parse_listing_date(rec["date_raw"]),
                url=rec["url"],
                source_id="alhaq",
                record_type=record_type,
                summary=None,  # deliberately not populated — link out, don't republish
                categories=categorise(rec["title"]),
                location_text=surface,
                matched_locality_id=matched_id,
                matched_from=matched_from,
                geometry=geometry,
                confidence=confidence,
                match_note=note,
            )
        )

    if body_lookups:
        print(f"    (fetched {body_lookups} article bodies for place matching)")
    return incidents
