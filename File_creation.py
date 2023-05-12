import pandas as pd
import geopandas as gpd
import shapely
from shapely.geometry import Point
from shapely import wkt, LineString
from typing import Union
from datetime import datetime, timedelta
import re
import numpy as np
import osmnx as ox

def open_file(path: str) -> pd.DataFrame:
    """
    opens csv file as a pandas dataframe
    :param path: path to the csv file
    :return: pandas DataFrame
    """
    return pd.read_csv(path)

def combine_taxi_dfs() -> pd.DataFrame:
    """
    :return: Combined 12 months of taxi trip data into one DataFrame
    """
    dfs = []
    for i in range(1, 13):
        df = pd.read_csv(f'taxi/Yellow_Taxi_Trip_Data_{i}_2018.csv', infer_datetime_format=True)
        dfs.append(df)
    combined = pd.concat(dfs)
    combined_sample = combined.sample(n=200000)
    combined_sample.to_csv('combined_taxi_2018_200k_sample.csv')
    return combined_sample

def format_index(df: pd.DataFrame, new_index_name: str) -> pd.DataFrame:
    """
    Format the index of a pandas dataframe.
    :param df: Pandas dataframe.
    :param new_index_name: Name of the index.
    :return: Pandas dataframe with index.
    """
    df.rename(columns={'Unnamed: 0': new_index_name}, inplace=True)
    df.set_index(new_index_name)
    return df


def keep_relevant_columns(df: pd.DataFrame, column_names: list) -> pd.DataFrame:
    """
    Removes unused columns. Keeps only the columns in the column_names list.
    :param df: Pandas dataframe.
    :param column_names: Column names to keep.
    :return: Pandas dataframe with only the relevant columns.
    """
    df = df[column_names]
    return df


def convert_to_geometry_point(coords: str) -> Union[shapely.Point, shapely.LineString]:
    """
    Converts a coordinates string to a geometry point object.
    :param coords: A string containing the coordinates in the format "(lat, lon)". Either a single coordinate point
        or a LineString with multiple coordinate points.
    :return: A Point or LineString object.
    >>> point = "(40.8018, -73.96108)"
    >>> point_obj = convert_to_geometry_point(point)
    >>> type(point_obj) == Point
    True
    >>> linestring = "LINESTRING (-73.7946273 40.7864093, -73.7930869 40.7869752)"
    >>> line_obj = convert_to_geometry_point(linestring)
    >>> type(line_obj) == LineString
    True
    """
    if coords.startswith('LINESTRING'):
        coords = coords.replace("LINESTRING (", "").replace(")", "")
        coords = [tuple(map(float, c.split())) for c in coords.split(",")]
        multipoint = [(float(lon), float(lat)) for lon, lat in coords]
        geo_point = LineString(multipoint)
    elif type(coords) == str:
        lat, lon = coords.strip("()").split(',')
        geo_point = Point(float(lon), float(lat))
    else:
        raise TypeError('Invalid location type. Must be string or list of coordinates.')
    return geo_point


def borough_match(borough_code: str, borough_name: str) -> bool:
    """
    Matches borough code from closure file to the borough name in taxi zone file.
    :param borough_code: A character representation of a New York borough
    :param borough_name: a string of a New York borough
    :return: True if the code and name refers to the same borough. False if the code and name do not refer to
        the same borough
    >>> match = borough_match('B', 'Brooklyn')
    >>> match
    True
    >>> match = borough_match('S', 'Manhattan')
    >>> match
    False
    """
    if borough_code == 'B' and borough_name == 'Brooklyn':
        return True
    elif borough_code == 'S' and borough_name == 'Staten Island':
        return True
    elif borough_code == 'M' and borough_name == 'Manhattan':
        return True
    elif borough_code == 'Q' and borough_name == 'Queens':
        return True
    elif borough_code == 'X' and borough_name == 'Bronx':
        return True
    else:
        return False


def add_zone_to_crash(df: pd.DataFrame, nyc_geo: gpd.geodataframe) -> gpd.GeoDataFrame:
    """
    Finds the zone corresponding to car crashes.
    :param df: Pandas dataframe with crashes data.
    :param nyc_geo: geopandas dataframe with taxi zone data.
    :return: geopandas dataframe with crash data and zones where the crash occurred.
    """
    crs = 'EPSG:4326'
    df['ZONE'] = [list() for x in range(len(df.index))]
    taxi_zones = nyc_geo.zone
    taxi_zones_boundaries = nyc_geo.geometry
    df['geometry'] = df['LOCATION'].apply(lambda x: convert_to_geometry_point(x))
    data_gdf = gpd.GeoDataFrame(df, geometry='geometry', crs=crs)

    for i, row in data_gdf.iterrows():
        coords = row['geometry']
        for boundary, zone in zip(taxi_zones_boundaries, taxi_zones):
            if boundary.contains(coords):
                data_gdf.at[i, 'ZONE'].append(zone)
                break
    data_gdf.to_csv('Crash_zones.csv', index=True)
    return data_gdf


def add_zone_to_closures(closures, street_geometries, nyc_geo) -> pd.DataFrame:
    """
    Finds the zone corresponding with the coordinates of a road closure. Creates a new
    :param closures: dataframe containing the street closures in New York city in 2018.
    :param street_geometries: dataframe containing the LineStrings representing the streets of New York city.
    :param nyc_geo: geopandas dataframe containing information about taxi zones in New York city.
    :return pandas dataframe with columns for road closure ID and zone where the road closure is.
    """
    # make connector table
    closure_zones = pd.DataFrame(columns=['SEGMENTID', 'ZONE'])

    # fix the coordinates and crs in street_geometries
    crs = 'EPSG:4326'
    street_geometries['geometry'] = street_geometries['geometry'].apply(lambda x: convert_to_geometry_point(x))
    street_geometries = gpd.GeoDataFrame(street_geometries, geometry='geometry', crs=crs)

    # make variables for taxi zone data
    taxi_zones = nyc_geo.zone
    zone_numbers = taxi_zones.index
    zone_borough = nyc_geo.borough
    taxi_zones_boundaries = nyc_geo.geometry
    zone_data = zip(taxi_zones_boundaries, zone_numbers, zone_borough)
    # make dict

    previous_zone = None
    # get unique values for st name and borough, group_by
    #S_Grimsby or tuple
    for i, closure in closures.iterrows():
        #
        street_name = closure['ONSTREETNAME']
        ID = closure['SEGMENTID']
        closure_borough = closure['BOROUGH_CODE']

        # find the geometries of the street
        matching_geometries = street_geometries[street_geometries['name'] == street_name]['geometry']
        geo_found = False
        for geometry in matching_geometries:
            # if geo_found:
            #     break
            for boundary, zone, borough in zone_data:
                # dict makes it fasted cause it looks for key
                # if the coordinates is within the zone boundary
                if boundary.contains(geometry):
                    # check the borough name
                    if not borough_match(closure_borough, borough):
                        break
                    if zone == previous_zone:  # Check if the zone is the same as the previous one
                        break
                    print(zone)
                    closure_zones.loc[len(closure_zones)] = [ID, zone]
                    previous_zone = zone
                    # geo_found = True
                    break
    closure_zones.to_csv('closure_zones.csv', index=True)
    return closure_zones


def crash_file_setup(crash_path, zone_geo):
    """
    Cleans the crash data.
    :param crash_path: path to crash data
    :param zone_geo: geopandas dataframe of taxi zones
    :return: the results of the function add_zone_to_crash. Which is a geopandas dataframe with the crash data and zones
    """
    # open crashes file
    crashes_data = format_index(open_file(crash_path), 'index')
    # remove rows with invalid rows
    crashes_data = crashes_data.loc[(crashes_data['LATITUDE'] >= 40) & (crashes_data['LATITUDE'] <= 41) & (
            crashes_data['LONGITUDE'] >= -74.5) & (crashes_data['LONGITUDE'] <= -73)]
    # remove columns and empty rows
    crashes_data = keep_relevant_columns(crashes_data, ['index', 'CRASH DATE_CRASH TIME', 'LOCATION'])

    crashes_data = crashes_data.dropna()

    return add_zone_to_crash(crashes_data, zone_geo)


def closure_file_setup(closures_path, street_geo_path, zone_geo):
    """
    cleans the closure and street geometries data.
    :param closures_path: path to closures data
    :param street_geo_path: path to street geometries data
    :param zone_geo: geopandas dataframe of taxi zones
    :return: pandas dataframe of street closures and a pandas dataframe of the zones where the closure occurred
    """
    # open file
    street_closures = open_file(closures_path)
    street_geometries = open_file(street_geo_path)

    # Make street names the same in both dataframes
    street_closures['ONSTREETNAME'] = street_closures['ONSTREETNAME'].str.lower()
    street_closures['ONSTREETNAME'] = street_closures['ONSTREETNAME'].str.replace('\s+', ' ', regex=True)
    street_geometries['name'] = street_geometries['name'].str.lower()

    # remove columns and empty rows
    street_closures = keep_relevant_columns(street_closures, ['SEGMENTID', 'ONSTREETNAME', 'WORK_START_DATE',
                                                              'WORK_END_DATE', 'BOROUGH_CODE'])
    street_closures = street_closures.dropna()
    street_closures.to_csv('closures_cleaned.csv', index=True)

    closure_zones = add_zone_to_closures(street_closures, street_geometries, zone_geo)
    return street_closures, closure_zones


def taxi_file_setup(taxi_path):
    """
    cleans the taxi trips data.
    :param taxi_path: path to taxi trip data
    :return: pandas dataframe of taxi trip data
    """
    # open file
    taxi_data = format_index(open_file(taxi_path), 'tripID')

    # remove taxi columns
    taxi_data = keep_relevant_columns(taxi_data,
                                      ['tripID', 'tpep_pickup_datetime', 'tpep_dropoff_datetime', 'trip_distance',
                                       'PULocationID', 'DOLocationID', 'fare_amount', 'tip_amount',
                                       'tolls_amount', 'total_amount'])
    return taxi_data


def events_during_trips(trips_df: pd.DataFrame, crashes_df: pd.DataFrame, closures_df: pd.DataFrame, closure_zones_df: pd.DataFrame) -> list:
    """
    Finds the number of events which occurred at within an hour time interval and same zone as a taxi trip
    :param trips_df: pandas dataframe of taxi trips data
    :param crashes_df: pandas dataframe of car crashes data
    :param closures_df: pandas dataframe of road closure data
    :param closure_zones_df: pandas dataframe of road closure zones data
    :return: a list containing dictuinaries of each trip ID, the number of crashes passed, and the number of road closures passed.
    >>> trips = pd.DataFrame({
    ...     'tripID': [1, 2],
    ...     'PULocationID': [10, 20],
    ...     'DOLocationID': [15, 25],
    ...     'tpep_pickup_datetime': [datetime(2023, 5, 1, 10, 0), datetime(2023, 5, 1, 11, 0)],
    ...     'tpep_dropoff_datetime': [datetime(2023, 5, 1, 10, 30), datetime(2023, 5, 1, 11, 30)]
    ... })
    >>> crash = pd.DataFrame({
    ...     'ZONE': [10, 20, 30],
    ...     'CRASH DATE_CRASH TIME': [datetime(2023, 5, 1, 9, 45), datetime(2023, 5, 1, 10, 15), datetime(2023, 5, 1, 11, 10)]
    ... })
    >>> close = pd.DataFrame({
    ...     'SEGMENTID': [100, 200],
    ...     'WORK_START_DATE': [datetime(2023, 5, 1, 9, 0), datetime(2023, 5, 1, 10, 30)],
    ...     'WORK_END_DATE': [datetime(2023, 5, 1, 10, 0), datetime(2023, 5, 1, 11, 0)]
    ... })
    >>> close_zone = pd.DataFrame({
    ...     'ZONE': [10, 20],
    ...     'SEGMENTID': [100, 200]
    ... })
    >>> events_during_trips(trips, crash, close, close_zone)
    [{'tripID': 1, 'num_of_crashes_passed': 1, 'num_of_road_closures_passed': 1}, {'tripID': 2, 'num_of_crashes_passed': 0, 'num_of_road_closures_passed': 1}]
    """
    events_encountered = []
    for index, trip in trips_df.iterrows():
        events_passed = {'tripID': trip['tripID'], 'num_of_crashes_passed': 0, 'num_of_road_closures_passed': 0}

        zone1 = trip["PULocationID"]
        zone2 = trip["DOLocationID"]
        pick_time = trip["tpep_pickup_datetime"]
        drop_time = trip["tpep_dropoff_datetime"]
        time_window = timedelta(minutes=30)

        rows_with_zone_and_time_crashes = crashes_df.loc[((crashes_df["ZONE"] == zone1) | (crashes_df["ZONE"] == zone2)) &
                                                 (crashes_df["CRASH DATE_CRASH TIME"] >= pick_time - time_window) &
                                                 (crashes_df["CRASH DATE_CRASH TIME"] <= drop_time + time_window)]
        events_passed["num_of_crashes_passed"] = len(rows_with_zone_and_time_crashes)

        rows_with_time_closures = closures_df.loc[(closures_df["WORK_START_DATE"] <= pick_time) &
                                                  (pick_time <= closures_df["WORK_END_DATE"])]
        rows_with_zone_closures = closure_zones_df.loc[((closure_zones_df["ZONE"] == zone1) |
                                                        (closure_zones_df["ZONE"] == zone2))]
        # get unique segment IDs
        rows_with_zone_closures = rows_with_zone_closures.drop_duplicates(subset=["SEGMENTID", "ZONE"])
        # find rows with same segmentID and timeframe
        rows_with_zone_and_time_collisions = pd.merge(rows_with_time_closures, rows_with_zone_closures,
                                                      on="SEGMENTID", how="inner")
        events_passed["num_of_road_closures_passed"] = len(rows_with_zone_and_time_collisions)

        events_encountered.append(events_passed)
    return events_encountered


def street_geometries():
    """
    creates a csv file containing the geometries of street in New York city.
    """
    g = ox.graph_from_place('NYC, NY, USA', network_type='drive')
    nyc = ox.graph_to_gdfs(g, nodes=False, edges=True, node_geometry=False, fill_edge_geometry=False)
    nyc = nyc[~nyc['name'].apply(lambda x: isinstance(x, list))]

    def remove_suffix(name: str) -> Union[str, np.nan]:
        """
        Removes the suffix from street name.
        :param name: The name of street.
        :return: returns a numpy nan or a the name of the street with no suffix
        """
        # check if value is a string
        if isinstance(name, str):
            # apply regular expression to remove suffix
            return re.sub(r'(?<=\d)(st|nd|rd|th)\b', '', name)
        # if value is not a string or is NaN, return NaN
        else:
            return np.nan

    # apply function to 'name' column and overwrite existing values
    nyc['name'] = nyc['name'].apply(remove_suffix)
    nyc[['name', 'geometry']].dropna().to_csv('street_geometries.csv')