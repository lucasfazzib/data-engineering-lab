"""Synthetic bronze + reference data for CI (no network, no real data).

    CORRIDAS_DATA=/tmp/corridas-ci python scripts/fixture_data.py

Includes the cases the warehouse must handle: the same race in two sources, a payment-variant duplicate
("- Pix" / "- Cartão"), a virtual event, an event outside SP, a track meet, and two collection days with a
price change (for the SCD2 snapshot).
"""

from __future__ import annotations

import os
import sys
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from corridas.ingest import RECORD_SCHEMA, write_bronze, write_run_log

DATA = Path(os.environ.get("CORRIDAS_DATA", "/tmp/corridas-ci"))
SOON = date.today() + timedelta(days=30)


def rec(source, sid, name, city, uf, *, distances, price=None, status=None, day=SOON):
    return {
        "source": source,
        "source_event_id": sid,
        "source_url": f"https://example.org/{source}/{sid}",
        "name": name,
        "event_date": day,
        "city": city,
        "uf": uf,
        "start_time": "07:00",
        "venue": None,
        "distances_km": distances,
        "price_brl": price,
        "price_max_brl": price,
        "price_batch": None,
        "status": status,
        "organizer": None,
        "registration_url": f"https://example.org/{source}/{sid}",
        "fetched_at": datetime.now(UTC),
        "content_hash": sid,
    }


def main() -> None:
    mi = [
        rec(
            "minhas_inscricoes", "1", "7ª Corrida Exemplo - Pix", "Santos", "SP", distances=[5.0, 10.0], price=90.0, status="open"
        ),
        rec(
            "minhas_inscricoes",
            "2",
            "7 CORRIDA EXEMPLO - Cartão",
            "Santos",
            "SP",
            distances=[5.0, 10.0],
            price=95.0,
            status="open",
        ),
        rec(
            "minhas_inscricoes",
            "3",
            "Meia Maratona Exemplo de Campinas",
            "Campinas",
            "SP",
            distances=[21.0975],
            price=150.0,
            status="open",
        ),
        rec("minhas_inscricoes", "4", "Desafio Virtual Exemplo", "São Paulo", "SP", distances=[5.0], price=50.0, status="open"),
        rec("minhas_inscricoes", "5", "Corrida Exemplo do Paraná", "Curitiba", "PR", distances=[10.0], price=80.0, status="open"),
    ]
    cbat = [
        rec("cbat", "100", "Meia Maratona Internacional Exemplo de Campinas", "Campinas", "SP", distances=[21.0975]),
        rec("cbat", "101", "Campeonato Exemplo de Atletismo em Pista", "São Paulo", "SP", distances=[]),
    ]
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    older = [{**r, "price_brl": (r["price_brl"] or 0) - 10, "fetched_at": r["fetched_at"] - timedelta(days=1)} for r in mi]
    write_bronze("minhas_inscricoes", older, DATA, day=yesterday)  # staging must keep only the newest version
    write_bronze("minhas_inscricoes", mi, DATA)
    write_bronze("cbat", cbat, DATA)
    for source, n in (("minhas_inscricoes", len(mi)), ("cbat", len(cbat))):
        write_run_log(source, datetime.now(UTC), n, None, DATA)
    ref = DATA / "reference"
    ref.mkdir(parents=True, exist_ok=True)
    pq.write_table(
        pa.Table.from_pylist(
            [
                {"ibge_code": "3548500", "name": "Santos", "uf": "SP", "lat": -23.96, "lon": -46.33},
                {"ibge_code": "3509502", "name": "Campinas", "uf": "SP", "lat": -22.91, "lon": -47.06},
                {"ibge_code": "3550308", "name": "São Paulo", "uf": "SP", "lat": -23.55, "lon": -46.63},
            ]
        ),
        ref / "municipalities_sp.parquet",
    )
    assert RECORD_SCHEMA  # imported for documentation: fixtures follow the same contract
    print(f"fixture data written to {DATA}")


if __name__ == "__main__":
    main()
