import gzip

import pytest

from election.feed import parse
from election.metrics import connect, has_data
from election.poller import backfill, store
from tests.fixtures import feed_json


def test_parse_handles_brazilian_number_format():
    snap = parse(feed_json("br", "20:49:10", 75.865101112, 51_000_000, 48_000_000))
    assert snap.scope == "br"
    assert snap.totals["pct_sections_counted"] == pytest.approx(75.865101112)
    assert snap.totals_at.hour == 20 and str(snap.totals_at.tzinfo) == "America/Sao_Paulo"
    lula = next(c for c in snap.candidates if c["number"] == 13)
    assert lula["votes"] == 51_000_000 and lula["pct_valid"] == pytest.approx(51.515151515, rel=1e-6)


def test_store_is_idempotent_per_version(tmp_path):
    raw = feed_json("sp", "20:00:00", 50, 100, 200)
    assert store(raw, tmp_path) is True
    assert store(raw, tmp_path) is False  # same scope + same TSE time = same version
    assert store(feed_json("sp", "20:02:00", 55, 110, 220), tmp_path) is True
    assert len(list((tmp_path / "silver" / "totals").glob("*.parquet"))) == 2
    assert len(list((tmp_path / "bronze" / "sp").glob("*.json.gz"))) == 2


def test_backfill_reads_raw_captures(tmp_path):
    raw_dir = tmp_path / "captures"
    raw_dir.mkdir()
    for i, t in enumerate(["20:00:00", "20:05:00", "20:05:00"]):  # last one is a duplicate
        (raw_dir / f"br_{i}.json.gz").write_bytes(gzip.compress(feed_json("br", t, 50 + i, 10, 9)))
    assert backfill(raw_dir, tmp_path / "data") == 2


@pytest.fixture
def lake(tmp_path):
    # national file + two states counted at different speeds, with opposite leaders
    store(feed_json("br", "20:00:00", 50.0, 600, 400), tmp_path)
    store(feed_json("br", "20:10:00", 75.0, 800, 700), tmp_path)
    store(feed_json("sp", "20:10:00", 40.0, 200, 300), tmp_path)  # 40% counted, Flavio leads
    store(feed_json("ba", "20:10:00", 80.0, 400, 100), tmp_path)  # 80% counted, Lula leads
    return connect(tmp_path)


def test_latest_totals_pick_the_newest_version(lake):
    pct = lake.execute("select pct_sections_counted from latest_totals where scope = 'br'").fetchone()[0]
    assert pct == 75.0


def test_timeline_keeps_every_version(lake):
    assert lake.execute("select count(distinct totals_at) from national_timeline").fetchone()[0] == 2


def test_projection_extrapolates_each_state_by_its_own_progress(lake):
    rows = dict(lake.execute("select name, projected_votes from projection").fetchall())
    # SP: 200/0.4 = 500 Lula, 300/0.4 = 750 Flavio; BA: 400/0.8 = 500 Lula, 100/0.8 = 125 Flavio
    assert rows["LULA"] == 1000
    assert rows["FLAVIO BOLSONARO"] == 875


def test_has_data(tmp_path):
    assert not has_data(tmp_path)
    store(feed_json("br", "20:00:00", 1, 1, 1), tmp_path)
    assert has_data(tmp_path)
