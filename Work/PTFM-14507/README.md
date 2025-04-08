API/ Dataset Creation Tracking a fleet with port call events


Context: 

Similarly to what we created for the live db here: PTFM-13784: LIVE DB DE SAMPLE: Creating a Fleet by Beneficial Owner and Matching Live Position Data
Done
 
We need a developer-focused business case focusing on API showing how to:

Define a fleet based on a specific vessel attribute

Retrieve and integrate this fleet’s live positions using the API.

Retrieve historical vessel activity (last 6 months) via the API, including:

Add Port call events

Acceptance Criteria
1. Fleet Creation and Filtering
Use the API to filter and retrieve all vessels where REGISTER_OWNER = PETROLEOS DE VENEZUELA SA.

2. Live Position Matching
Join the fleet with the live position API.

Plot all active vessels on a live map (marker view).

3. Historical Position Analysis
Retrieve 6 months of historical positions from the API.

Plot vessel movements on a heat map to show density/activity.

4. Port Call Event Integration
Query the port call API for the same vessels and period.

Visualize:

A timeline or sequence of events

Possibly annotate the map with port stop markers.

Include the port names and timestamps in a separate table or tooltip.