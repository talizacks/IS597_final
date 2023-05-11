import geopandas as gpd
import pandas as pd
from shapely import wkt
import matplotlib.pyplot as plt
import File_creation as fc
import datetime

def cluster_crashes(crashes_df: pd.DataFrame):
    """

    :param crashes_df:
    :return:
    >>> nyc_taxi_geo = gpd.read_file('NYC_Taxi_Zones.geojson')
    >>> crashes_data = datetime_conversions(fc.open_file("Crash_zones.csv"), ['CRASH DATE_CRASH TIME'], '%Y-%m-%d %H:%M:%S')
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
