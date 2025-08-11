# backfill_zone_numbers_knn.py
import pandas as pd
import numpy as np
from sklearn.neighbors import BallTree

# -----------------------
# Params (tweak as needed)
# -----------------------
K_NEIGHBORS = 5          # vote across k nearest known bays
MAX_METERS = 200         # only trust neighbors within this radius
INPUT_CSV = "bays_zones.csv"
OUTPUT_CSV = "bays_zones_backfilled.csv"

EARTH_RADIUS_M = 6371000.0

def to_radians(df):
    return np.radians(df[["Latitude", "Longitude"]].to_numpy())

def majority_vote(zone_array):
    # returns most frequent value; ties -> first encountered
    vals, counts = np.unique(zone_array, return_counts=True)
    return vals[np.argmax(counts)]

# 1) Load
df = pd.read_csv(INPUT_CSV)
print(f"Loaded {len(df):,} rows")

# 2) Split known vs unknown
known = df.dropna(subset=["Zone_Number"]).copy()
unknown = df[df["Zone_Number"].isna()].copy()

print(f"Known zones: {len(known):,} rows, Unknown zones: {len(unknown):,} rows")
if known.empty:
    raise SystemExit("No known Zone_Number rows found; cannot backfill.")

# Cast zone to int for clean voting
known["Zone_Number"] = known["Zone_Number"].astype(int)

# 3) Build BallTree on known bay coordinates (in radians) using haversine
known_rad = to_radians(known)
tree = BallTree(known_rad, metric="haversine")

# 4) Query neighbors for unknowns
unknown_rad = to_radians(unknown)
dist_rad, idx = tree.query(unknown_rad, k=K_NEIGHBORS)  # radians
dist_m = dist_rad * EARTH_RADIUS_M                      # meters

# 5) Decide assignments
assigned_zones = []
assignable_mask = (dist_m[:, 0] <= MAX_METERS)  # require nearest within radius

for i, can_assign in enumerate(assignable_mask):
    if not can_assign:
        assigned_zones.append(np.nan)
        continue
    neighbor_indices = idx[i]
    neighbor_zones = known.iloc[neighbor_indices]["Zone_Number"].to_numpy()
    assigned_zones.append(int(majority_vote(neighbor_zones)))

unknown_assigned = unknown.copy()
unknown_assigned["Zone_Number_backfill"] = assigned_zones

# 6) Merge back; prefer original Zone_Number, else backfill
df["Zone_Number_backfill"] = df["Zone_Number"]  # start with originals
df.loc[unknown_assigned.index, "Zone_Number_backfill"] = unknown_assigned["Zone_Number_backfill"].values

# 7) Metrics
before_pct = df["Zone_Number"].notna().mean()
after_pct = df["Zone_Number_backfill"].notna().mean()
newly_filled = df["Zone_Number_backfill"].notna().sum() - df["Zone_Number"].notna().sum()

print(f"\nCoverage before: {before_pct:.2%}")
print(f"Coverage after:  {after_pct:.2%}")
print(f"Newly inferred Zone_Number rows: {newly_filled:,}")
print(f"Radius used: {MAX_METERS} m, k={K_NEIGHBORS}")

# 8) (Optional) Quick sanity peek: distribution of backfilled distances
valid_new = (~df["Zone_Number"].notna()) & (df["Zone_Number_backfill"].notna())
if valid_new.any():
    # map back to distances for those rows
    # Build a quick lookup by index to closest distance
    closest_dist_m = np.full(len(df), np.nan)
    closest_dist_m[unknown.index] = dist_m[:,0]
    print("\nBackfilled distance stats (m):")
    print(pd.Series(closest_dist_m[valid_new]).describe([0.5, 0.9, 0.95]).round(1))

# 9) Save
df_out = df.drop(columns=["Zone_Number"]) \
           .rename(columns={"Zone_Number_backfill": "Zone_Number"})
df_out.to_csv(OUTPUT_CSV, index=False)
print(f"\nSaved {OUTPUT_CSV}")