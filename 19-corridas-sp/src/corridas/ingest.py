"""Run the enabled sources and land their records in the bronze layer.

    python -m corridas.ingest                 # all enabled sources
    python -m corridas.ingest --source manual

Bronze layout (one file per source per collection day; rerunning the same day overwrites it):
    data/bronze/<source>/dt=YYYY-MM-DD/records.parquet
    data/bronze/_runs/<source>__<timestamp>.parquet    # run log: counts, errors (freshness/volume checks)
"""

from __future__ import annotations

import argparse
import logging
import time
from datetime import UTC, datetime
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import yaml

from corridas.http import PoliteClient
from corridas.sources.cbat import CbatSource
from corridas.sources.minhas_inscricoes import MinhasInscricoesSource

log = logging.getLogger("ingest")
ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"

RECORD_SCHEMA = pa.schema(
    [
        ("source", pa.string()),
        ("source_event_id", pa.string()),
        ("source_url", pa.string()),
        ("name", pa.string()),
        ("event_date", pa.date32()),
        ("city", pa.string()),
        ("uf", pa.string()),
        ("start_time", pa.string()),
        ("venue", pa.string()),
        ("distances_km", pa.list_(pa.float64())),
        ("price_brl", pa.float64()),
        ("price_max_brl", pa.float64()),
        ("price_batch", pa.string()),
        ("status", pa.string()),
        ("organizer", pa.string()),
        ("registration_url", pa.string()),
        ("fetched_at", pa.timestamp("us", tz="UTC")),
        ("content_hash", pa.string()),
    ]
)


def load_config(path: Path = ROOT / "config" / "sources.yaml") -> dict:
    return yaml.safe_load(path.read_text())


def build_sources(cfg: dict, only: str | None = None) -> list:
    client = PoliteClient(
        cfg["user_agent"],
        DATA / "http_cache",
        cache_ttl_hours=cfg["cache_ttl_hours"],
        min_interval_seconds=cfg["min_interval_seconds"],
    )
    sources = []
    for name, sc in cfg["sources"].items():
        if not sc.get("enabled") or (only and name != only):
            continue
        if name == "cbat":
            sources.append(CbatSource(client, sc["sitemap"], sc["allowed_url_pattern"]))
        elif name == "minhas_inscricoes":
            sources.append(MinhasInscricoesSource(client, DATA / "reference" / "minhas_inscricoes_urls.json", uf=sc["uf"]))
    return sources


def write_bronze(source: str, rows: list[dict], data_dir: Path = DATA, day: str | None = None) -> Path:
    day = day or datetime.now(UTC).strftime("%Y-%m-%d")
    path = data_dir / "bronze" / source / f"dt={day}" / "records.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    pq.write_table(pa.Table.from_pylist(rows, schema=RECORD_SCHEMA), tmp)
    tmp.replace(path)
    return path


def write_run_log(source: str, started: datetime, records: int, errors: str | None, data_dir: Path = DATA) -> None:
    path = data_dir / "bronze" / "_runs" / f"{source}__{started:%Y%m%dT%H%M%S}.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(
        pa.Table.from_pylist(
            [
                {
                    "source": source,
                    "started_at": started,
                    "finished_at": datetime.now(UTC),
                    "records": records,
                    "errors": errors,
                }
            ]
        ),
        path,
    )


def run(only: str | None = None) -> None:
    cfg = load_config()
    for source in build_sources(cfg, only):
        started, t0 = datetime.now(UTC), time.perf_counter()
        rows, error = [], None
        try:
            rows = [r.as_row() for r in source.collect()]
            if rows:
                write_bronze(source.name, rows)
        except Exception as exc:  # one broken source must not stop the others
            error = f"{type(exc).__name__}: {exc}"
            log.exception("source %s failed", source.name)
        write_run_log(source.name, started, len(rows), error)
        elapsed = time.perf_counter() - t0
        log.info("%s: %d records in %.1fs%s", source.name, len(rows), elapsed, f" ERROR {error}" if error else "")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    parser = argparse.ArgumentParser()
    parser.add_argument("--source")
    run(parser.parse_args().source)


if __name__ == "__main__":
    main()
