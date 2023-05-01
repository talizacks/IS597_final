import osmnx as ox
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt


def map_events_to_zones(nyc_taxi_geo: gpd.geodataframe, crashes: pd.DataFrame, closures: pd.DataFrame)
    """
    Maps crashes and closures to
    :param nyc_taxi_geo:
    :param crashes:
    :param closures:
    :return:
    """


def zone_center():

def distance_between_two_zones():


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


zone_slide = ipywidgets.IntSlider(value=2, min=2, max=263)
@ipywidgets.interact(zone = zone_slide)
def plot_zone_speeds(df:pd.DataFrame, zone:int):
    sub1 = df[df['PULocationID'] == zone]
    sub2 = df[df['DOLocationID'] == zone]
    sub = pd.concat([sub1,sub2])
    # print((sub))
    plt.hist(sub['avg speed'], bins = 60)
    plt.xlabel('Average Speed (mph)')
    plt.ylabel('Number of trips')
    return plt.show()