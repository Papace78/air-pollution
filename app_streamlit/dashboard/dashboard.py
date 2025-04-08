import streamlit as st

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


from sidebar import create_sidebar
from data_generation import get_all_measures,get_all_filtered_data
from plots import generate_heatmap, bar_plot_ranking_sensors, bar_plot_average_concentrations
from data_transformation import rank_by_number_of_sensors, rank_by_average_concentration


pollutant_list = ["co", "o3", "no", "no2", "pm10", "pm25", "so2"]

all_measures = get_all_measures()

(
    location_filter_by,
    selected_location,
    selected_pollutant,
    start_date,
    end_date,
    df_final,
) = create_sidebar(all_measures)
location_options = sorted(all_measures[location_filter_by].dropna().unique())
start_date_str = start_date.strftime("%Y-%m-%d")
end_date_str = end_date.strftime("%Y-%m-%d")

# --------------------------------------------------------------------------------

st.markdown(f"### Data for {selected_location} and {selected_pollutant}")


data = get_all_filtered_data(selected_pollutant, start_date_str, end_date_str)

reduction_data = data["reduction_data"]
measurements_data = data["measurements_data"]
heat_data = data["heat_data"]
seasons_data = data["seasons_data"]
weekly_data = data["weekly_data"]


def generate_ranking_concentrations(measurements: pd.DataFrame):
    avg_values_df = (
        measurements.groupby([location_filter_by, "pollutant_name"])["value"]
        .mean()
        .reset_index()
    )
    avg_values_df["value"] = avg_values_df["value"].round(2)
    avg_values_sorted = avg_values_df.sort_values(by="value", ascending=False)
    filtered_df = avg_values_sorted[
        avg_values_sorted["pollutant_name"] == selected_pollutant
    ]

    df_top = filtered_df.head(10)
    df_bottom = filtered_df.tail(10)

    df_top.loc[:, "pollution_level"] = "Highest concentration"
    df_bottom.loc[:, "pollution_level"] = "Lowest concentration"

    df_combined = pd.concat([df_top, df_bottom])

    fig = px.bar(
        df_combined,
        x=f"{location_filter_by}",
        y="value",
        color="pollution_level",
        title=f"{location_filter_by.capitalize()}s with the Highest and Lowest {selected_pollutant}",
        labels={
            "average": f"Concentration (µg/m³)",
            f"{location_filter_by}": f"{location_filter_by}",
        },
    )

    fig.update_layout(
        xaxis_title="", yaxis_title="Average concentration (µg/m³)", showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True)


def generate_ranking_concentrations_per_polluant(measurements: pd.DataFrame):

    df_grouped = (
        measurements.groupby([location_filter_by, "pollutant_name", "pollutant_units"])[
            "value"
        ]
        .mean()
        .reset_index()
        .rename(columns={"value": "average"})
    )

    top3_list, bottom3_list = [], []

    for pollutant in df_grouped["pollutant_name"].unique():
        subset = df_grouped[df_grouped["pollutant_name"] == pollutant]

        top3 = subset.nlargest(3, "average").copy()
        bottom3 = subset.nsmallest(3, "average").copy()

        top3["pollution_level"] = "Higher Concentration"
        bottom3["pollution_level"] = "Lower Concentration"

        top3_list.append(top3)
        bottom3_list.append(bottom3)

    df_top3 = pd.concat(top3_list)
    df_bottom3 = pd.concat(bottom3_list)

    df_top3["x_label"] = df_top3[location_filter_by] + " - " + df_top3["pollutant_name"]
    df_bottom3["x_label"] = (
        df_bottom3[location_filter_by] + " - " + df_bottom3["pollutant_name"]
    )

    y_max = max(df_top3["average"].max(), df_bottom3["average"].max()) * 1.1
    y_label = f"Average concentration ({df_top3['pollutant_units'].iloc[0]})"

    fig_top = px.bar(
        df_top3,
        x="x_label",
        y="average",
        color="pollutant_name",
        title=f"Top 3 {location_filter_by.title()} with Highest Average Concentration per Pollutant",
        labels={"average": y_label, "pollutant_name": "Pollutant"},
    )
    fig_top.update_layout(yaxis=dict(range=[0, y_max]), xaxis_title="")

    fig_bottom = px.bar(
        df_bottom3,
        x="x_label",
        y="average",
        color="pollutant_name",
        title=f"Top 3 {location_filter_by.title()} with Lowest Average Concentration per Pollutant",
        labels={"average": y_label, "pollutant_name": "Pollutant"},
    )
    fig_bottom.update_layout(yaxis=dict(range=[0, y_max]), xaxis_title="")

    # Step 6: Display both in Streamlit
    st.plotly_chart(fig_top, use_container_width=True)
    st.plotly_chart(fig_bottom, use_container_width=True)


def generate_ranking_concentrations_all_polluant(measurements: pd.DataFrame):

    df_grouped = (
        measurements.groupby([location_filter_by, "pollutant_name"])["value"]
        .sum()
        .reset_index()
    )

    # Group by location to get the total pollution per location
    df_total_pollution = (
        df_grouped.groupby(location_filter_by)["value"].sum().reset_index()
    )
    df_total_pollution = df_total_pollution.rename(columns={"value": "total_pollution"})

    # Merge the total pollution data with the grouped data
    df_grouped = pd.merge(df_grouped, df_total_pollution, on=location_filter_by)

    # Calculate the contribution of each pollutant to the total pollution
    df_grouped["pollutant_contribution"] = (
        df_grouped["value"] / df_grouped["total_pollution"]
    )

    # Create a pivot table where each column is a pollutant, and the values are the summed values per location
    df_pivot = df_grouped.pivot_table(
        index=location_filter_by,
        columns="pollutant_name",
        values="value",
        aggfunc="sum",
        fill_value=0,
    )

    # Sort by total pollution in descending order and select the top 10 highest and top 10 lowest locations
    df_total_pollution_sorted = df_total_pollution.sort_values(
        by="total_pollution", ascending=False
    )

    # Check how many unique locations we have
    num_locations = len(df_total_pollution_sorted)

    # Select the top and bottom 10 locations
    if num_locations <= 20:
        # If fewer than 20 locations, select all locations (no overlap)
        df_combined = df_pivot.loc[df_total_pollution_sorted[location_filter_by]]
    else:
        # If more than 20 locations, select top 10 and bottom 10
        df_top_10 = df_pivot.loc[df_total_pollution_sorted[location_filter_by].head(10)]
        df_bottom_10 = df_pivot.loc[
            df_total_pollution_sorted[location_filter_by].tail(10)
        ]
        df_combined = pd.concat([df_top_10, df_bottom_10])

    # Create the stacked bar chart
    fig = px.bar(
        df_combined,
        x=df_combined.index,
        y=df_combined.columns,
        title=f"Pollutant Contribution by Location (Top 10 Highest and Bottom 10 Lowest)",
        labels={
            location_filter_by: f"{location_filter_by.title()}",
            "value": "Pollution (µg/m³)",
        },
    )

    fig.update_layout(
        barmode="stack",
        xaxis_title="",
        yaxis_title="Total Pollution (µg/m³)",
        showlegend=True,
    )

    # Display the chart
    st.plotly_chart(fig, use_container_width=True)


def generate_ranking_variation(reduction_data: pd.DataFrame):

    df_per_pollutant = reduction_data[reduction_data["pollutant"] == selected_pollutant]
    df_grouped = (
        df_per_pollutant.groupby(f"{location_filter_by}")["reduction"]
        .mean()
        .reset_index()
    )
    df_grouped_sorted = df_grouped.sort_values(by="reduction", ascending=False)

    df_top_positive = df_grouped_sorted.head(10).sort_values(by="reduction")
    df_top_negative = df_grouped_sorted.tail(10).sort_values(by="reduction")

    df_combined = pd.concat([df_top_negative, df_top_positive])

    fig = px.bar(
        df_combined,
        x=f"{location_filter_by}",
        y="reduction",
        color="reduction",
        title=f"{selected_pollutant} variation per {location_filter_by} between selected dates",
        labels={"reduction": f"Variation de {selected_pollutant} (µg/m³)"},
    )
    fig.update_layout(
        xaxis_title="",
        yaxis_title=f"Concentration variation (µg/m³)",
        coloraxis_showscale=False,
    )
    st.plotly_chart(fig, use_container_width=True)


def generate_ranking_variation_all_polluant(reduction_data: pd.DataFrame):

    # Step 1: Group by location and sum the reductions across all pollutants
    df_grouped = (
        reduction_data.groupby(f"{location_filter_by}")["reduction"].sum().reset_index()
    )

    # Step 2: Sort the data by the total reduction
    df_grouped_sorted = df_grouped.sort_values(by="reduction", ascending=False)

    # Step 3: Get the top 10 positive and top 10 negative reductions
    df_top_positive = df_grouped_sorted.head(10).sort_values(by="reduction")
    df_top_negative = df_grouped_sorted.tail(10).sort_values(by="reduction")

    # Combine top positive and negative reductions
    df_combined = pd.concat([df_top_negative, df_top_positive])

    # Step 4: Create the bar chart for the summed reduction
    fig = px.bar(
        df_combined,
        x=f"{location_filter_by}",
        y="reduction",
        color="reduction",
        title=f"Variation of Pollution Reduction across Locations from {start_date_str} to {end_date_str}",
        labels={"reduction": "Variation de la pollution (µg/m³)"},
    )

    # Step 5: Update the layout of the plot
    fig.update_layout(
        xaxis_title="Location",
        yaxis_title="Total Pollution Reduction (µg/m³)",
        coloraxis_showscale=False,  # No color scale since we don't need it here
    )

    # Step 6: Display the plot
    st.plotly_chart(fig, use_container_width=True)


tab1, tab2 = st.tabs(["Map", "Ranking"])

with tab1:
    generate_heatmap(heat_data)

with tab2:
    toggle_all = st.toggle("Include all pollutants", key=1, value=False)

    tab1, tab2, tab3 = st.tabs(["Concentrations", "Variation", "Number of sensors"])
    if toggle_all:
        with tab1:
            ranked_concentrations = rank_by_average_concentration(measurements_data, location_filter_by, pollutant_list)
            bar_plot_average_concentrations(ranked_concentrations, location_filter_by)
            #generate_ranking_concentrations_all_polluant(measurements_data)
        with tab2:
            generate_ranking_variation_all_polluant(reduction_data)
        with tab3:
            ranked_sensors = rank_by_number_of_sensors(all_measures, location_filter_by, pollutant_list)
            bar_plot_ranking_sensors(ranked_sensors, location_filter_by)
    else:
        with tab1:
            ranked_concentrations = rank_by_average_concentration(measurements_data, location_filter_by, [selected_pollutant])
            bar_plot_average_concentrations(ranked_concentrations, location_filter_by)
            #generate_ranking_concentrations(measurements_data)
        with tab2:
            generate_ranking_variation(reduction_data)
        with tab3:
            ranked_sensors = rank_by_number_of_sensors(all_measures, location_filter_by, [selected_pollutant])
            bar_plot_ranking_sensors(ranked_sensors, location_filter_by)


def generate_time_serie(
    measurements: pd.DataFrame, add_pollutant: list[str], compare_location: str
):
    # Now pass these string values to the RPC request
    if add_pollutant != ["None"]:
        add_pollutant.append(selected_pollutant)
        pollutants = add_pollutant
    else:
        print("imhere")
        pollutants = [selected_pollutant]

    df = measurements[measurements["pollutant_name"].isin(pollutants)]

    df_filtered = df[
        df[location_filter_by].str.contains(selected_location, case=False, na=False)
    ]

    # Step 1: Group by relevant columns and calculate the average concentration per group
    df_grouped = (
        df.groupby([location_filter_by, "pollutant_name", "datetime_to"])
        .agg(average=("value", "mean"))
        .reset_index()
    )

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


def generate_seasons_pie(seasons_df: pd.DataFrame):

    df_filtered = seasons_df[
        seasons_df.apply(
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


def generate_weekly_pie(weekly_df: pd.DataFrame):
    df_filtered = weekly_df[
        weekly_df.apply(
            lambda row: row.astype(str).str.contains(f"{selected_location}").any(),
            axis=1,
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


def get_concentration_ranking(
    measurements: pd.DataFrame,
    add_pollutant: list[str],
    location: str,
):
    df_grouped = (
        measurements.groupby([f"{location_filter_by}", "pollutant_name"])["value"]
        .sum()
        .reset_index()
    )
    df_sorted = df_grouped.sort_values(by="value", ascending=True)
    pollutants = [selected_pollutant]
    pollutants.extend(add_pollutant)
    filtered = df_sorted[df_sorted["pollutant_name"].isin(pollutants)].reset_index(
        drop=True
    )
    value = filtered[filtered["town"] == selected_location]["value"].to_numpy()[0]
    rank = filtered[filtered[f"{location_filter_by}"] == location].index[0]
    pool = filtered.shape[0]
    return value, rank, pool


def get_variation_ranking(
    reduction_df: pd.DataFrame,
    add_pollutant: list[str],
    location: str,
):
    df = (
        reduction_df.groupby([f"{location_filter_by}", "pollutant"]).sum().reset_index()
    )

    pollutants = [f"{selected_pollutant}"]
    pollutants.extend(add_pollutant)
    filtered_by_pol = df[df["pollutant"].isin(pollutants)]

    all_pol = (
        filtered_by_pol.groupby([f"{location_filter_by}"])
        .sum()
        .reset_index()
        .sort_values(by="reduction")
    ).reset_index(drop=True)
    all_pol_red = all_pol[all_pol[f"{location_filter_by}"] == f"{location}"][
        "reduction"
    ].to_numpy()[0]
    all_pol_rank = all_pol[all_pol[f"{location_filter_by}"] == f"{location}"].index[0]
    all_pol_pool = all_pol.shape[0] - 1

    return all_pol_red, all_pol_rank, all_pol_pool


toggle_all_2 = st.toggle("🔄 Show all pollutants", key=2, value=False)
tab1, tab2 = st.tabs(["📈 Time Series", "🏆 Rankings"])
if toggle_all_2:
    st.markdown("### 📊 Showing trends across all pollutants")

    with tab1:
        generate_time_serie(
            measurements=measurements_data,
            add_pollutant=pollutant_list,
            compare_location="",
        )
    with tab2:
        reduction, rank, pool = get_variation_ranking(
            reduction_df=reduction_data,
            add_pollutant=pollutant_list,
            location=selected_location,
        )
        st.markdown(f"red{reduction}, rank {rank}, pool {pool}")
else:
    with st.expander("🔍 Optional: Add a comparison"):
        col1, col2 = st.columns(2)
        with col1:
            add_pollutant = [
                st.radio(
                    "🧪 Compare with another pollutant:",
                    options=["None"] + pollutant_list,
                    horizontal=True,
                )
            ]
        with col2:
            compare_location = st.selectbox(
                f"🏘️ Compare with another {location_filter_by.lower()}",
                options=["None"] + location_options,
                index=0,
            )

    with tab1:
        generate_time_serie(
            measurements=measurements_data,
            add_pollutant=add_pollutant,
            compare_location=compare_location,
        )
    with tab2:
        # Header Section
        # Title Section
        st.markdown("### Pollution Overview")

        # Fetch concentration and reduction data
        value, con_rank, con_pool = get_concentration_ranking(
            measurements=measurements_data,
            add_pollutant=add_pollutant,
            location=selected_location,
        )
        reduction, rank, pool = get_variation_ranking(
            reduction_df=reduction_data,
            add_pollutant=add_pollutant,
            location=selected_location,
        )

        # Latest Concentration (Current value of pollutants)
        st.metric(
            label="Concentration (µg/m³)",
            value=f"{value:.2f} @ the end date",
            delta=f"{reduction:.2f} from start date to end date",
            delta_color="inverse",
        )

        # Ranking Section (How the location ranks in reduction)
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**🏆 Rank:** {rank}")
        with col2:
            st.markdown(f"**🌍 Pollution Pool:** {pool} locations")

        # Caption to explain the data source and timing
        st.caption("Based on data between the selected dates.")
        if compare_location != "None":
            reduction_2, rank_2, pool_2 = get_concentration_ranking(
                measurements=measurements_data,
                add_pollutant=add_pollutant,
                location=compare_location,
            )
            st.markdown(f"red{reduction_2}, rank {rank_2}, pool {pool_2}")


with st.expander("📊 Cyclical ?"):
    tab1, tab2 = st.tabs(["📅 By Season", "📆 By Week/Weekend"])
    with tab1:
        generate_seasons_pie(seasons_data)

    with tab2:
        generate_weekly_pie(weekly_data)


# --- Hide Streamlit Default Styling ---
hide_st_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
"""
st.markdown(hide_st_style, unsafe_allow_html=True)
