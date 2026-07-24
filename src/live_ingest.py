import argparse
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "railpulse.db"
API_URL = "https://api.irail.be/liveboard/"

MAJOR_HUBS = [
    "Brussel-Centraal",
    "Antwerpen-Centraal",
    "Gent-Sint-Pieters",
    "Liège-Guillemins",
    "Charleroi-Central",
]


def init_table(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS live_departures (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            pulled_at       TEXT NOT NULL,
            station_id      TEXT NOT NULL,
            station_name    TEXT,
            vehicle_id      TEXT,
            scheduled_time  TEXT,
            delay_seconds   INTEGER,
            platform        TEXT,
            canceled        INTEGER,
            trip_headsign   TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_live_departures_station_time
            ON live_departures (station_id, pulled_at);
        """
    )
    connection.commit()


def fetch_liveboard(station: str):
    params = {"station": station, "format": "json", "lang": "en"}
    headers = {"User-Agent": "RailPulseAnalytics/1.0 (student project; contact@railpulse.local)"}
    response = requests.get(API_URL, params=params, headers=headers, timeout=15)
    if response.status_code != 200:
        print(f"  Warning: {station} failed (HTTP {response.status_code})")
        return None
    return response.json()


def pull_once(connection: sqlite3.Connection) -> int:
    pulled_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    cursor = connection.cursor()
    total = 0

    for station in MAJOR_HUBS:
        data = fetch_liveboard(station)
        if not data:
            continue

        station_info = data.get("stationinfo", {})
        station_id = station_info.get("id", f"BE.NMBS.{station}")
        station_name = station

        for dep in data.get("departures", {}).get("departure", []):
            vehicle_id = dep.get("vehicle", "")
            epoch_time = int(dep.get("time", 0))
            scheduled_time = datetime.fromtimestamp(epoch_time, tz=timezone.utc).isoformat(timespec="seconds")

            cursor.execute(
                """
                INSERT INTO live_departures (
                    pulled_at, station_id, station_name, vehicle_id,
                    scheduled_time, delay_seconds, platform, canceled, trip_headsign
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    pulled_at,
                    station_id,
                    station_name,
                    vehicle_id,
                    scheduled_time,
                    int(dep.get("delay", 0)),
                    str(dep.get("platform", "Unknown")),
                    int(dep.get("cancelled", 0)),
                    dep.get("station", ""),
                ),
            )
            total += 1

        print(f"  {station_name}: {len(data.get('departures', {}).get('departure', []))} departures pulled")

    connection.commit()
    print(f"Snapshot @ {pulled_at} — {total} rows appended.")
    return total


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--loop-demo",
        action="store_true",
        help="Local demo only: pull 3 snapshots with a short pause. Not a real scheduler.",
    )
    args = parser.parse_args()

    (BASE_DIR / "data").mkdir(exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    init_table(connection)

    if args.loop_demo:
        for i in range(3):
            print(f"\n--- demo pull {i + 1}/3 ---")
            pull_once(connection)
            if i < 2:
                time.sleep(30)
    else:
        pull_once(connection)

    connection.close()


if __name__ == "__main__":
    main()