"""Step 2 - api-ingest: receives invoice items over HTTP and writes them to Kafka.

    POST /invoiceitem   -> 201, the item is in the topic (validated, keyed by InvoiceNo)
    GET  /health        -> liveness for Docker/Postman

Why an API in front of Kafka: producers (shops, apps, partners) speak HTTP, not the Kafka protocol;
the API validates the contract once, so the stream only ever carries well-formed messages.
"""

from __future__ import annotations

import json
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Annotated, Protocol

from fastapi import Depends, FastAPI, HTTPException, Request, status
from pydantic import BaseModel, Field

TOPIC = os.environ.get("INGEST_TOPIC", "ingestion-topic")


class InvoiceItem(BaseModel):
    """One line of an invoice. Same field names as the source CSV."""

    InvoiceNo: str = Field(min_length=1, max_length=20, examples=["536365"])
    StockCode: str = Field(min_length=1, max_length=20, examples=["85123A"])
    Description: str | None = Field(default=None, max_length=200, examples=["WHITE HANGING HEART T-LIGHT HOLDER"])
    Quantity: int = Field(examples=[6])  # negative on cancellations (InvoiceNo starting with 'C')
    InvoiceDate: datetime = Field(examples=["2010-12-01T08:26:00"])
    UnitPrice: float = Field(ge=0, examples=[2.55])
    CustomerID: str | None = Field(default=None, max_length=20, examples=["17850"])
    Country: str = Field(min_length=1, max_length=60, examples=["United Kingdom"])


class Producer(Protocol):
    def produce(self, topic: str, key: bytes, value: bytes) -> None: ...

    def flush(self, timeout: float) -> int: ...


def kafka_producer() -> Producer:
    from confluent_kafka import Producer as KafkaProducer

    return KafkaProducer(
        {
            "bootstrap.servers": os.environ.get("KAFKA_BOOTSTRAP", "localhost:29092"),
            "enable.idempotence": True,  # broker de-duplicates producer retries
            "acks": "all",
            "linger.ms": 5,
            "compression.type": "lz4",
        }
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    if getattr(app.state, "producer", None) is None:  # tests inject a fake producer before startup
        app.state.producer = kafka_producer()
    yield
    app.state.producer.flush(10)


app = FastAPI(title="api-ingest", version="1.0.0", lifespan=lifespan)


def get_producer(request: Request) -> Producer:
    return request.app.state.producer


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/invoiceitem", status_code=status.HTTP_201_CREATED)
def post_invoice_item(item: InvoiceItem, producer: Annotated[Producer, Depends(get_producer)]) -> dict:
    payload = item.model_dump(mode="json")
    try:
        # key = InvoiceNo: all items of an invoice go to the same partition, in order
        producer.produce(TOPIC, key=item.InvoiceNo.encode(), value=json.dumps(payload).encode())
    except BufferError as exc:  # local queue full: tell the client to retry instead of losing data
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "ingestion queue full, retry") from exc
    return {"status": "accepted", "topic": TOPIC, "item": payload}
