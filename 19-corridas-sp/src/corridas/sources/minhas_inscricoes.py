"""Minhas Inscrições: public race calendar (no robots.txt restrictions, no terms forbidding it - see README).

1. Listing pages /pt-br/Calendario/Filtro?pagina=N (20 cards each): id, name, date, "City, UF", type.
2. Each card links through a click counter (/ClickEventos/Redirecionar). To avoid inflating the organizers'
   click statistics, the redirect is resolved ONCE per event (without following it) and the target
   /Evento/<slug> URL is cached forever.
3. The event page is free-form HTML written by each organizer, and it can contain personal data (e.g. a
   contact e-mail inside the price table). So we extract only numbers and flags from it - distances,
   min/max price, registration status, start time - and never store any text from the page.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import unicodedata
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from urllib.parse import urlencode

from bs4 import BeautifulSoup

from corridas.http import PoliteClient
from corridas.sources.base import RaceRecord

log = logging.getLogger(__name__)
BASE = "https://www.minhasinscricoes.com.br"
MAX_PAGES = 60  # safety net: the calendar has ~15 pages


@dataclass
class Card:
    event_id: str
    key: str
    name: str
    event_date: date
    city: str | None
    uf: str | None
    kind: str


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    return "".join(c for c in text if not unicodedata.combining(c)).lower()


def listing_url(page: int, today: date) -> str:
    params = {
        "pagina": page,
        "Valor": "0,500",
        "PesquisaDataInicio": today.strftime("%d/%m/%Y"),
        "PesquisaDataFim": "31/12/9999",
        "exclusivo": "False",
        "internacional": "False",
    }
    return f"{BASE}/pt-br/Calendario/Filtro?{urlencode(params)}"


def parse_listing(html: str) -> list[Card]:
    soup = BeautifulSoup(html, "html.parser")
    cards = []
    for caption in soup.select("div.caption-evento[data-view-idevento]"):
        thumb = caption.find_parent(class_="thumbnail")
        link = thumb.select_one("a[data-evento-key]") if thumb else None
        title = caption.select_one(".titulo-destaque")
        cal = caption.select_one(".fa-calendar-alt")
        pin = caption.select_one(".fa-map-marker")
        if not (link and title and cal):
            continue
        try:
            event_date = datetime.strptime(cal.parent.get_text(strip=True), "%d/%m/%Y").date()
        except ValueError:
            continue
        city = uf = None
        place = pin.find_next("span").get_text(strip=True) if pin else ""
        if m := re.match(r"^(.*),\s*([A-Z]{2})$", place):
            city, uf = m.group(1).strip(), m.group(2)
        paragraphs = [p.get_text(" ", strip=True) for p in caption.find_all("p")]
        cards.append(
            Card(
                event_id=caption["data-view-idevento"].strip(),
                key=link["data-evento-key"],
                name=" ".join(title.get_text(" ", strip=True).split()),
                event_date=event_date,
                city=city,
                uf=uf,
                kind=paragraphs[-1] if paragraphs else "",
            )
        )
    return cards


# ---------- event page: numbers and flags only ----------
DISTANCE = re.compile(r"(?<![\d,.])(\d{1,2}(?:[.,]\d{1,3})?)\s*(?:k\b|km\b|kms\b|quil[oô]metros)", re.I)
PRICE = re.compile(r"R\$\s*(\d{1,4}(?:\.\d{3})*(?:,\d{2})?)")
START = re.compile(r"(?:largada|hor[aá]rio)[^0-9]{0,40}(\d{1,2})\s*[h:]\s*(\d{2})?", re.I)


def page_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    return " ".join(soup.get_text(" ").split())


def extract_distances(text: str) -> list[float]:
    found = {float(m.group(1).replace(",", ".")) for m in DISTANCE.finditer(text)}
    t = _norm(text)
    if "meia maratona" in t or "meia-maratona" in t:
        found.add(21.0975)
    if re.search(r"(?<!meia )(?<!meia-)maratona\b", t) and "42" in t:
        found.add(42.195)
    # keep plausible running distances only (walks of 1-2 km and typos like 500 km are dropped)
    return sorted(d for d in found if 3 <= d <= 100)


def extract_prices(text: str) -> tuple[float | None, float | None]:
    values = [float(v.replace(".", "").replace(",", ".")) for v in PRICE.findall(text)]
    values = [v for v in values if 10 <= v <= 2000]  # ignore fees/donations and absurd values
    return (min(values), max(values)) if values else (None, None)


def extract_status(text: str) -> str | None:
    t = _norm(text)
    if "esgotad" in t:
        return "sold_out"
    if "inscricoes encerradas" in t or "inscricao encerrada" in t:
        return "closed"
    if "cancelad" in t and "evento cancelado" in t:
        return "cancelled"
    if "adiad" in t and "evento adiado" in t:
        return "postponed"
    if "inscricoes abertas" in t or "inscreva-se" in t:
        return "open"
    return None


def extract_start_time(text: str) -> str | None:
    m = START.search(text)
    if not m or int(m.group(1)) > 23:
        return None
    return f"{int(m.group(1)):02d}:{m.group(2) or '00'}"


class MinhasInscricoesSource:
    name = "minhas_inscricoes"

    def __init__(self, client: PoliteClient, url_cache: Path, uf: str = "SP", today: date | None = None) -> None:
        self.client = client
        self.url_cache = url_cache
        self.uf = uf
        self.today = today or date.today()

    def _event_urls(self) -> dict[str, str]:
        return json.loads(self.url_cache.read_text()) if self.url_cache.exists() else {}

    def _save_event_urls(self, urls: dict[str, str]) -> None:
        self.url_cache.parent.mkdir(parents=True, exist_ok=True)
        self.url_cache.write_text(json.dumps(urls, indent=0, sort_keys=True))

    def cards(self) -> Iterator[Card]:
        for page in range(1, MAX_PAGES + 1):
            r = self.client.get(listing_url(page, self.today))
            found = parse_listing(r.text) if r.status == 200 else []
            if not found:
                return
            yield from found

    def collect(self) -> Iterator[RaceRecord]:
        urls = self._event_urls()
        cards = [c for c in self.cards() if c.uf == self.uf and "virtual" not in _norm(f"{c.name} {c.kind}")]
        log.info("minhas_inscricoes: %d in-person events in %s", len(cards), self.uf)
        for card in cards:
            if card.key not in urls:
                target = self.client.resolve_redirect(f"{BASE}/pt-br/ClickEventos/Redirecionar?origem=1&keycode={card.key}")
                if not target:
                    continue
                urls[card.key] = target if target.startswith("http") else f"{BASE}{target}"
                self._save_event_urls(urls)
            url = urls[card.key]
            r = self.client.get(url)
            text = page_text(r.text) if r.status == 200 else ""
            price_min, price_max = extract_prices(text)
            yield RaceRecord(
                source=self.name,
                source_event_id=card.event_id,
                source_url=url,
                name=card.name,
                event_date=card.event_date,
                city=card.city,
                uf=card.uf,
                start_time=extract_start_time(text),
                distances_km=extract_distances(f"{card.name} {text}"),
                price_brl=price_min,
                price_max_brl=price_max,
                status=extract_status(text),
                registration_url=url,
                fetched_at=datetime.now(UTC),
                content_hash=hashlib.sha256(r.text.encode()).hexdigest() if text else None,
            )
