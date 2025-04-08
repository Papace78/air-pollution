
import folium
from folium.plugins import HeatMap

import streamlit as st

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def generate_heatmap(heat_measures: pd.DataFrame):
    heat_data = heat_measures[["latitude", "longitude", "average"]].values.tolist()
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
    for i, row in heat_measures.iterrows():
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

    st.components.v1.html(
        f"""
        <div style="height:100%; width:100%;">
            <style>
                .folium-map {{
                    height: 100%;
                    width: 100%;
                    border-radius: 10px;
                    box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.1);
                }}
                #map {{
                    height: 100vh;
                }}
            </style>
            {m.get_root().render()}
        </div>
        """,
        height=700,  # You can adjust this if needed
        scrolling=False,
    )


def bar_plot_ranking_sensors(ranked_sensors_per_location: pd.DataFrame, location_filter_by: str):
    fig = px.bar(
        ranked_sensors_per_location,
        x=f"{location_filter_by}",
        y="sensor_id",
        color="pollutant_name",
        title=f"Top {location_filter_by}s with the Most Sensors",
        labels={
            "sensor_id": "Number of Sensors",
            "x_key": f"{location_filter_by} - Pollutant",
        },
    )

    fig.update_layout(
        xaxis=dict(
            tickmode="array",
            tickvals=ranked_sensors_per_location[f"{location_filter_by}"],
            ticktext=ranked_sensors_per_location[f"{location_filter_by}"],
        ),
        xaxis_title="",
        yaxis_title="Number of Sensors",
        showlegend=True,
        barmode='stack'
    )

    st.plotly_chart(fig, use_container_width=True)

def bar_plot_average_concentrations(avg_value_df: pd.DataFrame, location_filter_by: str):
    fig = px.bar(
        avg_value_df,
        x=f"{location_filter_by}",  # X-axis will be based on the location
        y="value",  # Y-axis will be the averaged value
        color="pollutant_name",  # Color by pollutant
        title=f"Average {location_filter_by}s with Average Pollutant Values",
        labels={
            "value": "Average Value",
            f"{location_filter_by}": f"{location_filter_by} - Pollutant",
        },
    )

    # Set x-ticks for each location and pollutant combination
    fig.update_layout(
        xaxis=dict(
            tickmode="array",
            tickvals=avg_value_df["x_key"],  # We use x_key to get a unique x-tick for each combination
            ticktext=avg_value_df[f"{location_filter_by}"]  # Tick text is the location name
        ),
        xaxis_title="",
        yaxis_title="Average Pollutant Value",
        showlegend=True,
        barmode='stack'
    )

    st.plotly_chart(fig, use_container_width=True)
