import Vis
import pandas as pd
import geopandas as gpd


def open_file(path: str) -> pd.DataFrame:
    """

    :param path:
    :return: pandas DataFrame
    """
    return pd.read_csv(path)


def keep_relevant_columns(df: pd.DataFrame, column_names: list) -> pd.DataFrame:
    """

    :param df:
    :param column_names:
    :return:
    """
    df = df.loc[:df.columns.isin(column_names)]
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

def removeWeirdTaxiData():
    """

    :return:
    """
    too_quick = trips_df['trip_time_h'] >= 0.01666666667
    too_long = trips_df['trip_time_h'] <= 24
    super_fast = trips_df['avg speed'] <= 90
    super_slow = trips_df['avg speed'] >= 1
    trips_df = trips_df[too_quick]
    trips_df = trips_df[too_long]
    trips_df = trips_df[super_fast]
    trips_df = trips_df[super_slow]

    return trips_df

def change_location_to_zones(df, locations_column_names):
    """

    :param df:
    :param locations_column_names:
    :return:
    """


if __name__ == '__main__':
    # open file
    taxi_data = open_file("sampled_combined_taxi_2018_600k.csv")
    #remove
    taxi_data = keep_relevant_columns(taxi_data, ['tpep_pickup_datetime', 'tpep_dropoff_datetime', 'trip_distance',
                                                  'PULocationID', 'DOLocationID', 'fare_amount', 'tip_amount',
                                                  'tolls_amount', 'total_amount'])
    #datetime_conversions
    taxi_data = datetime_conversions(taxi_data, ['tpep_pickup_datetime', 'tpep_dropoff_datetime'],
                                     '%m-%d-%Y %I:%M:%S %p')

    nyc_taxi_geo = gpd.read_file('NYC_Taxi_Zones.geojson')

    #open file
    crashes_data = open_file("2018_crashes.csv")
    #remove columns
    crashes_data = keep_relevant_columns(crashes_data, ['DATE_CRASH', 'TIME', 'LOCATION'])
    crashes_data['Date-time_of_crash'] = crashes_data[['DATE_CRASH', 'TIME']].agg('-'.join, axis=1)
    crashes_data = datetime_conversions(crashes_data, ['Date-time_of_crash'], '%Y-%m-%d-%H:%M:%S')


    #open file
    street_closures = open_file("2018_street_closures.csv")
    #remove columns
    street_closures = keep_relevant_columns(street_closures, ['FROMSTREETNAME', 'TOSTREETNAME',
                                                              'WORK_START_DATE', 'WORK_END_DATE'])
    #datetime conversions
    street_closures = datetime_conversions(street_closures, ['WORK_START_DATE', 'WORK_END_DATE'], '%Y-%m-%d %H:%M:%S')

