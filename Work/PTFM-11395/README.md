Polygon Split


Context:
It has been requested multiple times by clients how to split poligons. this work will be part of our data samples creation enrichment 

Specifications

Python algorithm to subdivide a polygon boundaries into smaller bounding boxes given follow condition:

ABS((MAXLAT - MINLAT) + (MAXLON - MINLON)) <= VALUE

Purpose is to divided into small coordinates to facilitate requests and data processing 

Vessel Historical Positions in an Area has a restriction of area size where The absolute value of coordinates has to be equal to or less than 2. This is a complex point of implementation for the client and a recurrent need for handle areas as well

Acceptance criteria:

Clear comments and placeholders should be included to indicate where customers need to input specific parameters and configurations. ( like the day we want to explore)