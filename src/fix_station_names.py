import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "railpulse.db"


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE live_departures SET station_name = 'Brussel-Centraal' "
        "WHERE station_name LIKE 'Brussel-Centraal%'"
    )
    conn.commit()
    print(f"Rows updated: {cursor.rowcount}")
    conn.close()


if __name__ == "__main__":
    main()