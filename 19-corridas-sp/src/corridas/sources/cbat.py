"""CBAt (Confederação Brasileira de Atletismo): official event pages listed in the public sitemap.

robots.txt allows /evento/ pages (it blocks /api/, /pesquisa, /download-dados - we use none of them).
From each page we read ONLY the header: date, "City - UF" and the event name. The page also has
"ATLETAS"/"CLUBES" tabs - never parsed, never stored.
"""

from __future__ import annotations

import hashlib
import logging
import re
import xml.etree.ElementTree as ET
from collections.abc import Iterator
from datetime import UTC, datetime

from bs4 import BeautifulSoup

from corridas.http import DisallowedByRobots, PoliteClient
from corridas.sources.base import RaceRecord

log = logging.getLogger(__name__)
NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
EVENT_ID = re.compile(r"/evento/(\d+)/")


def event_urls(sitemap_xml: str, allowed_pattern: str) -> list[str]:
    pattern = re.compile(allowed_pattern)
    root = ET.fromstring(sitemap_xml)
    urls = [loc.text.strip() for loc in root.findall(".//sm:loc", NS) if loc.text]
    return [u for u in urls if pattern.match(u)]


def parse_event(html: str, url: str) -> RaceRecord | None:
    """Header markup: <p class="font-black">26/07/2026</p><h3>São Paulo - SP</h3><h1>SP City Marathon</h1>."""
    soup = BeautifulSoup(html, "html.parser")
    h1 = soup.find("h1")
    if h1 is None:
        return None
    header = h1.parent
    date_p = header.find("p")
    place = header.find("h3")
    try:
        event_date = datetime.strptime(date_p.get_text(strip=True), "%d/%m/%Y").date()
    except (AttributeError, ValueError):
        return None
    city, uf = None, None
    if place:
        m = re.match(r"^(.*?)\s*-\s*([A-Z]{2})$", place.get_text(strip=True))
        if m:
            city, uf = m.group(1).strip(), m.group(2)
    id_match = EVENT_ID.search(url)
    return RaceRecord(
        source="cbat",
        source_event_id=id_match.group(1) if id_match else url,
        source_url=url,
        name=" ".join(h1.get_text(" ", strip=True).split()),
        event_date=event_date,
        city=city,
        uf=uf,
        organizer=None,
        registration_url=None,
        fetched_at=datetime.now(UTC),
        content_hash=hashlib.sha256(html.encode()).hexdigest(),
    )


class CbatSource:
    name = "cbat"

    def __init__(self, client: PoliteClient, sitemap: str, allowed_url_pattern: str) -> None:
        self.client = client
        self.sitemap = sitemap
        self.allowed_url_pattern = allowed_url_pattern

    def collect(self) -> Iterator[RaceRecord]:
        sitemap = self.client.get(self.sitemap)
        urls = event_urls(sitemap.text, self.allowed_url_pattern)
        log.info("cbat: %d event pages in the sitemap", len(urls))
        for url in urls:
            try:
                r = self.client.get(url)
            except DisallowedByRobots:
                log.warning("robots.txt disallows %s - skipped", url)
                continue
            if r.status != 200:
                log.warning("cbat: %s returned %s", url, r.status)
                continue
            record = parse_event(r.text, url)
            if record is None:
                log.warning("cbat: header not found in %s (layout change?)", url)
                continue
            yield record
