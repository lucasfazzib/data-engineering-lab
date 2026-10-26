"""Step 5 - Streamlit UI: pick a customer -> their invoices -> the items of an invoice.

Queries MongoDB with a read-only user. Refreshes every 10 s so new invoices appear while streaming.
"""

from __future__ import annotations

import os

import pandas as pd
import streamlit as st
from pymongo import MongoClient

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://dashboard:dashboard@localhost:27017/invoices?authSource=invoices")

st.set_page_config(page_title="Invoices", page_icon="🧾", layout="wide")
st.title("🧾 Customer invoices (live)")
st.caption("Kaggle Online Retail data · API -> Kafka -> Spark Structured Streaming -> MongoDB")


@st.cache_resource
def collection():
    return MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000).get_default_database()["invoices"]


# Aggregation building blocks: quantity x unit price, per item and per invoice
ITEM_TOTAL = {"$multiply": ["$items.Quantity", "$items.UnitPrice"]}
INVOICE_TOTAL = {"$sum": {"$map": {"input": "$items", "in": {"$multiply": ["$$this.Quantity", "$$this.UnitPrice"]}}}}

OVERVIEW = [
    {"$unwind": "$items"},
    {
        "$group": {
            "_id": None,
            "invoices": {"$addToSet": "$_id"},
            "customers": {"$addToSet": "$CustomerID"},
            "items": {"$sum": 1},
            "revenue": {"$sum": ITEM_TOTAL},
        }
    },
    {"$project": {"invoices": {"$size": "$invoices"}, "customers": {"$size": "$customers"}, "items": 1, "revenue": 1}},
]


@st.fragment(run_every=10)
def overview() -> None:
    stats = next(collection().aggregate(OVERVIEW), None)
    if not stats:
        st.info("No invoices yet: run `make send` to stream the sample.")
        return
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Invoices", f"{stats['invoices']:,}")
    c2.metric("Customers", f"{stats['customers']:,}")
    c3.metric("Items", f"{stats['items']:,}")
    c4.metric("Revenue", f"£{stats['revenue']:,.2f}")


try:
    collection().database.client.admin.command("ping")
except Exception as exc:
    st.error(f"MongoDB not reachable: {exc}")
    st.stop()

overview()

customers = sorted(c for c in collection().distinct("CustomerID") if c)
if not customers:
    st.stop()

left, right = st.columns([1, 3])
with left:
    customer = st.selectbox("Customer", customers, help="Guest checkouts (no CustomerID) are not listed")

invoices = list(
    collection().aggregate(
        [
            {"$match": {"CustomerID": customer}},
            {
                "$project": {
                    "_id": 0,
                    "InvoiceNo": 1,
                    "InvoiceDate": 1,
                    "Country": 1,
                    "IsCancellation": 1,
                    "items": {"$size": "$items"},
                    "total": {"$round": [INVOICE_TOTAL, 2]},
                }
            },
            {"$sort": {"InvoiceDate": -1}},
        ]
    )
)

with right:
    st.subheader(f"Invoices of customer {customer}")
    inv_df = pd.DataFrame(invoices)
    st.dataframe(inv_df, hide_index=True, width="stretch")

if invoices:
    invoice = st.selectbox("Invoice", [i["InvoiceNo"] for i in invoices])
    doc = collection().find_one({"_id": invoice})
    st.subheader(f"Items on invoice {invoice}")
    items = pd.DataFrame(doc["items"])
    items["LineTotal"] = (items["Quantity"] * items["UnitPrice"]).round(2)
    st.dataframe(items, hide_index=True, width="stretch")
    st.metric("Invoice total", f"£{items['LineTotal'].sum():,.2f}")
