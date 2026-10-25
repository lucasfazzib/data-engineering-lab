import os

BOOTSTRAP = os.environ.get("BOOTSTRAP_SERVERS", "localhost:29092")
ORDERS_TOPIC = "orders"
DLQ_TOPIC = "orders.dlq"
