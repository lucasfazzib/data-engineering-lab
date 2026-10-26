"""Step 1 - Kaggle CSV -> one JSON document per CSV row (JSON Lines file).

    python data_prep/csv_to_json.py                 # first 300 invoices (default sample)
    python data_prep/csv_to_json.py --invoices 0    # everything (~541k rows)

Each line of data/invoice_items.jsonl is one invoice ITEM, exactly what the input client will POST to
the API, in the order the items were created (InvoiceDate), so the stream replays the store's day.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path

DATASET = "carrie1/ecommerce-data/versions/1"  # pinned: reruns read the same file
OUT = Path("data/invoice_items.jsonl")


def download() -> Path:
    import kagglehub  # lazy: tests do not need it

    return Path(kagglehub.dataset_download(DATASET)) / "data.csv"


def row_to_item(row: dict) -> dict:
    """CSV row (all text) -> typed JSON document. Dates become ISO 8601, ids stay strings."""
    customer = (row.get("CustomerID") or "").strip()
    return {
        "InvoiceNo": row["InvoiceNo"].strip(),
        "StockCode": row["StockCode"].strip(),
        "Description": (row.get("Description") or "").strip() or None,
        "Quantity": int(row["Quantity"]),
        "InvoiceDate": datetime.strptime(row["InvoiceDate"], "%m/%d/%Y %H:%M").isoformat(),
        "UnitPrice": float(row["UnitPrice"]),
        # CustomerID comes as '17850' or '17850.0' depending on the export; missing for guest checkouts
        "CustomerID": str(int(float(customer))) if customer else None,
        "Country": row["Country"].strip(),
    }


def items(csv_path: Path, max_invoices: int) -> Iterator[dict]:
    seen: set[str] = set()
    # The file is Latin-1 encoded (product descriptions with £ and accents)
    with csv_path.open(newline="", encoding="latin-1") as f:
        for row in csv.DictReader(f):
            invoice = row["InvoiceNo"].strip()
            if max_invoices and invoice not in seen and len(seen) >= max_invoices:
                return
            seen.add(invoice)
            yield row_to_item(row)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--invoices", type=int, default=300, help="number of invoices to keep (0 = all)")
    parser.add_argument("--csv", type=Path, help="local data.csv (skips the download)")
    args = parser.parse_args()
    csv_path = args.csv or download()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with OUT.open("w", encoding="utf-8") as out:
        for item in items(csv_path, args.invoices):
            out.write(json.dumps(item, ensure_ascii=False) + "\n")
            n += 1
    print(f"wrote {n:,} invoice items to {OUT}")


if __name__ == "__main__":
    main()
