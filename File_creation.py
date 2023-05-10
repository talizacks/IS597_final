import pandas as pd
import geopandas as gpd
from geopandas import GeoDataFrame
from shapely.geometry import Point
from shapely import wkt, LineString

# def convert_to_geometry_point(coords):
#     """
#     Converts a series of strings to a geometry point object
#     :param coords: A string containing the coordinates in the format "(lat, lon)"
#     :return: A Point object with the specified coordinates and CRS
#     """
#     lat, lon = coords.strip("()").split(',')
#     geo_point = Point(float(lon), float(lat))
#     return geo_point
#
# def convert_to_geometry_LINESTRING(coords):
#     """
#
#     :param coords:
#     :return:
#     """
#     coords = coords.replace("LINESTRING (", "").replace(")", "")
#     coords = [tuple(map(float, c.split())) for c in coords.split(",")]
#     multipoint = [(float(lon), float(lat)) for lon, lat in coords]
#     geo_point = LineString(multipoint)
#     return geo_point

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

def borough_match(borough_code, borough_name):
    """

    :param borough_code:
    :param borough_name:
    :return:
    """
    if borough_code == 'B' and borough_name == 'Brooklyn':
        return True
    elif borough_code == 'S' and borough_name == 'Staten Island':
        return True
    elif borough_code == 'M' and borough_name == 'Manhattan':
        return True
    elif borough_code == 'Q' and borough_name == 'Queens':
        return True
    elif borough_code == 'X' and borough_name == 'Bronx':
        return True
    else:
        return False



def add_zone_to_closures(closures, street_geometries, nyc_geo):
    # get zone from coordinates
    # https://geopandas.org/en/stable/docs/reference/geoseries.html

    # Make street names the same in both dataframes
    closures['ONSTREETNAME'] = closures['ONSTREETNAME'].str.lower()
    closures['ONSTREETNAME'] = closures['ONSTREETNAME'].str.replace('\s+', ' ', regex=True)
    street_geometries['name'] = street_geometries['name'].str.lower()

    # make connector table
    collision_zones = pd.DataFrame(columns=['SEGMENTID', 'ZONE'])

    # fix the coordinates and crs in street_geometries
    crs = 'EPSG:4326'
    street_geometries['geometry'] = street_geometries['geometry'].apply(lambda x: convert_to_geometry_point(x))
    street_geometries = gpd.GeoDataFrame(street_geometries, geometry='geometry', crs=crs)

    # make variables for taxi zone data
    taxi_zones = nyc_geo.zone
    zone_numbers = taxi_zones.index
    zone_borough = nyc_geo.borough
    taxi_zones_boundaries = nyc_geo.geometry
    zone_data = zip(taxi_zones_boundaries, zone_numbers, zone_borough)
    # make dict

    previous_zone = None
    # get unique values for st name and borough, group_by
    #S_Grimsby or tuple
    for i, closure in closures.iterrows():
        #
        street_name = closure['ONSTREETNAME']
        ID = closure['SEGMENTID']
        closure_borough = closure['BOROUGH_CODE']

        # find the geometries of the street
        matching_geometries = street_geometries[street_geometries['name'] == street_name]['geometry']
        geo_found = False
        for geometry in matching_geometries:
            # if geo_found:
            #     break
            for boundary, zone, borough in zone_data:
                # dict makes it fasted cause it looks for key
                # if the coordinates is within the zone boundary
                if boundary.contains(geometry):
                    # check the borough name
                    if not borough_match(closure_borough, borough):
                        break
                    if zone == previous_zone:  # Check if the zone is the same as the previous one
                        break
                    print(zone)
                    collision_zones.loc[len(collision_zones)] = [ID, zone]
                    previous_zone = zone
                    # geo_found = True
                    break
    collision_zones.to_csv('closure_zones.csv', index=True)


# def add_zone_to_event(df, nyc_geo, col_name, connector_table = None):
#     """
#
#     :param df:
#     :param nyc_geo:
#     :param col_name:
#     :return:
#     """
#     # get zone from coordinates
#     # https://geopandas.org/en/stable/docs/reference/geoseries.html
#     crs = 'EPSG:4326'
#     # make a column called 'ZONE' with an empty list (MAKE IT OUTSIDE)
#     # df['ZONE'] = ''
#     taxi_zones = nyc_geo.zone
#     zone_numbers = taxi_zones.index
#     zone_borough = taxi_zones.borough
#     taxi_zones_boundaries = nyc_geo.geometry
#     df['geometry'] = df[col_name].apply(lambda x: convert_to_geometry_point(x))
#     data_gdf = gpd.GeoDataFrame(df, geometry='geometry', crs=crs)
#     previous_zone = None
#     for i, row in data_gdf.iterrows():
#         coords = row['geometry']
#         for boundary, zone in zip(taxi_zones_boundaries, zone_numbers):
#             if boundary.contains(coords):
#                 if zone == previous_zone:  # Check if the zone is the same as the previous one
#                     break  # Stop the calculation
#                 print(coords)
#                 print(zone)
#                 if connector_table is None and borough_match(row['BOROUGH_CODE'], zone_borough):
#                     data_gdf.at[i, 'ZONE'] = zone
#                 else:
#                     connector_table.loc[len(connector_table)] = [row['SEGMENTID'], zone]
#                     previous_zone = zone
#                 break
#     #data_gdf.to_csv('output.csv', index=True)
#     #vectorize later
#     # make separate tables
#     # connecting table
#     # save it
#     # keep IDs
#     connector_table.to_csv('closure_zones.csv', index=True)
#     return data_gdf
