# import Vis
import datetime

import pandas as pd
import geopandas as gpd
import numpy as np
from geopandas import GeoDataFrame
from matplotlib import pyplot as plt
from shapely.geometry import Point
from shapely import wkt, LineString
import folium



def open_file(path: str) -> pd.DataFrame:
    """

    :param path:
    :return: pandas DataFrame
    """
    return pd.read_csv(path, infer_datetime_format=True)


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
    :param gdf: taxi zones gdf
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
        PUzone_neighbors = neighbor_dict[PUzone]
        trips_zones_dict[trip['tripID']] = set(PUzone_neighbors)
    exclude = []
    for x in trips_df.iterrows():
        tripID = x[1][0]
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


def convert_to_geometry_point(coords):
    """
    Converts a series of strings to a geometry point object
    :param coords: A string containing the coordinates in the format "(lat, lon)"
    :return: A Point object with the specified coordinates and CRS
    """
    # if coords.startswith('LINESTRING'):
    #     coords = coords.replace("LINESTRING (", "").replace(")", "")
    #     coords = [tuple(map(float, c.split())) for c in coords.split(",")]
    #     multipoint = [(float(lon), float(lat)) for lon, lat in coords]
    #     geo_point = LineString(multipoint)
    # elif type(coords) == str:
    lat, lon = coords.strip("()").split(',')
    geo_point = Point(float(lon), float(lat))
    # else:
    #     raise TypeError('Invalid location type. Must be string or list of coordinates.')
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
    # make seperate tables
    # connecting table
    # save it
    # keep IDs

    return data_gdf


def cluster_crashes(crashes_df:pd.DataFrame):
    """

    :param crashes_df:
    :return:
    >>> nyc_taxi_geo = gpd.read_file('NYC_Taxi_Zones.geojson')
    >>> crashes_data = datetime_conversions(open_file("Crash_zones.csv"), ['CRASH DATE_CRASH TIME'], '%Y-%m-%d %H:%M:%S')
    >>> crashes_data['Date'] = crashes_data.apply(lambda x: x['CRASH DATE_CRASH TIME'].date(), axis=1)
    >>> cluster_crashes(crashes_data) #doctest:+ELLIPSIS
    Unnamed: 0 ...
    [38996 rows x 9 columns]
    """
    # Create Date Column
    crashes_df['Date'] = crashes_df.apply(lambda x: x['CRASH DATE_CRASH TIME'].date(), axis=1)
    # Create Time column (Copy of datetime column)
    crashes_df['Time'] = crashes_df.apply(lambda x: x['CRASH DATE_CRASH TIME'], axis=1)
    # Merge dataframe with itself on Zone and Date columns
    clusters = pd.merge(crashes_df[['index', 'Date', 'Time', 'ZONE', 'geometry']], crashes_df, how='inner',
                        left_on=['ZONE', 'Date'], right_on=['ZONE', 'Date'])
    # Drop NaNs
    clusters = clusters.dropna()
    # Keep only these columns
    clusters_df = clusters[['Unnamed: 0', 'index_x', 'index_y', 'geometry_x', 'geometry_y', 'ZONE', 'Date', 'Time_x', 'Time_y']]
    # Remove rows that merged the same collision with itself
    clusters_df = clusters_df.loc[clusters_df['index_x'] != clusters_df['index_y']]
    # Create a timedelta object of an hour to compare collision time differences to
    time_delta_hour = datetime.timedelta(hours=1)

    # Filter df to keep only crashes that occurred within an hour of one another
    clusters_df = clusters_df[(abs(clusters_df['Time_x']-clusters_df['Time_y'])) < time_delta_hour]

    # Getting rid of reverse duplicates:

    # Create a set for pairs of collisions that have been processed
    processed = set()
    # Create an empty list to keep track of rows to be removed
    to_remove = []
    # Loop through the rows of the dataframe
    for index, row in clusters_df.iterrows():
        # Check if the reverse of the row has already been processed
        if (row['index_y'], row['index_x']) in processed:
            # If it has, add the index of the row to the list of rows to be removed
            to_remove.append(index)
        else:
            # If it hasn't, add the row to the set of processed rows
            processed.add((row['index_x'], row['index_y']))

    # Drop rows of pairs which have already been processed
    clusters_df = clusters_df.drop(to_remove)

    # Create figure
    fig, ax = plt.subplots()
    clusters_df.groupby(['Date', 'ZONE']).count().reset_index().hist(['ZONE'], ax=ax, bins=247)
    ax.set_xlabel('Zone')
    ax.set_ylabel('Collision Pairs')
    ax.set_title('Collisions Occurring within an Hour of Another Collision in the Same Zone')
    plt.show()
    # Group by Date and Zone, count, and sort in descending order
    return clusters_df

def cluster_clusters(df:gpd.GeoDataFrame, nyc_gdf:gpd.GeoDataFrame):
    """

    :param df: cluster df
    :param nyc_gdf: GeoDataFrame of NYC taxi zones
    :return: DataFrame of clustered clusters with point geometry of collisions from the biggest
    clusters
    """

    for i in ['x', 'y']:
        # Rename geometry_x and geometry_y to geometry
        df.rename(columns={f'geometry_{i}': 'geometry'}, inplace=True)
        # Apply geometry from shapely to geometry objects in columns
        df[f'geometry_{i}'] = df['geometry'].apply(wkt.loads)
        # Remove geometry column
        df.drop('geometry', inplace=True, axis=1)
    df = gpd.GeoDataFrame(df, crs='epsg:4326', geometry='geometry_x')
    df.set_geometry('geometry_y', inplace=True)

    big_clusters = df.groupby(by='index_x').count().sort_values('Time_x', ascending=False).head(35)
    big_clusters.rename(columns={'Unnamed: 0': 'Number of times 2 crashes occurred within an hour/day'}, inplace=True)

    big_cluster_full = df.merge(big_clusters['Number of times 2 crashes occurred within an hour/day'], how='inner',
                               left_on='index_x', right_on='index_x')
    big_cluster_full.set_geometry('geometry_x').set_geometry('geometry_y')
    big_cluster_full.rename(columns={'Number of times 2 crashes occurred '
                                     'within an hour/day': 'Matches'}, inplace=True)
    big_cluster_full['Collisions in Cluster'] = big_cluster_full['Matches']+1
    print(big_cluster_full[['Date', 'ZONE', 'Collisions in Cluster']])
    fig, ax = plt.subplots()
    nyc_gdf.geometry.plot(linewidth=0.05,ax=ax)
    big_cluster_full.geometry.plot(ax=ax, c='r', alpha=.5)
    plt.title('Map of NYC Illustrating Locations of Largest Collision Clusters in 2018')
    plt.show()
    return big_cluster_full


if __name__ == '__main__':
    # open file
    taxi_data = format_index(open_file("sampled_combined_taxi_2018_600k.csv"), 'tripID')

    # remove taxi columns
    taxi_data = keep_relevant_columns(taxi_data, ['tripID', 'tpep_pickup_datetime', 'tpep_dropoff_datetime', 'trip_distance',
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
    crashes_data = open_file("Crash_zones.csv")
    # remove rows with invalid rows
    # crashes_data = crashes_data.loc[(crashes_data['LATITUDE'] >= 40) & (crashes_data['LATITUDE'] <= 41) & (
    #         crashes_data['LONGITUDE'] >= -74.5) & (crashes_data['LONGITUDE'] <= -73)]
    # remove columns and empty rows
    # crashes_data = keep_relevant_columns(crashes_data, ['index', 'CRASH DATE_CRASH TIME', 'LOCATION'])
    crashes_data = datetime_conversions(crashes_data, ['CRASH DATE_CRASH TIME'], '%Y-%m-%d %H:%M:%S')
    # crashes_data = crashes_data.dropna()

    # crashes_data = add_zone_to_event(crashes_data, nyc_taxi_geo, 'LOCATION')
    clusters_df = cluster_crashes(crashes_data)
    print(clusters_df.groupby(by=['Date', 'ZONE']).count().sort_values('index_x', ascending=False))

    clustered = cluster_clusters(clusters_df,nyc_taxi_geo)
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

