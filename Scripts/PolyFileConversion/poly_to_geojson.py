import os
import zipfile
import tempfile
import geopandas as gpd
import xml.etree.ElementTree as ET
import json

def convert_kmz_to_geojson(kmz_path, geojson_path):
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"📦 Extracting {kmz_path} to temporary directory...")
        with zipfile.ZipFile(kmz_path, 'r') as kmz:
            kmz.extractall(tmpdir)
        kml_files = [f for f in os.listdir(tmpdir) if f.endswith('.kml')]
        if not kml_files:
            raise FileNotFoundError("No .kml file found inside the .kmz archive.")
        kml_path = os.path.join(tmpdir, kml_files[0])
        print(f"📄 Found KML file: {kml_files[0]}")
        print(f"🌍 Reading KML and converting to GeoJSON...")
        gdf = gpd.read_file(kml_path, driver='KML')
        gdf.to_file(geojson_path, driver='GeoJSON')
        print(f"✅ Conversion successful! GeoJSON saved at: {geojson_path}")

def convert_kml_to_geojson(kml_path, geojson_path):
    print(f"🌍 Reading KML and converting to GeoJSON...")
    gdf = gpd.read_file(kml_path, driver='KML')
    gdf.to_file(geojson_path, driver='GeoJSON')
    print(f"✅ Conversion successful! GeoJSON saved at: {geojson_path}")

def convert_gml_xml_to_geojson(xml_path, geojson_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    ns = {
        'gml': 'http://www.opengis.net/gml',
        'ogc': 'http://www.opengis.net/ogc'
    }
    features = []
    for i, poslist in enumerate(root.findall('.//gml:posList', ns)):
        coords_text = poslist.text.strip()
        coords_split = coords_text.split()
        coords = []
        for j in range(0, len(coords_split), 2):
            lon = float(coords_split[j])
            lat = float(coords_split[j+1])
            coords.append([lon, lat])
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [coords]
            },
            "properties": {
                "name": f"Polygon {i+1}"
            }
        })
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    with open(geojson_path, 'w', encoding='utf-8') as f:
        json.dump(geojson, f, indent=2)
        print(f"✅ GeoJSON saved to: {geojson_path}")

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    files = os.listdir(script_dir)
    candidates = [f for f in files if f.lower().endswith(('.kmz', '.kml', '.xml'))]

    if not candidates:
        print("❌ No .kmz, .kml, or .xml files found in the script directory.")
        return

    print("Found the following files:")
    for idx, fname in enumerate(candidates):
        print(f"{idx+1}. {fname}")

    if len(candidates) == 1:
        choice = 0
    else:
        try:
            choice = int(input("Select a file to convert (number): ")) - 1
            if not (0 <= choice < len(candidates)):
                print("Invalid selection.")
                return
        except Exception:
            print("Invalid input.")
            return

    selected_file = candidates[choice]
    input_path = os.path.join(script_dir, selected_file)
    base_name = os.path.splitext(selected_file)[0]
    geojson_path = os.path.join(script_dir, f"{base_name}.geojson")

    ext = selected_file.lower().split('.')[-1]
    try:
        if ext == 'kmz':
            convert_kmz_to_geojson(input_path, geojson_path)
        elif ext == 'kml':
            convert_kml_to_geojson(input_path, geojson_path)
        elif ext == 'xml':
            convert_gml_xml_to_geojson(input_path, geojson_path)
        else:
            print("❌ Unsupported file type.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()