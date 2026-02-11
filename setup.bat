@echo off
echo ========================================
echo Placement Profile Enricher - Setup
echo ========================================
echo.

echo [1/4] Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

echo [2/4] Activating virtual environment...
call venv\Scripts\activate.bat

echo [3/4] Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo [4/4] Creating sample Excel file...
python create_sample.py

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo To start the server, run: start.bat
echo.
pause
