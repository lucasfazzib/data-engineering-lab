"""Invoice items -> nested MongoDB invoice documents (pure Python, unit-tested without Spark).

Document model (one per invoice, items embedded):
    {
      "_id": "536365", "InvoiceNo": "536365", "CustomerID": "17850", "Country": "United Kingdom",
      "InvoiceDate": datetime, "items": [{"StockCode": ..., "Description": ..., "Quantity": 6, "UnitPrice": 2.55}, ...]
    }
Embedding fits the read pattern (the UI always shows an invoice WITH its items) and an invoice is small.

Idempotent upsert: header fields with $set, items with $addToSet. Replaying the same Kafka messages
(restart from an old checkpoint, duplicate POSTs) never duplicates items.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime

from pymongo import UpdateOne

ITEM_FIELDS = ("StockCode", "Description", "Quantity", "UnitPrice")


def _as_datetime(value) -> datetime:
    return value if isinstance(value, datetime) else datetime.fromisoformat(str(value))


def build_updates(items: Iterable[dict]) -> list[UpdateOne]:
    by_invoice: dict[str, dict] = {}
    for it in items:
        doc = by_invoice.setdefault(
            it["InvoiceNo"],
            {
                "header": {
                    "InvoiceNo": it["InvoiceNo"],
                    "CustomerID": it.get("CustomerID"),
                    "Country": it.get("Country"),
                    "InvoiceDate": _as_datetime(it["InvoiceDate"]),
                    "IsCancellation": it["InvoiceNo"].startswith("C"),
                },
                "items": [],
            },
        )
        item = {f: it.get(f) for f in ITEM_FIELDS}
        if item not in doc["items"]:
            doc["items"].append(item)
    return [
        UpdateOne({"_id": invoice}, {"$set": d["header"], "$addToSet": {"items": {"$each": d["items"]}}}, upsert=True)
        for invoice, d in by_invoice.items()
    ]
