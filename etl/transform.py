"""Handles data transformations and returns dataframes suited for db loading."""

import time

import pandas as pd
from tqdm import tqdm
from geopy.geocoders import Nominatim
from extract import api_call

geolocator = Nominatim(user_agent="air-pollution")


def transform_data(extracted_data: dict) -> dict[pd.DataFrame]:
    countries_df = transform_countries(extracted_data["countries"])
    pollutants_df = transform_pollutants(extracted_data["pollutants"])
    locations_df = transform_locations(extracted_data["locations"])
    locations_df = add_regional_information(locations_df)
    sensors_df = transform_sensors(locations_df)
    measurements_df = transform_measurements(sensors_df)

    return {
        "countries": countries_df,
        "pollutants": pollutants_df,
        "locations": locations_df,
        "sensors": sensors_df,
        "measurements": measurements_df,
    }


def transform_countries(countries_json: dict) -> pd.DataFrame:
    return pd.DataFrame(countries_json)


def transform_pollutants(pollutants_json: dict) -> pd.DataFrame:
    """Transforms raw pollutants JSON data into a structured DataFrame."""
    return pd.DataFrame(pollutants_json["results"][0]["parameters"]).drop(
        columns=["displayName"]
    )


def transform_locations(locations_json: dict) -> pd.DataFrame:
    """Transforms raw locations JSON data into a structured DataFrame."""
    df = pd.DataFrame(locations_json["results"]).query("isMonitor == True").copy()

    drop_cols = [
        "isMonitor",
        "timezone",
        "bounds",
        "owner",
        "provider",
        "isMobile",
        "instruments",
        "licenses",
        "distance",
    ]
    df.drop(columns=drop_cols, inplace=True)
    df["name"] = df["name"].str.lower()
    df["locality"] = df["locality"].str.lower()
    df["locality"] = df["locality"].fillna("not_provided")

    df["country_id"] = df["country"].map(lambda s: s["id"])
    df["latitude"] = df["coordinates"].map(lambda s: round(s["latitude"], 3))
    df["longitude"] = df["coordinates"].map(lambda s: round(s["longitude"], 3))
    df.drop(columns=["country", "coordinates"], inplace=True)

    df["datetimeFirst"] = df["datetimeFirst"].map(lambda s: s["utc"])
    df["datetimeLast"] = df["datetimeLast"].map(lambda s: s["utc"])
    df[["datetimeFirst", "datetimeLast"]] = df[["datetimeFirst", "datetimeLast"]].apply(
        pd.to_datetime
    )

    df["active"] = df["datetimeLast"] >= (pd.Timestamp.utcnow() - pd.Timedelta(days=1))
    df = df[
        [
            "id",
            "name",
            "locality",
            "datetimeFirst",
            "datetimeLast",
            "country_id",
            "latitude",
            "longitude",
            "active",
            "sensors",
        ]
    ]

    return df.reset_index(drop=True)


def transform_sensors(locations_df: pd.DataFrame) -> pd.DataFrame:
    """Extracts and transforms sensor data from locations DataFrame."""
    sensors_df = locations_df[["id", "sensors"]].rename(columns={"id": "location_id"})
    locations_df.drop(columns=["sensors"], inplace=True)

    sensors_df = sensors_df.explode("sensors")
    sensors_df = pd.DataFrame(
        {
            "id": sensors_df["sensors"].map(lambda s: s["id"]),
            "location_id": sensors_df["location_id"],
            "pollutant_id": sensors_df["sensors"].map(lambda s: s["parameter"]["id"]),
        }
    )

    return sensors_df.reset_index(drop=True)


def transform_measurements(sensors_df: pd.DataFrame) -> pd.DataFrame:
    """Transforms sensor measurement data from API responses.

    Args:
        sensors_df (pd.DataFrame): DataFrame containing sensor IDs.

    Returns:
        pd.DataFrame: Transformed measurement data.
    """
    measurements_list = []

    minute_requests = 0
    hour_requests = 0

    for sensor_id in tqdm(sensors_df["id"], desc="Processing Sensors", unit="sensor"):
        if hour_requests >= 1500:
            print(
                f"Hourly rate limit reached. Waiting 1hr starting {time.strftime("%H:%M:%S", time.localtime())}..."
            )
            time.sleep(3600)
            hour_requests = 0

        if minute_requests >= 50:
            print(
                f"Minute rate limit reached. Waiting 1min starting {time.strftime("%H:%M:%S", time.localtime())}..."
            )
            time.sleep(60)
            minute_requests = 0

        measurements_json = api_call(
            f"sensors/{sensor_id}/days/monthly", {"limit": 1000}
        )
        measurements_df = pd.DataFrame(measurements_json.get("results", []))

        if measurements_df.empty:
            continue

        measurements_df["sensor_id"] = sensor_id

        measurements_df["datetimeFrom"] = pd.to_datetime(
            measurements_df["period"].str["datetimeFrom"].str["utc"]
        )
        measurements_df["datetimeTo"] = pd.to_datetime(
            measurements_df["period"].str["datetimeTo"].str["utc"]
        )
        summary_df = pd.json_normalize(measurements_df["summary"]).round(2)
        measurements_df.drop(columns=["period", "summary"], inplace=True)

        drop_cols = ["flagInfo", "parameter", "coordinates", "coverage"]
        measurements_df.drop(columns=drop_cols, inplace=True)

        measurements_list.append(pd.concat([measurements_df, summary_df], axis=1))

        minute_requests += 1
        hour_requests += 1

    measurements_df = (
        (
            pd.concat(measurements_list, ignore_index=True)
            if measurements_list
            else pd.DataFrame()
        )
        .reset_index(drop=False)
        .rename(columns={"index": "id"})
    )

    return measurements_df[
        [
            "id",
            "sensor_id",
            "datetimeFrom",
            "datetimeTo",
            "value",
            "min",
            "q02",
            "q25",
            "median",
            "q75",
            "q98",
            "max",
            "avg",
            "sd",
        ]
    ]

def get_city_and_region(latitude, longitude):
    """
    Retrieve the city, department, region, and postcode based on geographic coordinates.

    Parameters:
        latitude (float): Latitude coordinate of the location.
        longitude (float): Longitude coordinate of the location.

    Returns:
        tuple: A tuple containing the city, department, region, and postcode.

    Exceptions:
        If the geocoding request fails, None values are returned for all location attributes.

    Example:
        get_city_and_region(44.143, 4.139) -> ('Paris', 'Île-de-France', 'Île-de-France', '75000')
    """
    try:
        location = geolocator.reverse((latitude, longitude))
        if location:
            address = location.raw.get("address", {})
            town = address.get(
                "municipality", address.get("city_district", "Not_found")
            )
            department = address.get("county", address.get("city", "Not_found"))
            region = address.get("state", address.get("Île-de-france", "Not_found"))
            postcode = address.get("postcode", "00000")
            return town, department, region, postcode
    except Exception as e:
        print(f"Erreur lors du géocodage : {e}")
    return None, None, None


def add_regional_information(locations_df: pd.DataFrame) -> pd.DataFrame:
    """
    Add regional information (town, department, region, postcode) to a DataFrame based on geographic coordinates.

    Parameters:
        locations_df (pd.DataFrame): DataFrame containing columns 'latitude' and 'longitude' representing
                                     geographic coordinates.

    Returns:
        pd.DataFrame: The input DataFrame with additional columns for 'town', 'department', 'region', and 'postcode',
                      populated with the corresponding location information retrieved via reverse geocoding.
    """
    towns = []
    departments = []
    regions = []
    postcodes = []

    for index, row in locations_df.iterrows():
        town, department, region, postcode = get_city_and_region(
            row["latitude"], row["longitude"]
        )
        towns.append(town)
        departments.append(department)
        regions.append(region)
        postcodes.append(postcode)
        time.sleep(1)

    locations_df.loc[:, "town"] = towns
    locations_df.loc[:, "department"] = departments
    locations_df.loc[:, "region"] = regions
    locations_df.loc[:, "postcode"] = postcodes
    locations_df["postcode"] = locations_df["postcode"].astype(int)
    return locations_df
