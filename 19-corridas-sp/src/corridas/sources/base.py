"""The contract every source plugin follows.

A source yields RaceRecords: only FACTUAL event data (name, date, place, distances, price, status, link)
plus collection metadata. No HTML is kept: some event pages also list athletes (personal data, LGPD),
so the extractor reads only the fields below and stores a hash of the page as evidence of what it saw.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from typing import Protocol


@dataclass
class RaceRecord:
    source: str
    source_event_id: str
    source_url: str  # always kept: credit + link back to the original
    name: str
    event_date: date
    city: str | None = None
    uf: str | None = None
    start_time: str | None = None  # 'HH:MM' local time
    venue: str | None = None
    distances_km: list[float] = field(default_factory=list)
    price_brl: float | None = None  # lowest listed price (current batch / cheapest category)
    price_max_brl: float | None = None
    price_batch: str | None = None  # "lote"
    status: str | None = None  # open | sold_out | closed | postponed | cancelled
    organizer: str | None = None
    registration_url: str | None = None
    fetched_at: datetime | None = None
    content_hash: str | None = None

    def as_row(self) -> dict:
        return asdict(self)


class Source(Protocol):
    name: str

    def collect(self) -> Iterator[RaceRecord]: ...
