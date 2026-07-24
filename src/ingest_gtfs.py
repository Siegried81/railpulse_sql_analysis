import csv
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "railpulse.db"
DATA_DIR = BASE_DIR / "data" 

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS Agency (
    agency_id TEXT PRIMARY KEY,
    agency_name TEXT,
    agency_url TEXT,
    agency_timezone TEXT,
    agency_lang TEXT,
    agency_phone TEXT,
    agency_fare_url TEXT
);

CREATE TABLE IF NOT EXISTS Routes (
    route_id TEXT PRIMARY KEY,
    agency_id TEXT,
    route_short_name TEXT,
    route_long_name TEXT,
    route_desc TEXT,
    route_type INTEGER,
    route_url TEXT,
    route_color TEXT,
    route_text_color TEXT,
    FOREIGN KEY (agency_id) REFERENCES Agency(agency_id)
);

CREATE TABLE IF NOT EXISTS Calendar (
    service_id TEXT PRIMARY KEY,
    monday INTEGER,
    tuesday INTEGER,
    wednesday INTEGER,
    thursday INTEGER,
    friday INTEGER,
    saturday INTEGER,
    sunday INTEGER,
    start_date TEXT,
    end_date TEXT
);

CREATE TABLE IF NOT EXISTS Calendar_dates (
    service_id TEXT NOT NULL,
    date TEXT NOT NULL,
    exception_type INTEGER,
    PRIMARY KEY (service_id, date),
    FOREIGN KEY (service_id) REFERENCES Calendar(service_id)
);

CREATE TABLE IF NOT EXISTS Trips (
    trip_id TEXT PRIMARY KEY,
    route_id TEXT,
    service_id TEXT,
    trip_headsign TEXT,
    trip_short_name TEXT,
    direction_id INTEGER,
    block_id TEXT,
    shape_id TEXT,
    wheelchair_accessible INTEGER,
    bikes_allowed INTEGER,
    FOREIGN KEY (route_id) REFERENCES Routes(route_id),
    FOREIGN KEY (service_id) REFERENCES Calendar(service_id)
);

CREATE TABLE IF NOT EXISTS Stops (
    stop_id TEXT PRIMARY KEY,
    stop_code TEXT,
    stop_name TEXT,
    stop_desc TEXT,
    stop_lat REAL,
    stop_lon REAL,
    zone_id TEXT,
    stop_url TEXT,
    location_type INTEGER,
    parent_station TEXT,
    wheelchair_boarding TEXT,
    platform_code TEXT
);

CREATE TABLE IF NOT EXISTS Stop_times (
    trip_id TEXT NOT NULL,
    stop_sequence INTEGER NOT NULL,
    stop_id TEXT,
    arrival_time TEXT,
    departure_time TEXT,
    stop_headsign TEXT,
    pickup_type INTEGER,
    drop_off_type INTEGER,
    shape_dist_traveled REAL,
    PRIMARY KEY (trip_id, stop_sequence),
    FOREIGN KEY (trip_id) REFERENCES Trips(trip_id),
    FOREIGN KEY (stop_id) REFERENCES Stops(stop_id)
);

CREATE TABLE IF NOT EXISTS Transfers (
    from_stop_id TEXT NOT NULL,
    to_stop_id TEXT NOT NULL,
    from_trip_id TEXT NOT NULL,
    to_trip_id TEXT NOT NULL,
    transfer_type INTEGER,
    min_transfer_time INTEGER,
    PRIMARY KEY (from_stop_id, to_stop_id, from_trip_id, to_trip_id),
    FOREIGN KEY (from_stop_id) REFERENCES Stops(stop_id),
    FOREIGN KEY (to_stop_id) REFERENCES Stops(stop_id),
    FOREIGN KEY (from_trip_id) REFERENCES Trips(trip_id),
    FOREIGN KEY (to_trip_id) REFERENCES Trips(trip_id)
);

CREATE TABLE IF NOT EXISTS Feed_info (
    feed_id TEXT PRIMARY KEY,
    feed_publisher_name TEXT,
    feed_publisher_url TEXT,
    feed_lang TEXT,
    default_lang TEXT,
    feed_start_date TEXT,
    feed_end_date TEXT,
    feed_version TEXT,
    feed_contact_email TEXT,
    feed_contact_url TEXT
);

CREATE TABLE IF NOT EXISTS Translation (
    table_name TEXT NOT NULL,
    field_name TEXT NOT NULL,
    record_id TEXT NOT NULL,
    record_sub_id TEXT NOT NULL,
    language TEXT NOT NULL,
    field_value TEXT,
    translation TEXT,
    PRIMARY KEY (table_name, field_name, record_id, record_sub_id, language)
);
"""

FILE_MAP = [
    ("Agency", "agency.txt"),
    ("Calendar", "calendar.txt"),
    ("Calendar_dates", "calendar_dates.txt"),
    ("Routes", "routes.txt"),
    ("Stops", "stops.txt"),
    ("Trips", "trips.txt"),
    ("Stop_times", "stop_times.txt"),
    ("Transfers", "transfers.txt"),
    ("Feed_info", "feed_info.txt"),
    ("Translation", "translations.txt"),
]


def create_tables(connection: sqlite3.Connection) -> None:
    connection.executescript(SCHEMA_SQL)
    connection.commit()


def load_csv_rows(connection: sqlite3.Connection, table_name: str, csv_file: Path) -> int:
    with csv_file.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)

    if not rows:
        return 0

    columns = list(rows[0].keys())
    placeholders = ", ".join(["?"] * len(columns))
    column_sql = ", ".join(f'"{c}"' for c in columns)

    connection.executemany(
        f'INSERT OR IGNORE INTO "{table_name}" ({column_sql}) VALUES ({placeholders})',
        [[row.get(c, "") for c in columns] for row in rows],
    )
    return len(rows)


def load_data(connection: sqlite3.Connection) -> None:
    connection.execute("PRAGMA foreign_keys = OFF;")

    for table_name, filename in FILE_MAP:
        csv_file = DATA_DIR / filename
        if not csv_file.exists():
            print(f"Skipped {filename} (not found)")
            continue
        n = load_csv_rows(connection, table_name, csv_file)
        print(f"Loaded {n} rows from {filename} into {table_name}")

    connection.commit()
    connection.execute("PRAGMA foreign_keys = ON;")


def main() -> None:
    (BASE_DIR / "data").mkdir(exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        create_tables(connection)
        load_data(connection)
        print(f"Database ready at {DB_PATH}")
    finally:
        connection.close()


if __name__ == "__main__":
    main()