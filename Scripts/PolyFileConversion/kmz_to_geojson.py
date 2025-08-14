import os
import zipfile
import tempfile
import geopandas as gpd
import json

def convert_kmz_to_geojson(kmz_path, geojson_path):
    # Step 1: Extract KMZ (ZIP) contents
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"📦 Extracting {kmz_path} to temporary directory...")
        with zipfile.ZipFile(kmz_path, 'r') as kmz:
            kmz.extractall(tmpdir)

        # Step 2: Find the KML file in extracted contents
        kml_files = [f for f in os.listdir(tmpdir) if f.endswith('.kml')]
        if not kml_files:
            raise FileNotFoundError("No .kml file found inside the .kmz archive.")
        
        kml_path = os.path.join(tmpdir, kml_files[0])
        print(f"📄 Found KML file: {kml_files[0]}")

        # Step 3: Use geopandas to read and convert
        print(f"🌍 Reading KML and converting to GeoJSON...")
        gdf = gpd.read_file(kml_path, driver='KML')
        gdf.to_file(geojson_path, driver='GeoJSON')
        print(f"✅ Conversion successful! GeoJSON saved at: {geojson_path}")

def clean_geojson(input_path, output_path, custom_names=None):
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    cleaned_features = []
    for i, feature in enumerate(data['features']):
        geometry = feature['geometry']

        # Convert MultiPolygon to Polygon (if needed)
        if geometry['type'] == 'MultiPolygon':
            coords = geometry['coordinates'][0]  # Take first polygon in MultiPolygon
        else:
            coords = geometry['coordinates']

        # Remove 3rd dimension (altitude)
        cleaned_coords = [
            [[lon, lat] for lon, lat, *_ in ring] for ring in coords
        ]

        # Assign a clean name
        name = custom_names[i] if custom_names and i < len(custom_names) else f"Area {i + 1}"

        # Create new feature
        new_feature = {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": cleaned_coords
            },
            "properties": {
                "name": name
            }
        }
        cleaned_features.append(new_feature)

    cleaned_geojson = {
        "type": "FeatureCollection",
        "features": cleaned_features
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(cleaned_geojson, f, indent=2)
        print(f"✅ Cleaned GeoJSON saved to: {output_path}")

if __name__ == "__main__":
    # Get script's directory
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # File paths
    input_kmz = os.path.join(script_dir, "Surat Thani Area For Metocean Study and MTA.kmz")
    intermediate_geojson = os.path.join(script_dir, "AIS_output.geojson")
    final_geojson = os.path.join(script_dir, "AIS_cleaned.geojson")

    # Optional: provide clean names
    custom_names = [

    ]

    # Run the process
    try:
        convert_kmz_to_geojson(input_kmz, intermediate_geojson)
        clean_geojson(intermediate_geojson, final_geojson, custom_names)
    except Exception as e:
        print(f"❌ Error: {e}")
