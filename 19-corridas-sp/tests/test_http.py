import httpx

from corridas.http import DisallowedByRobots, PoliteClient

ROBOTS = "User-agent: *\nDisallow: /private/\n"


def make_client(tmp_path, handler, **kw):
    return PoliteClient("test-agent/1.0", tmp_path, min_interval_seconds=0, transport=httpx.MockTransport(handler), **kw)


def test_robots_txt_is_enforced(tmp_path):
    calls = []

    def handler(request):
        calls.append(request.url.path)
        return httpx.Response(200, text=ROBOTS if request.url.path == "/robots.txt" else "ok")

    client = make_client(tmp_path, handler)
    assert client.get("https://example.org/public/page").text == "ok"
    try:
        client.get("https://example.org/private/page")
        raise AssertionError("should have refused")
    except DisallowedByRobots:
        pass
    assert "/private/page" not in calls


def test_missing_robots_means_allowed_and_server_error_means_disallowed(tmp_path, monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)  # the 503 is retried with backoff
    client = make_client(tmp_path, lambda r: httpx.Response(404 if r.url.path == "/robots.txt" else 200, text="ok"))
    assert client.allowed("https://a.example/x")
    client = make_client(tmp_path / "b", lambda r: httpx.Response(503))
    assert not client.allowed("https://b.example/x")


def test_responses_are_cached(tmp_path):
    hits = {"n": 0}

    def handler(request):
        if request.url.path != "/robots.txt":
            hits["n"] += 1
        return httpx.Response(200, text="page")

    client = make_client(tmp_path, handler)
    client.get("https://example.org/a")
    client.get("https://example.org/a")
    assert hits["n"] == 1


def test_429_is_retried_with_backoff(tmp_path, monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)
    answers = iter([httpx.Response(429, headers={"Retry-After": "1"}), httpx.Response(200, text="finally")])

    def handler(request):
        return httpx.Response(404) if request.url.path == "/robots.txt" else next(answers)

    assert make_client(tmp_path, handler).get("https://example.org/a").text == "finally"


def test_user_agent_is_sent(tmp_path):
    seen = {}

    def handler(request):
        seen["ua"] = request.headers["User-Agent"]
        return httpx.Response(404)

    make_client(tmp_path, handler).allowed("https://example.org/a")
    assert seen["ua"] == "test-agent/1.0"
