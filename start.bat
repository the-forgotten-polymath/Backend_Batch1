@echo off
echo ========================================
echo Starting Placement Profile Enricher API
echo ========================================
echo.

call venv\Scripts\activate.bat

echo Server starting at http://localhost:5000
echo Press Ctrl+C to stop the server
echo.

python app.py
