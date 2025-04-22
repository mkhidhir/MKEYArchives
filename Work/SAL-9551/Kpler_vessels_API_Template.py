import requests
import json

# - 1. Set API endpoint and authentication
BASE_URL = "https://api.kpler.marinetraffic.com/v2/vessels/graphql"
API_KEY = ""  # <-- Replace with your actual API key

# - 2. Fetch vessel data with pagination
def fetch_vessels(after_cursor=None):
    # - 3. Define GraphQL query: you can comment out some of the sections to include more fields in the response.
    query = f"""
    query Vessels {{
        vessels(
            first: 1000  # Number of records per page, max value is 1000
            where: {{
                filters: [
                    {{
                        field: "identifier.imo"
                        op: IN
                        values: ["9431214", "9443401", "9862475", "9709025", "9762261", "9830898", "9830903", "9645736", "9750713", "9271248", "9853137", "9877145", "9256614", "9831684"]
                    }}
                   # {{
                   #     field: "identifier.mmsi"
                   #     op: EQ
                   #    values: ["9172571"]
                   # }}
                   # {{
                   #     field: "management.beneficialOwner.current.name"
                   #     op: LIKE
                   #     values: ["AASEN SHIPPING%"]
                   # }}
                ]
                operator: OR   # To combine multiple filters, use OR or AND
            }}
            after: {json.dumps(after_cursor)}  # Dynamically add cursor for pagination
        ) {{
            nodes {{

                ### Identifier - (Un)comment fields below to include/exclude them from the response
                identifier {{
                    imo
                    mmsi
                    callSign
                    eni
                    shipId
                }}

                ### Management - (Un)comment fields below to include/exclude them from the response
                management {{
                    beneficialOwner {{ current {{ name country address website startDate }} }}
                    registeredOwner {{ current {{ name country address website startDate }} }}
                    commercialManager {{ current {{ name country address website startDate }} }}
                    operator {{ current {{ name country address website startDate }} }}
                    technicalManager {{ current {{ name country address website startDate }} }}
                    ismManager {{ current {{ name country address website startDate }} }}
                }}

                ### Associated Companies - (Un)comment fields below to include/exclude them from the response
                # associatedCompanies {{
                #     shipBuilder {{ current {{ name country address website startDate }} }}
                #     engineBuilder {{ current {{ name country address website startDate }} }}
                #     classificationSociety {{ current {{ name country address website startDate }} }}
                #     piClub {{ current {{ name country address website startDate }} }}
                # }}

                ### Vessel Particulars - (Un)comment fields below to include/exclude them from the response
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
                    # hull {{
                    #     yearOfBuild
                    #     yardNumber
                    #     hullMaterial
                    #     hullType
                    #     decks
                    # }}
                    # aisTransceiver {{
                    #     lengthFore
                    #     lengthAft
                    #     widthLeft
                    #     widthRight
                    #     aisTransceiverClass
                    # }}
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
                    # capacity {{
                    #     liquidCapacity
                    #     gasCapacity
                    #     baleCapacity
                    #     grainCapacity
                    #     teuCapacity
                    #     ceuCapacity
                    #     passengerCapacity
                    #     ballastCapacity
                    # }}
                    # engine {{
                    #     enginePower
                    #     engineUnits
                    #     engineCylinderUnits
                    #     engineBore
                    #     engineStroke
                    #     engineRpm
                    #     engineType
                    #     speedService
                    #     propeller
                    # }}
                    # fuel {{
                    #     mainEngineFuelType
                    #     fuelCapacity
                    # }}
                }}
            }}

            # Pagination Info
            pageInfo {{
                hasNextPage
                endCursor
            }}
        }}
    }}
    """

    # - 4. Set up HTTP headers for authentication
    headers = {
        "Authorization": f"Basic {API_KEY}",
        "Content-Type": "application/json"
    }

    # - 5. Send the request 
    response = requests.post(BASE_URL, json={"query": query}, headers=headers)

    # - 6. Handle errors
    if response.status_code != 200:
        print(f"Error {response.status_code}: {response.text}")
        return None

    # - 7. Return formatted JSON response
    return response.json()

# - 8. Fetch first page
data = fetch_vessels()

# - 9. Display formatted JSON output
if data:
    print("Success! API Response:")
    print(json.dumps(data, indent=2))  # Pretty-print JSON

    # - 10. Handle pagination (automatically fetch additional pages)
    while data["data"]["vessels"]["pageInfo"]["hasNextPage"]:
        next_cursor = data["data"]["vessels"]["pageInfo"]["endCursor"]
        print("\n Fetching next page...")
        data = fetch_vessels(after_cursor=next_cursor)
        print(json.dumps(data, indent=2))  # Pretty-print subsequent pages
