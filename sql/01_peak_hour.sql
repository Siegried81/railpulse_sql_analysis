SELECT
  SUBSTR(st.departure_time, 1, 2) AS departure_hour,
  COUNT(*) AS total_departures
FROM stop_times st
WHERE st.departure_time IS NOT NULL
  AND st.departure_time <> ''
GROUP BY SUBSTR(st.departure_time, 1, 2)
ORDER BY total_departures DESC
LIMIT 3;