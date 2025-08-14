import os
import xml.etree.ElementTree as ET
import json

def convert_gml_xml_to_geojson(xml_filename, geojson_filename):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    xml_path = os.path.join(script_dir, xml_filename)
    geojson_path = os.path.join(script_dir, geojson_filename)

    tree = ET.parse(xml_path)
    root = tree.getroot()

    # Register namespaces for GML and OGC
    ns = {
        'gml': 'http://www.opengis.net/gml',
        'ogc': 'http://www.opengis.net/ogc'
    }

    features = []
    # Find all polygons in the XML
    for i, poslist in enumerate(root.findall('.//gml:posList', ns)):
        coords_text = poslist.text.strip()
        coords_split = coords_text.split()
        # GML posList is a flat list: lon lat lon lat ...
        coords = []
        for j in range(0, len(coords_split), 2):
            lon = float(coords_split[j])
            lat = float(coords_split[j+1])
            coords.append([lon, lat])
        # GeoJSON expects a list of linear rings (first is outer boundary)
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

if __name__ == "__main__":
    # Place your XML file in the same directory as this script and name it 'input.xml'
    convert_gml_xml_to_geojson("japan.xml", "output.geojson")