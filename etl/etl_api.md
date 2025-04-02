# ETL API Documentation

## Overview
This document describes the API endpoints used in the ETL process, their data structures, and expected responses. These endpoints provide data about countries, monitoring locations, and sensor measurements.

---

## 1. Countries Endpoint
**API URL:**
```plaintext
https://api.openaq.org/v3/countries/22
```
**Response Fields:**
| Field        | Description                                      |
|-------------|--------------------------------------------------|
| `id`        | Unique identifier for the country               |
| `code`      | Country code (e.g., "FR" for France)            |
| `name`      | Full country name                               |
| `pollutants` | List of pollutants tracked (`id`, `name`, `units`) |

---

## 2. Locations Endpoint
**API URL:**
```plaintext
https://api.openaq.org/v3/locations?countries_id=22
```
**Response Fields:**
| Field         | Description |
|--------------|-------------|
| `id`         | Unique station ID |
| `name`       | Name of the monitoring station |
| `locality`   | Geographical locality |
| `coordinates`| Latitude and longitude |
| `bounds`     | Boundaries of the monitoring area |
| `sensors`    | List of sensors (`id`, `pollutants {id, name, units}`) |
| `datetimeFirst` | Timestamp of the first recorded measurement |
| `datetimeLast`  | Timestamp of the most recent measurement |

---

## 3. Sensors & Measurements Endpoint
**API URL (Example for a single sensor):**
```plaintext
https://api.openaq.org/v3/sensors/{sensor_id}/days/monthly?limit=1000
```
**Response Fields:**
| Field        | Description |
|-------------|-------------|
| `value`      | Monthly aggregated value (average) |
| `pollutant`  | Contains `id`, `name`, and `units` |
| `period`     | Contains `label`, `interval`, `datetimeFrom`, `datetimeTo` |
| `coordinates`
