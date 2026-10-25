"""Consumer-group member with manual commits (at-least-once).

  python consumer.py --group g1 --name c1                  # run until idle
  python consumer.py --group g1 --name c1 --forever        # keep running (open several to see rebalances)
  python consumer.py --group g1 --crash-after 150          # die mid-batch to see redelivery
"""

import argparse
import json
import os
import sys
from collections import Counter

from confluent_kafka import Consumer, KafkaError

from common import BOOTSTRAP, ORDERS_TOPIC

parser = argparse.ArgumentParser()
parser.add_argument("--group", default="g1")
parser.add_argument("--name", default="c1")
parser.add_argument("--forever", action="store_true")
parser.add_argument("--idle-seconds", type=float, default=5)
parser.add_argument("--crash-after", type=int, default=0)
parser.add_argument("--commit-every", type=int, default=100)
args = parser.parse_args()

consumer = Consumer({
    "bootstrap.servers": BOOTSTRAP,
    "group.id": args.group,
    "client.id": args.name,
    "auto.offset.reset": "earliest",   # only used when the group has no committed offset yet
    "enable.auto.commit": False,       # we commit explicitly AFTER processing => at-least-once
    "partition.assignment.strategy": "cooperative-sticky",  # incremental rebalances
    # A member that dies without leaving keeps its partitions until this expires (default 45s).
    "session.timeout.ms": 10000,
})


def on_assign(c, partitions):
    print(f"[{args.name}] assigned: {[p.partition for p in partitions]}")


def on_revoke(c, partitions):
    print(f"[{args.name}] revoked: {[p.partition for p in partitions]}")


consumer.subscribe([ORDERS_TOPIC], on_assign=on_assign, on_revoke=on_revoke)

processed = 0
uncommitted = 0
last_seq: dict[tuple[str, int], int] = {}
out_of_order = 0
per_partition: Counter = Counter()
idle = 0.0


def process(event: dict) -> None:
    """Business logic. TODO (exercise 4): write to an idempotent sink keyed by event_id."""
    global out_of_order
    key, seq = (event["run_id"], event["customer_id"]), event["seq"]
    if seq < last_seq.get(key, 0):
        out_of_order += 1
    last_seq[key] = seq


def handle_poison(msg, error: Exception) -> None:
    """TODO (exercise 5): send the raw message + error to the DLQ topic instead of crashing."""
    raise error


try:
    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            idle += 1
            if not args.forever and idle >= args.idle_seconds:
                break
            continue
        idle = 0
        if msg.error():
            if msg.error().code() != KafkaError._PARTITION_EOF:
                print("error:", msg.error())
            continue

        try:
            process(json.loads(msg.value()))
        except json.JSONDecodeError as exc:
            handle_poison(msg, exc)

        processed += 1
        uncommitted += 1
        per_partition[msg.partition()] += 1

        if args.crash_after and processed == args.crash_after:
            print(f"[{args.name}] simulated crash after {processed} messages ({uncommitted} processed but not committed)")
            os._exit(1)  # no commit, no clean leave: like a killed pod

        if uncommitted >= args.commit_every:
            consumer.commit(asynchronous=False)
            uncommitted = 0
finally:
    if uncommitted:
        consumer.commit(asynchronous=False)
    consumer.close()  # clean leave => immediate rebalance for the rest of the group

print(f"[{args.name}] processed={processed} out_of_order={out_of_order} per_partition={dict(sorted(per_partition.items()))}")
sys.exit(0)
