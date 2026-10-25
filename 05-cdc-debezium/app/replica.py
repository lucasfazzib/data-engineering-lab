"""EXERCISE 2 — keep a DuckDB replica of `orders` in sync by applying the CDC stream.

Run with: make replica   (then compare with: make verify-replica)

This is what a CDC sink does (Debezium JDBC sink, a Spark/Flink job writing to Delta/Iceberg, Snowflake's
Kafka connector...). Requirements:
  - the replica table `orders` has the same columns as the source, with `id` as primary key
  - snapshot reads (op=r) and creates (op=c) insert, updates (op=u) upsert, deletes (op=d) delete
  - tombstones (value = None) are ignored
  - IDEMPOTENT: replaying the whole topic twice must give the same final state
  - commit Kafka offsets only after the change is applied
"""

import json
import os

import duckdb
from confluent_kafka import Consumer

TOPIC = "shop.public.orders"
REPLICA = os.environ.get("REPLICA_PATH", "/lab/replica.duckdb")

db = duckdb.connect(REPLICA)
db.execute("""
    create table if not exists orders (
        id integer primary key, customer_id integer, status varchar, amount decimal(10, 2),
        updated_at varchar  -- Debezium sends timestamptz as an ISO-8601 string (ZonedTimestamp)
    )
""")

consumer = Consumer({
    "bootstrap.servers": os.environ.get("BOOTSTRAP_SERVERS", "localhost:29092"),
    "group.id": "duckdb-replica",
    "auto.offset.reset": "earliest",
    "enable.auto.commit": False,
})
consumer.subscribe([TOPIC])


def apply(event: dict) -> None:
    # TODO: implement the upsert/delete logic described in the module docstring.
    #   Hints: event["op"], event["before"], event["after"]; DuckDB supports
    #   INSERT ... ON CONFLICT (id) DO UPDATE SET ...  (or INSERT OR REPLACE)
    raise NotImplementedError("exercise 2")


idle = 0
applied = 0
while idle < 6:
    msg = consumer.poll(1.0)
    if msg is None:
        idle += 1
        continue
    idle = 0
    if msg.error() or msg.value() is None:
        continue
    apply(json.loads(msg.value()))
    applied += 1
    consumer.commit(message=msg, asynchronous=False)

consumer.close()
print(f"applied {applied} events; replica has {db.execute('select count(*) from orders').fetchone()[0]} orders")
