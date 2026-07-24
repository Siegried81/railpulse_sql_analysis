SELECT
  t.trip_headsign,
  COUNT(*) AS trip_count
FROM trips t
JOIN stop_times st ON st.trip_id = t.trip_id
WHERE st.stop_sequence = 1
  AND st.departure_time < '12:00:00'
  AND t.trip_headsign IS NOT NULL
  AND t.trip_headsign <> ''
GROUP BY t.trip_headsign
ORDER BY trip_count DESC
LIMIT 3;