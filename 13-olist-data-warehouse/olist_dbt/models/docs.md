{% docs __overview__ %}
# Olist e-commerce data warehouse

A Kimball-style star schema built with dbt on DuckDB from the
[Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
(~100k orders, 2016-09 → 2018-10).

**Layers**
- `staging` — one view per source table: rename, cast, clean. No joins.
- `intermediate` — reusable building blocks (dedup, aggregation to order grain, geo centroids).
- `core` — conformed dimensions and facts (`dim_*`, `fct_*`), with enforced contracts on the main ones.
- `analytics` — business-ready marts that answer specific questions (monthly sales, seller scorecard,
  delivery performance, cohorts).

Use the lineage graph (bottom-right button) to follow any column from source to dashboard.
{% enddocs %}

{% docs order_status %}
Lifecycle status of the order:

| status | meaning |
|---|---|
| created | order created, not yet approved |
| approved | payment approved |
| invoiced | invoice issued |
| processing | being prepared by the seller |
| shipped | handed to the carrier |
| delivered | received by the customer |
| canceled | canceled before delivery |
| unavailable | item(s) unavailable, order not fulfilled |
{% enddocs %}

{% docs customer_key %}
Surrogate key of the customer (hash of `customer_unique_id`). Olist generates a new `customer_id` for every
order, so the natural person is `customer_unique_id`.
{% enddocs %}
