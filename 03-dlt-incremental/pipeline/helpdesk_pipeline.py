"""Incremental ingestion of the mock helpdesk API into DuckDB with dlt.

dlt is a Python library (not a service): you describe WHAT to extract, dlt handles pagination, retries,
schema inference/evolution, normalization of nested data, incremental state and loading.
"""

import os

import dlt
from dlt.sources.rest_api import rest_api_source

API_URL = os.environ.get("API_URL", "http://api:8000/api/v1/")


def helpdesk_source():
    return rest_api_source(
        {
            "client": {
                "base_url": API_URL,
                # Secrets never go in code: dlt resolves this from the env var SOURCES__HELPDESK__API_TOKEN
                # (or .dlt/secrets.toml, which is git-ignored).
                "auth": {"type": "bearer", "token": dlt.secrets["sources.helpdesk.api_token"]},
            },
            "resource_defaults": {
                "primary_key": "id",
                "endpoint": {"data_selector": "data"},
            },
            "resources": [
                {
                    # small dimension: reload it fully every run
                    "name": "customers",
                    "write_disposition": "replace",
                    "endpoint": {
                        "path": "customers",
                        "params": {"page_size": 50},
                        "paginator": {"type": "page_number", "base_page": 1, "page_param": "page", "total_path": "total_pages"},
                    },
                },
                {
                    # large, mutable fact: only fetch what changed since the last run and MERGE by primary key
                    "name": "tickets",
                    "write_disposition": "merge",
                    "endpoint": {
                        "path": "tickets",
                        "params": {
                            "updated_since": {
                                "type": "incremental",
                                "cursor_path": "updated_at",
                                "initial_value": "2026-01-01T00:00:00Z",
                            },
                        },
                        "paginator": {"type": "cursor", "cursor_path": "next_cursor", "cursor_param": "cursor"},
                    },
                },
                # TODO (exercise 1): add a `ticket_comments` child resource that calls
                #   tickets/{ticket_id}/comments for every ticket yielded by `tickets`.
                #   Hint: "path": "tickets/{resources.tickets.id}/comments" and include the parent id.
            ],
        },
        name="helpdesk",
    )


def main() -> None:
    pipeline = dlt.pipeline(
        pipeline_name="helpdesk",
        destination=dlt.destinations.duckdb(os.environ.get("DUCKDB_PATH", "/lab/warehouse/helpdesk.duckdb")),
        dataset_name="helpdesk_raw",
        pipelines_dir=os.environ.get("DLT_PIPELINES_DIR", "/lab/.dlt/pipelines"),
    )
    load_info = pipeline.run(helpdesk_source())
    print(load_info)

    # Row counts of what THIS run extracted/normalized (not the table totals)
    print("rows this run:", pipeline.last_trace.last_normalize_info.row_counts)


if __name__ == "__main__":
    main()
