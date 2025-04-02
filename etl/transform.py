"""Handles data transformations and returns dataframes suited for db loading."""

import time

import pandas as pd
from tqdm import tqdm

from extract import api_call


def transform_data(extracted_data: dict) -> dict[pd.DataFrame]:
    countries_df = transform_countries(extracted_data["countries"])
    pollutants_df = transform_pollutants(extracted_data["pollutants"])
    locations_df = transform_locations(extracted_data["locations"])
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
