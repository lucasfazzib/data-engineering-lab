"""Step 3 - input client: reads the JSON documents and sends them to the API one by one.

    python client/api_client.py                       # all items, as fast as the API answers
    python client/api_client.py --rate 20 --limit 500 # 20 items/s, first 500 items (watch it live)

Simulates the point-of-sale: invoices are created over time and pushed to the platform as they happen.
"""

from __future__ import annotations

import argparse
import json
import time
from collections.abc import Iterator
from pathlib import Path

import httpx


def read_items(path: Path, limit: int = 0) -> Iterator[dict]:
    with path.open(encoding="utf-8") as f:
        for i, line in enumerate(f):
            if limit and i >= limit:
                return
            if line.strip():
                yield json.loads(line)


def send(client: httpx.Client, url: str, item: dict, retries: int = 5) -> bool:
    """POST with retries on 5xx/connection errors (exponential backoff). 4xx = bad data: do not retry."""
    for attempt in range(retries):
        try:
            response = client.post(url, json=item)
        except httpx.TransportError:
            response = None
        if response is not None and response.status_code < 500:
            return response.status_code == 201
        time.sleep(min(2**attempt * 0.2, 5))
    return False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=Path, default=Path("data/invoice_items.jsonl"))
    parser.add_argument("--url", default="http://localhost:8000/invoiceitem")
    parser.add_argument("--rate", type=float, default=0, help="items per second (0 = no throttle)")
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    ok = failed = 0
    started = time.perf_counter()
    with httpx.Client(timeout=10) as client:
        for item in read_items(args.file, args.limit):
            if send(client, args.url, item):
                ok += 1
            else:
                failed += 1
                print(f"rejected: {item['InvoiceNo']}/{item['StockCode']}")
            if args.rate:
                time.sleep(1 / args.rate)
            if (ok + failed) % 500 == 0:
                print(f"{ok + failed:,} sent ({ok:,} accepted)")
    elapsed = time.perf_counter() - started
    print(f"done: {ok:,} accepted, {failed:,} rejected in {elapsed:.1f}s ({ok / max(elapsed, 1e-9):,.0f} items/s)")


if __name__ == "__main__":
    main()
