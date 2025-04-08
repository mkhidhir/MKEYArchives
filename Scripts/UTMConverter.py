import pandas as pd
import utm
import os

# Define the folder where CSV files are stored
csv_folder = "csv"
os.makedirs(csv_folder, exist_ok=True)  # Ensure the folder exists

# Define input and output file paths
input_csv = os.path.join(csv_folder, "file-to-add-UTM.csv")
output_csv = os.path.join(csv_folder, "converted-file.csv")

# Read the CSV file
df = pd.read_csv(input_csv)

# Check if required columns exist
if 'LAT' not in df.columns or 'LON' not in df.columns:
    raise ValueError("CSV file must contain 'LAT' and 'LON' columns")

# Function to convert LAT, LON to UTM NORTHING and EASTING
def latlon_to_utm(lat, lon):
    try:
        easting, northing, _, _ = utm.from_latlon(lat, lon)
        return easting, northing
    except Exception as e:
        print(f"Error converting ({lat}, {lon}): {e}")
        return None, None

# Convert LAT, LON to EASTING, NORTHING
df[['EASTING', 'NORTHING']] = df.apply(lambda row: pd.Series(latlon_to_utm(row['LAT'], row['LON'])), axis=1)

# Reorder columns to place EASTING & NORTHING next to LAT & LON
columns = df.columns.tolist()
lat_index = columns.index("LAT")  # Get LAT index
new_order = columns[:lat_index+2] + ["NORTHING", "EASTING"] + columns[lat_index+2:-2]  # Reorder
df = df[new_order]

# Save the updated DataFrame to a new CSV file in the csv folder
df.to_csv(output_csv, index=False)

print(f"File saved as {output_csv}")