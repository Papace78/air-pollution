import pandas as pd


def rank_by_number_of_sensors(
    locations_df: pd.DataFrame,
    location_filter_by: str,
    pollutants: list[str],
) -> pd.DataFrame:
    sensors_per_location = group_by_number_of_sensors(locations_df, location_filter_by)
    ranked_sensors = rank_by_number_of_sensors_per_pollutants(sensors_per_location, location_filter_by, pollutants)
    return ranked_sensors


def group_by_number_of_sensors(locations_df: pd.DataFrame, location_filter_by: str):

    sensors_per_location_filter = (
        locations_df.groupby([location_filter_by, "pollutant_name"])["sensor_id"]
        .nunique()
        .reset_index()
    )
    sensors_per_location_filter = sensors_per_location_filter.sort_values(
        by="sensor_id"
    )
    sensors_per_location_filter["x_key"] = (
        sensors_per_location_filter[location_filter_by]
        + "_"
        + sensors_per_location_filter["pollutant_name"]
    )
    return sensors_per_location_filter


def rank_by_number_of_sensors_per_pollutants(
    sensors_per_location: pd.DataFrame, location_filter_by: str, pollutants: list[str]
):
    sensors_per_location = sensors_per_location[sensors_per_location['pollutant_name'].isin(pollutants)]

    location_totals = (
        sensors_per_location.groupby(location_filter_by)["sensor_id"]
        .sum()
        .reset_index()
    )
    top_locations = location_totals.nlargest(15, "sensor_id")
    top_locations_sorted = top_locations.sort_values("sensor_id", ascending=True)

    filtered_grouped = sensors_per_location[
        sensors_per_location[location_filter_by].isin(
            top_locations_sorted[location_filter_by]
        )
    ]

    filtered_grouped[location_filter_by] = pd.Categorical(
        filtered_grouped[location_filter_by],
        categories=top_locations_sorted[location_filter_by].tolist(),
        ordered=True,
    )
    filtered_grouped = filtered_grouped.sort_values(location_filter_by)
    return filtered_grouped

def rank_by_average_concentration(locations_df: pd.DataFrame, location_filter_by: str, pollutants: list[str]) -> pd.DataFrame:
    # Step 1: Filter the dataframe based on the selected pollutants
    df_filtered = locations_df[locations_df['pollutant_name'].isin(pollutants)]

    # Step 2: Group by location and pollutant, calculating the average value
    avg_value_per_location = df_filtered.groupby([location_filter_by, 'pollutant_name'], as_index=False)['value'].mean()

    # Step 3: Compute the total average value per location by averaging across pollutants
    avg_value_per_location_total = avg_value_per_location.groupby(location_filter_by, as_index=False)['value'].sum()

    # Step 4: Sort locations by their average pollutant value (across all pollutants)
    avg_value_per_location_total_sorted = avg_value_per_location_total.sort_values(by='value', ascending=True)

    # Step 5: Reorder the location names based on sorted average values
    ordered_locations = avg_value_per_location_total_sorted[location_filter_by].tolist()

    # Step 6: Create the combined key for x-axis labels
    avg_value_per_location['x_key'] = avg_value_per_location[location_filter_by] + "_" + avg_value_per_location['pollutant_name']

    # Step 7: Apply the sorting by location to the avg_value_per_location DataFrame
    avg_value_per_location[location_filter_by] = pd.Categorical(
        avg_value_per_location[location_filter_by],
        categories=ordered_locations,  # Ensure order is based on average value
        ordered=True
    )

    # Step 8: Sort the data according to the ordered location names
    avg_value_per_location = avg_value_per_location.sort_values(location_filter_by)

    return avg_value_per_location
