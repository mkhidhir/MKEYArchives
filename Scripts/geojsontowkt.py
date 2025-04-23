import json
import sys
import os
import re

def geojson_to_wkt(input_folder, output_folder, sql_output_folder):
    if not os.path.exists(input_folder):
        print(f"Input folder not found: {input_folder}")
        sys.exit(1)

    for folder in [output_folder, sql_output_folder]:
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f"Created folder: {folder}")

    geojson_files = [f for f in os.listdir(input_folder) if f.endswith(".geojson")]

    if not geojson_files:
        print("No GeoJSON files found in the input folder.")
        sys.exit(1)

    for filename in geojson_files:
        input_path = os.path.join(input_folder, filename)
        wkt_output_path = os.path.join(output_folder, filename.replace(".geojson", ".wkt"))
        sql_output_path = os.path.join(sql_output_folder, filename.replace(".geojson", ".sql"))

        try:
            with open(input_path, 'r') as f:
                geojson_data = json.load(f)
            print(f"Processing file: {input_path}")
        except Exception as e:
            print(f"Error reading {input_path}: {e}")
            continue

        wkt_polygons = []

        for feature in geojson_data.get('features', []):
            geometry = feature.get('geometry', {})
            geo_type = geometry.get('type')
            coordinates = geometry.get('coordinates')

            if not isinstance(coordinates, list):
                print(f"Invalid coordinates in {input_path}")
                continue

            if geo_type == 'Polygon':
                polygons = [coordinates]
            elif geo_type == 'MultiPolygon':
                polygons = coordinates
            else:
                print(f"Unsupported geometry type '{geo_type}' in {input_path}")
                continue

            for polygon in polygons:
                try:
                    if not all(isinstance(point, list) and len(point) == 2 for point in polygon[0]):
                        print(f"Invalid polygon structure in {input_path}")
                        continue

                    # Convert to WKT format
                    wkt_polygon = 'POLYGON((' + ', '.join(f"{lng} {lat}" for lng, lat in polygon[0]) + '))'
                    wkt_polygons.append((wkt_polygon, polygon[0]))

                except Exception as e:
                    print(f"Error processing polygon in {input_path}: {e}")
                    continue

        if not wkt_polygons:
            print(f"No valid polygons found in {input_path}")
            continue

        try:
            with open(wkt_output_path, 'w') as f:
                f.write("\n".join(wkt for wkt, _ in wkt_polygons))
            print(f"Converted: {input_path} -> {wkt_output_path}")
        except Exception as e:
            print(f"Error writing WKT to {wkt_output_path}: {e}")

        # SQL Template
        sql_content = """
DROP TABLE IF EXISTS arch_tmpx..[SpatialTableSAL9512];

IF OBJECT_ID(N'arch_tmpx..[SpatialTableSAL9512]', N'U') IS NULL
    CREATE TABLE arch_tmpx..SpatialTableSAL9512
        (   id int IDENTITY (1,1),
            id_origin int,
            spat_name VARCHAR(50),
            x_min_lng real,
            y_min_lat real,
            x_max_lng real,
            y_max_lat real,
            TIMEZONE smallint,
            GeogCol1 geography,   
            GeogCol2 AS GeogCol1.STAsText(),
            PRIMARY KEY (id)
        );

"""

        # Helper function: Calculate bounding box for each polygon
        def get_bounding_box(coords):
            lngs, lats = zip(*coords)
            return min(lngs), min(lats), max(lngs), max(lats)

        insert_statements = []

        for idx, (wkt, coords) in enumerate(wkt_polygons, start=1):
            try:
                min_lng, min_lat, max_lng, max_lat = get_bounding_box(coords)
                insert_statements.append(
                    f"({idx}, {min_lng}, {min_lat}, {max_lng}, {max_lat}, geography::STGeomFromText('{wkt}', 4326))"
                )
            except Exception as e:
                print(f"Error calculating bounding box: {e}")

        if insert_statements:
            sql_content += "INSERT INTO arch_tmpx..SpatialTableSAL9512 (id_origin, x_min_lng, y_min_lat, x_max_lng, y_max_lat, GeogCol1) \nVALUES \n" + ",\n".join(insert_statements) + ";\n"

        sql_content += """
UPDATE arch_tmpx..SpatialTableSAL9512 SET GeogCol1 = GeogCol1.MakeValid() WHERE GeogCol1.STIsValid() = 0;
UPDATE arch_tmpx..SpatialTableSAL9512 SET GeogCol1 = GeogCol1.ReorientObject() WHERE GeogCol1.EnvelopeAngle() >= 180;

SELECT * FROM arch_tmpx..SpatialTableSAL9512;
"""

        try:
            with open(sql_output_path, 'w') as f:
                f.write(sql_content)
            print(f"SQL script generated: {sql_output_path}")

        except Exception as e:
            print(f"Error writing SQL file: {e}")

if __name__ == "__main__":
    print("Welcome to GeoJSON to WKT & SQL Converter")

    input_folder = "C:/output/input"
    output_folder = "C:/output/output"
    sql_output_folder = "C:/output/output"

    print(f"Starting conversion from: {input_folder} to {output_folder} and {sql_output_folder}")
    geojson_to_wkt(input_folder, output_folder, sql_output_folder)
    print("Conversion process completed.")
