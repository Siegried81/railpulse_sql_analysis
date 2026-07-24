import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "railpulse.db"
SQL_DIR = BASE_DIR / "sql"

def run_analysis():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query_files = [
        ("1. Peak Hour Problem", SQL_DIR / "01_peak_hour.sql"),
        ("2. Platform Bottlenecks (Brussels-Central)", SQL_DIR / "02_platform_bottlenecks.sql"),
        ("3. Busiest Morning Destinations", SQL_DIR / "03_busiest_morning_destinations.sql"),
        ("4. Service Frequency Classification (% per category)", SQL_DIR / "04_service_frequency.sql"),
        ("5. Accessibility Audit (wheelchair + bikes, lowest-scoring routes)", SQL_DIR / "05_accessibility_audit.sql"),
        ("6. Network Accessibility Summary", SQL_DIR / "06_network_accessibility_summary.sql"),
    ]

    for title, filepath in query_files:
        print(f"\n==============================================")
        print(f"{title}")
        print(f"==============================================")
        
        if not filepath.exists():
            print(f"File not found: {filepath}")
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            query = f.read()
        
        try:
            cursor.execute(query)
        except sqlite3.OperationalError as e:
            print(f"SQL Error: {e}")
            continue

        rows = cursor.fetchall()
        
        if not rows:
            print("No data available for this query.")
            continue
            
        headers = [description[0] for description in cursor.description]
        print(" | ".join(headers))
        print("-" * 50)
        
        for row in rows[:30]:
            print(" | ".join(str(val) for val in row))
            
        if len(rows) > 30:
            print(f"\n... and {len(rows) - 30} more rows hidden.")

    conn.close()

if __name__ == "__main__":
    run_analysis()