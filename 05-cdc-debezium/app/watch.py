"""Pretty-print Debezium change events.

  python watch.py                        # all shop.public.* topics from the beginning, until idle
  python watch.py --topics outbox.event.order --raw
"""

import argparse
import json
import os
import uuid
from collections import Counter

from confluent_kafka import Consumer

OPS = {"r": "READ (snapshot)", "c": "CREATE", "u": "UPDATE", "d": "DELETE"}

parser = argparse.ArgumentParser()
parser.add_argument("--topics", default="^shop\\.public\\..*")
parser.add_argument("--idle-seconds", type=float, default=6)
parser.add_argument("--quiet-snapshot", action="store_true", help="count snapshot reads instead of printing them")
parser.add_argument("--raw", action="store_true")
args = parser.parse_args()

consumer = Consumer({
    "bootstrap.servers": os.environ.get("BOOTSTRAP_SERVERS", "localhost:29092"),
    "group.id": f"watch-{uuid.uuid4().hex[:6]}",  # fresh group => always from the beginning
    "auto.offset.reset": "earliest",
    "enable.auto.commit": False,
})
consumer.subscribe(args.topics.split(","))

counts: Counter = Counter()
idle = 0
while idle < args.idle_seconds:
    msg = consumer.poll(1.0)
    if msg is None:
        idle += 1
        continue
    idle = 0
    if msg.error():
        continue
    key = msg.key().decode() if msg.key() else None
    if msg.value() is None:
        counts["tombstone"] += 1
        print(f"{msg.topic()}  key={key}  TOMBSTONE (value=null -> lets log compaction drop the key)")
        continue
    event = json.loads(msg.value())
    if args.raw:
        print(msg.topic(), key, json.dumps(event, indent=2))
        continue
    op = event.get("op")
    counts[op] += 1
    if op == "r" and args.quiet_snapshot:
        continue
    before, after = event.get("before"), event.get("after")
    if op == "u" and before and after:
        change = {k: f"{before.get(k)} -> {after[k]}" for k in after if before.get(k) != after[k]}
    else:
        change = after or before
    src = event.get("source", {})
    print(f"{msg.topic():<22} {OPS.get(op, op):<16} key={key:<12} lsn={src.get('lsn')} {change}")

consumer.close()
print("\nevent counts:", {OPS.get(k, k): v for k, v in counts.items()})
