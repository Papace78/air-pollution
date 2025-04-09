import streamlit as st
import pandas as pd
from datetime import datetime

def create_sidebar(all_measures: pd.DataFrame):
    """
    Create the sidebar for the Air Quality Dashboard.
    """
    # Sidebar image
    st.sidebar.image(
        "https://hlassets.paessler.com/common/files/graphics/iot/sub-visual_iot-monitoring_air-quality-monitoring-v1.png",
        use_container_width=True,
    )

    #st.sidebar.markdown("## 🌍 Air Quality Dashboard")

    # 📌 Step 1: Choose location filter type
    location_filter_by = st.sidebar.radio(
        "📌 Filter by location type",
        options=["town", "department", "region"],
        horizontal=True,
        label_visibility="collapsed"
    )

    # 📍 Step 2: Choose specific location value
    location_options = sorted(all_measures[location_filter_by].dropna().unique())

    col_loc, col_pollutant = st.sidebar.columns([2, 1])
    with col_loc:
        selected_location = st.selectbox(
            f"🏘️ Select a {location_filter_by}",
            options=location_options,
            key="location_select",
            index=132 if location_filter_by == "town" else 0,
        )

    df_location = all_measures[all_measures[location_filter_by] == selected_location].copy()

    # 🧪 Step 3: Now get pollutants based on filtered location
    pollutant_filter_by = sorted(df_location["pollutant_name"].dropna().unique())

    with col_pollutant:
        selected_pollutant = st.selectbox(
            "🧪 Polluant",
            options=pollutant_filter_by,
            key="pollutant_select",
        )

    df_pollutant = df_location[df_location["pollutant_name"] == selected_pollutant].copy()

    # 🗓️ Step 4: Date range selection
    min_date = df_pollutant["datetime_from"].min().date()
    max_date = df_pollutant["datetime_from"].max().date()
    default_start = datetime.strptime("2023-03-01", "%Y-%m-%d").date()

    if default_start < min_date:
        default_start = min_date
    elif default_start > max_date:
        default_start = max_date

    start_date, end_date = st.sidebar.slider(
    "Select date range:",
    min_value=min_date,
    max_value=max_date,
    value=(default_start, max_date),
    format="YYYY-MM-DD",
    label_visibility="visible"
    )
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    # Filter final dataset by date range
    df_final = df_pollutant[
        (df_pollutant["datetime_from"] >= start_date)
        & (df_pollutant["datetime_to"] <= end_date)
    ]

    # ✅ Show summary
    num_records = len(df_final)
    num_sensors = df_final["sensor_id"].nunique()

    st.sidebar.markdown("---")
    st.sidebar.success(
        f"🔢 {num_records} records matched\n"
        f"🛰️ {num_sensors} sensors"
    )
    with st.sidebar.expander("📊 Global Dataset Info"):
        st.markdown(
            f"🔢 **{all_measures.shape[0]}** total records \n\n"
            f"🛰️ **{all_measures['sensor_id'].nunique()}** sensors\n\n"
            f"📍 **{len(all_measures[location_filter_by].unique())}** {location_filter_by}s"
        )

    return location_filter_by, selected_location, pollutant_filter_by, selected_pollutant, start_date, end_date, df_final
