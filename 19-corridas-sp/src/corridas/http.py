"""A polite HTTP client: the only way the project talks to the internet.

- checks robots.txt before every URL (and refuses if disallowed)
- identifies itself with a descriptive User-Agent
- waits a minimum interval between requests to the same host
- caches responses on disk (TTL ~1 day): reruns the same day hit no server at all
- retries 429/5xx with exponential backoff, honoring Retry-After
- never logs in, never solves captchas, never rotates IPs or user agents
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

import httpx


class DisallowedByRobots(Exception):
    pass


@dataclass
class Response:
    url: str
    status: int
    text: str
    from_cache: bool


class PoliteClient:
    def __init__(
        self,
        user_agent: str,
        cache_dir: Path,
        *,
        cache_ttl_hours: float = 20,
        min_interval_seconds: float = 2,
        max_retries: int = 4,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.user_agent = user_agent
        self.cache_dir = cache_dir
        self.cache_ttl = cache_ttl_hours * 3600
        self.min_interval = min_interval_seconds
        self.max_retries = max_retries
        self._last_request: dict[str, float] = {}
        self._robots: dict[str, RobotFileParser] = {}
        self._http = httpx.Client(headers={"User-Agent": user_agent}, timeout=30, follow_redirects=True, transport=transport)

    # ---- robots.txt ----
    def allowed(self, url: str) -> bool:
        parts = urlsplit(url)
        origin = f"{parts.scheme}://{parts.netloc}"
        if origin not in self._robots:
            rp = RobotFileParser()
            r = self._request(f"{origin}/robots.txt", check_robots=False)
            # RFC 9309: 4xx = no rules (allowed); 5xx/unreachable = assume disallowed
            if r.status >= 500:
                rp.disallow_all = True
            elif r.status < 400:
                rp.parse(r.text.splitlines())
            else:
                rp.allow_all = True
            self._robots[origin] = rp
        return self._robots[origin].can_fetch(self.user_agent, url)

    # ---- fetching ----
    def get(self, url: str) -> Response:
        """Fetch a web PAGE: robots.txt is enforced."""
        return self._request(url, check_robots=True)

    def get_api(self, url: str) -> Response:
        """Call a documented public API built for programmatic use (e.g. IBGE).

        robots.txt governs crawlers of web pages; APIs are governed by their own terms of use,
        which are reviewed per API in docs/fontes.md. Rate limit, cache and backoff still apply.
        """
        return self._request(url, check_robots=False)

    def resolve_redirect(self, url: str) -> str | None:
        """Return the Location of a redirect WITHOUT following it (robots.txt and rate limit apply)."""
        if not self.allowed(url):
            raise DisallowedByRobots(url)
        self._wait_turn(url)
        r = self._http.get(url, follow_redirects=False)
        return r.headers.get("Location") if r.is_redirect else None

    def _cache_path(self, url: str) -> Path:
        return self.cache_dir / f"{hashlib.sha256(url.encode()).hexdigest()}.json"

    def _request(self, url: str, check_robots: bool) -> Response:
        cached = self._cache_path(url)
        if cached.exists() and time.time() - cached.stat().st_mtime < self.cache_ttl:
            data = json.loads(cached.read_text())
            return Response(url, data["status"], data["text"], from_cache=True)
        if check_robots and not self.allowed(url):
            raise DisallowedByRobots(url)

        for attempt in range(self.max_retries + 1):
            self._wait_turn(url)
            r = self._http.get(url)
            if r.status_code != 429 and r.status_code < 500:
                break
            retry_after = r.headers.get("Retry-After", "")
            delay = float(retry_after) if retry_after.isdigit() else min(2**attempt * 5, 300)
            if attempt < self.max_retries:
                time.sleep(delay)
        response = Response(url, r.status_code, r.text, from_cache=False)
        if r.status_code < 500 and r.status_code != 429:
            cached.parent.mkdir(parents=True, exist_ok=True)
            cached.write_text(json.dumps({"status": r.status_code, "text": r.text}))
        return response

    def _wait_turn(self, url: str) -> None:
        host = urlsplit(url).netloc
        elapsed = time.monotonic() - self._last_request.get(host, 0.0)
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self._last_request[host] = time.monotonic()
