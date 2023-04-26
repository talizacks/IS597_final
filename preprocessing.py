import osmnx as ox
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import ipywidgets
import datetime as dt

def taxi_zones(zone_filename) -> gpd.GeoDataFrame:
    nyc_gdf = gpd.read_file(zone_filename)
    nyc_gdf.set_index('objectid')
    return nyc_gdf

def taxi_data(taxi_filename) -> pd.DataFrame:
    """
    :param taxi_filename: path to file with taxi trip data
    :return: pandas DataFrame of taxi trips which include
    only trips that start and end in the same zone,
    neighboring zones, or zones that neighbor the
    neighboring zones
    """
    taxi_df = pd.read_csv(taxi_filename,
                    parse_dates=['tpep_pickup_datetime', 'tpep_dropoff_datetime'])
    taxi_df.rename(columns={'Unnamed: 0': 'tripID'}, inplace=True)
    taxi_df.set_index('tripID')
    return taxi_df

def find_neighboring_zones(zone_gdf) -> dict:
    """
    :param zones: taxi zones
    :return:
    """
    zones = zone_gdf
    # https://gis.stackexchange.com/questions/281652/finding-all-neighbors-using-geopandas
    neighbor_dict = {}
    for index, zone in zones.iterrows():
        # get 'not disjoint' countries
        neighbors = zones[~zones.geometry.disjoint(zone.geometry)].objectid.tolist()

        # remove own zone number from the list
        neighbors = [int(num) for num in neighbors if zone.objectid != num]
        neighbor_dict[index + 1] = neighbors
        # add list of neighboring zone numbers as neighbors value
        # nyc_gdf.at[index, "neighbors"] = ", ".join(neighbors).split(',')
        # if nyc_gdf.at[index, "neighbors"] == ['']:
        #     print(nyc_gdf.at[index, "zone"])
        #     nyc_gdf.at[index, "neighbors"] = None
        return neighbor_dict


def neighbor_neighbors(taxi_filename,zone_filename):

    neighbor_dict = find_neighboring_zones(taxi_zones(zone_filename))
    for index, trip in trips_df.iterrows():
        PUzone = trip['PULocationID']

        PUzone_neighbor_neighbors = []
        PUzone_neighbors = neighbor_dict[PUzone]
        PUzone_neighbor_neighbors.append(PUzone_neighbors)

        for i in PUzone_neighbors:
            PUzone_neighbor_neighbors.append(neighbor_dict[i])

        PUzone_neighbor_neighbors = [int(x) for x in list(np.concatenate(PUzone_neighbor_neighbors).flat)]

        trips_zones_dict[trip['tripID']] = set(PUzone_neighbor_neighbors)


if __init__ == 'main':
