import osmnx as ox
import geopandas as gpd
import matplotlib.pyplot as plt
import networkx as nx



def plot_routes_for_random_addresses_in_2_zones(gdf: gpd.GeoDataFrame, zone1: int, zone2: int):
    """
    Plots shortest route between two random points on map given their zones
    :param gdf: nyc geopandas GeoDataFrame
    :param zone1: integer value of Pickup (PU) zone
    :param zone2: integer value of Drop Off (DO) zone
    :return: map of random addresses in PU and DO zones, their nearest nodes, and shortest route between them
    """

    gdf.geometry.to_crs(4326)
    zone1_bbox = gdf.loc[gdf['objectid'] == str(zone1)]['geometry'].item()
    g_z1 = ox.graph_from_polygon(zone1_bbox, network_type='drive', retain_all=True)
    g_z1 = ox.utils_graph.get_undirected(g_z1)
    random_address_z1 = ox.utils_geo.sample_points(g_z1, 1).to_crs(4326)

    zone2_bbox = gdf.loc[gdf['objectid'] == str(zone2)]['geometry'].item()
    g_z2 = ox.graph_from_polygon(zone2_bbox, network_type='drive', retain_all=True)
    g_z2 = ox.utils_graph.get_undirected(g_z2)
    random_address_z2 = ox.utils_geo.sample_points(g_z2, 1).to_crs(4326)

    nyc_full = ox.graph_from_place('New York City, NY, USA', network_type = 'drive')

    address_dict = {}
    for address in [random_address_z1, random_address_z2]:
        address_list = address.to_list()
        lat = float((str(address_list).split(' '))[1].strip('('))
        lon = float((str(address_list).split(' '))[2].strip(')>]'))
        node = ox.nearest_nodes(nyc_full, lat, lon)
        address_dict[tuple(address.to_list())] = (lat, lon, node)
    route = ox.shortest_path(nyc_full, address_dict[tuple(random_address_z1.to_list())][2],
                             address_dict[tuple(random_address_z2.to_list())][2],
                             weight='length')

    zones = nx.compose(g_z1, g_z2).to_undirected()
    c = ox.graph_to_gdfs(zones, edges=False).unary_union.centroid
    bbox = ox.utils_geo.bbox_from_point(point=(c.y, c.x), dist=5000)

    fig, ax = ox.plot_graph_route(nyc_full, route, 'y', show=False, close=False, node_size=1, node_color='w', edge_color='b',
                        edge_linewidth=0.05, bbox=bbox)
    random_address_z1.plot(color='r', ax=ax)
    random_address_z2.plot(color='b', ax=ax)
    plt.title(f'Shortest Route Between Random Points in Zone {zone1} and Zone {zone2}')
    plt.autoscale()
    plt.show()
    return

# nyc_gdf = gpd.read_file('NYC_Taxi_Zones.geojson')
# plot_routes_for_random_addresses_in_2_zones(nyc_gdf, 12, 34)
# def events_during_trips(trips, crashes, closures):
#     """
#
#     :param trips:
#     :param crashes:
#     :param closures:
#     :return: List of dictionaries. Each dictionary...
#     """
#     events_in_trips = []
#     for trip in trips:
#         pass


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
#     return plt.show()