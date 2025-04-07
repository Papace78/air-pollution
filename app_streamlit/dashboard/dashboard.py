import streamlit as st

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from supabase import create_client, Client

import folium
from folium.plugins import HeatMap

# --- Supabase config ---
url = "https://dluhqrwmercbvgfhoxef.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRsdWhxcndtZXJjYnZnZmhveGVmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDM3NTc5ODUsImV4cCI6MjA1OTMzMzk4NX0._R5TinJKV42TU0pFn0ZhJnzDjqshX4NZesVl9O8KC9o"

supabase: Client = create_client(url, key)


# ----- SIDEBAR: Location Type → Location Value → Pollutant → Date ------

# Sidebar image
st.sidebar.image(
    "https://hlassets.paessler.com/common/files/graphics/iot/sub-visual_iot-monitoring_air-quality-monitoring-v1.png",
    use_container_width=True,
)

st.sidebar.markdown("## 🌍 Air Quality Dashboard")
# st.sidebar.markdown("### 🧭 Step-by-step filtering")

# Load full dataset
response = supabase.rpc("get_filter_data").execute()
all_measures = pd.DataFrame(response.data)

# Ensure datetime columns are parsed
all_measures["datetime_from"] = pd.to_datetime(all_measures["datetime_from"])
all_measures["datetime_to"] = pd.to_datetime(all_measures["datetime_to"])

# 📌 Step 1: Choose location filter type
location_filter_by = st.sidebar.radio(
    "📌 Filter by location type",
    options=["town", "department", "region"],
    horizontal=True,
)

# 📍 Step 2: Choose specific location value
location_options = sorted(all_measures[location_filter_by].dropna().unique())

col_loc, col_pollutant = st.sidebar.columns([2, 1])
with col_loc:
    selected_location = st.selectbox(
        f"🏘️ Select a {location_filter_by}",
        options=location_options,
        key="location_select",
    )
df_location = all_measures[all_measures[location_filter_by] == selected_location].copy()

# 🧪 Step 3: Now get pollutants based on filtered location
pollutants = sorted(df_location["pollutant_name"].dropna().unique())

with col_pollutant:
    selected_pollutant = st.selectbox(
        "🧪 Polluant", options=pollutants, key="pollutant_select"
    )

df_pollutant = df_location[df_location["pollutant_name"] == selected_pollutant].copy()

# 🗓️ Step 4: Date range selection
min_date = df_pollutant["datetime_from"].min().date()
max_date = df_pollutant["datetime_from"].max().date()

col1, col2 = st.sidebar.columns(2)
with col1:
    start_date = pd.to_datetime(
        st.date_input(
            "📅 Start date",
            value=min_date,
            min_value=min_date,
            max_value=max_date,
        )
    )
with col2:
    end_date = pd.to_datetime(
        st.date_input(
            "📅 End date",
            value=max_date,
            min_value=min_date,
            max_value=max_date,
        )
    )

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
    f"📍 `{selected_location}` • 🧪 `{selected_pollutant}`\n\n"
    f"🔢 {num_records} records matched\n"
    f"🛰️ {num_sensors} sensors"
)
with st.sidebar.expander("📊 Global Dataset Info"):
    st.markdown(
        f"🔢 **{all_measures.shape[0]}** total records \n\n"
        f"🛰️ **{all_measures['sensor_id'].nunique()}** sensors\n\n"
        f"📍 **{len(all_measures[location_filter_by].unique())}** {location_filter_by}s"
    )

st.markdown("### 📊 Dataset Summary")

col1, col2, col3 = st.columns(3)

col1.metric(label="Total Measurements", value=f"{all_measures.shape[0]:,}")
col2.metric(label="🛰️ Unique Sensors", value=f"{all_measures['sensor_id'].nunique()}")
col3.metric(
    label=f"📍 {location_filter_by.title()} Count",
    value=f"{all_measures[location_filter_by].nunique()}",
)


start_date_str = start_date.strftime("%Y-%m-%d")
end_date_str = end_date.strftime("%Y-%m-%d")

# HEATMAP
def generate_heatmap():
    response = supabase.rpc(
        "heatmap_data",
        {
            "pollutant_name": selected_pollutant,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
        },
    ).execute()

    heat_df = pd.DataFrame(response.data)
    heat_data = heat_df[["latitude", "longitude", "average"]].values.tolist()

    france_coordinates = [46.5, 2.2]
    # Create a folium map with a custom tile layer
    m = folium.Map(location=france_coordinates, zoom_start=6)

    # Define the heatmap gradient for better visualization
    gradient = {
        "0.2": "blue",
        "0.4": "lime",
        "0.6": "yellow",
        "0.8": "orange",
        "1": "red",
    }

    # Add HeatMap with smoother transitions
    HeatMap(heat_data, radius=25, blur=35, max_zoom=15, gradient=gradient).add_to(m)

    # Add custom tooltips without any markers/icons
    for i, row in heat_df.iterrows():
        tooltip = f"""
        <b>Ville:</b> {row['town']}<br>
        <b>Polluant:</b> {row['pollutant']}<br>
        <b>Valeur Moyenne:</b> {row['average']} {row['units']}<br>
        <i>Hover to explore</i>
        """

        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]],
            radius=10,
            color=None,
            fill=True,
            fill_opacity=0,
            tooltip=tooltip,
        ).add_to(m)

    # Apply custom CSS for map container
    st.markdown(
        """
        <style>
        .folium-map {
            height: 80vh;  /* 80% of the viewport height */
            width: 100%;
            border-radius: 10px;
            box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.1);
        }
        </style>
    """,
        unsafe_allow_html=True,
    )

    # Render the map with a responsive height
    st.components.v1.html(m._repr_html_(), height=600)

generate_heatmap()



def generate_time_serie(add_pollutant: str, compare_location: str):
    # Now pass these string values to the RPC request
    response = supabase.rpc(
        "get_measurements_by_date_range",
        {"start_date": start_date_str, "end_date": end_date_str},
    ).execute()
    df = pd.DataFrame(response.data)
    df = df[df["department"] != "Not_found"]
    df = df[df["region"] != "Île-de-france"]

    if add_pollutant != "None":
        pollutants = [selected_pollutant, add_pollutant]
    else:
        pollutants = [selected_pollutant]
    df = df[df["pollutant_name"].isin(pollutants)]

    df_filtered = df[
        df[location_filter_by].str.contains(selected_location, case=False, na=False)
    ]

    # Step 1: Group by relevant columns and calculate the average concentration per group
    df_grouped = (
        df.groupby([location_filter_by, "pollutant_name", "datetime_to"])
        .agg(average=("value", "mean"))
        .reset_index()
    )

    # Get rank
    df_rank = (
        df_grouped.groupby(by=[location_filter_by])
        .agg(average=("average", "mean"))
        .sort_values(by="average", ascending=False)
        .reset_index()
    )
    rank = df_rank[df_rank[location_filter_by] == selected_location].index[0]
    print(f"rank = {rank} / {df_rank.shape[0]}")

    # Step 2: Filter the data for the specific town (e.g., Orléans)
    df_filtered = df_grouped[df_grouped[location_filter_by] == f"{selected_location}"]
    df_compare = df_grouped[df_grouped[location_filter_by] == f"{compare_location}"]

    quantiles = (
        df.groupby(["datetime_to", "pollutant_name"])["value"]
        .quantile([0.25, 0.75])
        .unstack()
    )
    quantiles.columns = ["Q25", "Q75"]

    df_filtered = df_filtered.merge(
        quantiles,
        left_on=["datetime_to", "pollutant_name"],
        right_index=True,
        how="left",
    )

    fig = px.line(
        df_filtered,
        x="datetime_to",
        y="average",
        color="pollutant_name",
        title=f"Pollutant Concentration Over Time - {selected_location}",
        labels={
            "value": "Concentration (µg/m³)",
            "datetime_to": "Time",
            "name": "Pollutant",
        },
        markers=True,
    )
    fig.update_layout(
        xaxis=dict(title=""),
        yaxis=dict(title="Concentration (µg/m³)"),
        hovermode="x unified",
    )

    fig.update_traces(line=dict(width=2), marker=dict(size=4))

    fig.update_xaxes(
        showgrid=True,
        gridwidth=0.5,
        gridcolor="lightgray",
        showticklabels=True,
    )

    if compare_location != "None":
        fig.update_layout(
            title={
                "text": f"Pollutant Concentration Over Time comparison - {selected_location} / {compare_location}"
            }
        )
        for poll in df_compare["pollutant_name"].unique():
            poll_data = df_compare[df_compare["pollutant_name"] == poll]

            fig.add_trace(
                go.Scatter(
                    x=poll_data["datetime_to"],
                    y=poll_data["average"],
                    mode="lines",
                    line=dict(dash="dot", width=1),
                    name=f"{poll} ({compare_location})",
                    showlegend=True,
                    opacity=0.8,
                )
            )

    else:
        fig.update_layout(
            title={
                "text": f"Pollutant Concentration Over Time comparison {selected_location} <br><span style='font-size:10px;'>with lower (Q25) and upper (Q75) range</span>",
            }
        )
        for poll in df_filtered["pollutant_name"].unique():
            poll_data = df_filtered[df_filtered["pollutant_name"] == poll]

            fig.add_trace(
                go.Scatter(
                    x=poll_data["datetime_to"],
                    y=poll_data["Q25"],
                    mode="lines",
                    line=dict(dash="dot", width=1),
                    name=f"{poll} Q25",
                    showlegend=False,
                    opacity=0.4,
                )
            )

            fig.add_trace(
                go.Scatter(
                    x=poll_data["datetime_to"],
                    y=poll_data["Q75"],
                    mode="lines",
                    line=dict(dash="dot", width=1),
                    name=f"{poll} Q75",
                    showlegend=False,
                    opacity=0.4,
                )
            )

    st.plotly_chart(fig, use_container_width=True)

#generate_time_serie(add_pollutant, compare_location)

def generate_seasons_pie():
    response = supabase.rpc(
        "get_seasons",
        {
            "pollutant_name": selected_pollutant,
            "start_date": start_date_str,
            "end_date": end_date_str,
        },
    ).execute()
    df = pd.DataFrame(response.data)
    df = df[df["department"] != "Not_found"]
    df = df[df["region"] != "Île-de-france"]

    df_filtered = df[
        df.apply(
            lambda row: row.astype(str).str.contains(f"{selected_location}").any(),
            axis=1,
        )
    ]
    df_grouped = df_filtered.groupby("season")["average"].mean().reset_index()

    season_order = ["Spring", "Summer", "Fall", "Winter"]
    df_grouped["season"] = pd.Categorical(
        df_grouped["season"], categories=season_order, ordered=True
    )

    fig = px.pie(
        df_grouped,
        names="season",
        values="average",
        labels={"average": "Mean concentration (µg/m³)"},
    )

    fig.update_layout(showlegend=False)

    fig.update_traces(textinfo="percent+label")

    st.plotly_chart(fig, use_container_width=True)

def generate_weekly_pie():
    response = supabase.rpc(
        "get_week_type",
        {
            "pollutant_name": selected_pollutant,
            "start_date": start_date_str,
            "end_date": end_date_str,
        },
    ).execute()
    df = pd.DataFrame(response.data)
    df = df[df["department"] != "Not_found"]
    df = df[df["region"] != "Île-de-france"]
    df_filtered = df[
        df.apply(
            lambda row: row.astype(str).str.contains(f"{selected_location}").any(), axis=1
        )
    ]
    df_grouped = df_filtered.groupby("week_type")["average"].mean().reset_index()

    df_grouped["week_type"] = pd.Categorical(
        df_grouped["week_type"], categories=["Weekdays", "Weekend"], ordered=True
    )

    fig = px.pie(
        df_grouped,
        names="week_type",
        values="average",
        labels={"average": "Average concentration (µg/m³)"},
        color="week_type",
    )

    fig.update_layout(showlegend=False)
    fig.update_traces(textinfo="percent+label")

    st.plotly_chart(fig, use_container_width=True)


tab1, tab2, tab3 = st.tabs(["📅 All time", "📅 By Season", "📆 By Week/Weekend"])

with tab1:
    # Time serie
    col1, col2 = st.columns(2)

    # First selectbox for Compare Pollutant
    with col1:
        add_pollutant = st.selectbox(
            "🧪 Compare with polluant",
            options=["None"] + pollutants,
            index=0,
            key="pollutant_select_1",
        )

    with col2:
        compare_location = st.selectbox(
            f"🏘️ Compare with {location_filter_by}",
            options=["None"] + location_options,
            index=0,
            key="location_select_1",
        )

    generate_time_serie(add_pollutant, compare_location)

with tab2:
    generate_seasons_pie()

with tab3:
    generate_weekly_pie()


# --- Hide Streamlit Default Styling ---
hide_st_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
"""
st.markdown(hide_st_style, unsafe_allow_html=True)
