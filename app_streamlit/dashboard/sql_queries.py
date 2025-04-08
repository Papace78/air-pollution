#Output all sensors by locations, polluant and measurements dates
#"get_filter_data"
sql_query = """
SELECT
l.town,
l.region,
l.department,
s.id,
p.name,
m.datetimeFrom,
m.datetimeTo
FROM
locations AS l
JOIN sensors AS s ON s.location_id = l.id
JOIN pollutants AS p ON p.id = s.pollutant_id
JOIN measurements AS m ON m.sensor_id = s.id
"""


#heatmap_data
sql_query = """
SELECT
  l.town,
  p.name AS pollutant,
  p.units,
  ROUND(AVG(m.value)::numeric, 2) AS average,
  MIN(m.datetimeFrom) AS datetime_from,
  MAX(m.datetimeTo) AS datetime_to,
  ROUND(AVG(l.latitude)::numeric, 4) AS latitude,
  ROUND(AVG(l.longitude)::numeric, 4) AS longitude
FROM measurements AS m
JOIN sensors AS s ON s.id = m.sensor_id
JOIN locations AS l ON l.id = s.location_id
JOIN pollutants AS p ON p.id = s.pollutant_id
WHERE p.name = %s
  AND m.datetimeTo BETWEEN %s AND %s
GROUP BY l.town, p.name, p.units
ORDER BY average DESC;
"""


#timeseries data
get_measurements_by_date_range= """
SELECT
    l.town,
    l.department,
    l.region,
    p.name,
    p.units,
    m.value,
    m.datetimeFrom,
    m.datetimeTo
FROM measurements AS m
JOIN sensors AS s ON s.id = m.sensor_id
JOIN locations AS l ON l.id = s.location_id
JOIN pollutants AS p ON p.id = s.pollutant_id
WHERE
    m.datetimeFrom BETWEEN %s AND %s
"""


#season data
get_seasons = """
SELECT
  l.town,
  l.department,
  l.region,
  p.name AS pollutant,
  p.units,
  ROUND(AVG(m.value)::numeric, 2) AS average,
  MIN(m.datetimeFrom) AS datetime_from,
  MAX(m.datetimeTo) AS datetime_to,
  ROUND(AVG(l.latitude)::numeric, 4) AS latitude,
  ROUND(AVG(l.longitude)::numeric, 4) AS longitude,

  -- Définir les saisons en fonction du mois de `datetimeFrom` (ou `datetimeTo`)
  CASE
    WHEN EXTRACT(MONTH FROM m.datetimeFrom) IN (12, 1, 2) THEN 'Hiver'
    WHEN EXTRACT(MONTH FROM m.datetimeFrom) IN (3, 4, 5) THEN 'Printemps'
    WHEN EXTRACT(MONTH FROM m.datetimeFrom) IN (6, 7, 8) THEN 'Été'
    WHEN EXTRACT(MONTH FROM m.datetimeFrom) IN (9, 10, 11) THEN 'Automne'
  END AS season

FROM measurements AS m
JOIN sensors AS s ON s.id = m.sensor_id
JOIN locations AS l ON l.id = s.location_id
JOIN pollutants AS p ON p.id = s.pollutant_id
WHERE p.name = %s
  AND m.datetimeTo BETWEEN %s AND %s
GROUP BY l.town, l.department, l.region, p.name, p.units, season
ORDER BY season, average DESC;
"""


get_weeks="""
SELECT
  l.town,
  l.department,
  l.region,
  p.name AS pollutant,
  p.units,
  ROUND(AVG(m.value)::numeric, 2) AS average,
  MIN(m.datetimeFrom) AS datetime_from,
  MAX(m.datetimeTo) AS datetime_to,
  ROUND(AVG(l.latitude)::numeric, 4) AS latitude,
  ROUND(AVG(l.longitude)::numeric, 4) AS longitude,
  CASE
    WHEN EXTRACT(DOW FROM m.datetimeFrom) IN (0, 6) THEN 'Weekend'  -- Samedi (6) et Dimanche (0)
    ELSE 'Semaine'  -- Lundi (1) à Vendredi (5)
  END AS week_type
FROM measurements AS m
JOIN sensors AS s ON s.id = m.sensor_id
JOIN locations AS l ON l.id = s.location_id
JOIN pollutants AS p ON p.id = s.pollutant_id
WHERE p.name = %s
  AND m.datetimeTo BETWEEN %s AND %s
GROUP BY l.town, l.department, l.region, p.name, p.units, week_type
ORDER BY average DESC;
"""

get_pollution_reduction ="""
WITH pollution_values AS (
  SELECT
    l.town,
    l.department,
    l.region,
    p.name AS pollutant,
    p.units as unit,
    m.value,
    m.datetimeFrom,
    m.datetimeTo
  FROM measurements AS m
  JOIN sensors AS s ON s.id = m.sensor_id
  JOIN locations AS l ON l.id = s.location_id
  JOIN pollutants AS p ON p.id = s.pollutant_id
  WHERE p.name = %s
    AND m.datetimeTo BETWEEN %s AND %s
)

, first_last_values AS (
  -- Première et dernière valeur pour chaque ville
  SELECT
    town,
    department,
    region,
    pollutant,
    unit,
    FIRST_VALUE(value) OVER (PARTITION BY town ORDER BY datetimeFrom) AS first_value,
    LAST_VALUE(value) OVER (PARTITION BY town ORDER BY datetimeTo ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS last_value
  FROM pollution_values
)

-- Calcul de la réduction
SELECT
  town,
  department,
  region,
  pollutant,
  ROUND((first_value::numeric - last_value::numeric), 2) AS reduction,
  unit
FROM first_last_values
GROUP BY town, department, region, pollutant, reduction, unit
ORDER BY reduction;
"""
