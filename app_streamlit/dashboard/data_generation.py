"""Import data from postgreSQL database that is hosted on supabase."""

from supabase import create_client, Client
import pandas as pd
from tenacity import retry, stop_after_attempt, wait_random_exponential


# --- Supabase config ---
url = "https://dluhqrwmercbvgfhoxef.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRsdWhxcndtZXJjYnZnZmhveGVmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDM3NTc5ODUsImV4cCI6MjA1OTMzMzk4NX0._R5TinJKV42TU0pFn0ZhJnzDjqshX4NZesVl9O8KC9o"

supabase: Client = create_client(url, key)

pollutant_list = ["co", "o3", "no", "no2", "pm10", "pm25", "so2"]


def get_locations() -> pd.DataFrame:
    response = supabase.from_("locations").select("town, department, region").execute()
    return pd.DataFrame(response.data)


@retry(
    reraise=True,
    wait=wait_random_exponential(min=0.1, max=10),
    stop=stop_after_attempt(10),
)
def get_all_measures() -> pd.DataFrame:
    response = supabase.rpc("get_filter_data").execute()
    all_measures = pd.DataFrame(response.data)
    all_measures = all_measures[all_measures["department"] != "Not_found"]
    all_measures = all_measures[all_measures["region"] != "Île-de-france"]
    all_measures["datetime_from"] = pd.to_datetime(all_measures["datetime_from"])
    all_measures["datetime_to"] = pd.to_datetime(all_measures["datetime_to"])
    return all_measures


@retry(
    reraise=True,
    wait=wait_random_exponential(min=0.1, max=10),
    stop=stop_after_attempt(10),
)
def get_heatmap_measures(
    pollutant_name: str,
    start_date: str,
    end_date: str,
) -> pd.DataFrame:

    response = supabase.rpc(
        "heatmap_data",
        {
            "pollutant_name": pollutant_name,
            "start_date": end_date,  # hack to only generate latest instead of average
            "end_date": end_date,
        },
    ).execute()

    return pd.DataFrame(response.data)


def get_measurements_daterange_data(
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    response = supabase.rpc(
        "get_measurements_by_date_range",
        {
            "start_date": start_date,
            "end_date": end_date,
        },
    ).execute()
    df = pd.DataFrame(response.data)
    df = df[df["department"] != "Not_found"]
    df = df[df["region"] != "Île-de-france"]
    return df


def get_reduction_data(
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    response = supabase.rpc(
        "get_pollution_reduction",
        {"start_date": start_date, "end_date": end_date},
    ).execute()
    df = pd.DataFrame(response.data)
    df = df[df["department"] != "Not_found"]
    df = df[df["region"] != "Île-de-france"]
    return df
