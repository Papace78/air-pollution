# Air Pollution Dashboard

## Overview

This project aims to visualize air pollution data (PM2.5, PM10, NO2, etc.) in French towns through an interactive dashboard. The dashboard will allow users to explore air quality data, filter by location, pollutant, time period, and more.

### Key Features:
- **Data Exploration**: Filter data by town, pollutant, time period (season, day of the week, etc.).
- **Pollution Peaks**: Visualize pollution trends and peaks across different time periods.
- **Air Quality Improvement**: Identify towns with the most significant improvements in air quality.
- **Interactive Dashboard**: Users can interact with visualizations to gain insights into air pollution trends.

### Personal Objectives:
- Make requests to API for data collection.
- Clean and standardize the data.
- Store the data locally in a PostgreSQL database.
- Query and manipulate the data from the local database.
- Build an interactive web dashboard to display the data.
- Potential: Automate the data fetching process and update the dashboard dynamically.

---

## Data

The project uses data from the **OpenAQ API**, which is:
- **Open Source** and **Non-profit**.
- Provides data in **physical units** rather than an air quality index.
- Aggregates multiple air pollutants: PM2.5, PM10, SO2, NO2, CO, O3, BC, relative humidity, and temperature.
- Harmonizes the data into a consistent format for easy use.

For more information on the API, visit [OpenAQ](https://docs.openaq.org/about/about).

---

## Tech Stack

The following tools and libraries are used in this project:

- **httpx**: To fetch data from the OpenAQ API.
- **PostgreSQL**: For storing and managing the data locally.
- **Pandas**: For data manipulation and cleaning.
- **Plotly**: For creating interactive visualizations.
- **Dash (or Streamlit)**: For building the interactive web dashboard interface.

---

## Setup & Installation

### Prerequisites


### Install Dependencies
