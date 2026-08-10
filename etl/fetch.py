"""Cached HTTP fetching with a provenance manifest.

Every download records URL, SHA-256, byte size and retrieval timestamp into
data/raw/manifest.json. That manifest is what lets the map say "retrieved on
<date>" per layer, and what makes a build reproducible.
"""

from __future__ import annotations

import hashlib
import json
import time
from datetime import date, datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
INTERIM = ROOT / "data" / "interim"
PROCESSED = ROOT / "web" / "public" / "data"
MANIFEST = RAW / "manifest.json"

USER_AGENT = (
    "SettlementEncroachmentMap/0.1 (research; contact via repository) "
    "python-requests"
)

# Be a good citizen when crawling Al-Haq: one request per this many seconds.
CRAWL_DELAY_S = 1.5
_last_request_at = 0.0


def _ensure_dirs() -> None:
    for d in (RAW, INTERIM, PROCESSED):
        d.mkdir(parents=True, exist_ok=True)


def load_manifest() -> dict:
    if MANIFEST.exists():
        return json.loads(MANIFEST.read_text(encoding="utf-8"))
    return {"entries": {}}


def save_manifest(m: dict) -> None:
    _ensure_dirs()
    MANIFEST.write_text(json.dumps(m, indent=2, ensure_ascii=False), encoding="utf-8")


def _throttle() -> None:
    global _last_request_at
    delta = time.monotonic() - _last_request_at
    if delta < CRAWL_DELAY_S:
        time.sleep(CRAWL_DELAY_S - delta)
    _last_request_at = time.monotonic()


def get(url: str, *, throttle: bool = True, timeout: int = 60) -> requests.Response:
    if throttle:
        _throttle()
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=timeout)
    resp.raise_for_status()
    return resp


def download(url: str, filename: str, *, force: bool = False) -> Path:
    """Download to data/raw/<filename>, skipping if already present."""
    _ensure_dirs()
    dest = RAW / filename
    manifest = load_manifest()

    if dest.exists() and not force:
        return dest

    resp = get(url, throttle=False, timeout=180)
    dest.write_bytes(resp.content)

    manifest["entries"][filename] = {
        "url": url,
        "sha256": hashlib.sha256(resp.content).hexdigest(),
        "bytes": len(resp.content),
        "retrieved": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    save_manifest(manifest)
    return dest


def retrieved_date(filename: str) -> str:
    entry = load_manifest()["entries"].get(filename)
    if entry:
        return entry["retrieved"][:10]
    return date.today().isoformat()


def write_json(path: Path, data: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )
    return path
