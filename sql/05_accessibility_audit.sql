WITH trip_amenities AS (
    SELECT
        t.trip_id,
        t.route_id,
        CASE
            WHEN NULLIF(t.wheelchair_accessible, '') IS NULL THEN 0
            ELSE CAST(t.wheelchair_accessible AS INTEGER)
        END AS wheelchair_accessible_flag,
        CASE
            WHEN NULLIF(t.bikes_allowed, '') IS NULL THEN 0
            ELSE CAST(t.bikes_allowed AS INTEGER)
        END AS bikes_allowed_flag
    FROM trips t
),
route_stats AS (
    SELECT
        r.route_id,
        COALESCE(NULLIF(r.route_short_name, ''), '(no_short_name)') AS route_short_name,
        COALESCE(NULLIF(r.route_long_name, ''), '(no_long_name)') AS route_long_name,
        COUNT(DISTINCT ta.trip_id) AS total_trips,
        ROUND(100.0 * SUM(ta.wheelchair_accessible_flag) / NULLIF(COUNT(DISTINCT ta.trip_id), 0), 2) AS wheelchair_accessible_pct,
        ROUND(100.0 * SUM(ta.bikes_allowed_flag) / NULLIF(COUNT(DISTINCT ta.trip_id), 0), 2) AS bikes_allowed_pct,
        ROUND(100.0 * SUM(CASE WHEN ta.wheelchair_accessible_flag = 1 OR ta.bikes_allowed_flag = 1 THEN 1 ELSE 0 END) / NULLIF(COUNT(DISTINCT ta.trip_id), 0), 2) AS either_amenity_pct
    FROM trip_amenities ta
    JOIN routes r ON r.route_id = ta.route_id
    WHERE COALESCE(r.route_short_name, '') NOT LIKE '%BUS%'
      AND COALESCE(r.route_long_name, '') NOT LIKE '%BUS%'
    GROUP BY r.route_id, route_short_name, route_long_name
    HAVING total_trips > 5
)
SELECT 
    route_short_name,
    route_long_name,
    total_trips,
    wheelchair_accessible_pct,
    bikes_allowed_pct,
    either_amenity_pct
FROM route_stats
ORDER BY total_trips DESC
LIMIT 15;