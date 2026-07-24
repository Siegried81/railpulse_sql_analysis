@echo off
cd /d "D:\Users\Siegried\Desktop\Becode\railpulse_sql_analysis"

call .venv\Scripts\activate.bat

echo [1/3] Running main.py (database setup and import)...
python main.py
if errorlevel 1 (
    echo.
    echo [ERROR] main.py failed! Check the messages above.
    pause
    exit /b %errorlevel%
)

echo.
echo [2/3] Running run_all (from src folder)...
if exist src\run_all.py (
    python src\run_all.py
) else if exist run_all.py (
    python run_all.py
) else (
    echo run_all.py not found in root or src, skipping...
)

echo.
echo [3/3] Launching Streamlit dashboard...
streamlit run dashboard.py

pause