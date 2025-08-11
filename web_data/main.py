# main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import json
from datetime import datetime
from zoneinfo import ZoneInfo
import time
import requests
from typing import Optional, Dict, Any, List

app = FastAPI(title="Melbourne Parking Forecasts", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

TZ = ZoneInfo("Australia/Melbourne")

BASE = Path(__file__).parent
COMBINED = BASE / "web_data" / "bay_forecasts.json"
PER_BAY_DIR = BASE / "web_data" / "bay_forecasts"

# serve static JSON too (optional)
app.mount("/web_data", StaticFiles(directory=str(BASE / "web_data")), name="web_data")

_bay_idx = None
def load_index():
    global _bay_idx
    if _bay_idx is None:
        if not COMBINED.exists():
            raise FileNotFoundError("Run export_forecasts.py first to create web_data/")
        with COMBINED.open() as f:
            combined = json.load(f)
        _bay_idx = combined["bays"]  # dict[str -> list[points]]
    return _bay_idx


# --- LIVE DATA (City of Melbourne) ---
LIVE_API_URL = (
    "https://data.melbourne.vic.gov.au/api/explore/v2.1/catalog/datasets/"
    "on-street-parking-bay-sensors/records"
)

# Small in-memory cache keyed by params
_live_cache: Dict[str, Any] = {"key": None, "data": None, "fetched_at": 0.0}
LIVE_TTL_SECONDS = 30  # serve cached live data for this long

def _live_cache_key(limit: int, zone_number: Optional[str], bbox: Optional[str]) -> str:
    return f"{int(limit)}|{zone_number or ''}|{bbox or ''}"

def _get_live_cached(limit=1000, zone_number: Optional[str] = None, bbox: Optional[str] = None):
    now = time.time()
    key = _live_cache_key(limit, zone_number, bbox)
    if (
        _live_cache.get("key") == key and
        (now - _live_cache.get("fetched_at", 0.0)) < LIVE_TTL_SECONDS and
        _live_cache.get("data") is not None
    ):
        return _live_cache["data"]

    data = _fetch_live_bays(limit=limit, zone_number=zone_number, bbox=bbox)
    _live_cache.update({"key": key, "data": data, "fetched_at": now})
    return data

def _fetch_live_bays(limit: int = 1000, zone_number: Optional[str] = None,
                     bbox: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Pull live bay records from the open data API with paging.
    Socrata v2.1 commonly rejects very large single-page limits (400 errors),
    so we request pages of 100 and aggregate until we reach `limit` (capped at 5000).
    """
    # total desired rows (across pages)
    total_needed = max(1, min(int(limit or 100), 5000))
    per_page = 100  # safe per-page size for v2.1
    offset = 0

    base_params = {
        "limit": per_page,
        # Trim the payload to exactly what we use
        "select": "kerbsideid,zone_number,status_description,status_timestamp,location",
        # Optional: order for deterministic paging (field must exist)
        "order_by": "kerbsideid",
    }

    # Add a simple server-side filter if given
    where_clauses = []
    if zone_number:
        where_clauses.append(f"zone_number = '{zone_number}'")
    if where_clauses:
        base_params["where"] = " AND ".join(where_clauses)

    out: List[Dict[str, Any]] = []

    try:
        while len(out) < total_needed:
            params = dict(base_params)
            params["offset"] = offset
            r = requests.get(LIVE_API_URL, params=params, timeout=15, headers={"Accept": "application/json"})
            try:
                r.raise_for_status()
            except requests.HTTPError as e:
                # include response text to aid debugging
                raise HTTPException(
                    status_code=502,
                    detail=f"Live API HTTP error {e.response.status_code}: {e}; body={r.text[:300]}"
                )

            payload = r.json()
            rows = payload.get("results", [])
            if not rows:
                break

            # normalize fields
            for row in rows:
                out.append({
                    "KerbsideID": str(row.get("kerbsideid") or ""),
                    "Zone_Number": (str(row.get("zone_number") or "").strip() or None),
                    "Status_Description": (row.get("status_description") or "").strip(),
                    "Status_Timestamp": row.get("status_timestamp"),
                    "Location": row.get("location"),
                })
                if len(out) >= total_needed:
                    break

            # stop if fewer than a full page returned
            if len(rows) < per_page:
                break

            offset += per_page
    except Exception as e:
        # any other failure -> 502
        raise HTTPException(status_code=502, detail=f"Live API request failed: {e}")

    # Optional client-side bbox filter (string: "minLon,minLat,maxLon,maxLat")
    if bbox:
        try:
            min_lon, min_lat, max_lon, max_lat = [float(x) for x in bbox.split(",")]
            def in_bbox(rec: Dict[str, Any]) -> bool:
                loc = rec.get("Location")
                if not loc:
                    return False
                if isinstance(loc, str) and "," in loc:
                    # "lat,lon" format
                    lat_str, lon_str = [t.strip() for t in loc.split(",")]
                    lat, lon = float(lat_str), float(lon_str)
                elif isinstance(loc, dict):
                    lat, lon = float(loc.get("lat")), float(loc.get("lon"))
                else:
                    return False
                return (min_lat <= lat <= max_lat) and (min_lon <= lon <= max_lon)
            out = [r for r in out if in_bbox(r)]
        except Exception:
            # ignore bbox errors
            pass

    return out

@app.get("/bays/live")
def bays_live(limit: int = 1000, zone_number: Optional[str] = None, bbox: Optional[str] = None):
    """
    Current live bay statuses from the City of Melbourne API (cached ~30s).
    Optional: limit, zone_number, bbox (string: "minLon,minLat,maxLon,maxLat"; client-side filter).
    """
    rows = _get_live_cached(limit=limit, zone_number=zone_number, bbox=bbox)
    return {
        "fetchedAt": datetime.now(TZ).isoformat(),
        "ttlSeconds": LIVE_TTL_SECONDS,
        "count": len(rows),
        "rows": rows
    }

@app.get("/bays/with_forecast")
def bay_with_forecast(kerbside_id: str):
    """
    For a bay: return live status (if available) + forecast points (from bay_forecasts.json).
    """
    # Forecast
    idx = load_index()
    points = idx.get(str(kerbside_id))
    if not points:
        raise HTTPException(status_code=404, detail="kerbside_id not found in forecasts")

    # Live (cached)
    live_rows = _get_live_cached()
    live = next((r for r in live_rows if r["KerbsideID"] == str(kerbside_id)), None)

    # Optional: a simple "now" probability from live
    now_prob = None
    if live:
        s = (live.get("Status_Description") or "").strip().lower()
        if s == "unoccupied":
            now_prob = 1.0
        elif s == "present":
            now_prob = 0.0

    return {
        "kerbsideId": kerbside_id,
        "live": live,
        "nowProb": now_prob,
        "points": points  # keep the same field name as /bays/forecasts to simplify frontend reuse
    }

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/bays/forecasts")
def bay_forecasts(kerbside_id: str):
    idx = load_index()
    points = idx.get(str(kerbside_id))
    if not points:
        raise HTTPException(status_code=404, detail="kerbside_id not found")
    return {
        "kerbsideId": kerbside_id,
        "points": points
    }

@app.get("/bays/forecasts/all")
def all_bays():
    return load_index()
