"""Extract the Olist dataset from Kaggle and load it, untouched, into the `raw` schema of DuckDB.

Design choices (see docs/adr/0003-raw-layer-as-varchar.md):
  - The dataset version is pinned: re-running gives the same input.
  - Every column lands as VARCHAR. Typing happens in dbt staging, where it is tested and documented.
  - The expected columns per file are a contract: if Kaggle changes a file, ingestion fails loudly here
    instead of silently breaking models downstream.
  - Each run writes a manifest (rows + sha256 per file) for lineage and reproducibility.
  - Idempotent: tables are replaced, so re-running never duplicates data.

Usage:
  python ingestion/extract_load.py           # download (cached) + load
  python ingestion/extract_load.py --empty   # create empty raw tables only (CI: dbt build --empty)
"""

import argparse
import hashlib
import json
import logging
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

import duckdb

DATASET = "olistbr/brazilian-ecommerce/versions/2"
DB_PATH = os.environ.get("DUCKDB_PATH", "warehouse/olist.duckdb")
MANIFEST_PATH = Path(DB_PATH).with_name("ingestion_manifest.json")

# file name -> (raw table, expected header)
RAW_TABLES: dict[str, tuple[str, list[str]]] = {
    "olist_customers_dataset.csv": (
        "customers",
        ["customer_id", "customer_unique_id", "customer_zip_code_prefix", "customer_city", "customer_state"],
    ),
    "olist_geolocation_dataset.csv": (
        "geolocation",
        ["geolocation_zip_code_prefix", "geolocation_lat", "geolocation_lng", "geolocation_city", "geolocation_state"],
    ),
    "olist_order_items_dataset.csv": (
        "order_items",
        ["order_id", "order_item_id", "product_id", "seller_id", "shipping_limit_date", "price", "freight_value"],
    ),
    "olist_order_payments_dataset.csv": (
        "order_payments",
        ["order_id", "payment_sequential", "payment_type", "payment_installments", "payment_value"],
    ),
    "olist_order_reviews_dataset.csv": (
        "order_reviews",
        [
            "review_id",
            "order_id",
            "review_score",
            "review_comment_title",
            "review_comment_message",
            "review_creation_date",
            "review_answer_timestamp",
        ],
    ),
    "olist_orders_dataset.csv": (
        "orders",
        [
            "order_id",
            "customer_id",
            "order_status",
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ],
    ),
    "olist_products_dataset.csv": (
        "products",
        [
            "product_id",
            "product_category_name",
            "product_name_lenght",
            "product_description_lenght",
            "product_photos_qty",
            "product_weight_g",
            "product_length_cm",
            "product_height_cm",
            "product_width_cm",
        ],
    ),
    "olist_sellers_dataset.csv": (
        "sellers",
        ["seller_id", "seller_zip_code_prefix", "seller_city", "seller_state"],
    ),
    "product_category_name_translation.csv": (
        "product_category_name_translation",
        ["product_category_name", "product_category_name_english"],
    ),
}

log = logging.getLogger("extract_load")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download() -> Path:
    import kagglehub  # noqa: PLC0415 - only needed when actually downloading

    # Public dataset: no Kaggle credentials required. Files are cached in $KAGGLEHUB_CACHE.
    return Path(kagglehub.dataset_download(DATASET))


def check_contract(con: duckdb.DuckDBPyConnection, csv_path: Path, expected: list[str]) -> None:
    actual = [
        row[0]
        for row in con.execute(
            "select column_name from (describe select * from read_csv(?, header = true, all_varchar = true))",
            [str(csv_path)],
        ).fetchall()
    ]
    if actual != expected:
        raise ValueError(f"{csv_path.name}: schema drift\n  expected {expected}\n  got      {actual}")


def load(con: duckdb.DuckDBPyConnection, source_dir: Path) -> list[dict]:
    manifest = []
    for file_name, (table, expected) in RAW_TABLES.items():
        csv_path = source_dir / file_name
        if not csv_path.exists():
            raise FileNotFoundError(csv_path)
        check_contract(con, csv_path, expected)
        con.execute(
            f"""
            create or replace table raw.{table} as
            select *, current_timestamp as _loaded_at, ? as _source_file
            from read_csv(?, header = true, all_varchar = true)
            """,
            [file_name, str(csv_path)],
        )
        rows = con.execute(f"select count(*) from raw.{table}").fetchone()[0]
        manifest.append({"table": f"raw.{table}", "file": file_name, "rows": rows, "sha256": sha256(csv_path)})
        log.info("raw.%-36s %9d rows", table, rows)
    return manifest


def create_empty(con: duckdb.DuckDBPyConnection) -> None:
    for table, columns in RAW_TABLES.values():
        cols = ", ".join(f'"{c}" varchar' for c in columns)
        con.execute(f"create or replace table raw.{table} ({cols}, _loaded_at timestamptz, _source_file varchar)")
        log.info("raw.%s created empty", table)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--empty", action="store_true", help="create empty raw tables (no download)")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    with duckdb.connect(DB_PATH) as con:
        con.execute("create schema if not exists raw")
        if args.empty:
            create_empty(con)
            return 0
        source_dir = download()
        log.info("dataset %s at %s", DATASET, source_dir)
        manifest = load(con, source_dir)

    MANIFEST_PATH.write_text(
        json.dumps(
            {"dataset": DATASET, "loaded_at": datetime.now(UTC).isoformat(), "files": manifest},
            indent=2,
        )
    )
    log.info("manifest written to %s", MANIFEST_PATH)
    return 0


if __name__ == "__main__":
    sys.exit(main())
