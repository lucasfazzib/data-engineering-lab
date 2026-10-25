"""Mock helpdesk REST API — a deterministic, local stand-in for a SaaS API (Zendesk, HubSpot, Jira...).

Behaves like real APIs do, on purpose:
  - bearer token auth
  - page-number pagination (/customers) and cursor pagination (/tickets)
  - incremental filter: /tickets?updated_since=<iso>  (inclusive: >=)
  - rate limiting: every 7th request returns 429 with Retry-After
  - POST /admin/simulate mutates data so incremental loads have something to pick up
  - POST /admin/schema-v2 starts returning a new nested field (schema evolution)
"""

import base64
import os
import random
from datetime import datetime, timedelta, timezone
from itertools import count

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse

TOKEN = os.environ.get("API_TOKEN", "dummy-local-token")
RATE_LIMIT_EVERY = int(os.environ.get("RATE_LIMIT_EVERY", "7"))

app = FastAPI(title="mock-helpdesk-api")
rnd = random.Random(7)
requests_seen = count(1)
state = {"schema_v2": False}


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


T0 = datetime(2026, 9, 1, tzinfo=timezone.utc)
CUSTOMERS = [
    {"id": i, "name": f"Company {i:03d}", "plan": rnd.choice(["free", "pro", "enterprise"]), "country": rnd.choice(["BR", "US", "PT", "DE"])}
    for i in range(1, 201)
]
TICKETS: dict[int, dict] = {}
for i in range(1, 1001):
    created = T0 + timedelta(minutes=rnd.randint(0, 50 * 24 * 60))
    TICKETS[i] = {
        "id": i,
        "customer_id": rnd.randint(1, 200),
        "subject": f"Issue #{i}",
        "status": rnd.choice(["open", "pending", "solved", "solved", "closed"]),
        "tags": rnd.sample(["billing", "bug", "login", "export", "api", "ui"], rnd.randint(0, 3)),
        "created_at": iso(created),
        "updated_at": iso(created + timedelta(hours=rnd.randint(0, 72))),
        "deleted": False,
    }
COMMENTS = {
    t: [{"id": t * 10 + k, "ticket_id": t, "body": f"comment {k} on ticket {t}", "author": rnd.choice(["agent", "customer"])} for k in range(rnd.randint(0, 3))]
    for t in TICKETS
}


def auth(authorization: str | None = Header(default=None)) -> None:
    if authorization != f"Bearer {TOKEN}":
        raise HTTPException(status_code=401, detail="invalid or missing bearer token")


@app.middleware("http")
async def rate_limit(request: Request, call_next):
    if request.url.path.startswith("/api/") and next(requests_seen) % RATE_LIMIT_EVERY == 0:
        return JSONResponse(status_code=429, content={"detail": "rate limited"}, headers={"Retry-After": "1"})
    return await call_next(request)


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/api/v1/customers", dependencies=[Depends(auth)])
def customers(page: int = 1, page_size: int = 50):
    total_pages = (len(CUSTOMERS) + page_size - 1) // page_size
    start = (page - 1) * page_size
    return {"data": CUSTOMERS[start : start + page_size], "page": page, "total_pages": total_pages}


def render(ticket: dict) -> dict:
    out = dict(ticket)
    if state["schema_v2"]:
        out["sla"] = {"priority": "high" if "billing" in ticket["tags"] else "normal", "breached": ticket["id"] % 13 == 0}
    return out


@app.get("/api/v1/tickets", dependencies=[Depends(auth)])
def tickets(updated_since: str = "1970-01-01T00:00:00Z", cursor: str | None = None, limit: int = 100):
    rows = sorted((t for t in TICKETS.values() if t["updated_at"] >= updated_since), key=lambda t: (t["updated_at"], t["id"]))
    offset = int(base64.b64decode(cursor).decode()) if cursor else 0
    page = rows[offset : offset + limit]
    nxt = base64.b64encode(str(offset + limit).encode()).decode() if offset + limit < len(rows) else None
    return {"data": [render(t) for t in page], "next_cursor": nxt}


@app.get("/api/v1/tickets/{ticket_id}/comments", dependencies=[Depends(auth)])
def comments(ticket_id: int):
    return {"data": COMMENTS.get(ticket_id, [])}


@app.post("/admin/simulate")
def simulate(updates: int = 30, inserts: int = 20, deletes: int = 5):
    """Update some tickets, create new ones and soft-delete a few — all with updated_at = now."""
    now = datetime.now(timezone.utc)
    ids = list(TICKETS)
    for tid in rnd.sample(ids, updates):
        TICKETS[tid].update(status=rnd.choice(["pending", "solved", "closed"]), updated_at=iso(now))
    for tid in rnd.sample(ids, deletes):
        TICKETS[tid].update(deleted=True, updated_at=iso(now))
    for tid in range(max(TICKETS) + 1, max(TICKETS) + 1 + inserts):
        TICKETS[tid] = {"id": tid, "customer_id": rnd.randint(1, 200), "subject": f"Issue #{tid}", "status": "open",
                        "tags": [], "created_at": iso(now), "updated_at": iso(now), "deleted": False}
        COMMENTS[tid] = []
    return {"updated": updates, "inserted": inserts, "soft_deleted": deletes, "total_tickets": len(TICKETS)}


@app.post("/admin/schema-v2")
def schema_v2(enabled: bool = True):
    state["schema_v2"] = enabled
    return state
