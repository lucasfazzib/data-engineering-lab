"""Topic and consumer-group administration with the AdminClient.

  python admin.py create              # create the lab topics (idempotent)
  python admin.py describe            # partitions, leaders, configs
  python admin.py lag <group>         # committed offset vs log end offset per partition
"""

import sys

from confluent_kafka import Consumer, TopicPartition
from confluent_kafka.admin import AdminClient, ConfigResource, NewTopic

from common import BOOTSTRAP, DLQ_TOPIC, ORDERS_TOPIC

admin = AdminClient({"bootstrap.servers": BOOTSTRAP})

TOPICS = [
    NewTopic(ORDERS_TOPIC, num_partitions=6, replication_factor=1, config={"retention.ms": str(7 * 24 * 3600 * 1000)}),
    NewTopic(DLQ_TOPIC, num_partitions=1, replication_factor=1),
    # compacted topic: keeps only the latest value per key (exercise 7)
    NewTopic("customers.latest", num_partitions=3, replication_factor=1,
             config={"cleanup.policy": "compact", "segment.ms": "10000", "min.cleanable.dirty.ratio": "0.01"}),
]


def create() -> None:
    existing = admin.list_topics(timeout=10).topics
    todo = [t for t in TOPICS if t.topic not in existing]
    for topic, future in (admin.create_topics(todo).items() if todo else []):
        future.result()
        print(f"created {topic}")
    print("topics:", sorted(t for t in admin.list_topics(timeout=10).topics if not t.startswith("__")))


def describe() -> None:
    md = admin.list_topics(timeout=10)
    for name in sorted(t for t in md.topics if not t.startswith("__")):
        parts = md.topics[name].partitions
        print(f"{name}: {len(parts)} partitions, leaders={sorted({p.leader for p in parts.values()})}")
    res = ConfigResource(ConfigResource.Type.TOPIC, ORDERS_TOPIC)
    configs = admin.describe_configs([res])[res].result()
    for key in ("cleanup.policy", "retention.ms", "min.insync.replicas"):
        print(f"  {ORDERS_TOPIC}.{key} = {configs[key].value}")


def lag(group: str) -> None:
    consumer = Consumer({"bootstrap.servers": BOOTSTRAP, "group.id": group, "enable.auto.commit": False})
    partitions = [TopicPartition(ORDERS_TOPIC, p) for p in admin.list_topics(ORDERS_TOPIC).topics[ORDERS_TOPIC].partitions]
    committed = consumer.committed(partitions, timeout=10)
    total = 0
    print(f"group={group} topic={ORDERS_TOPIC}")
    for tp in committed:
        _, high = consumer.get_watermark_offsets(tp, timeout=10)
        offset = tp.offset if tp.offset >= 0 else 0
        total += high - offset
        print(f"  partition {tp.partition}: committed={tp.offset:>6}  end={high:>6}  lag={high - offset}")
    print(f"  TOTAL LAG = {total}")
    consumer.close()


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "describe"
    {"create": create, "describe": describe}.get(cmd, lambda: lag(sys.argv[2]))()
