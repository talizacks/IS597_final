# import Vis
import pandas as pd
import geopandas as gpd
import numpy as np
from geopandas import GeoDataFrame
from shapely.geometry import Point
from shapely import wkt, LineString
import folium



def open_file(path: str) -> pd.DataFrame:
    """

    :param path:
    :return: pandas DataFrame
    """
    return pd.read_csv(path)


def format_index(df: pd.DataFrame, new_index_name: str) -> pd.DataFrame:
    df.rename(columns={'Unnamed: 0': new_index_name}, inplace=True)
    df.set_index(new_index_name)
    return df


def keep_relevant_columns(df: pd.DataFrame, column_names: list) -> pd.DataFrame:
    """

    :param df:
    :param column_names:
    :return:
    """
    df = df[column_names]
    return df

def find_neighbors(gdf: gpd.GeoDataFrame) -> dict:
    """
    :param zones: taxi zones
    :return: dictionary with format:
    {zone1:[neighbor1,neighbor2,...], zone2:[neighbor1,neighbor2,...], ...}

    Reference:
    https://gis.stackexchange.com/questions/281652/finding-all-neighbors-using-geopandas

    """
    neighbor_dict = {}
    for index, zone in gdf.iterrows():
        # get 'not disjoint' countries
        neighbors = gdf[~gdf.geometry.disjoint(zone.geometry)].objectid.tolist()

        # remove own zone number from the list
        neighbors = [int(num) for num in neighbors if zone.objectid != num]

        #add zone neighbors to neighbor dictionary
        neighbor_dict[index + 1] = neighbors

    return neighbor_dict

def filter_trips_based_on_zones(df:pd.DataFrame, neighbor_dict: dict):
    """

    :param df:
    :param neighbor_dict:
    :return:
    """
    trips_zones_dict = {}
    # keep only trips that have PO and DO zones that aren't above 263
    limit_mask = (df['PULocationID'] < 264) & (df['DOLocationID'] < 264)

    # Find zones with no neighbors
    dont_include = []
    for x in neighbor_dict:
        if neighbor_dict[x] == []:
            dont_include.append(x)

    # create mask to remove trips that start or end in a zone without neighbors
    no_neighbors_mask = (~df['PULocationID'].isin(dont_include)) & (~df['DOLocationID'].isin(dont_include))

    # apply masks
    trips_df = df[limit_mask]
    trips_df = trips_df[no_neighbors_mask]

    for index, trip in trips_df.iterrows():

        PUzone = trip['PULocationID']

        PUzone_neighbor_neighbors = []
        PUzone_neighbors = neighbor_dict[PUzone]
        PUzone_neighbor_neighbors.append(PUzone_neighbors)

        for i in PUzone_neighbors:
            PUzone_neighbor_neighbors.append(neighbor_dict[i])

        PUzone_neighbor_neighbors = [int(x) for x in list(np.concatenate(PUzone_neighbor_neighbors).flat)]

        trips_zones_dict[trip['tripID']] = set(PUzone_neighbor_neighbors)
    exclude = []
    for x in trips_df.iterrows():
        tripID = x[1][0]
        PUzone = x[1][8]
        DOzone = x[1][9]
        # print(PUzone,DOzone)
        if DOzone not in (trips_zones_dict[tripID]):
            # print(tripID)
            exclude.append(tripID)
    trips_df = trips_df[~trips_df['tripID'].isin(exclude)]
    return trips_df
def datetime_conversions(df: pd.DataFrame, column_names: list, time_format: str) -> pd.DataFrame:
    """

    :return:
    """
    for column in column_names:
        df[column] = pd.to_datetime(df[column], format=time_format)
    return df


def add_time_and_speed(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates the trip time and average speed of a taxi trip and creates two columns in the taxi dataframe
     to store the data
    :param df: taxi pandas dataframe
    :return: The taxi dataframe with trip_time_h and avg speed columns
    """
    df['trip_time'] = (df['tpep_dropoff_datetime'] - df['tpep_pickup_datetime'])

    df['trip_time_h'] = [(x.total_seconds()) / 3600 for x in df['trip_time']]
    df['avg speed'] = df['trip_distance'] / df['trip_time_h']
    return df


def removeWeirdTaxiData(df: pd.DataFrame) -> pd.DataFrame:
    """

    :return:
    """
    too_quick = df['trip_time_h'] >= 0.01666666667
    too_long = df['trip_time_h'] <= 24
    super_fast = df['avg speed'] <= 90
    super_slow = df['avg speed'] >= 1
    df = df[too_quick]
    df = df[too_long]
    df = df[super_fast]
    df = df[super_slow]

    return df


def convert_to_geometry_point(coords):
    """
    Converts a series of strings to a geometry point object
    :param coords: A string containing the coordinates in the format "(lat, lon)"
    :return: A Point object with the specified coordinates and CRS
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


def add_zone_to_event(df, nyc_geo, col_name):
    # get zone from coordinates
    # https://geopandas.org/en/stable/docs/reference/geoseries.html
    crs = 'EPSG:4326'
    # make a column called 'ZONE' with an empty list
    df['ZONE'] = [list() for x in range(len(df.index))]
    taxi_zones = nyc_geo.zone
    taxi_zones_boundaries = nyc_geo.geometry
    df['geometry'] = df[col_name].apply(lambda x: convert_to_geometry_point(x))
    data_gdf = gpd.GeoDataFrame(df, geometry='geometry', crs=crs)
    for i, row in data_gdf.iterrows():
        coords = row['geometry']
        for boundary, zone in zip(taxi_zones_boundaries, taxi_zones):
            if boundary.contains(coords):
                data_gdf.at[i, 'ZONE'].append(zone)
                break
    #vectorize later

    return data_gdf


if __name__ == '__main__':
    # open file
    taxi_data = format_index(open_file("sampled_combined_taxi_2018_600k.csv"),'tripID')

    # remove taxi columns
    taxi_data = keep_relevant_columns(taxi_data, ['tripID','tpep_pickup_datetime', 'tpep_dropoff_datetime', 'trip_distance',
                                                  'PULocationID', 'DOLocationID', 'fare_amount', 'tip_amount',
                                                  'tolls_amount', 'total_amount'])
    # datetime_conversions
    taxi_data = datetime_conversions(taxi_data, ['tpep_pickup_datetime', 'tpep_dropoff_datetime'],
                                     '%m/%d/%Y %I:%M:%S %p')
    taxi_data = add_time_and_speed(taxi_data)


    # neighbors and zones
    nyc_taxi_geo = gpd.read_file('NYC_Taxi_Zones.geojson')
    neighbors = find_neighbors(nyc_taxi_geo)
    # taxi_data = filter_trips_based_on_zones(taxi_data, neighbors)


    # open crashes file
    crashes_data = format_index(open_file("2018_crashes.csv"), 'index')
    # remove rows with invalid rows
    crashes_data = crashes_data.loc[(crashes_data['LATITUDE'] >= 40) & (crashes_data['LATITUDE'] <= 41) & (
            crashes_data['LONGITUDE'] >= -74.5) & (crashes_data['LONGITUDE'] <= -73)]
    # remove columns and empty rows
    crashes_data = keep_relevant_columns(crashes_data, ['index', 'CRASH DATE_CRASH TIME', 'LOCATION'])
    crashes_data = datetime_conversions(crashes_data, ['CRASH DATE_CRASH TIME'], '%Y-%m-%d %H:%M:%S')
    crashes_data = crashes_data.dropna()

    crashes_data = add_zone_to_event(crashes_data, nyc_taxi_geo, 'LOCATION')


    # open file
    street_closures = open_file("2018_street_closures.csv")
    street_geometries = open_file("street_geometries.csv")

    # merge the dataframes
    street_closures['ONSTREETNAME'] = street_closures['ONSTREETNAME'].str.lower()
    street_closures['ONSTREETNAME'] = street_closures['ONSTREETNAME'].str.replace('\s+', ' ', regex=True)
    street_geometries['name'] = street_geometries['name'].str.lower()
    merged_streets_df = pd.merge(street_closures, street_geometries, left_on='ONSTREETNAME', right_on='name')

    # remove columns and empty rows
    merged_streets_df = keep_relevant_columns(merged_streets_df, ['ONSTREETNAME', 'WORK_START_DATE', 'WORK_END_DATE',
                                                                  'geometry'])
    merged_streets_df = merged_streets_df.dropna()
    # datetime conversions
    merged_streets_df = datetime_conversions(merged_streets_df, ['WORK_START_DATE', 'WORK_END_DATE'],
                                             '%Y-%m-%d %H:%M:%S')

    merged_streets_df = add_zone_to_event(merged_streets_df, nyc_taxi_geo, 'geometry')

