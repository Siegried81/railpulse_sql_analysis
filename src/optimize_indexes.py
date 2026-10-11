import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "railpulse.db"
SQL_DIR = BASE_DIR / "sql"
PEAK_HOUR_QUERY_PATH = SQL_DIR / "01_peak_hour.sql"

SUPPORTING_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_stop_times_trip_id ON Stop_times(trip_id);",
    "CREATE INDEX IF NOT EXISTS idx_stop_times_stop_id ON Stop_times(stop_id);",
    "CREATE INDEX IF NOT EXISTS idx_trips_route_id ON Trips(route_id);",
    "CREATE INDEX IF NOT EXISTS idx_trips_service_id ON Trips(service_id);",
    "CREATE INDEX IF NOT EXISTS idx_stops_parent_station ON Stops(parent_station);",
]

NAIVE_INDEX_NAME = "idx_stop_times_departure_time"
NAIVE_INDEX = f"CREATE INDEX IF NOT EXISTS {NAIVE_INDEX_NAME} ON Stop_times(departure_time);"

EXPRESSION_INDEX_NAME = "idx_stop_times_departure_hour"
EXPRESSION_INDEX = (
    f"CREATE INDEX IF NOT EXISTS {EXPRESSION_INDEX_NAME} "
    "ON Stop_times(SUBSTR(departure_time, 1, 2));"
)


def load_peak_hour_query() -> str:
    with open(PEAK_HOUR_QUERY_PATH, "r", encoding="utf-8") as f:
        return f.read()


def print_query_plan(cursor: sqlite3.Cursor, label: str, query: str) -> None:
    print(f"\n--- {label} ---")
    cursor.execute(f"EXPLAIN QUERY PLAN {query}")
    for row in cursor.fetchall():
        # row = (id, parent, notused, detail)
        print(f"  {row[-1]}")


def reset_relevant_indexes(cursor: sqlite3.Cursor) -> None:
    cursor.execute(f"DROP INDEX IF EXISTS {NAIVE_INDEX_NAME};")
    cursor.execute(f"DROP INDEX IF EXISTS {EXPRESSION_INDEX_NAME};")


def main() -> None:
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    query = load_peak_hour_query()

    # Ensure a clean slate so "baseline" is genuinely index-free for this benchmark.
    reset_relevant_indexes(cursor)

    print("Benchmarking 01_peak_hour.sql with EXPLAIN QUERY PLAN")
    print("=" * 60)

    # Stage 1: baseline, no relevant index
    print_query_plan(cursor, "1. Baseline (no relevant index)", query)

    # Stage 2: naive plain index on departure_time
    cursor.execute(NAIVE_INDEX)
    print_query_plan(cursor, "2. Naive index on departure_time", query)
    cursor.execute(f"DROP INDEX IF EXISTS {NAIVE_INDEX_NAME};")

    # Stage 3: expression index on SUBSTR(departure_time, 1, 2)
    cursor.execute(EXPRESSION_INDEX)
    print_query_plan(cursor, "3. Expression index on SUBSTR(departure_time, 1, 2)", query)

    # Leave the expression index + supporting indexes in place for normal use.
    for stmt in SUPPORTING_INDEXES:
        cursor.execute(stmt)

    connection.commit()
    connection.close()

    print("\nDone. Expression index + supporting indexes are now in place.")


if __name__ == "__main__":
    main()