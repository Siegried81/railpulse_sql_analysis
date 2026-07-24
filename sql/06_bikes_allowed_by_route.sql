SELECT
    r.route_id,
    r.route_short_name,
    r.route_long_name,
    COUNT(t.trip_id) AS total_trips,
    SUM(CASE WHEN t.bikes_allowed = 1 THEN 1 ELSE 0 END) AS flagged_trips,
    SUM(CASE WHEN t.bikes_allowed = 1 THEN 0 ELSE 1 END) AS unflagged_trips,
    ROUND(
        SUM(CASE WHEN t.bikes_allowed = 1 THEN 0 ELSE 1 END) * 100.0 / COUNT(t.trip_id),
        2
    ) AS unflagged_pct
FROM routes r
JOIN trips t ON r.route_id = t.route_id
WHERE r.route_short_name NOT LIKE '%BUS%'
  AND r.route_long_name NOT LIKE '%BUS%'
GROUP BY r.route_id, r.route_short_name, r.route_long_name
HAVING total_trips > 5
ORDER BY unflagged_pct DESC, total_trips DESC
LIMIT 15;