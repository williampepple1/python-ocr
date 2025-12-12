@echo off
REM Windows batch script to run tests
echo ========================================
echo OCR API Test Runner
echo ========================================
echo.

REM Check if server is running
echo Checking if server is running...
curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo ERROR: Server is not running!
    echo Please start the server first:
    echo   python api.py
    echo   OR
    echo   python run_server.py
    pause
    exit /b 1
)

echo Server is running!
echo.

REM Run tests
if "%1"=="" (
    echo Running basic tests (health check and languages)...
    python test_api.py
) else (
    echo Running tests with image: %1
    python test_api.py %1 %2
)

pause

