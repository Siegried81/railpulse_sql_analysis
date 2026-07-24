WITH service_trip_counts AS (
    SELECT 
        s.service_id,
        COUNT(t.trip_id) AS total_trips
    FROM calendar s
    LEFT JOIN trips t ON s.service_id = t.service_id
    GROUP BY s.service_id
),
service_classification AS (
    SELECT 
        service_id,
        total_trips,
        CASE 
            WHEN total_trips > 50 THEN 'High Frequency'
            WHEN total_trips BETWEEN 10 AND 50 THEN 'Medium Frequency'
            ELSE 'Low Frequency/Special'
        END AS frequency_category
    FROM service_trip_counts
)
SELECT 
    frequency_category,
    COUNT(*) AS service_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM service_classification), 2) AS percentage_share
FROM service_classification
GROUP BY frequency_category
ORDER BY service_count DESC;