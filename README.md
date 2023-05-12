# The Effect of Traffic Events on NYC Taxi Trips
## Tali Zacks and Raghid Alhazmy

## Original Data Files:
### Taxi trips:
- Downloaded from: 
https://data.cityofnewyork.us/Transportation/2018-Yellow-Taxi-Trip-Data/t29m-gskq/ 
- 12 files (1 for each month) exists in taxi.zip
- Unzip file and run combine_taxi_dfs in File_creation.py to sample 50,000 taxi trips from each month, combine the DataFrames, and save the result as a csv
- New file will be saved as: 
  - combined_taxi_2018_200k_sample.csv

### Collisions:
- Downloaded from:
https://data.cityofnewyork.us/Public-Safety/Motor-Vehicle-Collisions-Crashes/h9gi-nx95/
- Filtered to include collisions from only 2018 
- Path: 
  - 2018_crashes.csv

### Street Closures:
- Downloaded from:
https://data.cityofnewyork.us/Transportation/Street-Closures-due-to-construction-activities-by-/i6b5-j7bu
- Filtered to include street closures from only 2018
- Path:
  - 2018_street_closures.csv

### NYC Taxi Zones:
- Downloaded from:
https://data.cityofnewyork.us/Transportation/NYC-Taxi-Zones/d3c5-ddgc
- Path:
  - NYC_Taxi_Zones.geojson

### Street Geometries:
- Obtained from osmnx
- To save file:
  - Run street_geometries() from File_creation.py

## Required Python Packages:
- osmnx
- pandas
- geopandas
- matplotlib
- shapely
- datetime
- typing
- ipywidgets
- numpy
- networkx
- re

## Process:
In main.py:

- To setup final crash file, uncomment:
```crashes = fc.crash_file_setup("2018_crashes.csv", nyc_taxi_geo)```
  - New file: Crash_zones.csv
  - This will call crash_file_setup(), which in turns call add_zone_to_crash().
    - Add_zone_to_crash() will go through the crash coordinates and find the taxi zone where they occurred.
    - Computationally intensive.
- To setup final closure file, uncomment:
```closures, closure_zones = fc.closure_file_setup("2018_street_closures.csv", "street_geometries.csv", nyc_taxi_geo)```
  - New file: closures_cleaned.csv
  - This will call closure_file_setup(), which in turn calls add_zone_to_closures().
    - add_zone_to_closures() will go through the crash coordinates and find the taxi zone(s) where they occurred.
    - Computationally intensive.
- The resulting files are already present in the GitHub.

- fc.events_during_trips() goes through all the taxi trips and creates a dictionary with the trip ID as the key.
  - The values of the dictionary are dictionaries with the number of crashes and the number of collisions that occurred during and near the trip.

- clusters_df creates a pandas dataframe which groups crashes and the date of the crash to show that a car crash leads to more car crashes.

- Analysis of traffic events' effect on taxi trips
  - 
