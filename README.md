# 🌍 Air Pollution Dashboard

## 🚀 Overview
Visualize air pollution data (PM2.5, PM10, NO2, etc.) from **French towns** through an interactive [dashboard](air-pg.streamlit.app).

### 🔑 Key Features:
- **Data Exploration**: Easily filter pollution data by **pollutant**, **date range**, and **geographical location** (town, department, region).
- **Pollution Peaks**: Discover **pollution trends** and identify when pollution levels are at their highest.
- **Air Quality Improvements**: Track and identify localities with the **most significant improvements** in air quality.
- **Sensor Analysis**: Find out which localities have the **most sensors** measuring pollution per pollutant.
- **Interactive Dashboard**: Users can explore visual data and uncover insights about air pollution trends in real-time.

### 🎯 Personal Objectives

#### 1. **Data Collection & Processing (ETL)**
   - Fetch data from the **OpenAQ API**.
   - Clean, transform, and store data in a **PostgreSQL** database.
   - **Host the database on the cloud** to ensure constant availability.

   <img src="image/db_schema.png" alt="postgreSQL database" width="400"/>

   **Database Schema**

#### 2. **Data Visualization & Dashboard Creation**
   - Query the stored data for meaningful insights.
   - Use **Plotly** and **Streamlit** to build a **user-friendly** and **interactive dashboard**.

   **Example of initial filters:**
   ![Filtering Example 1](image/filtering_example.png)

   **Example of applied filters with graph:**
   ![Filtering Example 2](image/filtering_example_two.png)

---

## 🗂️ Data

The data for this project comes from the **OpenAQ API**, which is:

- **Open Source** and **Non-profit**.
- Provides pollution data in **physical units** (not air quality index).
- Covers a wide range of pollutants: **PM2.5, PM10, SO2, NO2, CO, O3**.

For more details, visit [OpenAQ](https://docs.openaq.org/about/about).

---

## ⚙️ Tech Stack

This project uses the following tools and libraries:

- **httpx**: To fetch real-time data from the OpenAQ API.
- **PostgreSQL**: For storing and managing large pollution datasets.
- **Pandas**: For data manipulation and analysis.
- **Plotly**: To create interactive and responsive visualizations.
- **Streamlit**: To build a **beautiful** and **user-friendly** interactive dashboard.
- **Supabase**: To host and manage the PostgreSQL database on the cloud.

---

### 🔗 Demo

Check out the live **Air Pollution Dashboard** [here](air-pg.streamlit.app).

---
