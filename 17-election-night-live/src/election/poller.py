"""Near-real-time ingestion: poll the TSE feed and keep EVERY version of it.

    python -m election.poller                 # poll forever (every 60 s)
    python -m election.poller --once          # one pass (cron / Airflow style)
    python -m election.poller --backfill DIR  # load raw *.json.gz captured earlier

Layout (a tiny lakehouse on the local disk):
  data/bronze/<scope>/<totals_at>.json.gz        raw file exactly as published (replayable)
  data/silver/totals/<scope>__<totals_at>.parquet       one row per (scope, version)
  data/silver/candidates/<scope>__<totals_at>.parquet   one row per (scope, version, candidate)

Idempotent: a version is identified by (scope, TSE generation time); re-polling or re-running a
backfill never duplicates it. Each version is its own file, so the dashboard reads while we write
(no database locks) and a crash mid-write only loses that one file.
"""

from __future__ import annotations

import argparse
import gzip
import logging
import time
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from election.feed import UFS, fetch, parse

log = logging.getLogger("poller")
DATA = Path("data")


def _stamp(snapshot) -> str:
    return snapshot.totals_at.strftime("%Y%m%dT%H%M%S")


def store(raw: bytes, data_dir: Path = DATA) -> bool:
    """Persist one published file. Returns False when that version was already stored."""
    snap = parse(raw)
    name = f"{snap.scope}__{_stamp(snap)}"
    totals_path = data_dir / "silver" / "totals" / f"{name}.parquet"
    if totals_path.exists():
        return False
    bronze = data_dir / "bronze" / snap.scope / f"{_stamp(snap)}.json.gz"
    bronze.parent.mkdir(parents=True, exist_ok=True)
    bronze.write_bytes(gzip.compress(raw))
    cand_path = data_dir / "silver" / "candidates" / f"{name}.parquet"
    cand_path.parent.mkdir(parents=True, exist_ok=True)
    totals_path.parent.mkdir(parents=True, exist_ok=True)
    if snap.candidates:
        _write(pa.Table.from_pylist(snap.candidates), cand_path)
    # totals last: its existence is the "commit marker" checked above
    _write(pa.Table.from_pylist([snap.totals]), totals_path)
    return True


def _write(table: pa.Table, path: Path) -> None:
    tmp = path.with_suffix(".tmp")
    pq.write_table(table, tmp)
    tmp.replace(path)  # atomic rename: readers never see a half-written file


def poll_once(data_dir: Path = DATA) -> int:
    new = 0
    for uf in UFS:
        try:
            new += store(fetch(uf), data_dir)
        except Exception as exc:  # one bad state must not stop the others
            log.warning("scope %s failed: %s", uf, exc)
        time.sleep(0.3)  # be polite to a public service on its busiest night
    return new


def backfill(source: Path, data_dir: Path = DATA) -> int:
    new = 0
    for path in sorted(source.rglob("*.json.gz")):
        try:
            new += store(gzip.decompress(path.read_bytes()), data_dir)
        except Exception as exc:
            log.warning("skip %s: %s", path.name, exc)
    return new


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--interval", type=int, default=60)
    parser.add_argument("--backfill", type=Path)
    args = parser.parse_args()
    if args.backfill:
        log.info("backfill: %d new versions", backfill(args.backfill))
        return
    while True:
        log.info("poll: %d new versions", poll_once())
        if args.once:
            return
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
