import pandas as pd
import geopandas as gpd
import shapely
from geopandas import GeoDataFrame
from shapely.geometry import Point
from shapely import wkt, LineString
from typing import Union

def open_file(path: str) -> pd.DataFrame:
    """
    opens csv file as a pandas dataframe
    :param path: path to the csv file
    :return: pandas DataFrame
    """
    return pd.read_csv(path)


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

    :param df:
    :param nyc_geo:
    :return:
    """
    crs = 'EPSG:4326'
    # make a column called 'ZONE' with an empty list
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

    return data_gdf


def add_zone_to_closures(closures, street_geometries, nyc_geo):
    """
    Finds the zone corresponding with the coordinates of a road closure
    :param closures: dataframe containing the street closures in New York city in 2018.
    :param street_geometries: dataframe containing the LineStrings representing the streets of New York city.
    :param nyc_geo: geopandas dataframe containing information about taxi zones in New York city.
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

    :param crash_path:
    :param zone_geo:
    :return:
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


def closure_file_setup(collision_path, street_geo_path, zone_geo):
    """

    :param collision_path:
    :param street_geo_path:
    :param zone_geo:
    :return:
    """
    # open file
    street_closures = open_file(collision_path)
    street_geometries = open_file(street_geo_path)

    # Make street names the same in both dataframes
    street_closures['ONSTREETNAME'] = street_closures['ONSTREETNAME'].str.lower()
    street_closures['ONSTREETNAME'] = street_closures['ONSTREETNAME'].str.replace('\s+', ' ', regex=True)
    street_geometries['name'] = street_geometries['name'].str.lower()

    # remove columns and empty rows
    street_closures = keep_relevant_columns(street_closures, ['SEGMENTID', 'ONSTREETNAME', 'WORK_START_DATE',
                                                              'WORK_END_DATE', 'BOROUGH_CODE', 'geometry'])
    street_closures = street_closures.dropna()

    closure_zones = add_zone_to_closures(street_closures, street_geometries, zone_geo)
    return street_closures, closure_zones


def taxi_file_setup(taxi_path):
    """

    :param taxi_path:
    :return:
    """
    # open file
    taxi_data = format_index(open_file(taxi_path), 'tripID')

    # remove taxi columns
    taxi_data = keep_relevant_columns(taxi_data,
                                      ['tripID', 'tpep_pickup_datetime', 'tpep_dropoff_datetime', 'trip_distance',
                                       'PULocationID', 'DOLocationID', 'fare_amount', 'tip_amount',
                                       'tolls_amount', 'total_amount'])
    return taxi_data
