import csv
import json
import os

# ==== Editable Parameters ====
csv_file_path = "C:/output/input/SAL-9546-HDPositions.csv"     # Path to your CSV file
json_file_path = "C:/output/output/SAL-9546-HDPositions.json"  # Path to save the JSON file
# =============================

def csv_to_json(csv_path, json_path):
    try:
        with open(csv_path, mode='r', encoding='utf-8-sig') as csv_file:
            reader = csv.DictReader(csv_file, delimiter=';')  # <-- key fix here
            data = [dict(row) for row in reader]

        with open(json_path, mode='w', encoding='utf-8') as json_file:
            json.dump(data, json_file, indent=4)

        print(f"✅ Successfully converted and saved to: {json_path}")

    except Exception as e:
        print(f"❌ Error during conversion: {e}")

if __name__ == '__main__':
    if not os.path.exists(csv_file_path):
        print(f"❌ CSV file not found: {csv_file_path}")
    else:
        csv_to_json(csv_file_path, json_file_path)
