"""Join data transformation and plots to render the graphs on dashboard."""

import pandas as pd

from data_transformation import (
    prepare_time_series_data,
    PollutionLevel,
    PollutionSensors,
    PollutionVariation,
)
from plots import (
    bar_plot_average_concentration,
    bar_plot_average_variation,
    bar_plot_ranking_sensors,
    plot_time_series,
)

def render_pollution_trend_tab(
    measurements: pd.DataFrame,
    location: str,
    loc_filter: str,
    pollutants: list[str],
    compare_location: str = "None",
):
    df_filtered, df_compare = prepare_time_series_data(
        measurements=measurements,
        selected_location=location,
        location_filter_by=loc_filter,
        pollutants=pollutants,
        compare_location=compare_location,
    )
    plot_time_series(
        df_filtered,
        df_compare,
        selected_location=location,
        compare_location=compare_location,
    )


def render_pollution_levels_tab(
    data: pd.DataFrame,
    loc_filter: str,
    pollutants: list[str],
    ref_locations: list[str],
):
    ranked = PollutionLevel.rank_by_average_concentration(
        data, loc_filter, pollutants, top_n=10, reference_locations=ref_locations
    )
    bar_plot_average_concentration(ranked, loc_filter)


def render_pollution_change_tab(
    data: pd.DataFrame,
    loc_filter: str,
    pollutants: list[str],
    ref_locations: list[str],
):
    ranked = PollutionVariation.rank_by_average_variation(
        data, loc_filter, pollutants, ref_locations, top_n=5
    )
    bar_plot_average_variation(ranked, loc_filter)


def render_sensors_tab(data: pd.DataFrame, loc_filter: str, pollutants: list[str]):
    ranked = PollutionSensors.rank_by_number_of_sensors(
        data,
        loc_filter,
        pollutants,
    )
    bar_plot_ranking_sensors(ranked, loc_filter)
