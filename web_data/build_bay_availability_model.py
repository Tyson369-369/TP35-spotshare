# build_bay_availability_model.py
import pandas as pd

SRC = "data/on-street-parking-bay-sensors.csv"
OUT = "bay_availability_model.csv"
OUT_ZONE = "parking_availability_model.csv"  # simple zone fallback from the same data

def to_slot_30(ts: pd.Timestamp) -> int:
    return ts.hour * 2 + (1 if ts.minute >= 30 else 0)

def clean_status(s):
    return (str(s).strip().lower() if pd.notna(s) else "")

print("Loading…")
df = pd.read_csv(
    SRC,
    dtype={"KerbsideID": "Int64", "Zone_Number": "Int64"},
)

# Expect these columns: KerbsideID, Status_Description, Status_Timestamp, Zone_Number
keep = ["KerbsideID", "Status_Description", "Status_Timestamp", "Zone_Number"]
missing = [c for c in keep if c not in df.columns]
if missing:
    raise ValueError(f"Missing columns in {SRC}: {missing}")

df = df[keep].copy()

df["ts"] = pd.to_datetime(df["Status_Timestamp"], errors="coerce", utc=True)\
             .dt.tz_convert("Australia/Melbourne")
df = df.dropna(subset=["KerbsideID", "ts"])

df["status"]  = df["Status_Description"].map(clean_status)
df["free"]    = (df["status"] == "unoccupied").astype(int)
df["weekday"] = df["ts"].dt.weekday
df["slot_30"] = df["ts"].apply(to_slot_30)

# one record per bay per date per slot (use last event in that slot)
df["slot_key"] = (
    df["KerbsideID"].astype(str) + "|" +
    df["ts"].dt.date.astype(str) + "|" +
    df["slot_30"].astype(str)
)
idx = df.groupby("slot_key")["ts"].idxmax()
df_slot = df.loc[idx, ["KerbsideID", "Zone_Number", "weekday", "slot_30", "free"]]

g_bay = df_slot.groupby(["KerbsideID", "weekday", "slot_30"]).agg(
    total_obs=("free", "size"),
    availability_rate=("free", "mean")
).reset_index()

print("Saving per‑bay model →", OUT)
g_bay.to_csv(OUT, index=False)

g_zone = df_slot.dropna(subset=["Zone_Number"]).groupby(
    ["Zone_Number", "weekday", "slot_30"]
).agg(
    total_obs=("free", "size"),
    availability_rate=("free", "mean")
).reset_index()

print("Saving zone model (fallback) →", OUT_ZONE)
g_zone.to_csv(OUT_ZONE, index=False)

print("Done.",
      "Rows (bay model):", len(g_bay),
      "Rows (zone model):", len(g_zone))