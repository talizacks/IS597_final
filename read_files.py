import numpy as np
import pandas
import pandas as pd
import datetime as dt
import requests
import json


def read_file(url: str, filename_to_write: str) -> pd.DataFrame:
    """
    :param url: url where data exists. url to NYC open data API
    :return: pandas DataFrame
    """
    response_API = requests.get(url)
    data = response_API.text
    parse = json.loads(data)
    print(parse)
    f = open(filename_to_write, "w")
    f.write(str(parse))
    f.close()
    print(pd.read_json(filename_to_write))
    return pd.read_json(filename_to_write)

# read_file('https://data.cityofnewyork.us/resource/t29m-gskq.json?$query=SELECT%0A%20%20%60vendorid%60%2C%0A%20%20%60tpep_pickup_datetime%60%2C%0A%20%20%60tpep_dropoff_datetime%60%2C%0A%20%20%60passenger_count%60%2C%0A%20%20%60trip_distance%60%2C%0A%20%20%60ratecodeid%60%2C%0A%20%20%60store_and_fwd_flag%60%2C%0A%20%20%60pulocationid%60%2C%0A%20%20%60dolocationid%60%2C%0A%20%20%60payment_type%60%2C%0A%20%20%60fare_amount%60%2C%0A%20%20%60extra%60%2C%0A%20%20%60mta_tax%60%2C%0A%20%20%60tip_amount%60%2C%0A%20%20%60tolls_amount%60%2C%0A%20%20%60improvement_surcharge%60%2C%0A%20%20%60total_amount%60%0AWHERE%0A%20%20%60tpep_pickup_datetime%60%0A%20%20%20%20BETWEEN%20%222018-01-01T13%3A16%3A36%22%20%3A%3A%20floating_timestamp%0A%20%20%20%20AND%20%222023-04-17T13%3A16%3A36%22%20%3A%3A%20floating_timestamp%0AORDER%20BY%20%60tpep_pickup_datetime%60%20DESC%20NULL%20LAST','taxi_data.json')
# read_file('https://data.cityofnewyork.us/Public-Safety/Motor-Vehicle-Collisions-Crashes/h9gi-nx95','crashes.json')
# read_file('https://data.cityofnewyork.us/resource/t29m-gskq.json?$query=SELECT%0A%20%20%60vendorid%60%2C%0A%20%20%60tpep_pickup_datetime%60%2C%0A%20%20%60tpep_dropoff_datetime%60%2C%0A%20%20%60passenger_count%60%2C%0A%20%20%60trip_distance%60%2C%0A%20%20%60ratecodeid%60%2C%0A%20%20%60store_and_fwd_flag%60%2C%0A%20%20%60pulocationid%60%2C%0A%20%20%60dolocationid%60%2C%0A%20%20%60payment_type%60%2C%0A%20%20%60fare_amount%60%2C%0A%20%20%60extra%60%2C%0A%20%20%60mta_tax%60%2C%0A%20%20%60tip_amount%60%2C%0A%20%20%60tolls_amount%60%2C%0A%20%20%60improvement_surcharge%60%2C%0A%20%20%60total_amount%60%0AWHERE%0A%20%20(%60tpep_pickup_datetime%60%0A%20%20%20%20%20BETWEEN%20%222018-01-01T14%3A14%3A23%22%20%3A%3A%20floating_timestamp%0A%20%20%20%20%20AND%20%222023-04-17T14%3A14%3A23%22%20%3A%3A%20floating_timestamp)%0A%20%20AND%20(%60trip_distance%60%20%3E%200)%0AORDER%20BY%20%60tpep_pickup_datetime%60%20DESC%20NULL%20LAST','taxi_trips.json')
# print(pd.read_csv('taxi/Yellow_Taxi_Trip_Data_1_2018.csv'))


# def combine_taxi_dfs() -> pd.DataFrame:
#     dfs = []
#     for i in range(1,13):
#         df = pd.read_csv(f'taxi/Yellow_Taxi_Trip_Data_{i}_2018.csv', infer_datetime_format=True)
#         dfs.append(df)
#     combined = pd.concat(dfs)
#     combined_sample = combined.sample(n=200000)
#     combined_sample.to_csv('combined_taxi_2018_200k_sample.csv')
#     return combined_sample
#
# print(sorted(combine_taxi_dfs()))

