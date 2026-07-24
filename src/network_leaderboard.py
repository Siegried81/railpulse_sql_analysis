import sqlite3
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "railpulse.db"
DOCS_DIR = BASE_DIR / "docs"
OUTPUT_PATH = DOCS_DIR / "network_leaderboard.png"

ON_TIME_THRESHOLD_SECONDS = 60 


def fetch_leaderboard(connection: sqlite3.Connection):
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT
            station_name,
            COUNT(*) AS total_departures,
            ROUND(AVG(delay_seconds), 1) AS avg_delay_seconds,
            ROUND(
                SUM(CASE WHEN delay_seconds <= ? THEN 1 ELSE 0 END) * 100.0 / COUNT(*),
                2
            ) AS on_time_pct
        FROM live_departures
        GROUP BY station_name
        ORDER BY on_time_pct DESC, avg_delay_seconds ASC;
        """,
        (ON_TIME_THRESHOLD_SECONDS,),
    )
    return cursor.fetchall()


def main() -> None:
    connection = sqlite3.connect(DB_PATH)
    rows = fetch_leaderboard(connection)
    connection.close()

    if not rows:
        print(
            "No data in live_departures yet. Run 'python src/live_ingest.py' first "
            "(ideally several times, on different days, to get a meaningful ranking)."
        )
        return

    print(f"\n{'Station':<25} | {'Departures':>10} | {'Avg delay (s)':>13} | {'On-time %':>10}")
    print("-" * 68)
    for station_name, total, avg_delay, on_time_pct in rows:
        print(f"{station_name:<25} | {total:>10} | {avg_delay:>13} | {on_time_pct:>9}%")

    stations = [r[0] for r in rows]
    on_time_pcts = [r[3] for r in rows]

    DOCS_DIR.mkdir(exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(stations, on_time_pcts, color="#2E7D32")
    ax.set_ylabel("On-time departures (%)")
    ax.set_title(f"RailPulse Network Leaderboard — on-time within {ON_TIME_THRESHOLD_SECONDS}s")
    ax.set_ylim(0, 108)
    plt.xticks(rotation=20, ha="right")
    for bar, pct in zip(bars, on_time_pcts):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1.5, f"{pct}%", ha="center", va="bottom")
    plt.tight_layout()
    plt.savefig(OUTPUT_PATH, dpi=150)
    print(f"\nChart saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()