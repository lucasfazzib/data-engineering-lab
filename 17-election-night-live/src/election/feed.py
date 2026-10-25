"""TSE results feed: download and flatten.

The TSE publishes one JSON per scope (Brazil + 27 states) and OVERWRITES it on every counted batch.
These functions turn one file into flat rows; the poller keeps every version (append-only history).

Field glossary (abbreviated keys in the feed):
  dg/hg   date/time the totals were generated          s.st/s.ts  sections counted / total sections
  s.pst   % of sections counted                        e.te       registered voters
  e.c/e.a turnout / abstention                         v.vv       valid votes
  v.vb    blank votes   v.tvn  null votes              cand.vap   candidate votes, cand.pvap % of valid
"""

from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

# Brazil + 27 federative units, as used in the feed URLs
UFS = "br ac al am ap ba ce df es go ma mg ms mt pa pb pe pi pr rj rn ro rr rs sc se sp to".split()  # noqa: SIM905
ELECTION_CODE = "6258"  # 2026, 2nd round, federal offices
URL = "https://resultados.tse.jus.br/oficial/ele2026/{code}/dados/{uf}/{uf}-c0001-e00{code}-u.json"
BRASILIA = ZoneInfo("America/Sao_Paulo")


def url_for(uf: str, code: str = ELECTION_CODE) -> str:
    return URL.format(code=code, uf=uf)


def fetch(uf: str, timeout: int = 20) -> bytes:
    req = urllib.request.Request(url_for(uf), headers={"User-Agent": "data-engineering-lab/election-study"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def _int(value: str | None) -> int:
    return int(value) if value not in (None, "") else 0


def _pct(value: str | None) -> float:
    """TSE uses Brazilian decimal commas: '75,865101112' -> 75.865101112."""
    return float(value.replace(",", ".")) if value not in (None, "") else 0.0


@dataclass(frozen=True)
class Snapshot:
    scope: str
    totals_at: datetime  # when the TSE generated these totals (Brasilia time, tz-aware)
    totals: dict
    candidates: list[dict]

    @property
    def key(self) -> str:
        """Identity of a version of the file: same scope + same generation time = same data."""
        return f"{self.scope}|{self.totals_at.isoformat()}"


def parse(raw: bytes | str) -> Snapshot:
    d = json.loads(raw)
    scope = d["cdabr"].lower()
    totals_at = datetime.strptime(f"{d['dg']} {d['hg']}", "%d/%m/%Y %H:%M:%S").replace(tzinfo=BRASILIA)
    s, e, v = d.get("s", {}), d.get("e", {}), d.get("v", {})
    totals = {
        "scope": scope,
        "totals_at": totals_at,
        "sections_total": _int(s.get("ts")),
        "sections_counted": _int(s.get("st")),
        "pct_sections_counted": _pct(s.get("pstn") or s.get("pst")),
        "voters": _int(e.get("te")),
        "turnout": _int(e.get("c")),
        "abstention": _int(e.get("a")),
        "valid_votes": _int(v.get("vv")),
        "blank_votes": _int(v.get("vb")),
        "null_votes": _int(v.get("tvn")),
        "is_final": d.get("tf") == "s",
    }
    candidates = []
    for office in d.get("carg", []):
        for group in office.get("agr", []):
            for party in group.get("par", []):
                for c in party.get("cand", []):
                    candidates.append(
                        {
                            "scope": scope,
                            "totals_at": totals_at,
                            "number": _int(c.get("n")),
                            "name": c.get("nmu") or c.get("nm"),
                            "party": party.get("sg"),
                            "votes": _int(c.get("vap")),
                            "pct_valid": _pct(c.get("pvapn") or c.get("pvap")),
                            "is_elected": c.get("e") == "s",
                        }
                    )
    return Snapshot(scope, totals_at, totals, candidates)
