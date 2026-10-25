"""Smoke test: the dashboard renders against the data produced by the poller (fixture feed)."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

from election.poller import store
from tests.fixtures import feed_json

APP = Path(__file__).resolve().parents[1] / "dashboard" / "app.py"


def test_dashboard_renders(tmp_path, monkeypatch):
    for uf, pct, lula, flavio in [("br", 50.0, 600, 400), ("sp", 40.0, 200, 300), ("ba", 60.0, 400, 100)]:
        store(feed_json(uf, "20:00:00", pct, lula, flavio), tmp_path)
    monkeypatch.setenv("ELECTION_DATA", str(tmp_path))
    at = AppTest.from_file(str(APP), default_timeout=30).run()
    assert not at.exception, at.exception
    assert any("50.00% das seções apuradas" in m.value for m in at.markdown)
    assert at.metric[0].label == "LULA"


def test_dashboard_without_data(tmp_path, monkeypatch):
    monkeypatch.setenv("ELECTION_DATA", str(tmp_path))
    at = AppTest.from_file(str(APP), default_timeout=30).run()
    assert not at.exception
    assert "Ainda sem dados" in at.info[0].value
