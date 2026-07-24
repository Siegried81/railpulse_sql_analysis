SELECT
    'wheelchair_accessible' AS Field,
    SUM(CASE WHEN CAST(NULLIF(wheelchair_accessible, '') AS INTEGER) = 1 THEN 1 ELSE 0 END) || ' (' || 
    ROUND(SUM(CASE WHEN CAST(NULLIF(wheelchair_accessible, '') AS INTEGER) = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) || '%)' AS "Flagged / positive",
    SUM(CASE WHEN wheelchair_accessible IS NULL OR wheelchair_accessible = '' THEN 1 ELSE 0 END) || ' (' || 
    ROUND(SUM(CASE WHEN wheelchair_accessible IS NULL OR wheelchair_accessible = '' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) || '%)' AS "Blank / no data"
FROM trips

UNION ALL

SELECT
    'bikes_allowed' AS Field,
    SUM(CASE WHEN CAST(NULLIF(bikes_allowed, '') AS INTEGER) = 1 THEN 1 ELSE 0 END) || ' (' || 
    ROUND(SUM(CASE WHEN CAST(NULLIF(bikes_allowed, '') AS INTEGER) = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) || '%)' AS "Flagged / positive",
    SUM(CASE WHEN bikes_allowed IS NULL OR bikes_allowed = '' THEN 1 ELSE 0 END) || ' (' || 
    ROUND(SUM(CASE WHEN bikes_allowed IS NULL OR bikes_allowed = '' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) || '%)' AS "Blank / no data"
FROM trips;