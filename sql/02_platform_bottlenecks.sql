SELECT
  s.platform_code,
  s.stop_name,
  COUNT(*) AS total_operations
FROM stop_times st
JOIN stops s ON s.stop_id = st.stop_id
JOIN stops parent ON parent.stop_id = s.parent_station
WHERE parent.stop_name IN ('Bruxelles-Central', 'Brussel-Centraal')
  AND s.platform_code IS NOT NULL
  AND s.platform_code <> ''
GROUP BY s.platform_code, s.stop_name
ORDER BY total_operations DESC
LIMIT 3;