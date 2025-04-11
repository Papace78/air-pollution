"""Plot functions once dataframe are transformed."""

import pandas as pd

import folium
from folium.plugins import HeatMap

import plotly.express as px
import plotly.graph_objects as go

import streamlit as st


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
        <b>Town:</b> {row['town']}<br>
        <b>Pollutant:</b> {row['pollutant']}<br>
        <b>Value:</b> {row['average']} {row['units']}<br>
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


def bar_plot_ranking_sensors(
    ranked_sensors_per_location: pd.DataFrame,
    location_filter_by: str,
):
    fig = px.bar(
        ranked_sensors_per_location,
        x=f"{location_filter_by}",
        y="sensor_id",
        color="pollutant_name",
        title=f"{location_filter_by.capitalize()}s with the Most Sensors",
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
        barmode="stack",
    )

    st.plotly_chart(fig, use_container_width=True)


def bar_plot_average_concentration(
    avg_value_df: pd.DataFrame,
    location_filter_by: str,
):
    fig = px.bar(
        avg_value_df,
        x=f"{location_filter_by}",
        y="value",
        color="pollutant_name",
        title=f"Highest Average Concentration Across Selected Date Range",
        labels={
            "value": "Average Value",
            f"{location_filter_by}": f"{location_filter_by} - Pollutant",
        },
    )

    fig.update_layout(
        xaxis=dict(
            tickmode="array",
            tickvals=avg_value_df[f"{location_filter_by}"],
            ticktext=avg_value_df[f"{location_filter_by}"],
        ),
        xaxis_title="",
        yaxis_title="Concentration (µg/m³)",
        showlegend=True,
        barmode="stack",
    )

    st.plotly_chart(fig, use_container_width=True)


def bar_plot_average_variation(
    df: pd.DataFrame,
    location_filter_by="town",
):
    """
    Generates an interactive Plotly bar chart showing total pollution reductions
    by specified locations with pollutant breakdowns on hover.

    Args:
        df (pd.DataFrame): DataFrame containing pollution data with columns
                           'location_filter_by' (e.g., 'town', 'department'),
                           'pollutant', 'reduction', 'total_reduction'.
        location_filter_by (str): Column name to group data by (default: 'town').
    """
    avg_reduction = (
        df.groupby([location_filter_by, "pollutant_name"])["reduction"]
        .mean()
        .reset_index(name="avg_reduction")
    )

    avg_hover_data = (
        avg_reduction.groupby(location_filter_by)
        .apply(
            lambda x: "<br>".join(
                [
                    f"{p}: {r:.2f} µg/m³"
                    for p, r in zip(x["pollutant_name"], x["avg_reduction"])
                ]
            )
        )
        .reset_index(name="hover_text")
    )

    plot_df = df.groupby(location_filter_by)["total_reduction"].max().reset_index()

    plot_df = plot_df.merge(avg_hover_data, on=location_filter_by)
    plot_df["sort_order"] = plot_df[location_filter_by].apply(
        lambda x: 0 if "SELECTED" in str(x) else 1
    )
    plot_df = plot_df.sort_values(
        by=["sort_order", "total_reduction"], ascending=[False, False]
    )

    fig = px.bar(
        plot_df,
        x=location_filter_by,
        y="total_reduction",
        labels={"total_reduction": "Total Reduction (µg/m³)"},
        hover_data={
            "hover_text": True,
            location_filter_by: True,
            "total_reduction": ":.2f",
        },
    )

    fig.update_traces(
        hovertemplate="<b>%{x}</b><br>Total: %{y:.2f} µg/m³<br>%{customdata[0]}",
        marker_line_color="rgba(0,0,0,0.2)",
        marker_line_width=1,
    )

    fig.update_layout(
        title=f"Largest Pollutant Variation Across Selected Date Range",
        xaxis_title=None,
        yaxis_title="Total Reduction (µg/m³)",
    )

    st.plotly_chart(fig, use_container_width=True)


def plot_time_series(
    df_filtered: pd.DataFrame,
    df_compare: pd.DataFrame,
    location_filter_by: str,
    selected_location: str,
    compare_locations: list[str] = None,  # Accepts a list of compare locations
):
    if compare_locations is None:
        compare_locations = ["None"]  # Default to an empty list if None provided

    fig = px.line(
        df_filtered,
        x="datetime_to",
        y="average",
        color="pollutant_name",
        title="",
        labels={
            "value": "Concentration (µg/m³)",
            "datetime_to": "Time",
            "name": "Pollutant",
        },
        markers=True,
    )
    for trace in fig.data:
        trace.name = f"{trace.name} ({selected_location})"

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

    # If there are compare locations, add them to the plot
    if "None" not in compare_locations and not df_compare.empty:
        fig.update_layout(title={"text": "Pollutant Level Over Time"})

        for compare_location in compare_locations:
            for poll in df_compare["pollutant_name"].unique():
                poll_data = df_compare[
                    df_compare[location_filter_by] == compare_location
                ]
                poll_data = poll_data[poll_data["pollutant_name"] == poll]

                fig.add_trace(
                    go.Scatter(
                        x=poll_data["datetime_to"],
                        y=poll_data["average"],
                        mode="lines",
                        line=dict(dash="solid", width=0.8),
                        name=f"{poll} ({compare_location})",
                        opacity=0.8,
                        showlegend=True
                    )
                )
    else:
        # Plot the Q25–Q75 range for the selected location if no compare locations are specified
        fig.update_layout(
            title={
                "text": f"Pollutant Level Over Time <br><span style='font-size:12px;'>with Q25–Q75 range</span>"
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


def pie_plot_seasons(df: pd.DataFrame):
    fig = px.pie(
        df,
        names="season",
        title="Seasonal Distribution of Pollutants",
        values="value",
        labels={"value": "Mean concentration (µg/m³)"},
    )

    fig.update_layout(showlegend=False)
    fig.update_traces(textinfo="percent+label")

    st.plotly_chart(fig, use_container_width=True)
