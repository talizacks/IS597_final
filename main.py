import Vis as viz
import File_creation as fc
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from shapely import wkt, LineString
import folium
import clusters as c
import numpy as np


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
    trips_df = df[limit_mask]

    # Find zones with no neighbors
    dont_include = []
    for x in neighbor_dict:
        if neighbor_dict[x] == []:
            dont_include.append(x)

    # create mask to remove trips that start or end in a zone without neighbors
    no_neighbors_mask = (~trips_df['PULocationID'].isin(dont_include)) & (~trips_df['DOLocationID'].isin(dont_include))

    # apply masks
    trips_df = trips_df[no_neighbors_mask]

    for index, trip in trips_df.iterrows():
        PUzone = trip['PULocationID']
        PUzone_neighbors = neighbor_dict[PUzone]
        trips_zones_dict[trip['tripID']] = set(PUzone_neighbors)
    exclude = []
    for x in trips_df.iterrows():
        tripID = x[1][0]
        DOzone = x[1][9]
        if DOzone not in (trips_zones_dict[tripID]):
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
    # Take difference between drop off and pickup time
    df['trip_time'] = (df['tpep_dropoff_datetime'] - df['tpep_pickup_datetime'])

    # Calculate length of trip in hours
    df['trip_time_h'] = [(x.total_seconds()) / 3600 for x in df['trip_time']]
    # Calculate average speed with distance/time
    df['avg speed'] = df['trip_distance'] / df['trip_time_h']
    return df


def removeWeirdTaxiData(df: pd.DataFrame) -> pd.DataFrame:
    """

    :return:
    """
    too_quick = df['trip_time_h'] >= 0.01666666667      # less than a minute
    too_long = df['trip_time_h'] <= 24      # more than 24hrs
    super_fast = df['avg speed'] <= 90      # drove faster than 90mph
    super_slow = df['avg speed'] >= 1       # drove slower than 1mph
    df = df[too_quick]
    df = df[too_long]
    df = df[super_fast]
    df = df[super_slow]

    return df

def two_random_zones(neighbor_dict):
    zones_with_neighbors = []
    for x in neighbor_dict:
        if neighbor_dict[x] != []:
            zones_with_neighbors.append(x)
    return np.random.choice(zones_with_neighbors, 2)

if __name__ == '__main__':

    # set up for taxi data
    taxi_data = fc.taxi_file_setup("sampled_combined_taxi_2018_600k.csv")
    taxi_data = datetime_conversions(taxi_data, ['tpep_pickup_datetime', 'tpep_dropoff_datetime'],
                                     '%m/%d/%Y %I:%M:%S %p')
    taxi_data = add_time_and_speed(taxi_data)


    # neighbors and zones
    nyc_taxi_geo = gpd.read_file('NYC_Taxi_Zones.geojson')
    neighbors = find_neighbors(nyc_taxi_geo)
    taxi_data = filter_trips_based_on_zones(taxi_data, neighbors)


    # set up for crash data
    crashes = fc.crash_file_setup("2018_crashes.csv", nyc_taxi_geo)
    crashes = datetime_conversions(crashes, ['CRASH DATE_CRASH TIME'], '%Y-%m-%d %H:%M:%S')


    # crashes_data = add_zone_to_event(crashes_data, nyc_taxi_geo, 'LOCATION')
    clusters_df = c.cluster_crashes(crashes)
    print(clusters_df.groupby(by=['Date', 'ZONE']).count().sort_values('index_x', ascending=False))

    clustered = c.cluster_clusters(clusters_df, nyc_taxi_geo)


    random_zones = two_random_zones()
    viz.plot_routes_for_random_addresses_in_2_zones(random_zones)

    # open file
    # street_closures = open_file("2018_street_closures.csv")
    # street_geometries = open_file("street_geometries.csv")
    #
    # # merge the dataframes
    # street_closures['ONSTREETNAME'] = street_closures['ONSTREETNAME'].str.lower()
    # street_closures['ONSTREETNAME'] = street_closures['ONSTREETNAME'].str.replace('\s+', ' ', regex=True)
    # street_geometries['name'] = street_geometries['name'].str.lower()
    # merged_streets_df = pd.merge(street_closures, street_geometries, left_on='ONSTREETNAME', right_on='name')
    #
    # # remove columns and empty rows
    # merged_streets_df = keep_relevant_columns(merged_streets_df, ['ONSTREETNAME', 'WORK_START_DATE', 'WORK_END_DATE',
    #                                                               'geometry'])
    # merged_streets_df = merged_streets_df.dropna()
    # # datetime conversions
    # merged_streets_df = datetime_conversions(merged_streets_df, ['WORK_START_DATE', 'WORK_END_DATE'],
    #                                          '%Y-%m-%d %H:%M:%S')
    #
    # merged_streets_df = add_zone_to_event(merged_streets_df, nyc_taxi_geo, 'geometry')

    # set up for collision data
    closures, closure_zones = fc.closure_file_setup("2018_street_closures.csv", "street_geometries.csv", nyc_taxi_geo)
    closures = datetime_conversions(closures, ['WORK_START_DATE', 'WORK_END_DATE'],
                                    '%Y-%m-%d %H:%M:%S')


