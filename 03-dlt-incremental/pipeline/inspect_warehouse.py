"""Print what landed in DuckDB: tables, row counts and the incremental state."""

import json
import os

import dlt
import duckdb

con = duckdb.connect(os.environ.get("DUCKDB_PATH", "/lab/warehouse/helpdesk.duckdb"), read_only=True)

print("== tables in helpdesk_raw (note the child table for the nested `tags` list and the _dlt_* tables)")
for (table,) in con.execute(
    "select table_name from information_schema.tables where table_schema = 'helpdesk_raw' order by 1"
).fetchall():
    n = con.execute(f'select count(*) from helpdesk_raw."{table}"').fetchone()[0]
    print(f"  {table:<28} {n:>6} rows")

print("\n== tickets: total vs distinct ids (merge => equal), soft-deleted, latest updated_at")
print(con.execute("""
    select count(*) as rows, count(distinct id) as distinct_ids,
           count(*) filter (where deleted) as soft_deleted, max(updated_at) as max_updated_at
    from helpdesk_raw.tickets
""").fetchone())

print("\n== load history (_dlt_loads)")
for row in con.execute("select load_id, status, inserted_at from helpdesk_raw._dlt_loads order by inserted_at").fetchall():
    print("  ", row)

con.close()

print("\n== incremental cursor in the pipeline state (also persisted in _dlt_pipeline_state at the destination)")
pipeline = dlt.attach("helpdesk", pipelines_dir=os.environ.get("DLT_PIPELINES_DIR", "/lab/.dlt/pipelines"))
resources = pipeline.state.get("sources", {}).get("helpdesk", {}).get("resources", {})
incremental = resources.get("tickets", {}).get("incremental", {})
print(json.dumps({param: value.get("last_value") for param, value in incremental.items()}, indent=2))
