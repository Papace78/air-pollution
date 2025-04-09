import streamlit as st

from data_generation import get_all_measures, get_all_filtered_data
from data_transformation import (
    build_seasons_df,
    build_weekly_df,
    prepare_time_series_data,
    PollutionLevel,
    PollutionSensors,
    PollutionVariation,
)
from plots import (
    bar_plot_average_concentration,
    bar_plot_average_variation,
    bar_plot_ranking_sensors,
    generate_heatmap,
    plot_time_series,
    pie_plot_weekly,
    pie_plot_seasons,
)
from pollutants import pollutant_info
from sidebar import create_sidebar


all_pollutants = ["co", "o3", "no", "no2", "pm10", "pm25", "so2"]

all_measures = get_all_measures()

(
    location_filter_by,
    selected_location,
    pollutant_filter_by,
    selected_pollutant,
    start_date,
    end_date,
    df_final,
) = create_sidebar(all_measures)

start_date_str = start_date.strftime("%Y-%m-%d")
end_date_str = end_date.strftime("%Y-%m-%d")
pollutant_list = [selected_pollutant]
filtered_df = all_measures[
    (all_measures["pollutant_name"].isin(pollutant_filter_by))
    & (all_measures["datetime_to"] >= start_date)
    & (all_measures["datetime_to"] <= end_date)
]
# --------------------------------------------------------------------------------
st.title("🌍 Air Quality Dashboard")
st.markdown(f"📍 `{selected_location}` • 🧪 `{selected_pollutant}`\n\n")
st.markdown(pollutant_info[selected_pollutant])
with st.expander(label="See all pollutants information"):
    for pol in all_pollutants:
        st.markdown(pollutant_info[pol])


data = get_all_filtered_data(selected_pollutant, start_date_str, end_date_str)

reduction_data = data["reduction_data"]
measurements_data = data["measurements_data"]
heat_data = data["heat_data"]
seasons_data = data["seasons_data"]
weekly_data = data["weekly_data"]


def render_pollution_trend_tab(
    measurements,
    location,
    loc_filter,
    pollutants,
    compare_location="None",
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
    data,
    loc_filter,
    pollutants,
    ref_locations,
):
    st.write("Compare pollution levels between the selected location and others.")
    ranked = PollutionLevel.rank_by_average_concentration(
        data, loc_filter, pollutants, top_n=10, reference_locations=ref_locations
    )
    bar_plot_average_concentration(ranked, loc_filter)


def render_pollution_change_tab(
    data,
    loc_filter,
    pollutants,
    ref_locations,
):
    st.write("Compare pollution change between the selected location and others.")

    ranked = PollutionVariation.rank_by_average_variation(
        data, loc_filter, pollutants, ref_locations, top_n=5
    )
    bar_plot_average_variation(ranked, loc_filter)


def render_sensors_tab(data, loc_filter, pollutants):
    st.write("Explore the available sensors and their coverage.")
    ranked = PollutionSensors.rank_by_number_of_sensors(
        data,
        loc_filter,
        pollutants,
    )
    bar_plot_ranking_sensors(ranked, loc_filter)


def display_cyclical_pollution(
    selected_pollutant,
    seasons_data,
    weekly_data,
    selected_location,
    location_filter_by,
    pollutant_list,
):
    with st.expander(f"📊 Is the pollution level of {selected_pollutant.upper()} cyclical?"):
        tab1, tab2 = st.tabs(["📅 By Season", "📆 By Week/Weekend"])
        with tab1:
            seasons_df = build_seasons_df(
                seasons_data,
                selected_location,
                location_filter_by,
                pollutant_list,
            )
            pie_plot_seasons(seasons_df)

        with tab2:
            weekly_df = build_weekly_df(
                weekly_data, selected_location, location_filter_by, pollutant_list
            )
            pie_plot_weekly(weekly_df)


tab1, tab2, tab3 = st.tabs(
    ["🗺️ Latest recorded across France", "📈 Pollution Trend", "📊 Comparison"]
)

with tab1:
    st.caption(f"🕒 `{end_date_str}` • 🧪 `{selected_pollutant.upper()}`")
    generate_heatmap(heat_data)

toggle_all = st.toggle("🔄 Show all pollutants", value=False)

if toggle_all:
    with tab2:
        with st.spinner("📈 Loading pollution trend..."):
            render_pollution_trend_tab(
                measurements_data,
                selected_location,
                location_filter_by,
                pollutant_filter_by,
            )

    with tab3:
        t1, t2, t3 = st.tabs(
            ["📊 Pollution Levels", "↗️ Pollution Change", "📡 Monitoring Sensors"]
        )
        with t1:
            with st.spinner("📊 Loading level comparison..."):
                render_pollution_levels_tab(
                    measurements_data,
                    location_filter_by,
                    pollutant_filter_by,
                    [selected_location],
                )
        with t2:
            with st.spinner("📈 Calculating variation..."):
                render_pollution_change_tab(
                    reduction_data,
                    location_filter_by,
                    pollutant_filter_by,
                    [selected_location],
                )
        with t3:
            with st.spinner("📡 Loading sensor data..."):
                render_sensors_tab(
                    all_measures,
                    location_filter_by,
                    pollutant_filter_by,
                )

else:
    with st.expander("🔍 Optional: Add a comparison"):
        selected_locations = [selected_location]
        pollutant_optional_list = pollutant_list.copy()
        location_options = sorted(
            filtered_df[filtered_df["pollutant_name"].isin(pollutant_optional_list)][
                location_filter_by
            ]
            .dropna()
            .unique()
        )

        col1, col2 = st.columns(2)
        with col1:
            add_pollutants = st.multiselect(
                "🧪 Compare with another pollutant:",
                options=pollutant_filter_by,
            )
            pollutant_optional_list.extend(add_pollutants)

        with col2:
            compare_location = st.selectbox(
                f"🏘️ Compare with another {location_filter_by.lower()}",
                options=["None"] + location_options,
                index=0,
            )
            selected_locations = [selected_location, compare_location]
            location_options = sorted(
                filtered_df[
                    filtered_df["pollutant_name"].isin(pollutant_optional_list)
                ][location_filter_by]
                .dropna()
                .unique()
            )

    with tab2:
        with st.spinner("📈 Loading pollution trend..."):
            render_pollution_trend_tab(
                measurements_data,
                selected_location,
                location_filter_by,
                pollutant_optional_list,
                compare_location,
            )

    with tab3:
        t1, t2, t3 = st.tabs(
            [
                "📊 Pollution Levels",
                "↗️ Pollution Change",
                "📡 Monitoring Sensors",
            ]
        )
        with t1:
            with st.spinner("📊 Loading level comparison..."):
                render_pollution_levels_tab(
                    measurements_data,
                    location_filter_by,
                    pollutant_optional_list,
                    selected_locations,
                )
        with t2:
            with st.spinner("📈 Calculating variation..."):
                render_pollution_change_tab(
                    reduction_data,
                    location_filter_by,
                    pollutant_optional_list,
                    selected_locations,
                )
        with t3:
            with st.spinner("📡 Loading sensor data..."):
                render_sensors_tab(
                    all_measures,
                    location_filter_by,
                    pollutant_optional_list,
                )


display_cyclical_pollution(
    selected_pollutant,
    seasons_data,
    weekly_data,
    selected_location,
    location_filter_by,
    pollutant_list,
)


st.markdown('---')
with st.expander(label='going further'):
    st.markdown('hallo')

# --- Hide Streamlit Default Styling ---
hide_st_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
"""
st.markdown(hide_st_style, unsafe_allow_html=True)
