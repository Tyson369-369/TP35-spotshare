# export_forecast.py
import os, json
import sys, time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import pandas as pd

BAY_MODEL = "bay_availability_model.csv"          # per-bay historical probs
ZONE_MODEL = "parking_availability_model.csv"     # per-zone fallback (weekday+slot_30)
BAY_TO_ZONE = "bays_zones_final.csv"              # KerbsideID -> Zone_Number (strings ok)

OUT_DIR = "web_data/bay_forecasts"
OUT_COMBINED = "web_data/bay_forecasts.json"
OUT_COMBINED_ALT = "bay_forecasts_latest.json"    # so main.py can load this if it expects it

TZ = ZoneInfo("Australia/Melbourne")
STEP_HOURS = 1
NUM_STEPS = 13

def _now_tz():
    return datetime.now(TZ).isoformat()

def log(msg: str):
    print(f"[{_now_tz()}] {msg}", flush=True)

def to_slot_30(dt): return dt.hour * 2 + (1 if dt.minute >= 30 else 0)
def wd(dt): return dt.weekday()

def round_up_to_next_hour(dt: datetime) -> datetime:
    loc = dt.astimezone(TZ)
    base = loc.replace(minute=0, second=0, microsecond=0)
    return base if loc.minute == 0 else base + timedelta(hours=1)

def load_models():
    log("load_models(): start")
    t0 = time.time()
    # Bay model
    bay = pd.read_csv(BAY_MODEL)
    for c in ["KerbsideID","weekday","slot_30","availability_rate","total_obs"]:
        if c in bay: bay[c] = pd.to_numeric(bay[c], errors="coerce")
    bay = bay.dropna(subset=["KerbsideID","slot_30","availability_rate"])
    log(f"Bay model loaded: rows={len(bay):,}, unique kerbs={bay['KerbsideID'].nunique():,}")

    # Zone model (fallback)
    zone = None
    if os.path.exists(ZONE_MODEL):
        zone = pd.read_csv(ZONE_MODEL)
        for c in ["Zone_Number","weekday","slot_30","availability_rate","total_obs"]:
            if c in zone: zone[c] = pd.to_numeric(zone[c], errors="coerce")
        zone = zone.dropna(subset=["Zone_Number","slot_30","availability_rate"])
    if zone is not None:
        log(f"Zone model loaded: rows={len(zone):,}, unique zones={zone['Zone_Number'].nunique():,}")
    else:
        log("Zone model not found — zone fallback disabled")

    # Bay -> Zone map (strings fine, we’ll cast where needed)
    bay2zone = None
    if os.path.exists(BAY_TO_ZONE):
        m = pd.read_csv(BAY_TO_ZONE, usecols=["KerbsideID","Zone_Number"])
        m["KerbsideID"] = m["KerbsideID"].astype(str).str.strip()
        m["Zone_Number"] = m["Zone_Number"].astype(str).str.strip()
        bay2zone = dict(zip(m["KerbsideID"], m["Zone_Number"]))
        log(f"Bay→Zone map loaded: entries={len(bay2zone):,}")

    log(f"load_models(): done in {time.time()-t0:.2f}s")
    return bay, zone, bay2zone

def get_prob_bay(bay_df, kerb, w, s):
    # strict match by weekday+slot
    m = bay_df[(bay_df.KerbsideID == kerb) & (bay_df.weekday == w) & (bay_df.slot_30 == s)]
    if not m.empty:
        return float(m.iloc[0]["availability_rate"])
    # fallback: same slot across weekdays
    m = bay_df[(bay_df.KerbsideID == kerb) & (bay_df.slot_30 == s)]
    if not m.empty:
        return float(m["availability_rate"].mean())
    return None

def get_prob_zone(zone_df, zone, w, s):
    if zone_df is None or zone is None:
        return None
    try:
        zone_i = int(zone)
    except:
        return None
    m = zone_df[(zone_df.Zone_Number == zone_i) & (zone_df.weekday == w) & (zone_df.slot_30 == s)]
    if not m.empty:
        return float(m.iloc[0]["availability_rate"])
    m = zone_df[(zone_df.Zone_Number == zone_i) & (zone_df.slot_30 == s)]
    if not m.empty:
        return float(m["availability_rate"].mean())
    return None

def export():
    log("export(): start")
    t_start = time.time()
    bay_df, zone_df, bay2zone = load_models()
    log("Models loaded into memory")
    os.makedirs(OUT_DIR, exist_ok=True)
    log(f"Output dir ready: {OUT_DIR}")

    now = datetime.now(TZ)
    start = round_up_to_next_hour(now)
    log(f"Generation time window: start={start.isoformat()}, steps={NUM_STEPS}, step_hours={STEP_HOURS}")

    kerbs = sorted(bay_df["KerbsideID"].dropna().astype(int).unique().tolist())
    log(f"Total kerbs to process: {len(kerbs):,}")
    if kerbs:
        log(f"Sample kerbs: {kerbs[:5]}")

    combined = {
        "generatedAt": now.isoformat(),
        "stepHours": STEP_HOURS,
        "bays": {}
    }

    for k in kerbs:
        if (len(combined["bays"]) % 1000) == 0 and len(combined["bays"]) > 0:
            log(f"Progress: processed {len(combined['bays']):,} kerbs")
        k_str = str(int(k))
        z = bay2zone.get(k_str) if bay2zone else None

        points = []
        for i in range(NUM_STEPS):
            ti = start + timedelta(hours=i)
            w = wd(ti)
            s = to_slot_30(ti)

            p = get_prob_bay(bay_df, k, w, s)
            if p is None and z is not None:
                p = get_prob_zone(zone_df, z, w, s)

            points.append({
                "timeISO": ti.isoformat(),
                "prob": None if p is None else round(float(p), 4)
            })

        obj = {
            "kerbsideId": int(k),
            "generatedAt": now.isoformat(),
            "startTime": start.isoformat(),
            "stepHours": STEP_HOURS,
            "points": points
        }
        with open(os.path.join(OUT_DIR, f"{int(k)}.json"), "w") as f:
            json.dump(obj, f, indent=2)
        if len(combined["bays"]) < 3:
            log(f"Wrote per-bay file: {os.path.join(OUT_DIR, f'{int(k)}.json')}")

        combined["bays"][k_str] = points

    with open(OUT_COMBINED, "w") as f:
        json.dump(combined, f, indent=2)
    with open(OUT_COMBINED_ALT, "w") as f:
        json.dump(combined, f, indent=2)

    try:
        size1 = os.path.getsize(OUT_COMBINED)
    except Exception:
        size1 = -1
    try:
        size2 = os.path.getsize(OUT_COMBINED_ALT)
    except Exception:
        size2 = -1
    log(f"Wrote combined artifacts: {OUT_COMBINED} ({size1} bytes), {OUT_COMBINED_ALT} ({size2} bytes)")

    log(f"Exported {len(kerbs):,} bays → {OUT_DIR}, {OUT_COMBINED}, {OUT_COMBINED_ALT}")
    log(f"export(): done in {time.time()-t_start:.2f}s")

if __name__ == "__main__":
    log("Starting export_forecast.py as a script")
    export()