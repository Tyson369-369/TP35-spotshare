import pandas as pd

# Load sensor status data
sensor_df = pd.read_excel("Datasets/on-street-parking-bay-sensors.xlsx")
print("Sensor Data Columns:", sensor_df.columns)

# Load parking bay metadata
bays_df = pd.read_excel("Datasets/on-street-parking-bays.xlsx")
print("Bay Data Columns:", bays_df.columns)

# Ensure both KerbsideID columns are of type string
sensor_df["KerbsideID"] = sensor_df["KerbsideID"].astype(str)
bays_df["KerbsideID"] = bays_df["KerbsideID"].astype(str)

# Merge them on KerbsideID
merged_df = pd.merge(sensor_df, bays_df, on="KerbsideID", how="inner")

# Keep relevant columns
columns_to_keep = [
    "KerbsideID", "Status_Description", "Status_Timestamp",
    "Latitude", "Longitude", "RoadSegmentDescription", "Zone_Number"
]
merged_df = merged_df[columns_to_keep]

# Show a preview
print("\nMerged Data Preview:")
print(merged_df.head())

# Optional: Save to CSV or JSON
merged_df.to_csv("merged_parking_data.csv", index=False)


# Check Zone_Number completeness
total_rows = len(merged_df)
nan_rows = merged_df["Zone_Number"].isna().sum()
valid_rows = total_rows - nan_rows

print(f"\nTotal merged rows: {total_rows}")
print(f"Rows with missing Zone_Number: {nan_rows}")
print(f"Rows to keep (valid Zone_Number): {valid_rows}")