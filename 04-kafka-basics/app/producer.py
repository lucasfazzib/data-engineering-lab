"""Produce order events keyed by customer_id.

  python producer.py --count 1000            # keyed, idempotent producer
  python producer.py --count 100 --no-key    # no key: see how partitions are chosen
  python producer.py --poison 3              # also send 3 malformed messages (for the DLQ exercise)
"""

import argparse
import json
import random
import time
import uuid
from collections import Counter

from confluent_kafka import Producer

from common import BOOTSTRAP, ORDERS_TOPIC

parser = argparse.ArgumentParser()
parser.add_argument("--count", type=int, default=1000)
parser.add_argument("--customers", type=int, default=50)
parser.add_argument("--no-key", action="store_true")
parser.add_argument("--poison", type=int, default=0)
args = parser.parse_args()

producer = Producer({
    "bootstrap.servers": BOOTSTRAP,
    # Idempotent producer: broker dedups retries using (producer id, sequence number) => no duplicates,
    # ordering preserved per partition. Implies acks=all and max.in.flight <= 5.
    "enable.idempotence": True,
    "acks": "all",
    "linger.ms": 20,          # wait a bit to build bigger batches (throughput vs latency)
    "compression.type": "lz4",
})

per_partition: Counter = Counter()
failures = 0


def on_delivery(err, msg) -> None:
    global failures
    if err:
        failures += 1
        print("delivery failed:", err)
    else:
        per_partition[msg.partition()] += 1


run_id = uuid.uuid4().hex[:8]
seq_per_customer: Counter = Counter()
for _ in range(args.count):
    customer_id = random.randint(1, args.customers)
    seq_per_customer[customer_id] += 1
    event = {
        "event_id": str(uuid.uuid4()),
        "customer_id": customer_id,
        "run_id": run_id,
        "seq": seq_per_customer[customer_id],  # per-customer sequence within this run: lets the consumer check ordering
        "amount": round(random.uniform(5, 500), 2),
        "ts": time.time(),
    }
    key = None if args.no_key else str(customer_id)
    producer.produce(ORDERS_TOPIC, key=key, value=json.dumps(event), on_delivery=on_delivery)
    producer.poll(0)  # serve delivery callbacks

for i in range(args.poison):
    producer.produce(ORDERS_TOPIC, key="poison", value=b"{not json" + str(i).encode(), on_delivery=on_delivery)

producer.flush(30)
print(f"produced {sum(per_partition.values())} messages, failures={failures}")
print("messages per partition:", dict(sorted(per_partition.items())))
