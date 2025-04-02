# ETL Process Explanation

## Overview
This document explains the decisions made in processing the OpenAQ data, including filtering criteria, transformations, and database schema design.

---

## Data Filtering and Cleaning
### 1. Locations
- OpenAQ provides **920 monitoring stations** for France.
- Some stations are **no longer monitored**:
  - **35 stations** have a recorded start and end date.
  - **81 stations** are inactive with names like `"testmi"`, `"test"`, `"testfix"`, etc.
  - **All non-monitored stations have been removed**.
- After filtering, **804 monitored stations** remain.
- **355 stations have outdated measurements**, meaning their last recorded data is from a long time ago.
  - These are still included but **marked as inactive** with a new `"active"` column.

### 2. Sensors & Measurements
- **Each location contains sensors** that track specific pollutants.
- The **measurements** endpoint will aggregates data per month.
- The final dataset keeps only the relevant fields:
  - **Sensor id**.
  - **Timestamps** of the measurement period.
  - **Statistical summaries** (min, max, median, quartiles, etc.).

---

## Database Schema Decisions
- The `locations` table contains an `"active"` column to indicate if a station is still reporting data.
- The `sensors` table **links sensors to their locations** and tracks which pollutants they measure.
- The `measurements` table **stores aggregated monthly pollutant data** with timestamps and statistical values.

---

## Summary
- The data pipeline extracts, transforms, and loads pollution data from OpenAQ.
- Filters remove inactive and test locations, ensuring data quality.
- The database schema supports structured storage of monitoring stations, sensors, and aggregated pollutant data.

---

## Final Database Schema

```sql
CREATE TABLE countries (
    id BIGSERIAL NOT NULL PRIMARY KEY,
    code VARCHAR(10) NOT NULL,
    name VARCHAR(60) NOT NULL
);

CREATE TABLE pollutants (
    id BIGSERIAL NOT NULL PRIMARY KEY,
    name VARCHAR(60) NOT NULL,
    units VARCHAR(60) NOT NULL
);

CREATE TABLE locations (
    id BIGSERIAL NOT NULL PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    locality VARCHAR(150) NOT NULL,
    datetimeFirst TIMESTAMP NOT NULL,
    datetimeLast TIMESTAMP NOT NULL,
    country_id BIGINT REFERENCES countries(id),
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    active BOOLEAN NOT NULL
);

CREATE TABLE sensors (
    id BIGSERIAL NOT NULL PRIMARY KEY,
    location_id BIGINT REFERENCES locations(id),
    pollutant_id BIGINT REFERENCES pollutants(id)
);

CREATE TABLE measurements (
    id BIGSERIAL NOT NULL PRIMARY KEY,
    sensor_id BIGINT REFERENCES sensors(id),
    datetimeFrom TIMESTAMP NOT NULL,
    datetimeTo TIMESTAMP NOT NULL,
    value REAL NOT NULL,
    min REAL NOT NULL,
    q02 REAL NOT NULL,
    q25 REAL NOT NULL,
    median REAL NOT NULL,
    q75 REAL NOT NULL,
    q98 REAL NOT NULL,
    max REAL NOT NULL,
    avg REAL NOT NULL,
    sd REAL NOT NULL
);
```
