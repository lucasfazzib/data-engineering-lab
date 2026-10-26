import csv
import json

import httpx
import pytest
from fastapi.testclient import TestClient

from api_ingest import main as api
from client.api_client import read_items, send
from data_prep.csv_to_json import items, row_to_item
from spark.jobs.mongo_sink import build_updates

ROW = {
    "InvoiceNo": "536365",
    "StockCode": "85123A",
    "Description": "WHITE HANGING HEART T-LIGHT HOLDER",
    "Quantity": "6",
    "InvoiceDate": "12/1/2010 8:26",
    "UnitPrice": "2.55",
    "CustomerID": "17850.0",
    "Country": "United Kingdom",
}


# ---------- data prep ----------
def test_row_to_item_types_and_dates():
    item = row_to_item(ROW)
    assert item["Quantity"] == 6 and item["UnitPrice"] == 2.55
    assert item["InvoiceDate"] == "2010-12-01T08:26:00"
    assert item["CustomerID"] == "17850"


def test_guest_checkout_has_no_customer():
    assert row_to_item({**ROW, "CustomerID": ""})["CustomerID"] is None


def test_items_stops_after_n_invoices(tmp_path):
    path = tmp_path / "data.csv"
    with path.open("w", newline="", encoding="latin-1") as f:
        w = csv.DictWriter(f, fieldnames=list(ROW))
        w.writeheader()
        for inv in ["1", "1", "2", "3", "3"]:
            w.writerow({**ROW, "InvoiceNo": inv})
    assert [i["InvoiceNo"] for i in items(path, max_invoices=2)] == ["1", "1", "2"]
    assert len(list(items(path, max_invoices=0))) == 5


# ---------- api-ingest ----------
class FakeProducer:
    def __init__(self):
        self.messages = []

    def produce(self, topic, key, value):
        self.messages.append((topic, key, json.loads(value)))

    def flush(self, timeout):
        return 0


@pytest.fixture
def api_client():
    producer = FakeProducer()
    api.app.state.producer = producer
    with TestClient(api.app) as client:
        yield client, producer
    api.app.state.producer = None


def test_valid_item_is_produced_keyed_by_invoice(api_client):
    client, producer = api_client
    r = client.post("/invoiceitem", json=row_to_item(ROW))
    assert r.status_code == 201
    topic, key, value = producer.messages[0]
    assert topic == "ingestion-topic" and key == b"536365" and value["StockCode"] == "85123A"


@pytest.mark.parametrize("bad", [{"Quantity": "six"}, {"UnitPrice": -1}, {"InvoiceNo": ""}, {"InvoiceDate": "yesterday"}])
def test_invalid_items_are_rejected_before_kafka(api_client, bad):
    client, producer = api_client
    assert client.post("/invoiceitem", json={**row_to_item(ROW), **bad}).status_code == 422
    assert producer.messages == []


def test_queue_full_returns_503(api_client):
    client, producer = api_client

    def full(*_, **__):
        raise BufferError

    producer.produce = full
    assert client.post("/invoiceitem", json=row_to_item(ROW)).status_code == 503


# ---------- input client ----------
def test_client_retries_server_errors_but_not_bad_requests(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda _: None)
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        return httpx.Response(503 if calls["n"] < 3 else 201)

    with httpx.Client(transport=httpx.MockTransport(handler)) as c:
        assert send(c, "http://api/invoiceitem", {}) is True and calls["n"] == 3
    with httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(422))) as c:
        assert send(c, "http://api/invoiceitem", {}) is False


def test_read_items_respects_limit(tmp_path):
    f = tmp_path / "items.jsonl"
    f.write_text("\n".join(json.dumps({"i": i}) for i in range(10)))
    assert len(list(read_items(f, limit=3))) == 3


# ---------- Spark -> MongoDB document model ----------
def test_items_are_grouped_into_one_nested_document_per_invoice():
    rows = [row_to_item(ROW), row_to_item({**ROW, "StockCode": "71053"}), row_to_item({**ROW, "InvoiceNo": "C536379"})]
    updates = build_updates(rows)
    assert len(updates) == 2
    first = updates[0]._doc
    assert first["$set"]["CustomerID"] == "17850"
    assert [i["StockCode"] for i in first["$addToSet"]["items"]["$each"]] == ["85123A", "71053"]
    assert updates[1]._doc["$set"]["IsCancellation"] is True


def test_replayed_items_do_not_duplicate_inside_a_batch():
    updates = build_updates([row_to_item(ROW), row_to_item(ROW)])
    assert len(updates[0]._doc["$addToSet"]["items"]["$each"]) == 1
