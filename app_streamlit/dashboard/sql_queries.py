"""Stored in supabase, call supabase.rpc('{function_name}',params = dict)"""

get_filter_data = """
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

heatmap_data = """
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
