@echo off
REM Windows batch script to start NexLattice dashboard

echo.
echo ====================================
echo   NexLattice Dashboard Launcher
echo ====================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Virtual environment not found. Creating...
    python -m venv venv
    if errorlevel 1 (
        echo Error: Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -q -r requirements.txt
if errorlevel 1 (
    echo Error: Failed to install dependencies
    pause
    exit /b 1
)

REM Start dashboard
echo.
echo Starting NexLattice Dashboard...
echo Dashboard will be available at: http://localhost:8080
echo.
echo Press Ctrl+C to stop the dashboard
echo.

cd dashboard
python app.py

pause

