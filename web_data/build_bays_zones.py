# build_bays_zones.py
import pandas as pd

sensor = pd.read_csv("data/on-street-parking-bay-sensors.csv")  # KerbsideID, Zone_Number, Status_*, Location
bays   = pd.read_csv("data/on-street-parking-bays.csv")         # KerbsideID, Latitude, Longitude, RoadSegmentDescription, ...

# Clean types
sensor["KerbsideID"] = sensor["KerbsideID"].astype(str).str.strip()
bays["KerbsideID"]   = bays["KerbsideID"].astype(str).str.strip()

# Best-effort Zone_Number: take the most frequent zone per KerbsideID from sensor feed
zone_by_bay = (sensor.dropna(subset=["Zone_Number","KerbsideID"])
                      .assign(Zone_Number=lambda d: pd.to_numeric(d["Zone_Number"], errors="coerce"))
                      .dropna(subset=["Zone_Number"])
                      .astype({"Zone_Number": int})
                      .groupby("KerbsideID")["Zone_Number"]
                      .agg(lambda s: s.value_counts().idxmax())
                      .reset_index())

bz = (bays.merge(zone_by_bay, on="KerbsideID", how="left")
          .dropna(subset=["Latitude","Longitude"])
          [["KerbsideID","Zone_Number","Latitude","Longitude","RoadSegmentDescription"]])

bz.to_csv("bays_zones.csv", index=False)
print("Saved bays_zones.csv with", len(bz), "rows")