import Vis
import pandas as pd
import geopandas as gpd


def open_file(path: str) -> pd.DataFrame:
    """

    :param path:
    :return: pandas DataFrame
    """
    return pd.read_csv(path)


def combine_taxi_dataframes(df_list: list) -> pd.DataFrame:
    """
    Combines a list of taxi data into one dataframe
    :param df_list: A list of dataframes
    :return: A concatenated dataframe
    """
    concatenated_df = pd.concat(df_list)
    return concatenated_df


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

if __name__ == '__main__':
    # Load files into pandas dataframes
    taxi_data = open_file("sampled_combined_taxi_2018_600k.csv")
    crashes_data = open_file("2018_crashes.csv")
    street_closures = open_file("2018_street_closures.csv")
    # taxi zone data
    nyc_taxi_geo = gpd.read_file('NYC_Taxi_Zones.geojson')

    # Remove Unnecessary columns
    taxi_data = keep_relevant_columns(taxi_data, ['tpep_pickup_datetime', 'tpep_dropoff_datetime', 'trip_distance',
                                                  'PULocationID', 'DOLocationID', 'fare_amount', 'tip_amount',
                                                  'tolls_amount', 'total_amount'])
    crashes_data = keep_relevant_columns(crashes_data, ['DATE_CRASH', 'TIME', 'LOCATION'])
    crashes_data['Date-time_of_crash'] = crashes_data[['DATE_CRASH', 'TIME']].agg('-'.join, axis=1)
    street_closures = keep_relevant_columns(street_closures, ['FROMSTREETNAME', 'TOSTREETNAME',
                                                              'WORK_START_DATE', 'WORK_END_DATE'])

    # change date formats to datetime

    taxi_data = datetime_conversions(taxi_data, ['tpep_pickup_datetime', 'tpep_dropoff_datetime'],
                                     '%m-%d-%Y %I:%M:%S %p')
    crashes_data = datetime_conversions(crashes_data, ['Date-time_of_crash'], '%Y-%m-%d-%H:%M:%S')
    street_closures = datetime_conversions(street_closures, ['WORK_START_DATE', 'WORK_END_DATE'], '%Y-%m-%d %H:%M:%S')


    #make events_during_trip list
    events_during_trips = Vis.events_during_trip(taxi_data, crashes_data, street_closures)


