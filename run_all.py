import argparse
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
LOG_DIR = ROOT_DIR / "logs"

def run_script(script_name: str, *args: str, log_file=None) -> None:
    print(f"# Running {script_name}")
    cmd = [sys.executable, str(SRC_DIR / script_name), *args]
    
    if log_file:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"\nRunning {script_name}\n")
            subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, check=True)
    else:
        subprocess.run(cmd, check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--live",
        action="store_true",
        help="Also run live_ingest.py + network_leaderboard.py.",
    )
    parser.add_argument(
        "--save-log",
        action="store_true",
        help="Save execution output to a log file.",
    )
    args = parser.parse_args()

    log_path = None
    if args.save_log:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        log_path = LOG_DIR / "railpulse_results.log"
        print(f"Logging output to: {log_path}")
        
    run_script("run_queries.py", log_file=log_path)
    run_script("optimize_indexes.py", log_file=log_path)
    
    if args.live:
        run_script("live_ingest.py", log_file=log_path)
        run_script("network_leaderboard.py", log_file=log_path)

if __name__ == "__main__":
    main()