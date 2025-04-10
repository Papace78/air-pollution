import streamlit as st
import pandas as pd
from datetime import datetime

from data_generation import (
    get_all_measures,
    get_heatmap_measures,
    get_measurements_daterange_data,
    get_locations,
)
from data_transformation import transforms_measures_to_reduction, build_seasons_df
from plots import generate_heatmap, pie_plot_seasons
from pollutants import pollutants_info
from rendering import (
    render_pollution_change_tab,
    render_pollution_levels_tab,
    render_pollution_trend_tab,
    render_sensors_tab,
)


st.markdown(
    """
    <style>
        .block-container {
            padding: 10;   /* Remove internal padding to use full screen */
            margin: 10;    /* Remove any margin around the content */
            max-width: 100%; /* Use the full width available */
        }
        .main {
            width: 100%;  /* Make sure content uses the entire screen width */
        }
    </style>
    """,
    unsafe_allow_html=True,
)
left_co, cent_co, last_co = st.columns([1, 1, 1])
with cent_co:
    st.image(
        "https://hlassets.paessler.com/common/files/graphics/iot/sub-visual_iot-monitoring_air-quality-monitoring-v1.png",
        use_container_width=True,
    )
st.markdown(
    """
    <style>
        .skip-space {
            height: 10vh;  /* Skip one full screen height */
        }
    </style>
    """,
    unsafe_allow_html=True,
)
st.markdown('<div class="skip-space"></div>', unsafe_allow_html=True)
st.markdown("___", unsafe_allow_html=True)


# Initialize session state variables
if "go1" not in st.session_state:
    st.session_state.go1 = False
if "go2" not in st.session_state:
    st.session_state.go2 = False


# Title
left_co, cent_co, last_co = st.columns([0.9,1,0.9])
with cent_co:
    st.title("🌿 Air Quality Dashboard")


# ------ FIRST SET OF FILTERS SELECTION ---------------
# Filters for pollutants and for date

st.markdown("## 🔬 Select one or more pollutants")

col1, col2, col3 = st.columns([1, 1, 1])


selected_pollutant = None
pollutant_details = None
selected_pollutants = []


def create_expandable_tile_with_checkbox(pollutant_name, pollutant_details, key):
    col1, col2 = st.columns([1, 15])
    with col1:
        selected = st.checkbox(
            pollutant_name, key=f"checkbox_{key}", label_visibility="collapsed"
        )  # Checkbox for selection
    with col2:
        with st.expander(
            pollutant_name, expanded=False
        ):  # Expandable section for details
            st.markdown(f"### {pollutant_name}")
            st.write(f"**Sources:** {pollutant_details['sources']}")
            st.write(f"**Health Effects:** {pollutant_details['health_effects']}")
            st.write(
                f"**Environmental Impact:** {pollutant_details['environmental_impact']}"
            )
    return selected


with col1:
    if create_expandable_tile_with_checkbox(
        "🚗 Carbon Monoxide (CO)", pollutants_info["🚗 Carbon Monoxide (CO)"], key="co"
    ):
        selected_pollutants.append("🚗 Carbon Monoxide (CO)")
    if create_expandable_tile_with_checkbox(
        "🌞 Ozone (O₃)", pollutants_info["🌞 Ozone (O₃)"], key="o3"
    ):
        selected_pollutants.append("🌞 Ozone (O₃)")
    if create_expandable_tile_with_checkbox(
        "⚡ Nitric Oxide (NO)", pollutants_info["⚡ Nitric Oxide (NO)"], key="no"
    ):
        selected_pollutants.append("⚡ Nitric Oxide (NO)")

with col2:
    if create_expandable_tile_with_checkbox(
        "⚡ Nitrogen Dioxide (NO₂)",
        pollutants_info["⚡ Nitrogen Dioxide (NO₂)"],
        key="no2",
    ):
        selected_pollutants.append("⚡ Nitrogen Dioxide (NO₂)")
    if create_expandable_tile_with_checkbox(
        "🌫️ Particulate Matter (PM₁₀)",
        pollutants_info["🌫️ Particulate Matter (PM₁₀)"],
        key="pm10",
    ):
        selected_pollutants.append("🌫️ Particulate Matter (PM₁₀)")
    if create_expandable_tile_with_checkbox(
        "🌫️ Fine Particulate Matter (PM₂.₅)",
        pollutants_info["🌫️ Fine Particulate Matter (PM₂.₅)"],
        key="pm25",
    ):
        selected_pollutants.append("🌫️ Fine Particulate Matter (PM₂.₅)")

with col3:
    if create_expandable_tile_with_checkbox(
        "🌋 Sulfur Dioxide (SO₂)", pollutants_info["🌋 Sulfur Dioxide (SO₂)"], key="so2"
    ):
        selected_pollutants.append("🌋 Sulfur Dioxide (SO₂)")

min_date = datetime.strptime("2017-01-01", "%Y-%m-%d").date()
max_date = datetime.strptime("2025-04-01", "%Y-%m-%d").date()

start_date, end_date = st.slider(
    "Select date range:",
    min_value=min_date,
    max_value=max_date,
    value=(min_date, max_date),
    format="YYYY-MM-DD",
    label_visibility="visible",
)
start_date_str = pd.to_datetime(start_date).replace(day=1).strftime("%Y-%m-%d")
end_date_str = pd.to_datetime(end_date).replace(day=1).strftime("%Y-%m-%d")


# 🔹 Track Go1 button click
go1_clicked = False

# ------ AFTER FIRST SET OF FILTERS SELECTED ---------------
if st.button("Go", key=1):
    st.session_state.go1 = True
    st.session_state.go2 = False
    st.session_state.selected_pollutants = selected_pollutants
    st.session_state.start_date_str = start_date_str
    st.session_state.end_date_str = end_date_str
    go1_clicked = True

if st.session_state.get("go1", False):
    st.markdown(f"`{', '.join(selected_pollutants)}`\n\n")

# ------ SECOND SET OF (LOCAL) FILTERS ---------------
if go1_clicked:
    selected_pollutants = st.session_state.selected_pollutants
    start_date_str = st.session_state.start_date_str
    end_date_str = st.session_state.end_date_str

    if selected_pollutants == []:
        st.write("No pollutants selected.")
    else:
        with st.spinner("📈 Loading data..."):
            pollutants_code = [
                pollutants_info[pollutant]["code"] for pollutant in selected_pollutants
            ]

            # 🔹 Heavy data fetching and processing (run once)
            heat_data = pd.DataFrame()
            for pol in pollutants_code:
                heat_data = pd.concat(
                    [heat_data, get_heatmap_measures(pol, start_date_str, end_date_str)]
                )
            if heat_data.empty:
                heat_data = pd.DataFrame(
                    columns=[
                        "town",
                        "latitude",
                        "longitude",
                        "pollutant",
                        "units",
                        "average",
                        "datetime_from",
                        "datetime_to",
                    ]
                )
            df_grouped = (
                heat_data.groupby(["town", "latitude", "longitude"]).sum().reset_index()
            )
            df_grouped = df_grouped[df_grouped["pollutant"] == "".join(pollutants_code)]

            st.session_state.heat_data = heat_data
            st.session_state.df_grouped = df_grouped
            st.session_state.pollutants_code = pollutants_code

# ------ AFTER SECOND SET OF FILTERS SELECTED ---------------
if st.session_state.get("go1", False) and "df_grouped" in st.session_state:
    selected_pollutants = st.session_state.selected_pollutants
    start_date_str = st.session_state.start_date_str
    end_date_str = st.session_state.end_date_str
    df_grouped = st.session_state.df_grouped
    pollutants_code = st.session_state.pollutants_code

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("## 🗺️ National")
        st.caption(
            f"Displaying locations that have records for all selected pollutants at 🕒`{end_date_str}`"
        )
        tab1, tab2 = st.tabs(["🗺️ Map", "📋 Table"])
        with tab1:
            generate_heatmap(df_grouped)
        with tab2:
            st.dataframe(df_grouped)

    with col2:
        locations = get_locations()
        st.markdown("## 🏙️ Local")
        col1, col2, col3 = st.columns([4, 4, 1])
        with col1:
            location_filter_by = st.radio(
                "📌 Filter by location type",
                options=["town", "department", "region"],
                horizontal=True,
                index=1,
            )
            location_options = sorted(locations[location_filter_by].dropna().unique())
        with col2:
            selected_location = st.selectbox(
                f"🏘️ Select a {location_filter_by}",
                options=location_options,
                key="location_select",
            )
        with col3:
            st.caption("")
            go2_clicked = False
            if st.button("Go", key=2):
                st.session_state.go2 = True
                st.session_state.location_filter_by = location_filter_by
                st.session_state.selected_location = selected_location
                with st.spinner(""):
                    try:
                        st.session_state.measurements_df = (
                            get_measurements_daterange_data(
                                start_date_str,
                                end_date_str,
                            )
                        )
                        # Optionally, you can also store other relevant data from here, like `seasons_df`
                    except Exception as e:
                        st.markdown(
                            "⚠️ Issue loading data. Try with a shorter time range."
                        )
                        st.error(f"❌ Error: {e}")
                go2_clicked = True

        if st.session_state.go1 and st.session_state.go2:
            location_filter_by = st.session_state.location_filter_by
            selected_location = st.session_state.selected_location
            measurements_df = st.session_state.measurements_df

            with st.container(height=700):
                with st.spinner("📈 Loading pollution trend..."):
                    try:
                        tab1, tab2 = st.tabs(["📊 Graph", "📋 Table"])
                        with tab1:
                            render_pollution_trend_tab(
                                measurements_df,
                                selected_location,
                                location_filter_by,
                                pollutants_code,
                            )
                        with tab2:
                            measurements_df
                        with st.expander(label="Is the data cyclical ?"):
                            seasons_df = build_seasons_df(
                                measurements_df,
                                pollutants_code,
                            )
                            pie_plot_seasons(seasons_df)
                    except Exception as e:
                        st.markdown(
                            "⚠️ Issue loading data. Try with shorter time range or load again."
                        )
                        st.error(f"❌ Error: {e}")
                st.markdown("___", unsafe_allow_html=True)
                with st.spinner("📊 Loading level comparison..."):
                    try:
                        tab1, tab2 = st.tabs(["📊 Graph", "📋 Table"])
                        with tab1:
                            render_pollution_levels_tab(
                                measurements_df,
                                location_filter_by,
                                pollutants_code,
                                [selected_location],
                            )
                        with tab2:
                            measurements_df
                    except Exception as e:
                        st.markdown(
                            "⚠️ Issue loading data. Try with shorter time range or load again."
                        )
                        st.error(f"❌ Error: {e}")
                st.markdown("___", unsafe_allow_html=True)

                with st.spinner("📊 Loading variation comparison..."):
                    try:
                        reduction_data = transforms_measures_to_reduction(
                            measurements_df,
                            start_date_str,
                            end_date_str,
                        )
                        tab1, tab2 = st.tabs(["📊 Graph", "📋 Table"])
                        with tab1:
                            render_pollution_change_tab(
                                reduction_data,
                                location_filter_by,
                                pollutants_code,
                                [selected_location],
                            )
                        with tab2:
                            reduction_data
                    except Exception as e:
                        st.markdown(
                            "⚠️ Issue loading data. Try with shorter time range or load again."
                        )
                        st.error(f"❌ Error: {e}")
                st.markdown("___", unsafe_allow_html=True)
                with st.spinner("📡 Loading sensor data..."):
                    try:
                        sensors_df = get_all_measures()
                        tab1, tab2 = st.tabs(["📊 Graph", "📋 Table"])
                        with tab1:
                            render_sensors_tab(
                                sensors_df,
                                location_filter_by,
                                pollutants_code,
                            )
                        with tab2:
                            sensors_df
                    except Exception as e:
                        st.markdown(
                            "⚠️ Issue loading data. Try with shorter time range or load again."
                        )
                        st.error(f"❌ Error: {e}")


st.markdown("---")
with st.expander(label="going further"):
    st.markdown("hallo")

# --- Hide Streamlit Default Styling ---
hide_st_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
"""
st.markdown(hide_st_style, unsafe_allow_html=True)
