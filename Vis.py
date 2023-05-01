import osmnx as ox
import osmnx.utils_geo
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt


def map_events_to_zones(nyc_taxi_geo: gpd.geodataframe, crashes: pd.DataFrame, closures: pd.DataFrame):
    """
    Maps crashes and closures to
    :param nyc_taxi_geo:
    :param crashes:
    :param closures:
    :return:
    """
    pass

def zone_center(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    gdf['centroid'] = gdf['geometry'].centroid
    # print(gdf)
    return gdf


def distance_between_two_zones(gdf:gpd.GeoDataFrame, zone1: int, zone2: int):
    zone1_bbox = gdf.loc['object_id' == zone1]['geometry']
    g_z1 = osmnx.graph_from_polygon(zone1_bbox)
    random_address_z1 = osmnx.utils_geo.sample_points(g_z1,1)
    zone2_bbox = gdf.loc['object_id' == zone2]['geometry']
    g_z2 = osmnx.graph_from_polygon(zone2_bbox)
    random_address_z2 = osmnx.utils_geo.sample_points(g_z2, 1)
    # zone1_centroid = gdf.loc['object_id' == zone1]['centroid']
    # zone2_centroid = gdf.loc['object_id' == zone2]['centroid']
    distance = random_address_z1.distance(random_address_z2)
    return distance


def events_during_trips(trips, crashes, closures):
    """

    :param trips:
    :param crashes:
    :param closures:
    :return: List of dictionaries. Each dictionary...
    """
    events_in_trips = []
    for trip in trips:
        pass


# zone_slide = ipywidgets.IntSlider(value=2, min=2, max=263)
# @ipywidgets.interact(zone = zone_slide)
# def plot_zone_speeds(df:pd.DataFrame, zone:int):
#     sub1 = df[df['PULocationID'] == zone]
#     sub2 = df[df['DOLocationID'] == zone]
#     sub = pd.concat([sub1,sub2])
#     # print((sub))
#     plt.hist(sub['avg speed'], bins = 60)
#     plt.xlabel('Average Speed (mph)')
#     plt.ylabel('Number of trips')
    return plt.show()