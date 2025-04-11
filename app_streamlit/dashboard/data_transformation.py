"""Transforms the data imported from postgreSQL database."""

import pandas as pd


class PollutionSensors:

    @classmethod
    def rank_by_number_of_sensors(
        cls,
        locations_df: pd.DataFrame,
        location_filter_by: str,
        pollutants: list[str],
    ) -> pd.DataFrame:
        """
        Rank locations by the number of sensors per pollutant and return a ranked dataframe.
        """
        # Step 1: Get the number of sensors per location and pollutant
        sensors_per_location = cls.group_by_number_of_sensors(
            locations_df, location_filter_by
        )

        # Step 2: Rank the locations based on the number of sensors
        ranked_sensors = cls.rank_by_number_of_sensors_per_pollutants(
            sensors_per_location, location_filter_by, pollutants
        )

        return ranked_sensors

    @staticmethod
    def group_by_number_of_sensors(
        locations_df: pd.DataFrame, location_filter_by: str
    ) -> pd.DataFrame:
        """
        Group the dataframe by location and pollutant, and count the number of unique sensors.
        """
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

    @staticmethod
    def rank_by_number_of_sensors_per_pollutants(
        sensors_per_location: pd.DataFrame,
        location_filter_by: str,
        pollutants: list[str],
    ) -> pd.DataFrame:
        """
        Rank locations by the number of sensors they have for each pollutant.
        """
        # Filter the data for the relevant pollutants
        sensors_per_location = sensors_per_location[
            sensors_per_location["pollutant_name"].isin(pollutants)
        ]

        # Get the total number of sensors per location
        location_totals = (
            sensors_per_location.groupby(location_filter_by)["sensor_id"]
            .sum()
            .reset_index()
        )

        # Get the top 15 locations with the most sensors
        top_locations = location_totals.nlargest(15, "sensor_id")
        top_locations_sorted = top_locations.sort_values("sensor_id", ascending=True)

        # Filter the original data to include only the top locations
        filtered_grouped = sensors_per_location[
            sensors_per_location[location_filter_by].isin(
                top_locations_sorted[location_filter_by]
            )
        ]

        # Order the locations and sort
        filtered_grouped[location_filter_by] = pd.Categorical(
            filtered_grouped[location_filter_by],
            categories=top_locations_sorted[location_filter_by].tolist(),
            ordered=True,
        )
        filtered_grouped = filtered_grouped.sort_values(location_filter_by)

        return filtered_grouped


class PollutionVariation:
    @classmethod
    def rank_by_average_variation(
        cls,
        df: pd.DataFrame,
        location_filter_by: str,
        pollutants: list[str],
        reference_locations: list[str] = [],
        top_n: int = 5,
    ) -> pd.DataFrame:
        filtered_df = df[df["pollutant_name"].isin(pollutants)]
        lowest_locs, highest_locs = cls.get_top_and_bottom_reductions(
            filtered_df, location_filter_by, top_n
        )

        main_df = cls.filter_df_by_top_bottom_locations(
            filtered_df, lowest_locs, highest_locs, location_filter_by
        )

        reference_df = cls.build_reference_location_df(
            df, location_filter_by, pollutants, reference_locations
        )
        if not reference_df.empty:
            reference_df[location_filter_by] = "SELECTED: " + reference_df[
                location_filter_by
            ].astype(str)

        combined_df = (
            pd.concat([main_df, reference_df], ignore_index=True)
            if not reference_df.empty
            else main_df
        )
        combined_df = cls.add_total_reduction_column(combined_df, location_filter_by)
        return combined_df

    @staticmethod
    def get_top_and_bottom_reductions(
        df_filtered: pd.DataFrame, location_filter_by: str, top_n: int = 5
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        reduction_sums = (
            df_filtered.groupby(location_filter_by, as_index=False)["reduction"]
            .sum()
            .rename(columns={"reduction": "total_reduction"})
        )
        lowest = reduction_sums.nsmallest(top_n, "total_reduction")
        highest = reduction_sums.nlargest(top_n, "total_reduction")
        return lowest, highest

    @staticmethod
    def filter_df_by_top_bottom_locations(
        df_filtered: pd.DataFrame,
        lowest: pd.DataFrame,
        highest: pd.DataFrame,
        location_filter_by: str,
    ) -> pd.DataFrame:
        top_locations = pd.concat([lowest, highest])[location_filter_by].unique()
        return df_filtered[df_filtered[location_filter_by].isin(top_locations)]

    @staticmethod
    def build_reference_location_df(
        df: pd.DataFrame,
        location_filter_by: str,
        pollutants: list[str],
        reference_locations: list[str],
    ) -> pd.DataFrame:
        if not reference_locations:
            return pd.DataFrame()

        ref_df = df[
            (df[location_filter_by].isin(reference_locations))
            & (df["pollutant_name"].isin(pollutants))
        ]

        grouped_ref = ref_df.groupby([location_filter_by, "pollutant_name"], as_index=False)[
            "reduction"
        ].mean()
        return grouped_ref

    @staticmethod
    def add_total_reduction_column(
        df: pd.DataFrame, location_filter_by: str
    ) -> pd.DataFrame:
        avg_reduction_per_pollutant = (
            df.groupby([location_filter_by, "pollutant_name"])["reduction"]
            .mean()
            .reset_index()
        )
        total_reduction = (
            avg_reduction_per_pollutant.groupby(location_filter_by)["reduction"]
            .sum()
            .reset_index()
        )
        df["total_reduction"] = df[location_filter_by].map(
            total_reduction.set_index(location_filter_by)["reduction"]
        )
        return df


class PollutionLevel:

    @classmethod
    def rank_by_average_concentration(
        cls,
        measurements_df: pd.DataFrame,
        location_filter_by: str,
        pollutants: list[str],
        top_n: int = 10,
        reference_locations: list[str] = None,
    ) -> pd.DataFrame:
        # Step 1: Get valid locations with all target pollutants
        valid_locations = cls.get_valid_locations(
            measurements_df, location_filter_by, pollutants
        )

        # Step 2: Filter and average pollutants
        avg_pollutant_df = cls.filter_and_avg_pollutants(
            measurements_df, location_filter_by, pollutants, valid_locations
        )

        # Step 3: Get top N locations based on average concentration
        top_locations = cls.get_top_locations(
            avg_pollutant_df, location_filter_by, top_n
        )

        # Step 4: Filter the dataframe for the top locations
        avg_pollutant_df = avg_pollutant_df[
            avg_pollutant_df[location_filter_by].isin(top_locations)
        ]

        # Step 5: Build reference location data if provided
        reference_location_df = (
            cls.build_reference_location_df(
                measurements_df, location_filter_by, pollutants, reference_locations
            )
            if reference_locations
            else pd.DataFrame()
        )

        # Step 6: Finalize and return the dataframe
        return cls.finalize_avg_df(
            avg_pollutant_df,
            top_locations,
            reference_location_df,
            reference_locations,
            location_filter_by,
        )

    @staticmethod
    def get_valid_locations(
        df: pd.DataFrame,
        location_filter_by: str,
        pollutants: list[str],
    ) -> pd.Series:
        """
        Returns a Series of locations (e.g., towns, departments, etc.) that have at
        least one entry for each pollutant in the `pollutants` list.
        """
        pollutant_counts = (
            df[df["pollutant_name"].isin(pollutants)]
            .groupby(location_filter_by)["pollutant_name"]
            .nunique()
            .reset_index(name="pollutant_count")
        )
        return pollutant_counts[pollutant_counts["pollutant_count"] >= len(pollutants)][
            location_filter_by
        ]

    @staticmethod
    def filter_and_avg_pollutants(
        df: pd.DataFrame,
        location_filter_by: str,
        pollutants: list[str],
        valid_locations: pd.Series,
    ) -> pd.DataFrame:
        """
        Filters the dataframe and calculates the average value per pollutant for each location.
        """
        df_filtered = df[
            (df[location_filter_by].isin(valid_locations))
            & (df["pollutant_name"].isin(pollutants))
        ]
        return df_filtered.groupby(
            [location_filter_by, "pollutant_name"], as_index=False
        )["value"].mean()

    @staticmethod
    def get_top_locations(
        avg_df: pd.DataFrame,
        location_filter_by: str,
        top_n: int,
    ) -> list[str]:
        """
        Returns the top N locations based on average pollutant concentration.
        """
        totals = avg_df.groupby(location_filter_by, as_index=False)["value"].mean()
        top_locations = totals.sort_values(by="value", ascending=False).head(top_n)
        return top_locations[location_filter_by].tolist()

    @staticmethod
    def build_reference_location_df(
        df: pd.DataFrame,
        location_filter_by: str,
        pollutants: list[str],
        reference_locations: list[str],
    ) -> pd.DataFrame:
        """
        Builds a dataframe for reference locations.
        """
        ref_dfs = []
        for ref in reference_locations:
            ref_df = df[
                (df[location_filter_by] == ref)
                & (df["pollutant_name"].isin(pollutants))
            ]
            if ref_df.empty:
                continue
            ref_avg = ref_df.groupby("pollutant_name", as_index=False)["value"].mean()
            ref_avg[location_filter_by] = f"SELECTED: {ref}"
            ref_dfs.append(ref_avg[[location_filter_by, "pollutant_name", "value"]])

        return pd.concat(ref_dfs, ignore_index=True) if ref_dfs else pd.DataFrame()

    @staticmethod
    def finalize_avg_df(
        avg_df: pd.DataFrame,
        top_locations: list[str],
        reference_location_df: pd.DataFrame,
        reference_locations: list[str],
        location_filter_by: str,
    ) -> pd.DataFrame:
        """
        Finalizes the dataframe, sorting locations and adding the reference data.
        """
        ordered_locations = top_locations.copy()
        if not reference_location_df.empty:
            avg_df = pd.concat([avg_df, reference_location_df], ignore_index=True)
            ordered_locations += [f"SELECTED: {ref}" for ref in reference_locations]

        avg_df[location_filter_by] = pd.Categorical(
            avg_df[location_filter_by], categories=ordered_locations, ordered=True
        )
        avg_df = avg_df.sort_values(location_filter_by)

        avg_df["x_key"] = (
            avg_df[location_filter_by].astype(str) + "_" + avg_df["pollutant_name"]
        )
        return avg_df


def prepare_time_series_data(
    measurements: pd.DataFrame,
    selected_location: str,
    location_filter_by: str,
    pollutants: list[str],
    compare_location: str = "None",
):
    # Filter to keep only selected pollutants
    df = measurements[measurements["pollutant_name"].isin(pollutants)]

    # Group and average values
    df_grouped = (
        df.groupby([location_filter_by, "pollutant_name", "datetime_to"])
        .agg(average=("value", "mean"))
        .reset_index()
    )

    # Split data
    df_filtered = df_grouped[df_grouped[location_filter_by] == selected_location]
    df_compare = df_grouped[df_grouped[location_filter_by] == compare_location]

    # Compute Q25 / Q75
    quantiles = (
        df.groupby(["datetime_to", "pollutant_name"])["value"]
        .quantile([0.25, 0.75])
        .unstack()
    )
    quantiles.columns = ["Q25", "Q75"]

    # Merge quantiles with main df
    df_filtered = df_filtered.merge(
        quantiles,
        left_on=["datetime_to", "pollutant_name"],
        right_index=True,
        how="left",
    )

    return df_filtered, df_compare


def build_seasons_df(
    df: pd.DataFrame,
    selected_pollutants: list[str],
):
    df_filtered = df[df["pollutant_name"].isin(selected_pollutants)]

    df_filtered["datetime_from"] = pd.to_datetime(df_filtered["datetime_from"])

    # Function to determine the season from a datetime
    def get_season(date):
        month = date.month
        if month in [12, 1, 2]:
            return "Winter"
        elif month in [3, 4, 5]:
            return "Spring"
        elif month in [6, 7, 8]:
            return "Summer"
        else:
            return "Fall"

    # Apply the function to create a 'season' column
    df_filtered["season"] = df_filtered["datetime_from"].apply(get_season)

    # Calculate total values per season
    seasonal_values = (
        df_filtered.groupby(["season"])["value"].mean().round(2).reset_index()
    )

    season_order = ["Spring", "Summer", "Fall", "Winter"]
    seasonal_values["season"] = pd.Categorical(
        seasonal_values["season"], categories=season_order, ordered=True
    )

    return seasonal_values


def transforms_measures_to_reduction(df, start_date, end_date):
    df['datetime_from'] = pd.to_datetime(df['datetime_from'])
    df['datetime_to'] = pd.to_datetime(df['datetime_to'])

    # Define your start and end date
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    # Find the closest datetime_from and datetime_to for each town and pollutant
    def find_closest_dates(group, start_date, end_date):
        closest_start = group.iloc[(group['datetime_from'] - start_date).abs().argmin()]
        closest_end = group.iloc[(group['datetime_to'] - end_date).abs().argmin()]

        return pd.DataFrame([{
            'town': closest_start['town'],
            'department': closest_start['department'],
            'region': closest_start['region'],
            'pollutant_name': closest_start['pollutant_name'],
            'pollutant_units': closest_start['pollutant_units'],
            'value': closest_start['value'],
            'datetime_from': closest_start['datetime_from'],
            'datetime_to': closest_end['datetime_to'],
            'reduction': closest_start['value'] - closest_end['value']
        }])

    return df.groupby(['town', 'pollutant_name']).apply(find_closest_dates, start_date=start_date, end_date=end_date).reset_index(drop=True)
