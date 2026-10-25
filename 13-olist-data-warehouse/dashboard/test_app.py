"""Smoke test: the dashboard renders against the built warehouse without exceptions.

Run with: make test-dashboard
"""

from streamlit.testing.v1 import AppTest


def test_dashboard_renders() -> None:
    app = AppTest.from_file("app.py", default_timeout=60).run()
    assert not app.exception, app.exception
    assert len(app.metric) == 5
    assert app.title[0].value.startswith("Olist")


if __name__ == "__main__":
    test_dashboard_renders()
    print("dashboard OK")
