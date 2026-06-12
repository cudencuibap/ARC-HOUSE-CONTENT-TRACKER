@echo off
REM ============================================
REM  Arc House Tracker - Launcher cho Windows
REM  Double-click file nay de chay tool
REM ============================================

cd /d "%~dp0"

echo Kiem tra Docker...
docker version >nul 2>&1
if errorlevel 1 (
    echo [LOI] Docker chua chay. Mo Docker Desktop roi thu lai.
    pause
    exit /b 1
)

REM Build image neu chua co (lan dau se hoi lau mot chut)
docker image inspect arc-house-tracker >nul 2>&1
if errorlevel 1 (
    echo Lan dau: dang build Docker image...
    docker compose build
)

echo.
echo Khoi dong Arc House Tracker...
docker compose run --rm arc-tracker

echo.
echo Tool da dong. Hen gap lai!
pause
