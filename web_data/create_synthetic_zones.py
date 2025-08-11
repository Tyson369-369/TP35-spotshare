# create_synthetic_zones.py
import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN

# -----------------------
# Tunables
# -----------------------
INPUT_CSV = "bays_zones_backfilled.csv"   # from your KNN backfill step
OUTPUT_CSV = "bays_zones_final.csv"
ZONE_CENTROIDS_JSON = "zone_centroids_final.json"

# DBSCAN params (haversine):
EPS_METERS = 150         # radius to group nearby bays into one synthetic zone
MIN_SAMPLES = 3          # minimum bays to form a cluster
START_SYNTH_ZONE = 900000  # starting ID for synthetic zones

EARTH_RADIUS_M = 6371000.0

def to_radians(df):
    return np.radians(df[["Latitude", "Longitude"]].to_numpy())

# 1) Load
df = pd.read_csv(INPUT_CSV)
print(f"Loaded {len(df):,} rows")

# 2) Split: keep bays that still lack a zone after backfill
known_mask = df["Zone_Number"].notna()
unknown = df.loc[~known_mask].copy()
known = df.loc[known_mask].copy()

print(f"Already zoned: {len(known):,} | Still unzoned: {len(unknown):,}")

if not unknown.empty:
    # 3) DBSCAN on unzoned bays (haversine)
    coords_rad = to_radians(unknown)
    eps_rad = EPS_METERS / EARTH_RADIUS_M

    clustering = DBSCAN(eps=eps_rad, min_samples=MIN_SAMPLES, metric="haversine")
    labels = clustering.fit_predict(coords_rad)  # -1 = noise

    unknown["cluster_label"] = labels

    # 4) Assign synthetic zone IDs for clusters (label >= 0)
    cluster_ids = sorted(l for l in np.unique(labels) if l >= 0)
    synth_map = {lab: START_SYNTH_ZONE + i for i, lab in enumerate(cluster_ids)}

    unknown["Zone_Number_synth"] = unknown["cluster_label"].map(synth_map)

    # 5) Fallback: singletons/noise (-1) → one-bay = one-zone (unique id each)
    noise_mask = unknown["cluster_label"] == -1
    if noise_mask.any():
        # unique incremental IDs after the last synthetic cluster
        offset = START_SYNTH_ZONE + len(cluster_ids)
        # give each noise row its own zone id
        unknown.loc[noise_mask, "Zone_Number_synth"] = (
            offset + np.arange(noise_mask.sum())
        )

    # 6) Merge back: prefer existing Zone_Number, else synthetic
    df["Zone_Number_final"] = df["Zone_Number"]
    df.loc[unknown.index, "Zone_Number_final"] = unknown["Zone_Number_synth"].values

else:
    # Nothing to synthesize; just copy
    df["Zone_Number_final"] = df["Zone_Number"]

# 7) Metrics
before_pct = df["Zone_Number"].notna().mean()
after_pct = df["Zone_Number_final"].notna().mean()
print(f"\nCoverage before: {before_pct:.2%}")
print(f"Coverage after:  {after_pct:.2%}")

# 8) Save final CSV (drop old column, rename)
out = df.drop(columns=["Zone_Number"]).rename(columns={"Zone_Number_final": "Zone_Number"})
out.to_csv(OUTPUT_CSV, index=False)
print(f"Saved {OUTPUT_CSV}")

# 9) Export zone centroids (useful for IT/API & map)
centroids = (
    out.groupby("Zone_Number")[["Latitude", "Longitude"]]
      .mean()
      .reset_index()
      .rename(columns={"Latitude": "lat", "Longitude": "lon"})
)
centroids.to_json(ZONE_CENTROIDS_JSON, orient="records", indent=2)
print(f"Saved {ZONE_CENTROIDS_JSON}")

# 10) Quick summary
total_zones = centroids["Zone_Number"].nunique()
synthetic_count = centroids["Zone_Number"].astype(int).ge(START_SYNTH_ZONE).sum()
print(f"\nZones total: {total_zones:,} (synthetic: {synthetic_count:,})")