"""Simulates an EL tool (Fivetran, Airbyte, dlt...) landing CSV extracts into the `raw` schema.

dbt does NOT load data — it only transforms what is already in the warehouse.
This script plays the role of the ingestion layer so dbt has sources to read from.

Load semantics per table (as many real extracts behave):
  - customers, books     -> full extract: table is REPLACED on every load
  - orders, order_items  -> append-only: every load adds rows (updates arrive as new rows)
"""

import argparse
import os
from pathlib import Path

import duckdb

LANDING = Path(__file__).resolve().parent.parent / "landing"
FULL_EXTRACT = {"customers", "books"}
APPEND_ONLY = {"orders", "order_items"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("batch", help="folder inside landing/, e.g. batch_1")
    parser.add_argument("--reset", action="store_true", help="drop the raw schema first")
    args = parser.parse_args()

    batch_dir = LANDING / args.batch
    db_path = os.environ.get("DUCKDB_PATH", str(LANDING.parent / "warehouse" / "bookstore.duckdb"))
    con = duckdb.connect(db_path)

    if args.reset:
        con.execute("drop schema if exists raw cascade")
    con.execute("create schema if not exists raw")

    for csv_file in sorted(batch_dir.glob("*.csv")):
        table = csv_file.stem
        select = f"""
            select *, current_timestamp as _loaded_at, '{args.batch}' as _batch
            from read_csv('{csv_file}', header = true, all_varchar = true)
        """
        exists = con.execute(
            "select count(*) from information_schema.tables where table_schema = 'raw' and table_name = ?",
            [table],
        ).fetchone()[0]

        if table in FULL_EXTRACT or not exists:
            con.execute(f"create or replace table raw.{table} as {select}")
        elif table in APPEND_ONLY:
            con.execute(f"insert into raw.{table} {select}")
        else:
            raise ValueError(f"unknown load semantics for table {table}")

        total = con.execute(f"select count(*) from raw.{table}").fetchone()[0]
        print(f"raw.{table:<12} <- {csv_file.name:<16} (table now has {total} rows)")

    con.close()


if __name__ == "__main__":
    main()
