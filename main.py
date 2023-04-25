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
    pass

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

