"""Generate changes in the source database.

  python workload.py              # 1 insert, 2 updates, 1 delete (in separate transactions)
  python workload.py --outbox     # place an order + write its outbox event in ONE transaction
"""

import argparse
import json
import os

import psycopg

parser = argparse.ArgumentParser()
parser.add_argument("--outbox", action="store_true")
args = parser.parse_args()

with psycopg.connect(os.environ.get("PG_DSN", "postgresql://postgres:postgres@localhost:5432/shop"), autocommit=True) as conn:
    if args.outbox:
        with conn.transaction():
            order_id = conn.execute(
                "insert into orders (customer_id, status, amount) values (3, 'placed', 99.90) returning id"
            ).fetchone()[0]
            conn.execute(
                "insert into outbox (aggregatetype, aggregateid, type, payload) values ('order', %s, 'OrderPlaced', %s)",
                (str(order_id), json.dumps({"order_id": order_id, "customer_id": 3, "amount": "99.90"})),
            )
        print(f"order {order_id} placed and OrderPlaced event written atomically")
    else:
        new_id = conn.execute(
            "insert into customers (name, email) values ('New Customer', 'new@example.com') returning id"
        ).fetchone()[0]
        conn.execute("update customers set tier = 'premium', updated_at = now() where id = %s", (new_id,))
        conn.execute("update orders set status = 'shipped', updated_at = now() where id = 1")
        conn.execute("delete from orders where id = 2")
        print(f"inserted customer {new_id}, upgraded it to premium, shipped order 1, deleted order 2")
