import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "railpulse.db"

SUPPORTING_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_stop_times_trip_id ON Stop_times(trip_id);",
    "CREATE INDEX IF NOT EXISTS idx_stop_times_stop_id ON Stop_times(stop_id);",
    "CREATE INDEX IF NOT EXISTS idx_trips_route_id ON Trips(route_id);",
    "CREATE INDEX IF NOT EXISTS idx_trips_service_id ON Trips(service_id);",
    "CREATE INDEX IF NOT EXISTS idx_stops_parent_station ON Stops(parent_station);",
]

NAIVE_INDEX = "CREATE INDEX IF NOT EXISTS idx_stop_times_departure_time ON Stop_times(departure_time);"

EXPRESSION_INDEX = (
    "CREATE INDEX IF NOT EXISTS idx_stop_times_departure_hour "
    "ON Stop_times(SUBSTR(departure_time, 1, 2));"
)


def main() -> None:
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute(NAIVE_INDEX)
    cursor.execute(EXPRESSION_INDEX)

    for stmt in SUPPORTING_INDEXES:
        cursor.execute(stmt)

    connection.commit()
    connection.close()


if __name__ == "__main__":
    main()