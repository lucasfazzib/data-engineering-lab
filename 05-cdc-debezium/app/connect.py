"""Tiny client for the Kafka Connect REST API.

  python connect.py register ../connectors/shop-connector.json   # create or update (idempotent PUT)
  python connect.py status [name]
  python connect.py delete <name>
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request

CONNECT = os.environ.get("CONNECT_URL", "http://localhost:8083")


def call(method: str, path: str, body: dict | None = None, allow_404: bool = False):
    req = urllib.request.Request(
        f"{CONNECT}{path}", method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as exc:
        if allow_404 and exc.code == 404:
            return None
        sys.exit(f"{method} {path} -> {exc.code}: {exc.read().decode()}")


def register(path: str) -> None:
    spec = json.load(open(path))
    config = {k: v for k, v in spec["config"].items() if not k.startswith("_comment")}
    # PUT /connectors/<name>/config creates the connector or updates it: safe to re-run
    call("PUT", f"/connectors/{spec['name']}/config", config)
    st = None
    for _ in range(30):
        # status is 404 for a moment right after creation
        st = call("GET", f"/connectors/{spec['name']}/status", allow_404=True) or {}
        tasks = [t["state"] for t in st.get("tasks", [])]
        if tasks and all(s == "RUNNING" for s in tasks):
            print(f"{spec['name']}: connector={st['connector']['state']} tasks={tasks}")
            return
        if "FAILED" in tasks:
            sys.exit(json.dumps(st, indent=2))
        time.sleep(1)
    sys.exit(f"{spec['name']} did not reach RUNNING: {st}")


def status(name: str | None) -> None:
    names = [name] if name else call("GET", "/connectors")
    for n in names:
        st = call("GET", f"/connectors/{n}/status")
        print(f"{n}: connector={st['connector']['state']} tasks={[t['state'] for t in st['tasks']]}")


if __name__ == "__main__":
    cmd, arg = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else None)
    if cmd == "register":
        register(arg)
    elif cmd == "status":
        status(arg)
    elif cmd == "delete":
        call("DELETE", f"/connectors/{arg}")
        print(f"deleted {arg}")
