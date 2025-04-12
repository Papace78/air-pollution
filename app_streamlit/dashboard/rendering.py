"""Join data transformation and plots to render the graphs on dashboard."""

import pandas as pd
import streamlit as st

from data_transformation import (
    build_seasons_df,
    prepare_time_series_data,
    prepare_time_stats_data,
    PollutionLevel,
    PollutionSensors,
    PollutionVariation,
)
from plots import (
    bar_plot_average_concentration,
    bar_plot_average_variation,
    bar_plot_ranking_sensors,
    plot_time_series,
    pie_plot_seasons,
)


def render_pollution_trend_tab(
    measurements: pd.DataFrame,
    location: list[str],
    loc_filter: str,
    pollutants: list[str],
):
    selected_location = location[0]
    compare_locations = location[1:]
    df_filtered, df_compare = prepare_time_series_data(
        measurements=measurements,
        selected_location=selected_location,
        location_filter_by=loc_filter,
        pollutants=pollutants,
        compare_locations=compare_locations,
    )
    if df_filtered.empty and df_compare.empty:
        st.markdown("*No data for selected pollutants and locations.*")
        return None
    plot_time_series(
        df_filtered,
        df_compare,
        location_filter_by=loc_filter,
        selected_location=selected_location,
        compare_locations=compare_locations,
    )
    with st.expander(label="Summary Statistics", expanded=True):
        df_concat = pd.concat(
            [df_filtered.drop(columns=["Q25", "Q75"]), df_compare],
            axis=0,
            ignore_index=True,
        )
        st.dataframe(prepare_time_stats_data(df_concat, loc_filter, location))
        st.markdown("_All values are expressed in µg/m³ (micrograms per cubic meter)._")

    with st.expander(label="Is the pollution seasonal ?"):
        seasons_df = build_seasons_df(
            measurements,
            pollutants,
        )
        pie_plot_seasons(seasons_df)


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
