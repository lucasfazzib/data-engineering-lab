"""Olist sales & operations dashboard — reads only the analytics/core marts (never staging or raw)."""

import os

import altair as alt
import duckdb
import pandas as pd
import streamlit as st

DB_PATH = os.environ.get("DUCKDB_PATH", "warehouse/olist.duckdb")

st.set_page_config(page_title="Olist DWH", layout="wide")


@st.cache_data(ttl=600)
def query(sql: str) -> pd.DataFrame:
    # read_only: the dashboard must never lock or modify the warehouse
    with duckdb.connect(DB_PATH, read_only=True) as con:
        return con.execute(sql).df()


monthly = query("select * from analytics.mart_monthly_sales where in_analysis_window order by month")
delivery = query("select * from analytics.mart_delivery_performance order by delivered_orders desc")
cohorts = query("""
    select cohort_month, months_since_first_order, retention_rate
    from analytics.mart_customer_cohorts
    where cohort_month between '2017-01-01' and '2018-06-01' and months_since_first_order between 1 and 12
""")
categories = query("""
    select p.category_name_en as category, sum(i.price) as gmv
    from core.fct_order_items i
    join core.dim_products p using (product_key)
    where i.is_sale
    group by 1 order by 2 desc limit 15
""")
sellers = query("select pareto_segment, count(*) as sellers, sum(gmv) as gmv from analytics.mart_seller_scorecard group by 1")

st.title("Olist e-commerce — sales & operations")
st.caption("Brazilian E-Commerce Public Dataset by Olist (Kaggle, CC BY-NC-SA 4.0) · analysis window Jan/2017 to Aug/2018")

kpi = st.columns(5)
kpi[0].metric("GMV (BRL)", f"{monthly.gmv.sum() / 1e6:,.2f} M")
kpi[1].metric("Orders", f"{monthly.orders.sum():,}")
kpi[2].metric("Avg order value", f"R$ {monthly.gmv.sum() / monthly.orders.sum():,.2f}")
kpi[3].metric("Avg review", f"{(monthly.avg_review_score * monthly.orders).sum() / monthly.orders.sum():.2f} / 5")
kpi[4].metric("Late deliveries", f"{(monthly.late_delivery_rate * monthly.orders).sum() / monthly.orders.sum():.1%}")

left, right = st.columns(2)
with left:
    st.subheader("Monthly GMV")
    st.bar_chart(monthly, x="month", y="gmv", height=300)
with right:
    st.subheader("Late-delivery rate vs review score")
    base = alt.Chart(monthly).encode(x=alt.X("month:T", title=None))
    late = base.mark_line(color="#d62728").encode(y=alt.Y("late_delivery_rate:Q", axis=alt.Axis(format="%"), title="late rate"))
    review = base.mark_line(color="#1f77b4").encode(
        y=alt.Y("avg_review_score:Q", scale=alt.Scale(zero=False), title="avg review")
    )
    st.altair_chart(alt.layer(late, review).resolve_scale(y="independent").properties(height=300), width="stretch")

left, right = st.columns(2)
with left:
    st.subheader("Delivery time by state")
    st.bar_chart(delivery.sort_values("avg_delivery_days"), x="state_code", y="avg_delivery_days", height=320)
    st.caption("Late orders average a much lower review than on-time ones — see the table below.")
    st.dataframe(
        delivery[
            ["state_code", "delivered_orders", "avg_delivery_days", "late_delivery_rate", "avg_review_on_time", "avg_review_late"]
        ],
        hide_index=True,
        width="stretch",
    )
with right:
    st.subheader("Top categories by GMV")
    st.bar_chart(categories, x="category", y="gmv", horizontal=True, height=320)
    st.subheader("Seller concentration")
    st.dataframe(sellers, hide_index=True, width="stretch")

st.subheader("Repeat-purchase retention by acquisition cohort")
heat = (
    alt.Chart(cohorts)
    .mark_rect()
    .encode(
        x=alt.X("months_since_first_order:O", title="months since first order"),
        y=alt.Y("yearmonth(cohort_month):O", title="cohort"),
        color=alt.Color("retention_rate:Q", scale=alt.Scale(scheme="blues"), legend=alt.Legend(format="%")),
        tooltip=["cohort_month:T", "months_since_first_order:O", alt.Tooltip("retention_rate:Q", format=".2%")],
    )
    .properties(height=420)
)
st.altair_chart(heat, width="stretch")
st.caption("Retention below 1% after month 1: Olist acquires customers, it barely retains them.")
