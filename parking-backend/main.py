from fastapi import FastAPI, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from typing import Optional, Tuple, List
import requests
from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

DATASET_SLUG = "on-street-parking-bay-sensors"
BASE = f"https://data.melbourne.vic.gov.au/api/explore/v2.1/catalog/datasets/{DATASET_SLUG}/records"
SELECT = "kerbsideid,status_description,lastupdated,location"
PAGE_LIMIT = 100
FETCH_CAP = 20000

APP_KEY = os.getenv("MELB_API_KEY", "").strip()

SESSION = requests.Session()
if APP_KEY:
    SESSION.headers.update({"Authorization": f"Apikey {APP_KEY}"})

app = FastAPI(title="Melbourne Parking Proxy", version="1.2.2")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=500)

def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

def build_params(since_iso: Optional[str]) -> dict:
    if since_iso:
        try:
            since = datetime.fromisoformat(since_iso.replace("Z", "+00:00"))
        except Exception:
            since = datetime.now(timezone.utc) - timedelta(minutes=30)
    else:
        since = datetime.now(timezone.utc) - timedelta(minutes=30)
    buffered = since - timedelta(minutes=10)
    where = f'location IS NOT NULL AND lastupdated > "{_iso(buffered)}"'
    return {"select": SELECT, "where": where, "order_by": "lastupdated ASC"}

def fetch_all(params: dict) -> tuple[list, List[str], dict]:
    offset = 0
    all_rows = []
    urls = []
    rate = {}
    while True:
        p = dict(params)
        p["limit"] = PAGE_LIMIT
        p["offset"] = offset
        if APP_KEY:
            p["apikey"] = APP_KEY
        req = requests.Request("GET", BASE, params=p).prepare()
        urls.append(req.url)
        r = SESSION.send(req, timeout=30)
        r.raise_for_status()
        rate = {
            "limit": r.headers.get("X-RateLimit-Limit"),
            "remaining": r.headers.get("X-RateLimit-Remaining"),
            "reset": r.headers.get("X-RateLimit-Reset"),
        }
        data = r.json()
        rows = data.get("results", [])
        all_rows.extend(rows)
        if len(rows) < PAGE_LIMIT or len(all_rows) >= FETCH_CAP:
            break
        offset += PAGE_LIMIT
    return all_rows[:FETCH_CAP], urls, rate

def normalize(rows: list) -> list:
    out = []
    for r in rows:
        loc = r.get("location") or {}
        try:
            lat = float(loc.get("lat"))
            lon = float(loc.get("lon"))
        except (TypeError, ValueError):
            continue
        out.append({
            "id": r.get("kerbsideid"),
            "status": (r.get("status_description") or "").lower(),
            "lastupdated": r.get("lastupdated"),
            "lat": lat,
            "lon": lon,
        })
    return out

def filter_bbox(records: list, bbox: Optional[Tuple[float, float, float, float]]) -> list:
    if not bbox:
        return records
    s, w, n, e = bbox
    return [r for r in records if s <= r["lat"] <= n and w <= r["lon"] <= e]

def thin_grid(records: list, cell: float, max_points: int) -> list:
    if not records:
        return records
    if max_points and max_points > 0 and len(records) > max_points:
        grid = {}
        for r in records:
            key = (round(r["lat"]/cell), round(r["lon"]/cell))
            prev = grid.get(key)
            if prev is None or (r.get("lastupdated") or "") > (prev.get("lastupdated") or ""):
                grid[key] = r
        thinned = list(grid.values())
        if len(thinned) > max_points:
            thinned.sort(key=lambda x: x.get("lastupdated") or "", reverse=True)
            thinned = thinned[:max_points]
        return thinned
    return records

@app.get("/api/bays")
def bays(
    since: Optional[str] = Query(default=None),
    bbox: Optional[str] = Query(default=None),
    debug: Optional[int] = Query(default=0),
    max_points: Optional[int] = Query(default=3000, ge=100),
    cell: Optional[float] = Query(default=0.0008, gt=0),
    response: Response = None,
):
    params = build_params(since)
    raw, urls, rate = fetch_all(params)
    recs_all = normalize(raw)
    bbox_tuple = None
    if bbox:
        try:
            s, w, n, e = (float(x) for x in bbox.split(","))
            bbox_tuple = (s, w, n, e)
        except Exception:
            bbox_tuple = None
    recs_bbox = filter_bbox(recs_all, bbox_tuple)
    next_since = since
    for r in recs_bbox:
        ts = r.get("lastupdated")
        if ts and (next_since is None or ts > next_since):
            next_since = ts
    recs = thin_grid(recs_bbox, cell=cell, max_points=max_points)
    resp = {"next_since": next_since, "count": len(recs), "records": recs}
    if debug:
        resp["upstream_urls"] = urls
        resp["has_key"] = bool(APP_KEY)
        resp["upstream_rate"] = rate
        resp["thin_cell"] = cell
        resp["thin_limit"] = max_points
    if response is not None:
        response.headers["Cache-Control"] = "public, max-age=5"
    return resp
