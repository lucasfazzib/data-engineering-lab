"""Analytics over the silver Parquet files, in DuckDB SQL (views recreated on every connection).

    totals / candidates      every version of every scope
    latest_totals            the current state of each scope
    latest_candidates        current votes per scope and candidate
    projection               naive per-state projection of the final result (see below)
    national_timeline        how the national race evolved as sections were counted

Projection method (deliberately simple and explainable):
  each state's remaining votes are split like the votes already counted IN THAT STATE,
  i.e. projected_votes = votes / (% sections counted in the state).
  It corrects the classic "counting order" bias (states that report early are not a random sample),
  but not the bias inside a state (capital vs interior). Treat it as a scenario, not a forecast.
"""

from __future__ import annotations

from pathlib import Path

import duckdb

VIEWS = """
create or replace view totals as
    select * from read_parquet('{data}/silver/totals/*.parquet', union_by_name = true);
create or replace view candidates as
    select * from read_parquet('{data}/silver/candidates/*.parquet', union_by_name = true);

create or replace view latest_totals as
    select * from totals
    qualify row_number() over (partition by scope order by totals_at desc) = 1;

create or replace view latest_candidates as
    select c.* from candidates as c
    inner join latest_totals as t on c.scope = t.scope and c.totals_at = t.totals_at;

create or replace view state_race as
    select
        t.scope as uf,
        t.totals_at,
        t.pct_sections_counted,
        t.sections_total - t.sections_counted as sections_remaining,
        t.valid_votes,
        c.name,
        c.number,
        c.votes,
        c.pct_valid,
        c.votes / nullif(t.pct_sections_counted / 100, 0) as projected_votes
    from latest_totals as t
    inner join latest_candidates as c on t.scope = c.scope and t.totals_at = c.totals_at
    where t.scope <> 'br';

create or replace view projection as
    select
        name,
        number,
        sum(votes) as counted_votes,
        round(sum(projected_votes)) as projected_votes,
        round(100 * sum(projected_votes) / sum(sum(projected_votes)) over (), 2) as projected_pct_valid,
        count(*) filter (where pct_sections_counted > 0) as states_reporting
    from state_race
    group by name, number;

create or replace view national_timeline as
    select
        t.totals_at,
        t.pct_sections_counted,
        c.name,
        c.votes,
        c.pct_valid
    from totals as t
    inner join candidates as c on t.scope = c.scope and t.totals_at = c.totals_at
    where t.scope = 'br';
"""


def connect(data_dir: Path | str = "data") -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    con.execute("set TimeZone = 'America/Sao_Paulo'")
    con.execute(VIEWS.format(data=Path(data_dir).as_posix()))
    return con


def has_data(data_dir: Path | str = "data") -> bool:
    return any((Path(data_dir) / "silver" / "totals").glob("*.parquet"))
