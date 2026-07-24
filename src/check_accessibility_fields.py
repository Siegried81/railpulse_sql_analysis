import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "railpulse.db"


def main() -> None:
    with sqlite3.connect(DB_PATH) as connection:
        cursor = connection.cursor()

        print("== trips.wheelchair_accessible value distribution ==")
        cursor.execute(
            "SELECT wheelchair_accessible, COUNT(*) AS n FROM trips GROUP BY wheelchair_accessible;"
        )
        for row in cursor.fetchall():
            print(row)

        print("\n== stops.wheelchair_boarding value distribution ==")
        cursor.execute(
            "SELECT wheelchair_boarding, COUNT(*) AS n FROM stops GROUP BY wheelchair_boarding;"
        )
        for row in cursor.fetchall():
            print(row)

        print("\n== trips.bikes_allowed value distribution ==")
        cursor.execute(
            "SELECT bikes_allowed, COUNT(*) AS n FROM trips GROUP BY bikes_allowed;"
        )
        for row in cursor.fetchall():
            print(row)


if __name__ == "__main__":
    main()