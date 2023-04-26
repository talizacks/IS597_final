# import Vis
import pandas as pd
import geopandas as gpd
import numpy as np


def open_file(path: str) -> pd.DataFrame:
    """

    :param path:
    :return: pandas DataFrame
    """
    return pd.read_csv(path)

def format_index(df:pd.DataFrame,new_index_name)->pd.DataFrame:
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


def add_time_and_speed(df:pd.DataFrame) -> pd.DataFrame:
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

def change_location_to_zones(df, locations_column_names):
    """

    :param df:
    :param locations_column_names:
    :return:
    """


if __name__ == '__main__':
    # open file
    taxi_data = format_index(open_file("sampled_combined_taxi_2018_600k.csv"),'tripID')

    # remove taxi columns
    taxi_data = keep_relevant_columns(taxi_data, ['tripID','tpep_pickup_datetime', 'tpep_dropoff_datetime', 'trip_distance',
                                                  'PULocationID', 'DOLocationID', 'fare_amount', 'tip_amount',
                                                  'tolls_amount', 'total_amount'])
    # datetime_conversions
    taxi_data = datetime_conversions(taxi_data, ['tpep_pickup_datetime', 'tpep_dropoff_datetime'],
                                     '%m-%d-%Y %I:%M:%S %p')
    taxi_data = add_time_and_speed(taxi_data)


    # neighbors and zones
    nyc_taxi_geo = gpd.read_file('NYC_Taxi_Zones.geojson')
    neighbors = find_neighbors(nyc_taxi_geo)
    taxi_data = filter_trips_based_on_zones(taxi_data, neighbors)


    # open crashes file
    crashes_data = format_index(open_file("2018_crashes.csv"), 'index')

    # remove columns
    crashes_data = keep_relevant_columns(crashes_data, ['index','DATE_CRASH', 'TIME', 'LOCATION'])
    crashes_data['Date-time_of_crash'] = crashes_data[['DATE_CRASH', 'TIME']].agg('-'.join, axis=1)
    crashes_data = datetime_conversions(crashes_data, ['Date-time_of_crash'], '%Y-%m-%d-%H:%M:%S')


    #open file
    street_closures = open_file("2018_street_closures.csv")
    #remove columns
    street_closures = keep_relevant_columns(street_closures, ['FROMSTREETNAME', 'TOSTREETNAME',
                                                              'WORK_START_DATE', 'WORK_END_DATE'])
    #datetime conversions
    street_closures = datetime_conversions(street_closures, ['WORK_START_DATE', 'WORK_END_DATE'], '%Y-%m-%d %H:%M:%S')
    taxi_data

