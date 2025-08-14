import requests
import json
import pandas as pd

# 1. Set API endpoint and authentication
BASE_URL = "https://api.kpler.marinetraffic.com/v2/vessels/graphql"
API_KEY = "RTZCQWF2ZHJpWWVheXJZTmZIenFNRXFzZTQzdDNaUEQ6MU1vZ0dqWUQtZHFMMXNTMnNER21CZzNzSjcyUUdzQ0hfSHBFWlFRTk9pT2NwVWpzeF9TclZ0QzNvU0NwMlJpQg=="  # <-- Replace with your actual API key

def fetch_vessels(after_cursor=None):
    query = f"""
    query Vessels {{
        vessels(
            first: 1000
            where: {{
                 filters: [
                    {{
                        field: "identifier.mmsi"
                        op: IN
                        values: ["261010170", "636020532", "209313000", "230643000", "305201000", "314545000", "636018385", "275523000", "563226500", "210586000", "261011140", "636018491", "305287000", "244874000", "255806370", "209956000", "255806436", "305773000", "305576000", "314261000", "211286440", "305313000", "246924000", "477759600", "209525000"]
                    }}
                 ]
                # operator: OR
            }}
            after: {json.dumps(after_cursor)}
        ) {{
            nodes {{
                identifier {{
                    imo
                    mmsi
                    callSign
                    eni
                    shipId
                }}
                management {{
                    beneficialOwner {{ current {{ name country address website startDate }} }}
                    registeredOwner {{ current {{ name country address website startDate }} }}
                    commercialManager {{ current {{ name country address website startDate }} }}
                    operator {{ current {{ name country address website startDate }} }}
                    technicalManager {{ current {{ name country address website startDate }} }}
                    ismManager {{ current {{ name country address website startDate }} }}
                }}
                associatedCompanies {{
                    shipBuilder {{ current {{ name country address website startDate }} }}
                    engineBuilder {{ current {{ name country address website startDate }} }}
                    classificationSociety {{ current {{ name country address website startDate }} }}
                    piClub {{ current {{ name country address website startDate }} }}
                }}
                particulars {{
                    general {{
                        name
                        commercialFleet
                        generalVesselType
                        detailedVesselType
                        serviceStatus
                        flag
                        portOfRegistry
                        keelLaidDate
                    }}
                    hull {{
                        yearOfBuild
                        yardNumber
                        hullMaterial
                        hullType
                        decks
                    }}
                    aisTransceiver {{
                        lengthFore
                        lengthAft
                        widthLeft
                        widthRight
                        aisTransceiverClass
                    }}
                    dimension {{
                        lengthOverall
                        lengthBetweenPerpendiculars
                        breadthExtreme
                        breadthMoulded
                        draught
                        depth
                        freeboard
                    }}
                    tonnage {{
                        grossTonnage
                        deadweightTonnage
                        netTonnage
                        loadedDisplacementTonnage
                        lightDisplacementTonnage
                    }}
                    capacity {{
                        liquidCapacity
                        gasCapacity
                        baleCapacity
                        grainCapacity
                        teuCapacity
                        ceuCapacity
                        passengerCapacity
                        ballastCapacity
                    }}
                    engine {{
                        enginePower
                        engineUnits
                        engineCylinderUnits
                        engineBore
                        engineStroke
                        engineRpm
                        engineType
                        speedService
                        propeller
                    }}
                    fuel {{
                        mainEngineFuelType
                        fuelCapacity
                    }}
                }}
            }}
            pageInfo {{
                hasNextPage
                endCursor
            }}
        }}
    }}
    """

    headers = {
        "Authorization": f"Basic {API_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.post(BASE_URL, json={"query": query}, headers=headers)

    if response.status_code != 200:
        print(f"Error {response.status_code}: {response.text}")
        return None

    return response.json()

# Fetch and normalize all paginated data
all_nodes = []
data = fetch_vessels()

if data and "data" in data and "vessels" in data["data"]:
    print("Success! API Response:")
    nodes = data["data"]["vessels"]["nodes"]
    all_nodes.extend(nodes)

    # Pagination
    while data["data"]["vessels"]["pageInfo"]["hasNextPage"]:
        next_cursor = data["data"]["vessels"]["pageInfo"]["endCursor"]
        print("\nFetching next page...")
        data = fetch_vessels(after_cursor=next_cursor)
        if data and "data" in data and "vessels" in data["data"]:
            nodes = data["data"]["vessels"]["nodes"]
            all_nodes.extend(nodes)
        else:
            print("No more data or error fetching page.")
            break

    # Normalize and save to CSV
    if all_nodes:
        df = pd.json_normalize(all_nodes)
        df.to_csv("kpler_vessels_output.csv", index=False)
        print(f"\nData normalized and saved to kpler_vessels_output.csv with {len(df)} rows and {len(df.columns)} columns.")
    else:
        print("No vessel data found.")
else:
    print("Initial fetch failed or no data returned.")