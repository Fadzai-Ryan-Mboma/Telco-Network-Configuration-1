@echo off
REM Quick Start Script for Liquid Zimbabwe Network Optimizer
REM Powered by Cassava Technologies

echo 🚀 Starting Liquid Zimbabwe Network Optimizer...
echo 📡 Powered by Cassava Technologies
echo.

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not running. Please start Docker and try again.
    pause
    exit /b 1
)

REM Build and start the container
echo 🔨 Building Docker container...
docker-compose build

echo 📊 Starting network optimizer...
docker-compose up -d

REM Wait for container to be ready
echo ⏳ Waiting for application to start...
timeout /t 10 /nobreak >nul

REM Check if container is running
docker-compose ps | findstr "Up" >nul
if %errorlevel% equ 0 (
    echo ✅ Success! Liquid Zimbabwe Network Optimizer is running
    echo.
    echo 🌐 Open your browser and go to: http://localhost:8507
    echo.
    echo 📋 Default Huawei API Credentials:
    echo    - URL: https://41.174.191.214:31127
    echo    - Username: cassava.ai
    echo    - Password: #Pass123#
    echo.
    echo 🔄 To import historical data:
    echo    docker exec telco-network-configuration-telco_ui-1 python import_historical_data.py
    echo.
    echo 🛑 To stop: docker-compose down
) else (
    echo ❌ Failed to start. Check logs with: docker-compose logs
)

pause