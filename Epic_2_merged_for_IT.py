# Epic_2_merged_for_IT.py
import pandas as pd

# 1) Load zone-level availability (from your model script)
#    Expected cols: Zone_Number, slot_30, total_obs, availability_rate
avail = pd.read_csv("parking_availability_model.csv")
print("avail cols:", avail.columns.tolist())

# 2) Load zone centroids (Zone_Number, Latitude, Longitude)
# Try standard read first
centroids = pd.read_json("zone_centroids_final.json")
# If it's a dict-like mapping (e.g., {"7550":{"lat":...,"lon":...}, ...})
if isinstance(centroids.columns[0], (int, str)) and centroids.shape[1] == 1 and centroids.iloc[0].apply(lambda x: isinstance(x, dict)).any():
    # Flatten dict-of-dicts to rows
    centroids = pd.DataFrame.from_dict(pd.read_json("zone_centroids_final.json", typ="series").to_dict(), orient="index").reset_index()
    centroids = centroids.rename(columns={"index": "Zone_Number"})

# Normalise likely column names
rename_map = {
    "zone": "Zone_Number",
    "zone_number": "Zone_Number",
    "zoneNumber": "Zone_Number",
    "lat": "Latitude",
    "lng": "Longitude",
    "lon": "Longitude",
    "Lat": "Latitude",
    "Lon": "Longitude",
}
centroids = centroids.rename(columns=rename_map)

# If there’s a nested 'centroid' col with dicts {lat, lon}, expand it
if "centroid" in centroids.columns and centroids["centroid"].apply(lambda v: isinstance(v, dict)).any():
    cxy = pd.json_normalize(centroids["centroid"])
    centroids = pd.concat([centroids.drop(columns=["centroid"]), cxy], axis=1)
    centroids = centroids.rename(columns=rename_map)

print("centroids cols (raw/normalised):", centroids.columns.tolist())

# Keep only what we need
need_cols = ["Zone_Number", "Latitude", "Longitude"]
missing = [c for c in need_cols if c not in centroids.columns]
if missing:
    raise ValueError(f"Centroids JSON is missing required columns: {missing}. "
                     f"Found: {centroids.columns.tolist()}")

centroids = centroids[need_cols].drop_duplicates()

# 3) Load bay -> zone mapping for live API joins (KerbsideID -> Zone_Number)
bays = pd.read_csv("bays_zones_final.csv", usecols=["KerbsideID", "Zone_Number"])
print("bays cols:", bays.columns.tolist())

# --- Type harmonisation (important for merge keys) ---
# Coerce Zone_Number to string in all frames to avoid int/object merge issues
for df in (avail, centroids, bays):
    df["Zone_Number"] = df["Zone_Number"].astype(str)

# Make sure slot_30 is numeric
if "slot_30" in avail.columns:
    avail["slot_30"] = pd.to_numeric(avail["slot_30"], errors="coerce")

# --- Create zone-level master (coords + availability) ---
zone_master = avail.merge(centroids, on="Zone_Number", how="left")

# Optional: Pivot slot_30 to wide for simpler API reads (one row per zone with columns for common slots)
if {"Zone_Number", "Latitude", "Longitude", "slot_30", "availability_rate"}.issubset(zone_master.columns):
    wide = (
        zone_master
        .assign(slot_col=lambda d: "slot_" + d["slot_30"].astype("Int64").astype(str))
        .pivot_table(
            index=["Zone_Number", "Latitude", "Longitude"],
            columns="slot_col",
            values="availability_rate",
            aggfunc="mean"
        )
        .reset_index()
    )
else:
    # Fallback if columns aren’t present for wide pivot
    wide = zone_master.groupby(["Zone_Number", "Latitude", "Longitude"], as_index=False)["availability_rate"].mean()

# Keep a tidy (long) version too (handy for BI tools)
zone_master = zone_master.sort_values(["Zone_Number", "slot_30"], na_position="last")

# --- Save deliverables ---
zone_master.to_csv("IT_zone_availability_long.csv", index=False)
wide.to_csv("IT_zone_availability_wide.csv", index=False)
bays.to_csv("IT_bay_to_zone_map.csv", index=False)

print("Saved:")
print("- IT_zone_availability_long.csv  (Zone_Number, slot_30, availability_rate, total_obs, Latitude, Longitude)")
print("- IT_zone_availability_wide.csv  (Zone_Number, Latitude, Longitude, slot_XX columns with probabilities)")
print("- IT_bay_to_zone_map.csv         (KerbsideID -> Zone_Number)")