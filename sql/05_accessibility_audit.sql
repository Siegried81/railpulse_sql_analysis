WITH trip_flags AS (
    SELECT
        t.trip_id,
        t.route_id,
        CASE WHEN CAST(COALESCE(NULLIF(t.wheelchair_accessible, ''), '0') AS INTEGER) = 1 THEN 1 ELSE 0 END AS wheelchair_ok,
        CASE WHEN CAST(COALESCE(NULLIF(t.bikes_allowed, ''), '0') AS INTEGER) = 1 THEN 1 ELSE 0 END AS bike_ok
    FROM trips t
),
route_stats AS (
    SELECT
        r.route_id,
        COALESCE(NULLIF(r.route_short_name, ''), '(no_short_name)') AS route_short_name,
        COALESCE(NULLIF(r.route_long_name, ''), '(no_long_name)') AS route_long_name,
        COUNT(tf.trip_id) AS total_trips,
        SUM(tf.wheelchair_ok) AS wheelchair_trips,
        SUM(tf.bike_ok) AS bike_trips,
        SUM(CASE WHEN tf.wheelchair_ok = 1 OR tf.bike_ok = 1 THEN 1 ELSE 0 END) AS amenity_trips
    FROM routes r
    JOIN trip_flags tf ON tf.route_id = r.route_id
    WHERE COALESCE(r.route_short_name, '') NOT LIKE '%BUS%'
      AND COALESCE(r.route_long_name, '') NOT LIKE '%BUS%'
    GROUP BY r.route_id, route_short_name, route_long_name
)
SELECT
    route_id,
    route_short_name,
    route_long_name,
    total_trips,

    wheelchair_trips || '/' || total_trips AS wheelchair_ratio,
    ROUND(wheelchair_trips * 100.0 / NULLIF(total_trips, 0), 2) AS wheelchair_pct,

    bike_trips || '/' || total_trips AS bikes_ratio,
    ROUND(bike_trips * 100.0 / NULLIF(total_trips, 0), 2) AS bikes_pct,

    amenity_trips || '/' || total_trips AS either_amenity_ratio,
    ROUND(amenity_trips * 100.0 / NULLIF(total_trips, 0), 2) AS either_amenity_pct
FROM route_stats
WHERE total_trips > 5
ORDER BY either_amenity_pct ASC, total_trips DESC
LIMIT 20;